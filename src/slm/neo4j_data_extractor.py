"""
Neo4j Data Extractor for SLM Training
Extracts conversation sequences from Neo4j graph database
"""

import json
import logging
from typing import List, Dict, Any, Optional, Tuple, Iterator
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib
from collections import defaultdict

try:
    from neo4j import GraphDatabase
    HAS_NEO4J = True
except ImportError:
    HAS_NEO4J = False
    print("Warning: neo4j package not installed. Some features will be disabled.")

logger = logging.getLogger(__name__)

@dataclass
class ConversationNode:
    """Represents a conversation node in the graph"""
    node_id: str
    message: str
    speaker: str
    timestamp: datetime
    personality_type: Optional[str] = None
    emotional_state: Optional[str] = None
    relationship_type: Optional[str] = None
    context_tags: List[str] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat() if self.timestamp else None
        return data

@dataclass
class ConversationSequence:
    """Represents a sequence of conversation nodes"""
    sequence_id: str
    nodes: List[ConversationNode]
    topic: Optional[str] = None
    participants: List[str] = None
    duration_minutes: Optional[float] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['nodes'] = [node.to_dict() for node in self.nodes]
        return data

@dataclass
class TrainingExample:
    """Training example for the SLM"""
    example_id: str
    input_text: str
    target_text: str
    speaker_name: str
    personality_type: Optional[str] = None
    emotional_state: Optional[str] = None
    relationship_type: Optional[str] = None
    conversation_history: List[Dict[str, str]] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class Neo4jDataExtractor:
    """Extracts conversation data from Neo4j for SLM training"""
    
    def __init__(self, 
                 uri: str,
                 user: str,
                 password: str,
                 database: str = "neo4j"):
        """
        Initialize Neo4j connection
        
        Args:
            uri: Neo4j URI (e.g., "bolt://localhost:7687")
            user: Neo4j username
            password: Neo4j password
            database: Database name
        """
        if not HAS_NEO4J:
            raise ImportError("neo4j package required. Install with: pip install neo4j")
            
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self.driver = None
        self._connect()
        
    def _connect(self):
        """Establish connection to Neo4j"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri, 
                auth=(self.user, self.password)
            )
            # Test connection
            with self.driver.session(database=self.database) as session:
                session.run("RETURN 1")
            logger.info(f"Connected to Neo4j at {self.uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
            
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        
    def extract_conversation_sequences(self,
                                      speaker_filter: Optional[str] = None,
                                      min_sequence_length: int = 2,
                                      max_sequence_length: int = 20,
                                      limit: Optional[int] = None) -> Iterator[ConversationSequence]:
        """
        Extract conversation sequences from Neo4j
        
        Args:
            speaker_filter: Filter by specific speaker
            min_sequence_length: Minimum nodes in sequence
            max_sequence_length: Maximum nodes in sequence
            limit: Maximum sequences to extract
            
        Yields:
            ConversationSequence objects
        """
        query = """
        MATCH (n:Message)-[:FOLLOWS*1..%d]->(m:Message)
        WHERE size((n)-[:FOLLOWS*]->()) >= %d
        %s
        WITH n, collect(m) as following
        RETURN n, following
        %s
        """ % (
            max_sequence_length,
            min_sequence_length - 1,
            f"AND n.speaker = '{speaker_filter}'" if speaker_filter else "",
            f"LIMIT {limit}" if limit else ""
        )
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query)
            
            for record in result:
                start_node = record["n"]
                following_nodes = record["following"]
                
                # Create conversation nodes
                nodes = []
                
                # Add start node
                nodes.append(self._create_conversation_node(start_node))
                
                # Add following nodes
                for node in following_nodes:
                    nodes.append(self._create_conversation_node(node))
                    
                # Create sequence
                sequence = ConversationSequence(
                    sequence_id=self._generate_sequence_id(nodes),
                    nodes=nodes,
                    participants=list(set(n.speaker for n in nodes)),
                    duration_minutes=self._calculate_duration(nodes),
                    metadata={"source": "neo4j"}
                )
                
                yield sequence
                
    def _create_conversation_node(self, neo4j_node: Dict) -> ConversationNode:
        """Convert Neo4j node to ConversationNode"""
        return ConversationNode(
            node_id=str(neo4j_node.id) if hasattr(neo4j_node, 'id') else str(hash(str(neo4j_node))),
            message=neo4j_node.get("message", ""),
            speaker=neo4j_node.get("speaker", "unknown"),
            timestamp=self._parse_timestamp(neo4j_node.get("timestamp")),
            personality_type=neo4j_node.get("personality_type"),
            emotional_state=neo4j_node.get("emotional_state"),
            relationship_type=neo4j_node.get("relationship_type"),
            context_tags=neo4j_node.get("context_tags", []),
            metadata={k: v for k, v in neo4j_node.items() 
                     if k not in ["message", "speaker", "timestamp"]}
        )
        
    def _parse_timestamp(self, timestamp_value: Any) -> Optional[datetime]:
        """Parse timestamp from various formats"""
        if not timestamp_value:
            return None
            
        if isinstance(timestamp_value, datetime):
            return timestamp_value
            
        if isinstance(timestamp_value, str):
            try:
                return datetime.fromisoformat(timestamp_value)
            except:
                pass
                
        # Default to current time if parsing fails
        return datetime.now()
        
    def _generate_sequence_id(self, nodes: List[ConversationNode]) -> str:
        """Generate unique ID for sequence"""
        content = "".join([n.message for n in nodes])
        return hashlib.md5(content.encode()).hexdigest()[:16]
        
    def _calculate_duration(self, nodes: List[ConversationNode]) -> Optional[float]:
        """Calculate duration of conversation in minutes"""
        timestamps = [n.timestamp for n in nodes if n.timestamp]
        if len(timestamps) >= 2:
            duration = (timestamps[-1] - timestamps[0]).total_seconds() / 60
            return round(duration, 2)
        return None
        
    def create_training_examples(self,
                                sequences: List[ConversationSequence],
                                context_window: int = 3,
                                include_speaker_tags: bool = True) -> List[TrainingExample]:
        """
        Create training examples from conversation sequences
        
        Args:
            sequences: List of conversation sequences
            context_window: Number of previous messages to include
            include_speaker_tags: Whether to add speaker tags
            
        Returns:
            List of TrainingExample objects
        """
        examples = []
        
        for sequence in sequences:
            nodes = sequence.nodes
            
            for i in range(1, len(nodes)):
                # Get context messages
                start_idx = max(0, i - context_window)
                context_nodes = nodes[start_idx:i]
                
                # Create conversation history
                history = []
                for node in context_nodes:
                    msg = node.message
                    if include_speaker_tags:
                        msg = f"[{node.speaker}]: {msg}"
                    history.append({
                        "speaker": node.speaker,
                        "message": msg,
                        "emotional_state": node.emotional_state
                    })
                    
                # Current node is the target
                current = nodes[i]
                
                # Previous message is the input
                previous = nodes[i-1]
                input_text = previous.message
                if include_speaker_tags:
                    input_text = f"[{previous.speaker}]: {input_text}"
                    
                target_text = current.message
                if include_speaker_tags:
                    target_text = f"[{current.speaker}]: {target_text}"
                    
                # Create training example
                example = TrainingExample(
                    example_id=f"{sequence.sequence_id}_{i}",
                    input_text=input_text,
                    target_text=target_text,
                    speaker_name=current.speaker,
                    personality_type=current.personality_type,
                    emotional_state=current.emotional_state,
                    relationship_type=current.relationship_type,
                    conversation_history=history,
                    metadata={
                        "sequence_id": sequence.sequence_id,
                        "position": i,
                        "total_length": len(nodes)
                    }
                )
                
                examples.append(example)
                
        return examples
        
    def get_speaker_statistics(self) -> Dict[str, Any]:
        """Get statistics about speakers in the database"""
        query = """
        MATCH (n:Message)
        WITH n.speaker as speaker, 
             count(n) as message_count,
             collect(DISTINCT n.personality_type) as personalities,
             collect(DISTINCT n.emotional_state) as emotions
        RETURN speaker, message_count, personalities, emotions
        ORDER BY message_count DESC
        """
        
        stats = {}
        with self.driver.session(database=self.database) as session:
            result = session.run(query)
            
            for record in result:
                speaker = record["speaker"]
                stats[speaker] = {
                    "message_count": record["message_count"],
                    "personality_types": [p for p in record["personalities"] if p],
                    "emotional_states": [e for e in record["emotions"] if e]
                }
                
        return stats
        
    def export_training_data(self,
                            output_path: str,
                            speaker_filter: Optional[str] = None,
                            max_examples: Optional[int] = None):
        """
        Export training data to JSON file
        
        Args:
            output_path: Path to output JSON file
            speaker_filter: Filter by specific speaker
            max_examples: Maximum examples to export
        """
        # Extract sequences
        sequences = list(self.extract_conversation_sequences(
            speaker_filter=speaker_filter,
            limit=max_examples // 10 if max_examples else None
        ))
        
        # Create training examples
        examples = self.create_training_examples(sequences)
        
        # Limit examples if specified
        if max_examples:
            examples = examples[:max_examples]
            
        # Export to JSON
        data = {
            "metadata": {
                "total_examples": len(examples),
                "total_sequences": len(sequences),
                "speaker_filter": speaker_filter,
                "export_timestamp": datetime.now().isoformat()
            },
            "examples": [e.to_dict() for e in examples]
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
            
        logger.info(f"Exported {len(examples)} training examples to {output_path}")
        return len(examples)

# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Connection parameters
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "your_password"
    
    # Extract and export training data
    with Neo4jDataExtractor(uri, user, password) as extractor:
        # Get speaker statistics
        stats = extractor.get_speaker_statistics()
        print("Speaker Statistics:")
        for speaker, data in stats.items():
            print(f"  {speaker}: {data['message_count']} messages")
            
        # Export training data
        extractor.export_training_data(
            "training_data.json",
            speaker_filter=None,  # Extract all speakers
            max_examples=10000
        )
