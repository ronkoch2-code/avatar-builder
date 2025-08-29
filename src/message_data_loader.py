#!/usr/bin/env python3
"""
Message Data Loader for Avatar-Engine
======================================

This module integrates message loading functionality from the iMessage Autoprocessor
into the Avatar-Engine system, providing a unified pipeline for:
1. Loading message data from SQLite/JSON sources
2. Cleaning and processing message text
3. Creating Person, Message, and GroupChat nodes in Neo4j
4. Establishing relationships between entities

Author: Avatar-Engine Integration
Date: 2025-01-10
"""

import json
import sqlite3
import re
import logging
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import unicodedata
from datetime import datetime
from neo4j import GraphDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from src.config_manager import ConfigManager
except ImportError:
    # Fallback configuration
    class ConfigManager:
        def __init__(self):
            self.neo4j = type('obj', (object,), {
                'uri': os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                'username': os.getenv("NEO4J_USERNAME", "neo4j"),
                'password': os.getenv("NEO4J_PASSWORD", ""),
                'database': os.getenv("NEO4J_DATABASE", "neo4j")
            })()


class MessageCleaner:
    """Clean and process message text"""
    
    @staticmethod
    def clean_message_body(raw_body: str) -> str:
        """Enhanced message body cleaning"""
        if not raw_body:
            return ""
        
        # Remove control characters and replacement chars
        cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', raw_body)
        cleaned = cleaned.replace('\ufffd', '')
        
        # Remove Apple binary patterns
        binary_patterns = [
            r'bplist00.*?(?=\w|\s|$)',
            r'NS\w+\x00*',
            r'\$\w+\x00*', 
            r'__kIM\w+.*?\x00*',
            r'NSDictionary\x00*',
            r'NSData\x00*',
            r'DDScannerResult\x00*',
        ]
        
        for pattern in binary_patterns:
            cleaned = re.sub(pattern, '', cleaned)
        
        # Extract meaningful text
        text_segments = []
        current_segment = ""
        
        for char in cleaned:
            if char.isprintable() or char.isspace():
                current_segment += char
            else:
                if current_segment.strip():
                    segment = current_segment.strip()
                    # Remove artifacts
                    segment = re.sub(r'^[+\*\d\s\x01\x02\x03]+', '', segment)
                    segment = re.sub(r'[iI]+[\d,\*\s]*$', '', segment)
                    segment = re.sub(r'[\*,\s]+$', '', segment)
                    if len(segment) > 3:
                        text_segments.append(segment)
                current_segment = ""
        
        if current_segment.strip():
            segment = current_segment.strip()
            segment = re.sub(r'^[+\*\d\s\x01\x02\x03]+', '', segment)
            segment = re.sub(r'[iI]+[\d,\*\s]*$', '', segment)
            segment = re.sub(r'[\*,\s]+$', '', segment)
            if len(segment) > 3:
                text_segments.append(segment)
        
        if not text_segments:
            return ""
        
        result = ' '.join(text_segments)
        result = re.sub(r'\s+', ' ', result).strip()
        result = unicodedata.normalize('NFC', result)
        
        return result if len(result) > 3 else ""


