"""
Neo4j Graph Builder for Avatar-Engine
Handles database operations for persons and nicknames
Last Updated: September 29, 2025
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from loguru import logger

# Try to import Neo4j driver
try:
    from neo4j import GraphDatabase, Transaction
    from neo4j.exceptions import ServiceUnavailable, AuthError
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logger.warning("Neo4j driver not available. Install with: pip3 install neo4j")

# Try to import retry library
try:
    from tenacity import retry, stop_after_attempt, wait_exponential
    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False
    logger.info("Tenacity not available for retry logic. Install with: pip3 install tenacity")
    # Create a dummy decorator
    def retry(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

from models.graph_models import Person, Nickname, NicknameRelationship, NicknameSource


class GraphBuilder:
    """Build and manage the Neo4j knowledge graph"""
    
    def __init__(self, uri: str = None, username: str = None, password: str = None):
        """
        Initialize Neo4j connection
        
        Args:
            uri: Neo4j URI (defaults to env variable NEO4J_URI)
            username: Neo4j username (defaults to env variable NEO4J_USERNAME)
            password: Neo4j password (defaults to env variable NEO4J_PASSWORD)
        """
        if not NEO4J_AVAILABLE:
            raise ImportError("Neo4j driver is required. Install with: pip3 install neo4j")
        
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.username = username or os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD")
        
        if not self.password:
            logger.warning("Neo4j password not provided.")
            logger.warning("Set NEO4J_PASSWORD environment variable or pass it as parameter.")
            logger.warning("You can also add it to a .env file in the project root.")
            raise ValueError("Neo4j password not provided. Set NEO4J_PASSWORD environment variable.")
        
        self.driver = None
        self._connect()

    def _connect(self):
        """Establish connection to Neo4j"""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            self._verify_connection()
            self._create_indexes()
            logger.info(f"Connected to Neo4j at {self.uri}")
        except ServiceUnavailable as e:
            logger.error(f"Neo4j is not running at {self.uri}")
            logger.error("Please start Neo4j with: neo4j start")
            logger.error("Or use Neo4j Desktop/AuraDB")
            raise
        except AuthError as e:
            logger.error(f"Neo4j authentication failed for user '{self.username}'")
            logger.error("Check your password and username")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    def _verify_connection(self):
        """Verify Neo4j connection"""
        with self.driver.session() as session:
            result = session.run("RETURN 1 AS num")
            record = result.single()
            if record["num"] != 1:
                raise ConnectionError("Failed to verify Neo4j connection")

    def _create_indexes(self):
        """Create necessary indexes and constraints"""
        with self.driver.session() as session:
            try:
                # Try modern constraint syntax first
                session.run("""
                    CREATE CONSTRAINT person_id_unique IF NOT EXISTS
                    FOR (p:Person) REQUIRE p.id IS UNIQUE
                """)
            except:
                try:
                    # Fall back to older syntax
                    session.run("""
                        CREATE CONSTRAINT ON (p:Person)
                        ASSERT p.id IS UNIQUE
                    """)
                except:
                    # Constraint might already exist
                    pass
            
            # Create indexes
            try:
                session.run("""
                    CREATE INDEX nickname_name_index IF NOT EXISTS
                    FOR (n:Nickname) ON (n.name)
                """)
                
                session.run("""
                    CREATE INDEX person_fullname_index IF NOT EXISTS
                    FOR (p:Person) ON (p.full_name)
                """)
            except:
                # Indexes might already exist
                pass
            
            logger.debug("Neo4j indexes and constraints created/verified")

    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)) if TENACITY_AVAILABLE else lambda f: f
    def create_person(self, person: Person) -> str:
        """
        Create or update a Person node in the graph
        
        Args:
            person: Person object to create/update
            
        Returns:
            Person ID
        """
        with self.driver.session() as session:
            # Generate ID if not provided
            if not person.id:
                import uuid
                person.id = str(uuid.uuid4())
            
            # First create/update the Person node
            person_data = person.to_neo4j_dict()
            
            result = session.run("""
                MERGE (p:Person {id: $id})
                SET p += $properties
                RETURN p.id AS person_id
            """, id=person.id, properties=person_data)
            
            person_id = result.single()["person_id"]
            
            # Then create nickname relationships
            for nickname in person.nicknames:
                self._create_nickname_relationship(session, person_id, nickname)
            
            logger.info(f"Created/updated person: {person.full_name} with {len(person.nicknames)} nicknames")
            return person_id

    def _create_nickname_relationship(self, session, person_id: str, nickname: Nickname):
        """Create a Nickname node and KNOWN_AS relationship"""
        nickname_data = nickname.to_neo4j_dict()
        
        session.run("""
            MATCH (p:Person {id: $person_id})
            MERGE (n:Nickname {name: $nickname_name})
            SET n += $nickname_properties
            MERGE (p)-[r:KNOWN_AS]->(n)
            SET r.created_at = COALESCE(r.created_at, $created_at),
                r.confidence = $confidence,
                r.source = $source
        """, 
        person_id=person_id,
        nickname_name=nickname.name,
        nickname_properties=nickname_data,
        created_at=datetime.now().isoformat(),
        confidence=nickname.confidence,
        source=nickname.source.value
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)) if TENACITY_AVAILABLE else lambda f: f
    def add_nickname_to_person(
        self, 
        person_id: str, 
        nickname: Nickname,
        update_if_exists: bool = True
    ) -> bool:
        """
        Add a nickname to an existing person
        
        Args:
            person_id: ID of the person
            nickname: Nickname to add
            update_if_exists: Whether to update existing nickname
            
        Returns:
            True if successful
        """
        with self.driver.session() as session:
            # Check if person exists
            result = session.run("""
                MATCH (p:Person {id: $person_id})
                RETURN p
            """, person_id=person_id)
            
            if not result.single():
                logger.error(f"Person with ID {person_id} not found")
                return False
            
            # Check if nickname relationship exists
            existing = session.run("""
                MATCH (p:Person {id: $person_id})-[r:KNOWN_AS]->(n:Nickname {name: $nickname_name})
                RETURN r, n
            """, person_id=person_id, nickname_name=nickname.name).single()
            
            if existing and not update_if_exists:
                logger.debug(f"Nickname '{nickname.name}' already exists for person {person_id}")
                return True
            
            # Create or update the nickname
            self._create_nickname_relationship(session, person_id, nickname)
            logger.info(f"Added nickname '{nickname.name}' to person {person_id}")
            return True

    def find_person_by_nickname(self, nickname: str) -> List[Dict[str, Any]]:
        """
        Find all persons with a specific nickname
        
        Args:
            nickname: The nickname to search for
            
        Returns:
            List of person records with confidence scores
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Person)-[r:KNOWN_AS]->(n:Nickname)
                WHERE toLower(n.name) = toLower($nickname)
                RETURN p AS person, 
                       r.confidence AS confidence,
                       r.source AS source,
                       n AS nickname
                ORDER BY r.confidence DESC
            """, nickname=nickname)
            
            persons = []
            for record in result:
                persons.append({
                    'person': dict(record['person']),
                    'confidence': record['confidence'],
                    'source': record['source'],
                    'nickname': dict(record['nickname'])
                })
            
            return persons

    def get_person_with_nicknames(self, person_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a person with all their nicknames
        
        Args:
            person_id: ID of the person
            
        Returns:
            Person data with nicknames
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Person {id: $person_id})
                OPTIONAL MATCH (p)-[r:KNOWN_AS]->(n:Nickname)
                RETURN p AS person,
                       collect({
                           nickname: n,
                           confidence: r.confidence,
                           source: r.source
                       }) AS nicknames
            """, person_id=person_id)
            
            record = result.single()
            if not record:
                return None
            
            return {
                'person': dict(record['person']),
                'nicknames': record['nicknames']
            }

    def merge_duplicate_persons(self, person1_id: str, person2_id: str, keep_id: str = None):
        """
        Merge two person nodes that represent the same person
        
        Args:
            person1_id: ID of first person
            person2_id: ID of second person  
            keep_id: Which ID to keep (defaults to person1_id)
        """
        keep_id = keep_id or person1_id
        remove_id = person2_id if keep_id == person1_id else person1_id
        
        with self.driver.session() as session:
            # Transfer all relationships from remove_id to keep_id
            session.run("""
                MATCH (remove:Person {id: $remove_id})
                MATCH (keep:Person {id: $keep_id})
                OPTIONAL MATCH (remove)-[r:KNOWN_AS]->(n:Nickname)
                FOREACH (ignored IN CASE WHEN r IS NOT NULL THEN [1] ELSE [] END |
                    MERGE (keep)-[new_r:KNOWN_AS]->(n)
                    SET new_r += properties(r)
                )
                DETACH DELETE remove
            """, remove_id=remove_id, keep_id=keep_id)
            
            logger.info(f"Merged person {remove_id} into {keep_id}")

    def find_similar_persons(self, person: Person, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Find persons similar to the given person based on names and nicknames
        
        Args:
            person: Person to compare
            threshold: Similarity threshold (0-1)
            
        Returns:
            List of similar persons with similarity scores
        """
        with self.driver.session() as session:
            # Get all persons and their nicknames
            all_names = person.get_all_names()
            
            # Use Cypher to find similar persons
            result = session.run("""
                MATCH (p:Person)
                WHERE p.id <> $person_id
                OPTIONAL MATCH (p)-[:KNOWN_AS]->(n:Nickname)
                WITH p, collect(n.name) AS nicknames
                WITH p, 
                     [p.full_name, p.first_name, p.last_name] + nicknames AS all_names
                WITH p, 
                     [name IN all_names WHERE name IN $search_names] AS matches
                WHERE size(matches) > 0
                RETURN p AS person,
                       toFloat(size(matches)) / toFloat(size($search_names)) AS similarity
                ORDER BY similarity DESC
            """, person_id=person.id, search_names=all_names)
            
            similar_persons = []
            for record in result:
                similarity = record['similarity']
                if similarity >= threshold:
                    similar_persons.append({
                        'person': dict(record['person']),
                        'similarity': similarity
                    })
            
            return similar_persons

    def get_statistics(self) -> Dict[str, int]:
        """Get graph statistics"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Person)
                WITH count(p) AS person_count
                MATCH (n:Nickname)
                WITH person_count, count(n) AS nickname_count
                MATCH (:Person)-[r:KNOWN_AS]->(:Nickname)
                RETURN person_count, 
                       nickname_count,
                       count(r) AS relationship_count
            """)
            
            record = result.single()
            if record:
                return {
                    'persons': record['person_count'],
                    'nicknames': record['nickname_count'],
                    'relationships': record['relationship_count']
                }
            else:
                return {
                    'persons': 0,
                    'nicknames': 0,
                    'relationships': 0
                }

    def export_graph(self, format: str = "cypher") -> str:
        """
        Export the graph in various formats
        
        Args:
            format: Export format ('cypher', 'json')
            
        Returns:
            Exported data as string
        """
        with self.driver.session() as session:
            if format == "cypher":
                # Export as Cypher CREATE statements
                persons = session.run("MATCH (p:Person) RETURN p")
                nicknames = session.run("MATCH (n:Nickname) RETURN n")
                relationships = session.run("""
                    MATCH (p:Person)-[r:KNOWN_AS]->(n:Nickname)
                    RETURN p.id AS person_id, n.name AS nickname_name, properties(r) AS props
                """)
                
                export_lines = ["// Avatar-Engine Graph Export\n"]
                
                # Export persons
                export_lines.append("// Persons")
                for record in persons:
                    props = dict(record['p'])
                    props_str = ", ".join([f"{k}: '{v}'" for k, v in props.items() if v])
                    export_lines.append(f"CREATE (p:Person {{{props_str}}})")
                
                # Export nicknames
                export_lines.append("\n// Nicknames")
                for record in nicknames:
                    props = dict(record['n'])
                    props_str = ", ".join([f"{k}: '{v}'" for k, v in props.items() if v])
                    export_lines.append(f"CREATE (n:Nickname {{{props_str}}})")
                
                # Export relationships
                export_lines.append("\n// Relationships")
                for record in relationships:
                    export_lines.append(
                        f"MATCH (p:Person {{id: '{record['person_id']}'}}), "
                        f"(n:Nickname {{name: '{record['nickname_name']}'}}) "
                        f"CREATE (p)-[:KNOWN_AS]->(n)"
                    )
                
                return "\n".join(export_lines)
            
            elif format == "json":
                import json
                
                result = session.run("""
                    MATCH (p:Person)
                    OPTIONAL MATCH (p)-[r:KNOWN_AS]->(n:Nickname)
                    RETURN p AS person,
                           collect({
                               nickname: n,
                               relationship: properties(r)
                           }) AS nicknames
                """)
                
                data = []
                for record in result:
                    person_data = dict(record['person'])
                    person_data['nicknames'] = record['nicknames']
                    data.append(person_data)
                
                return json.dumps(data, indent=2, default=str)
            
            else:
                raise ValueError(f"Unsupported export format: {format}")

    def clear_graph(self):
        """Clear all nodes and relationships (use with caution!)"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            logger.warning("Graph cleared - all nodes and relationships deleted")
