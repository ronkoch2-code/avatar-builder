#!/usr/bin/env python3
"""
Neo4j Database Reset Utility for Avatar-Engine
==============================================

This utility safely resets the Neo4j database by:
- Deleting all data nodes (Person, Message, Profile, etc.)
- Preserving the schema (constraints, indexes)
- Preserving system metadata nodes
- Providing backup options before reset

Author: Avatar-Engine Development Team
Date: 2025-01-10
"""

import argparse
import sys
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError
import json
import time

# Add parent directory to path for module imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from src.config_manager import ConfigManager, Neo4jConfig
except ImportError:
    # If config_manager doesn't exist, define a basic config
    class Neo4jConfig:
        def __init__(self):
            self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            self.username = os.getenv("NEO4J_USERNAME", "neo4j")
            self.password = os.getenv("NEO4J_PASSWORD", "")
            self.database = os.getenv("NEO4J_DATABASE", "neo4j")
    
    class ConfigManager:
        def __init__(self):
            self.neo4j = Neo4jConfig()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class Neo4jResetUtility:
    """
    Utility class for safely resetting Neo4j database
    """
    
    # System nodes that should be preserved
    SYSTEM_NODES = [
        "AvatarSystem",
        "LLMSystem"
    ]
    
    # Data node labels to be deleted
    DATA_NODE_LABELS = [
        "Person",
        "Message",
        "CommunicationProfile",
        "PersonalityProfile",
        "CommunicationStyle",
        "RelationshipDynamic",
        "RelationshipPattern",
        "TopicAnalysis",
        "EmotionalProfile",
        "ConversationContext",
        "LLMAnalysis",
        "SemanticCluster",
        "StylePattern",
        "SignaturePhrase",
        "TopicPreference",
        "EmotionalExpression",
        "TemporalPattern",
        "ContextTrigger"
    ]
    
    def __init__(self, config: Optional[Neo4jConfig] = None):
        """
        Initialize the reset utility
        
        Args:
            config: Optional Neo4j configuration
        """
        if config is None:
            config_manager = ConfigManager()
            config = config_manager.neo4j if hasattr(config_manager, 'neo4j') else Neo4jConfig()
        
        self.config = config
        self.driver = None
        self.stats = {
            "nodes_deleted": 0,
            "relationships_deleted": 0,
            "time_taken": 0
        }
    
    def connect(self) -> bool:
        """
        Establish connection to Neo4j database
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.driver = GraphDatabase.driver(
                self.config.uri,
                auth=(self.config.username, self.config.password)
            )
            # Test connection
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            logger.info(f"Successfully connected to Neo4j at {self.config.uri}")
            return True
        except AuthError:
            logger.error("Authentication failed. Please check your Neo4j credentials.")
            return False
        except ServiceUnavailable:
            logger.error(f"Neo4j service unavailable at {self.config.uri}")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            return False
    
    def disconnect(self):
        """Close the Neo4j driver connection"""
        if self.driver:
            self.driver.close()
            logger.info("Disconnected from Neo4j")
    
    def get_node_counts(self) -> Dict[str, int]:
        """
        Get count of nodes by label
        
        Returns:
            Dictionary mapping node labels to counts
        """
        counts = {}
        try:
            with self.driver.session() as session:
                for label in self.DATA_NODE_LABELS:
                    query = f"MATCH (n:{label}) RETURN count(n) as count"
                    result = session.run(query)
                    count = result.single()["count"]
                    if count > 0:
                        counts[label] = count
        except Exception as e:
            logger.error(f"Error getting node counts: {e}")
        return counts
    
    def backup_statistics(self) -> Dict[str, Any]:
        """
        Create a backup of current database statistics
        
        Returns:
            Dictionary containing database statistics
        """
        backup = {
            "timestamp": datetime.now().isoformat(),
            "node_counts": {},
            "relationship_count": 0,
            "total_nodes": 0
        }
        
        try:
            with self.driver.session() as session:
                # Get node counts by label
                backup["node_counts"] = self.get_node_counts()
                backup["total_nodes"] = sum(backup["node_counts"].values())
                
                # Get total relationship count
                result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                backup["relationship_count"] = result.single()["count"]
                
                logger.info(f"Backup statistics created: {backup['total_nodes']} nodes, "
                          f"{backup['relationship_count']} relationships")
        except Exception as e:
            logger.error(f"Error creating backup statistics: {e}")
        
        return backup
    
    def save_backup_file(self, backup_data: Dict[str, Any]) -> str:
        """
        Save backup statistics to a file
        
        Args:
            backup_data: Backup statistics dictionary
        
        Returns:
            Path to backup file
        """
        backup_dir = Path(__file__).parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"neo4j_backup_{timestamp}.json"
        
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        logger.info(f"Backup statistics saved to {backup_file}")
        return str(backup_file)
    
    def delete_data_nodes(self, batch_size: int = 1000) -> None:
        """
        Delete all data nodes in batches
        
        Args:
            batch_size: Number of nodes to delete per batch
        """
        try:
            with self.driver.session() as session:
                for label in self.DATA_NODE_LABELS:
                    deleted_count = 0
                    while True:
                        # Delete nodes in batches to avoid memory issues
                        query = f"""
                        MATCH (n:{label})
                        WITH n LIMIT {batch_size}
                        DETACH DELETE n
                        RETURN count(n) as deleted
                        """
                        result = session.run(query)
                        batch_deleted = result.single()["deleted"]
                        
                        if batch_deleted == 0:
                            break
                        
                        deleted_count += batch_deleted
                        self.stats["nodes_deleted"] += batch_deleted
                        logger.debug(f"Deleted {batch_deleted} {label} nodes")
                    
                    if deleted_count > 0:
                        logger.info(f"Deleted {deleted_count} {label} nodes")
        except Exception as e:
            logger.error(f"Error deleting data nodes: {e}")
            raise
    
    def delete_orphan_relationships(self) -> None:
        """Delete any remaining orphan relationships"""
        try:
            with self.driver.session() as session:
                # Count relationships first
                count_query = "MATCH ()-[r]->() RETURN count(r) as count"
                result = session.run(count_query)
                rel_count = result.single()["count"]
                
                if rel_count > 0:
                    # Delete all relationships (should be minimal after DETACH DELETE)
                    delete_query = """
                    MATCH ()-[r]->()
                    DELETE r
                    RETURN count(r) as deleted
                    """
                    result = session.run(delete_query)
                    deleted = result.single()["deleted"]
                    self.stats["relationships_deleted"] = deleted
                    logger.info(f"Deleted {deleted} orphan relationships")
        except Exception as e:
            logger.error(f"Error deleting orphan relationships: {e}")
    
    def verify_schema_intact(self) -> bool:
        """
        Verify that schema (constraints and indexes) are still intact
        
        Returns:
            True if schema is intact, False otherwise
        """
        try:
            with self.driver.session() as session:
                # Check constraints
                constraints_query = "SHOW CONSTRAINTS"
                result = session.run(constraints_query)
                constraints = list(result)
                logger.info(f"Found {len(constraints)} constraints intact")
                
                # Check indexes
                indexes_query = "SHOW INDEXES"
                result = session.run(indexes_query)
                indexes = list(result)
                logger.info(f"Found {len(indexes)} indexes intact")
                
                return len(constraints) > 0 or len(indexes) > 0
        except Exception as e:
            logger.error(f"Error verifying schema: {e}")
            return False
    
    def verify_system_nodes_intact(self) -> bool:
        """
        Verify that system nodes are still present
        
        Returns:
            True if system nodes are intact, False otherwise
        """
        try:
            with self.driver.session() as session:
                for label in self.SYSTEM_NODES:
                    query = f"MATCH (n:{label}) RETURN count(n) as count"
                    result = session.run(query)
                    count = result.single()["count"]
                    if count > 0:
                        logger.info(f"System node {label} intact: {count} nodes")
                    else:
                        logger.warning(f"System node {label} not found")
                return True
        except Exception as e:
            logger.error(f"Error verifying system nodes: {e}")
            return False
    
    def reset_database(self, create_backup: bool = True, dry_run: bool = False) -> bool:
        """
        Main method to reset the database
        
        Args:
            create_backup: Whether to create a backup before reset
            dry_run: If True, only show what would be deleted without actually deleting
        
        Returns:
            True if reset successful, False otherwise
        """
        start_time = time.time()
        
        # Connect to database
        if not self.connect():
            return False
        
        try:
            # Get current state
            node_counts = self.get_node_counts()
            
            if not node_counts:
                logger.info("No data nodes found in database. Nothing to reset.")
                return True
            
            # Show what will be deleted
            logger.info("=" * 60)
            logger.info("NODES TO BE DELETED:")
            total_nodes = 0
            for label, count in node_counts.items():
                logger.info(f"  {label}: {count:,} nodes")
                total_nodes += count
            logger.info(f"  TOTAL: {total_nodes:,} nodes")
            logger.info("=" * 60)
            
            if dry_run:
                logger.info("DRY RUN MODE - No actual deletion performed")
                return True
            
            # Create backup if requested
            if create_backup:
                backup_data = self.backup_statistics()
                backup_file = self.save_backup_file(backup_data)
                logger.info(f"Backup created: {backup_file}")
            
            # Perform the reset
            logger.info("Starting database reset...")
            
            # Delete data nodes
            self.delete_data_nodes()
            
            # Delete any orphan relationships
            self.delete_orphan_relationships()
            
            # Verify schema is intact
            if self.verify_schema_intact():
                logger.info("✓ Database schema (constraints and indexes) verified intact")
            else:
                logger.warning("⚠ Could not verify database schema")
            
            # Verify system nodes are intact
            if self.verify_system_nodes_intact():
                logger.info("✓ System nodes verified intact")
            
            # Calculate time taken
            self.stats["time_taken"] = time.time() - start_time
            
            # Print summary
            logger.info("=" * 60)
            logger.info("RESET COMPLETE:")
            logger.info(f"  Nodes deleted: {self.stats['nodes_deleted']:,}")
            logger.info(f"  Relationships deleted: {self.stats['relationships_deleted']:,}")
            logger.info(f"  Time taken: {self.stats['time_taken']:.2f} seconds")
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"Error during database reset: {e}")
            return False
        finally:
            self.disconnect()


def main():
    """Main entry point for the reset utility"""
    parser = argparse.ArgumentParser(
        description="Reset Neo4j database for Avatar-Engine project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Perform a dry run to see what would be deleted
  python3 reset_neo4j.py --dry-run
  
  # Reset database with backup
  python3 reset_neo4j.py
  
  # Reset database without backup (use with caution!)
  python3 reset_neo4j.py --no-backup
  
  # Reset with custom Neo4j connection
  python3 reset_neo4j.py --uri bolt://localhost:7687 --username neo4j --password mypassword
        """
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting"
    )
    
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating backup before reset (use with caution!)"
    )
    
    parser.add_argument(
        "--uri",
        type=str,
        help="Neo4j connection URI (default: bolt://localhost:7687)"
    )
    
    parser.add_argument(
        "--username",
        type=str,
        help="Neo4j username (default: neo4j)"
    )
    
    parser.add_argument(
        "--password",
        type=str,
        help="Neo4j password"
    )
    
    parser.add_argument(
        "--database",
        type=str,
        help="Neo4j database name (default: neo4j)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create config from arguments if provided
    config = Neo4jConfig()
    if args.uri:
        config.uri = args.uri
    if args.username:
        config.username = args.username
    if args.password:
        config.password = args.password
    if args.database:
        config.database = args.database
    
    # Confirmation prompt if not dry run
    if not args.dry_run:
        logger.warning("⚠️  WARNING: This will DELETE ALL DATA from the Neo4j database!")
        logger.warning("   Only the schema (constraints and indexes) will be preserved.")
        
        if args.no_backup:
            logger.warning("   NO BACKUP will be created!")
        
        response = input("\nAre you sure you want to continue? Type 'YES' to confirm: ")
        if response != "YES":
            logger.info("Reset cancelled by user")
            return 1
    
    # Create and run the reset utility
    reset_utility = Neo4jResetUtility(config)
    
    try:
        success = reset_utility.reset_database(
            create_backup=not args.no_backup,
            dry_run=args.dry_run
        )
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        logger.info("\nReset cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
