"""
Person Entity Deduplication Module
==================================

This module provides functionality to identify, merge, and track duplicate person entities
in a Neo4j knowledge graph while maintaining original mapping for future data loads.

Key Features:
- Fuzzy matching for potential duplicates
- Relationship-aware merging
- Original mapping preservation
- Confidence-based matching
- Audit trail maintenance

Author: Avatar-Engine Project
Created: 2025-08-29
"""

import logging
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from datetime import datetime
import uuid
from neo4j import GraphDatabase
from fuzzywuzzy import fuzz, process
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PersonEntity:
    """Represents a person entity with matching metadata."""
    node_id: str
    name: str
    email: Optional[str] = None
    properties: Dict = None
    relationships: Set[str] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}
        if self.relationships is None:
            self.relationships = set()


@dataclass
class MergeCandidate:
    """Represents a potential merge between two person entities."""
    entity1: PersonEntity
    entity2: PersonEntity
    confidence_score: float
    match_reasons: List[str]
    
    @property
    def is_high_confidence(self) -> bool:
        """Returns True if confidence score indicates a likely match."""
        return self.confidence_score >= 0.8


class PersonEntityMatcher:
    """Handles identification of potential duplicate person entities."""
    
    def __init__(self, neo4j_driver):
        self.driver = neo4j_driver
        self.name_similarity_threshold = 0.8
        self.email_exact_match_weight = 0.9
        
    def find_potential_duplicates(self) -> List[MergeCandidate]:
        """
        Identifies potential duplicate person entities using various matching strategies.
        
        Returns:
            List[MergeCandidate]: List of potential merges with confidence scores
        """
        logger.info("Starting duplicate detection for person entities...")
        
        # Get all person entities
        person_entities = self._get_all_person_entities()
        logger.info(f"Found {len(person_entities)} person entities to analyze")
        
        merge_candidates = []
        
        # Compare each entity with every other entity
        for i, entity1 in enumerate(person_entities):
            for entity2 in person_entities[i+1:]:
                candidate = self._evaluate_match(entity1, entity2)
                if candidate and candidate.confidence_score > 0.6:  # Only keep promising candidates
                    merge_candidates.append(candidate)
        
        # Sort by confidence score (highest first)
        merge_candidates.sort(key=lambda x: x.confidence_score, reverse=True)
        
        logger.info(f"Identified {len(merge_candidates)} potential merge candidates")
        return merge_candidates
    
    def _get_all_person_entities(self) -> List[PersonEntity]:
        """Retrieves all person entities from the Neo4j database."""
        query = """
        MATCH (p:Person)
        OPTIONAL MATCH (p)-[r]-()
        RETURN p.id as id, 
               p.name as name, 
               p.email as email,
               properties(p) as props,
               collect(DISTINCT type(r)) as rel_types
        """
        
        entities = []
        with self.driver.session() as session:
            result = session.run(query)
            for record in result:
                entity = PersonEntity(
                    node_id=record["id"],
                    name=record["name"] or "",
                    email=record["email"],
                    properties=dict(record["props"]),
                    relationships=set(record["rel_types"])
                )
                entities.append(entity)
        
        return entities
    
    def _evaluate_match(self, entity1: PersonEntity, entity2: PersonEntity) -> Optional[MergeCandidate]:
        """
        Evaluates whether two entities are potential duplicates.
        
        Args:
            entity1, entity2: PersonEntity objects to compare
            
        Returns:
            MergeCandidate if potential match, None otherwise
        """
        match_reasons = []
        confidence_components = []
        
        # Name similarity matching
        if entity1.name and entity2.name:
            name_similarity = fuzz.ratio(entity1.name.lower(), entity2.name.lower()) / 100.0
            if name_similarity >= self.name_similarity_threshold:
                match_reasons.append(f"name_similarity_{name_similarity:.2f}")
                confidence_components.append(name_similarity * 0.7)  # Weight name matching
        
        # Exact email matching (if both have emails)
        if entity1.email and entity2.email:
            if entity1.email.lower() == entity2.email.lower():
                match_reasons.append("email_exact_match")
                confidence_components.append(self.email_exact_match_weight)
        
        # Relationship similarity (entities connected to similar people/organizations)
        relationship_similarity = self._calculate_relationship_similarity(entity1, entity2)
        if relationship_similarity > 0.3:
            match_reasons.append(f"relationship_similarity_{relationship_similarity:.2f}")
            confidence_components.append(relationship_similarity * 0.3)
        
        # Calculate overall confidence score
        if confidence_components:
            confidence_score = min(1.0, sum(confidence_components))
            return MergeCandidate(
                entity1=entity1,
                entity2=entity2,
                confidence_score=confidence_score,
                match_reasons=match_reasons
            )
        
        return None
    
    def _calculate_relationship_similarity(self, entity1: PersonEntity, entity2: PersonEntity) -> float:
        """Calculate similarity based on shared relationship types and patterns."""
        if not entity1.relationships or not entity2.relationships:
            return 0.0
        
        # Simple Jaccard similarity for relationship types
        intersection = entity1.relationships.intersection(entity2.relationships)
        union = entity1.relationships.union(entity2.relationships)
        
        return len(intersection) / len(union) if union else 0.0