class MessageDataLoader:
    """Load message data into Neo4j for Avatar-Engine"""
    
    def __init__(self, neo4j_driver=None, config=None):
        """Initialize the data loader"""
        if neo4j_driver:
            self.driver = neo4j_driver
        else:
            if not config:
                config_manager = ConfigManager()
                config = config_manager.neo4j
            
            self.driver = GraphDatabase.driver(
                config.uri,
                auth=(config.username, config.password)
            )
        
        self.cleaner = MessageCleaner()
        self.batch_size = 1000
        self.stats = {
            'persons_created': 0,
            'messages_created': 0,
            'groups_created': 0,
            'relationships_created': 0,
            'errors': 0
        }
    
    def load_from_sqlite(self, db_path: str, limit: Optional[int] = None) -> Dict:
        """
        Load messages from SQLite database
        
        Args:
            db_path: Path to SQLite database
            limit: Optional limit on number of messages to process
            
        Returns:
            Dictionary with loading statistics
        """
        logger.info(f"Loading messages from SQLite: {db_path}")
        
        if not Path(db_path).exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
        
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Get messages with cleaned body if available, otherwise clean on the fly
            query = """
                SELECT rowid, date, 
                       COALESCE(cleaned_body, body) as body,
                       phone_number, is_from_me, 
                       cache_roomname, group_chat_name,
                       first_name, last_name
                FROM messages 
                WHERE (cleaned_body IS NOT NULL AND cleaned_body != '')
                   OR (body IS NOT NULL AND body != '')
                ORDER BY rowid
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor = conn.execute(query)
            
            batch = []
            total_processed = 0
            
            for row in cursor:
                message_data = dict(row)
                
                # Clean the message body if needed
                if 'cleaned_body' not in message_data or not message_data.get('cleaned_body'):
                    message_data['cleaned_body'] = self.cleaner.clean_message_body(
                        message_data.get('body', '')
                    )
                
                # Skip if no meaningful content
                if not message_data['cleaned_body'] or len(message_data['cleaned_body']) < 3:
                    continue
                
                batch.append(message_data)
                
                # Process batch when it reaches batch_size
                if len(batch) >= self.batch_size:
                    self._process_batch(batch)
                    total_processed += len(batch)
                    logger.info(f"Processed {total_processed} messages")
                    batch = []
            
            # Process remaining messages
            if batch:
                self._process_batch(batch)
                total_processed += len(batch)
        
        logger.info(f"Loading complete. Total messages processed: {total_processed}")
        return self.stats
    
    def load_from_json(self, json_path: str, limit: Optional[int] = None) -> Dict:
        """
        Load messages from JSON file
        
        Args:
            json_path: Path to JSON file
            limit: Optional limit on number of messages to process
            
        Returns:
            Dictionary with loading statistics
        """
        logger.info(f"Loading messages from JSON: {json_path}")
        
        if not Path(json_path).exists():
            raise FileNotFoundError(f"JSON file not found: {json_path}")
        
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        messages = data if isinstance(data, list) else data.get('messages', [])
        
        if limit:
            messages = messages[:limit]
        
        batch = []
        total_processed = 0
        
        for msg in messages:
            # Clean the message body
            msg['cleaned_body'] = self.cleaner.clean_message_body(
                msg.get('body', msg.get('text', ''))
            )
            
            # Skip if no meaningful content
            if not msg['cleaned_body'] or len(msg['cleaned_body']) < 3:
                continue
            
            # Standardize field names
            if 'text' in msg and 'body' not in msg:
                msg['body'] = msg['text']
            
            batch.append(msg)
            
            # Process batch when it reaches batch_size
            if len(batch) >= self.batch_size:
                self._process_batch(batch)
                total_processed += len(batch)
                logger.info(f"Processed {total_processed} messages")
                batch = []
        
        # Process remaining messages
        if batch:
            self._process_batch(batch)
            total_processed += len(batch)
        
        logger.info(f"Loading complete. Total messages processed: {total_processed}")
        return self.stats
    
    def _process_batch(self, messages: List[Dict]) -> None:
        """Process a batch of messages and load into Neo4j"""
        
        # Prepare Neo4j data
        persons = {}
        groups = {}
        neo4j_messages = []
        
        for msg in messages:
            # Extract person info
            phone = (msg.get('phone_number', '') or '').strip()
            if phone and phone != 'Me':
                person_id = f"person_{phone.replace('+', '').replace('-', '').replace(' ', '')}"
                first_name = (msg.get('first_name', '') or '').strip()
                last_name = (msg.get('last_name', '') or '').strip()
                name = f"{first_name} {last_name}".strip() if (first_name or last_name) else phone
                
                persons[person_id] = {
                    'id': person_id,
                    'phone': phone,
                    'name': name
                }
            
            # Extract group info
            group_id = None
            cache_roomname = (msg.get('cache_roomname', '') or '').strip()
            if cache_roomname:
                group_id = f"group_{cache_roomname}"
                group_name = (msg.get('group_chat_name', '') or '').strip() or cache_roomname
                
                groups[group_id] = {
                    'id': group_id,
                    'name': group_name
                }
            
            # Prepare message
            message_id = f"msg_{msg.get('rowid', hash(str(msg)))}"
            neo4j_messages.append({
                'id': message_id,
                'body': msg['cleaned_body'],
                'date': msg.get('date', ''),
                'isFromMe': bool(msg.get('is_from_me', 0)),
                'groupChat': group_id,
                'person': person_id if phone and phone != 'Me' else None
            })
        
        # Load into Neo4j
        try:
            with self.driver.session() as session:
                # Create persons
                if persons:
                    session.run("""
                        UNWIND $persons as person
                        MERGE (p:Person {id: person.id})
                        SET p.phone = person.phone,
                            p.name = person.name
                    """, persons=list(persons.values()))
                    self.stats['persons_created'] += len(persons)
                
                # Create groups
                if groups:
                    session.run("""
                        UNWIND $groups as group
                        MERGE (g:GroupChat {id: group.id})
                        SET g.name = group.name
                    """, groups=list(groups.values()))
                    self.stats['groups_created'] += len(groups)
                
                # Create messages and relationships
                for msg in neo4j_messages:
                    # Create message
                    session.run("""
                        MERGE (m:Message {id: $id})
                        SET m.body = $body,
                            m.date = $date,
                            m.isFromMe = $isFromMe
                    """, **msg)
                    
                    # Create SENT relationship
                    if msg.get('person'):
                        session.run("""
                            MATCH (p:Person {id: $person_id})
                            MATCH (m:Message {id: $message_id})
                            MERGE (p)-[:SENT]->(m)
                        """, person_id=msg['person'], message_id=msg['id'])
                        self.stats['relationships_created'] += 1
                    
                    # Create SENT_TO relationship
                    if msg.get('groupChat'):
                        session.run("""
                            MATCH (m:Message {id: $message_id})
                            MATCH (g:GroupChat {id: $group_id})
                            MERGE (m)-[:SENT_TO]->(g)
                        """, message_id=msg['id'], group_id=msg['groupChat'])
                        self.stats['relationships_created'] += 1
                        
                        # Create MEMBER_OF relationship
                        if msg.get('person'):
                            session.run("""
                                MATCH (p:Person {id: $person_id})
                                MATCH (g:GroupChat {id: $group_id})
                                MERGE (p)-[:MEMBER_OF]->(g)
                            """, person_id=msg['person'], group_id=msg['groupChat'])
                
                self.stats['messages_created'] += len(neo4j_messages)
                
        except Exception as e:
            logger.error(f"Error processing batch: {e}")
            self.stats['errors'] += 1


def main():
    """Command line interface for message data loading"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Load message data into Neo4j for Avatar-Engine")
    parser.add_argument("source", help="Path to SQLite database or JSON file")
    parser.add_argument("--type", choices=['sqlite', 'json', 'auto'], default='auto',
                       help="Source type (auto-detect by default)")
    parser.add_argument("--limit", type=int, help="Limit number of messages to process")
    parser.add_argument("--neo4j-uri", default="bolt://localhost:7687", help="Neo4j URI")
    parser.add_argument("--username", default="neo4j", help="Neo4j username")
    parser.add_argument("--password", required=True, help="Neo4j password")
    
    args = parser.parse_args()
    
    # Auto-detect source type
    if args.type == 'auto':
        source_path = Path(args.source)
        if source_path.suffix == '.json':
            source_type = 'json'
        elif source_path.suffix in ['.db', '.sqlite', '.sqlite3']:
            source_type = 'sqlite'
        else:
            # Try to detect by content
            try:
                with open(args.source, 'r') as f:
                    json.load(f)
                source_type = 'json'
            except:
                source_type = 'sqlite'
    else:
        source_type = args.type
    
    # Create config
    config = type('Config', (), {
        'uri': args.neo4j_uri,
        'username': args.username,
        'password': args.password,
        'database': 'neo4j'
    })()
    
    # Initialize loader
    loader = MessageDataLoader(config=config)
    
    # Load data
    try:
        if source_type == 'json':
            stats = loader.load_from_json(args.source, limit=args.limit)
        else:
            stats = loader.load_from_sqlite(args.source, limit=args.limit)
        
        print("\nLoading Complete!")
        print("=" * 50)
        for key, value in stats.items():
            print(f"{key}: {value}")
        
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