class PersonEntityMerger:
    """Handles the actual merging of duplicate person entities."""
    
    def __init__(self, neo4j_driver):
        self.driver = neo4j_driver
    
    def merge_entities(self, merge_candidate: MergeCandidate, preserve_original_mapping: bool = True) -> str:
        """
        Merges two person entities while preserving relationships and tracking the merge.
        
        Args:
            merge_candidate: MergeCandidate object containing entities to merge
            preserve_original_mapping: Whether to create mapping records
            
        Returns:
            str: ID of the canonical (merged) entity
        """
        logger.info(f"Merging entities: {merge_candidate.entity1.node_id} -> {merge_candidate.entity2.node_id}")
        
        # Determine canonical entity (keep the one with more complete data)
        canonical_entity = self._select_canonical_entity(merge_candidate.entity1, merge_candidate.entity2)
        duplicate_entity = merge_candidate.entity2 if canonical_entity == merge_candidate.entity1 else merge_candidate.entity1
        
        with self.driver.session() as session:
            with session.begin_transaction() as tx:
                try:
                    # 1. Merge properties
                    self._merge_properties(tx, canonical_entity, duplicate_entity)
                    
                    # 2. Redirect relationships
                    self._redirect_relationships(tx, duplicate_entity.node_id, canonical_entity.node_id)
                    
                    # 3. Create mapping record if requested
                    if preserve_original_mapping:
                        self._create_mapping_record(tx, duplicate_entity.node_id, canonical_entity.node_id, merge_candidate)
                    
                    # 4. Delete duplicate entity
                    self._delete_entity(tx, duplicate_entity.node_id)
                    
                    tx.commit()
                    logger.info(f"Successfully merged entities. Canonical ID: {canonical_entity.node_id}")
                    return canonical_entity.node_id
                    
                except Exception as e:
                    tx.rollback()
                    logger.error(f"Error during merge: {str(e)}")
                    raise
    
    def _select_canonical_entity(self, entity1: PersonEntity, entity2: PersonEntity) -> PersonEntity:
        """Selects which entity should be the canonical one after merge."""
        # Prefer entity with email
        if entity1.email and not entity2.email:
            return entity1
        if entity2.email and not entity1.email:
            return entity2
        
        # Prefer entity with more complete properties
        if len(entity1.properties) > len(entity2.properties):
            return entity1
        elif len(entity2.properties) > len(entity1.properties):
            return entity2
        
        # Default to first entity if equal
        return entity1
    
    def _merge_properties(self, tx, canonical_entity: PersonEntity, duplicate_entity: PersonEntity):
        """Merges properties from duplicate entity into canonical entity."""
        # Build property merge query
        merge_props = {}
        
        # Start with canonical properties
        merge_props.update(canonical_entity.properties)
        
        # Add missing properties from duplicate (don't overwrite existing)
        for key, value in duplicate_entity.properties.items():
            if key not in merge_props or not merge_props[key]:
                merge_props[key] = value
        
        # Update canonical entity with merged properties
        set_clauses = []
        params = {"canonical_id": canonical_entity.node_id}
        
        for key, value in merge_props.items():
            param_key = f"prop_{key}"
            set_clauses.append(f"p.{key} = ${param_key}")
            params[param_key] = value
        
        if set_clauses:
            query = f"""
            MATCH (p:Person {{id: $canonical_id}})
            SET {', '.join(set_clauses)}
            """
            tx.run(query, params)
    
    def _redirect_relationships(self, tx, duplicate_id: str, canonical_id: str):
        """Redirects all relationships from duplicate entity to canonical entity."""
        # Redirect incoming relationships
        tx.run("""
            MATCH (other)-[r]->(duplicate:Person {id: $duplicate_id})
            MATCH (canonical:Person {id: $canonical_id})
            WHERE NOT exists((other)-[]->(canonical))
            CREATE (other)-[new_r:RELATED_TO]->(canonical)
            SET new_r = properties(r)
            DELETE r
        """, {"duplicate_id": duplicate_id, "canonical_id": canonical_id})
        
        # Redirect outgoing relationships  
        tx.run("""
            MATCH (duplicate:Person {id: $duplicate_id})-[r]->(other)
            MATCH (canonical:Person {id: $canonical_id})
            WHERE NOT exists((canonical)-[]->(other))
            CREATE (canonical)-[new_r:RELATED_TO]->(other)
            SET new_r = properties(r)
            DELETE r
        """, {"duplicate_id": duplicate_id, "canonical_id": canonical_id})
    
    def _create_mapping_record(self, tx, duplicate_id: str, canonical_id: str, merge_candidate: MergeCandidate):
        """Creates a mapping record to track the merge operation."""
        mapping_id = str(uuid.uuid4())
        
        tx.run("""
            CREATE (m:EntityMapping {
                mapping_id: $mapping_id,
                original_entity_id: $duplicate_id,
                canonical_entity_id: $canonical_id,
                merge_timestamp: datetime(),
                merge_confidence: $confidence,
                merge_reasons: $reasons,
                source_system: $source
            })
        """, {
            "mapping_id": mapping_id,
            "duplicate_id": duplicate_id,
            "canonical_id": canonical_id,
            "confidence": merge_candidate.confidence_score,
            "reasons": json.dumps(merge_candidate.match_reasons),
            "source": "avatar_engine_deduplication"
        })
    
    def _delete_entity(self, tx, entity_id: str):
        """Deletes the duplicate entity after successful merge."""
        tx.run("MATCH (p:Person {id: $entity_id}) DELETE p", {"entity_id": entity_id})


class PersonDeduplicationEngine:
    """Main orchestrator for person entity deduplication process."""
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.matcher = PersonEntityMatcher(self.driver)
        self.merger = PersonEntityMerger(self.driver)
    
    def run_deduplication(self, auto_merge_threshold: float = 0.9, interactive_mode: bool = True) -> Dict:
        """
        Runs the complete deduplication process.
        
        Args:
            auto_merge_threshold: Confidence threshold for automatic merging
            interactive_mode: Whether to prompt user for merge decisions
            
        Returns:
            Dict with deduplication results and statistics
        """
        logger.info("Starting person entity deduplication process...")
        
        # Step 1: Find potential duplicates
        candidates = self.matcher.find_potential_duplicates()
        
        if not candidates:
            logger.info("No duplicate candidates found.")
            return {"status": "completed", "merges_performed": 0, "candidates_found": 0}
        
        # Step 2: Process merge candidates
        auto_merges = []
        manual_review = []
        
        for candidate in candidates:
            if candidate.confidence_score >= auto_merge_threshold:
                auto_merges.append(candidate)
            else:
                manual_review.append(candidate)
        
        # Step 3: Perform automatic merges
        merged_count = 0
        for candidate in auto_merges:
            try:
                self.merger.merge_entities(candidate)
                merged_count += 1
                logger.info(f"Auto-merged entities with confidence {candidate.confidence_score:.2f}")
            except Exception as e:
                logger.error(f"Failed to auto-merge entities: {str(e)}")
        
        # Step 4: Handle manual review candidates
        if interactive_mode and manual_review:
            logger.info(f"{len(manual_review)} candidates require manual review")
            # In a real implementation, you'd present these to the user
            # For now, we'll just log them
            for candidate in manual_review:
                logger.info(f"Manual review needed: {candidate.entity1.name} vs {candidate.entity2.name} "
                          f"(confidence: {candidate.confidence_score:.2f})")
        
        return {
            "status": "completed",
            "candidates_found": len(candidates),
            "auto_merges": merged_count,
            "manual_review_count": len(manual_review),
            "manual_review_candidates": manual_review if interactive_mode else []
        }
    
    def get_mapping_by_original_id(self, original_id: str) -> Optional[str]:
        """
        Retrieves the canonical entity ID for a given original entity ID.
        
        Args:
            original_id: The original entity ID to look up
            
        Returns:
            str: Canonical entity ID if mapping exists, None otherwise
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (m:EntityMapping {original_entity_id: $original_id})
                RETURN m.canonical_entity_id as canonical_id
                ORDER BY m.merge_timestamp DESC
                LIMIT 1
            """, {"original_id": original_id})
            
            record = result.single()
            return record["canonical_id"] if record else None
    
    def close(self):
        """Closes the Neo4j driver connection."""
        self.driver.close()


if __name__ == "__main__":
    # Example usage
    import os
    
    # Configuration (these should be environment variables in production)
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
    
    # Initialize deduplication engine
    engine = PersonDeduplicationEngine(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    
    try:
        # Run deduplication process
        results = engine.run_deduplication(
            auto_merge_threshold=0.9,
            interactive_mode=True
        )
        
        print(f"Deduplication completed: {results}")
        
    finally:
        engine.close()
