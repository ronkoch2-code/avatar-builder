#!/usr/bin/env python3
"""
Neo4j Database Backup Utility for Avatar-Engine
===============================================

This utility creates comprehensive backups of Neo4j data including:
- All nodes with properties
- All relationships with properties
- Export to JSON or Cypher format
- Compression support

Author: Avatar-Engine Development Team
Date: 2025-01-10
"""

import argparse
import sys
import os
import logging
import json
import gzip
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Set
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError

# Add parent directory to path for module imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from src.config_manager import ConfigManager, Neo4jConfig
except ImportError:
    # Basic config if config_manager doesn't exist
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


class Neo4jBackupUtility:
    """
    Utility class for backing up Neo4j database
    """
    
    def __init__(self, config: Optional[Neo4jConfig] = None):
        """
        Initialize the backup utility
        
        Args:
            config: Optional Neo4j configuration
        """
        if config is None:
            config_manager = ConfigManager()
            config = config_manager.neo4j if hasattr(config_manager, 'neo4j') else Neo4jConfig()
        
        self.config = config
        self.driver = None
        self.stats = {
            "nodes_exported": 0,
            "relationships_exported": 0,
            "file_size": 0,
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
    
    def get_all_labels(self) -> List[str]:
        """
        Get all node labels in the database
        
        Returns:
            List of node labels
        """
        labels = []
        try:
            with self.driver.session() as session:
                result = session.run("CALL db.labels()")
                labels = [record["label"] for record in result]
        except Exception as e:
            logger.error(f"Error getting labels: {e}")
        return labels
    
    def get_all_relationship_types(self) -> List[str]:
        """
        Get all relationship types in the database
        
        Returns:
            List of relationship types
        """
        types = []
        try:
            with self.driver.session() as session:
                result = session.run("CALL db.relationshipTypes()")
                types = [record["relationshipType"] for record in result]
        except Exception as e:
            logger.error(f"Error getting relationship types: {e}")
        return types
    
    def export_nodes(self, labels: Optional[List[str]] = None, batch_size: int = 1000) -> List[Dict[str, Any]]:
        """
        Export nodes from the database
        
        Args:
            labels: Specific labels to export (None for all)
            batch_size: Number of nodes to fetch per batch
        
        Returns:
            List of node dictionaries
        """
        nodes = []
        
        try:
            with self.driver.session() as session:
                if labels is None:
                    labels = self.get_all_labels()
                
                for label in labels:
                    skip = 0
                    while True:
                        query = f"""
                        MATCH (n:{label})
                        RETURN n, labels(n) as labels, id(n) as id
                        SKIP {skip} LIMIT {batch_size}
                        """
                        result = session.run(query)
                        batch = []
                        for record in result:
                            node_data = dict(record["n"])
                            node_data["_id"] = record["id"]
                            node_data["_labels"] = record["labels"]
                            batch.append(node_data)
                            self.stats["nodes_exported"] += 1
                        
                        if not batch:
                            break
                        
                        nodes.extend(batch)
                        skip += batch_size
                        logger.debug(f"Exported {len(batch)} {label} nodes")
                    
                    logger.info(f"Exported {skip} {label} nodes")
        
        except Exception as e:
            logger.error(f"Error exporting nodes: {e}")
        
        return nodes
    
    def export_relationships(self, batch_size: int = 1000) -> List[Dict[str, Any]]:
        """
        Export relationships from the database
        
        Args:
            batch_size: Number of relationships to fetch per batch
        
        Returns:
            List of relationship dictionaries
        """
        relationships = []
        
        try:
            with self.driver.session() as session:
                skip = 0
                while True:
                    query = f"""
                    MATCH (a)-[r]->(b)
                    RETURN id(a) as start_id, id(b) as end_id, 
                           type(r) as type, properties(r) as props, id(r) as id
                    SKIP {skip} LIMIT {batch_size}
                    """
                    result = session.run(query)
                    batch = []
                    for record in result:
                        rel_data = {
                            "_id": record["id"],
                            "_start_id": record["start_id"],
                            "_end_id": record["end_id"],
                            "_type": record["type"],
                            **record["props"]
                        }
                        batch.append(rel_data)
                        self.stats["relationships_exported"] += 1
                    
                    if not batch:
                        break
                    
                    relationships.extend(batch)
                    skip += batch_size
                    logger.debug(f"Exported {len(batch)} relationships")
                
                logger.info(f"Exported {len(relationships)} total relationships")
        
        except Exception as e:
            logger.error(f"Error exporting relationships: {e}")
        
        return relationships
    
    def export_to_json(self, output_file: str, labels: Optional[List[str]] = None, 
                      compress: bool = False) -> bool:
        """
        Export database to JSON format
        
        Args:
            output_file: Path to output file
            labels: Specific node labels to export (None for all)
            compress: Whether to compress the output
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Export data
            logger.info("Exporting nodes...")
            nodes = self.export_nodes(labels)
            
            logger.info("Exporting relationships...")
            relationships = self.export_relationships()
            
            # Prepare export data
            export_data = {
                "metadata": {
                    "export_date": datetime.now().isoformat(),
                    "database_uri": self.config.uri,
                    "total_nodes": len(nodes),
                    "total_relationships": len(relationships),
                    "avatar_engine_version": "1.0.0"
                },
                "nodes": nodes,
                "relationships": relationships
            }
            
            # Write to file
            if compress:
                output_file = output_file + ".gz"
                with gzip.open(output_file, 'wt', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, default=str)
            else:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, default=str)
            
            # Update stats
            self.stats["file_size"] = Path(output_file).stat().st_size
            
            logger.info(f"Backup saved to {output_file}")
            logger.info(f"File size: {self.stats['file_size'] / 1024 / 1024:.2f} MB")
            
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            return False
    
    def export_to_cypher(self, output_file: str, labels: Optional[List[str]] = None) -> bool:
        """
        Export database to Cypher script format
        
        Args:
            output_file: Path to output file
            labels: Specific node labels to export (None for all)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                # Write header
                f.write("// Avatar-Engine Neo4j Database Export\n")
                f.write(f"// Generated: {datetime.now().isoformat()}\n")
                f.write(f"// Database: {self.config.uri}\n\n")
                
                # Export nodes
                f.write("// ===== NODES =====\n\n")
                nodes = self.export_nodes(labels)
                
                # Create a mapping of old IDs to new variable names
                id_mapping = {}
                for i, node in enumerate(nodes):
                    var_name = f"n{i}"
                    id_mapping[node["_id"]] = var_name
                    
                    labels_str = ":".join(node["_labels"])
                    props = {k: v for k, v in node.items() if not k.startswith("_")}
                    props_str = json.dumps(props, default=str)
                    
                    f.write(f"CREATE ({var_name}:{labels_str} {props_str});\n")
                
                f.write("\n// ===== RELATIONSHIPS =====\n\n")
                
                # Export relationships
                relationships = self.export_relationships()
                for rel in relationships:
                    start_var = id_mapping.get(rel["_start_id"], f"n{rel['_start_id']}")
                    end_var = id_mapping.get(rel["_end_id"], f"n{rel['_end_id']}")
                    rel_type = rel["_type"]
                    props = {k: v for k, v in rel.items() if not k.startswith("_")}
                    
                    if props:
                        props_str = json.dumps(props, default=str)
                        f.write(f"CREATE ({start_var})-[:{rel_type} {props_str}]->({end_var});\n")
                    else:
                        f.write(f"CREATE ({start_var})-[:{rel_type}]->({end_var});\n")
                
                f.write("\n// ===== END OF EXPORT =====\n")
            
            logger.info(f"Cypher export saved to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to Cypher: {e}")
            return False
    
    def create_backup(self, format: str = "json", labels: Optional[List[str]] = None,
                     compress: bool = False) -> Optional[str]:
        """
        Create a backup of the database
        
        Args:
            format: Output format ('json' or 'cypher')
            labels: Specific node labels to backup (None for all)
            compress: Whether to compress the output
        
        Returns:
            Path to backup file if successful, None otherwise
        """
        import time
        start_time = time.time()
        
        # Connect to database
        if not self.connect():
            return None
        
        try:
            # Create backup directory
            backup_dir = Path(__file__).parent / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if format == "json":
                filename = f"neo4j_backup_{timestamp}.json"
            elif format == "cypher":
                filename = f"neo4j_export_{timestamp}.cypher"
            else:
                logger.error(f"Unknown format: {format}")
                return None
            
            output_file = str(backup_dir / filename)
            
            # Perform backup
            logger.info(f"Creating {format.upper()} backup...")
            
            if format == "json":
                success = self.export_to_json(output_file, labels, compress)
            elif format == "cypher":
                success = self.export_to_cypher(output_file, labels)
            
            if success:
                self.stats["time_taken"] = time.time() - start_time
                
                # Print summary
                logger.info("=" * 60)
                logger.info("BACKUP COMPLETE:")
                logger.info(f"  Format: {format.upper()}")
                logger.info(f"  Nodes exported: {self.stats['nodes_exported']:,}")
                logger.info(f"  Relationships exported: {self.stats['relationships_exported']:,}")
                if self.stats.get("file_size"):
                    logger.info(f"  File size: {self.stats['file_size'] / 1024 / 1024:.2f} MB")
                logger.info(f"  Time taken: {self.stats['time_taken']:.2f} seconds")
                logger.info(f"  Output file: {output_file}")
                logger.info("=" * 60)
                
                return output_file
            
            return None
            
        except Exception as e:
            logger.error(f"Error during backup: {e}")
            return None
        finally:
            self.disconnect()


def main():
    """Main entry point for the backup utility"""
    parser = argparse.ArgumentParser(
        description="Backup Neo4j database for Avatar-Engine project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create JSON backup
  python3 backup_neo4j.py
  
  # Create compressed JSON backup
  python3 backup_neo4j.py --compress
  
  # Create Cypher script backup
  python3 backup_neo4j.py --format cypher
  
  # Backup specific node types only
  python3 backup_neo4j.py --nodes Person Message CommunicationProfile
  
  # Custom output location
  python3 backup_neo4j.py --output /path/to/backup.json
        """
    )
    
    parser.add_argument(
        "--format",
        type=str,
        choices=["json", "cypher"],
        default="json",
        help="Backup format (default: json)"
    )
    
    parser.add_argument(
        "--nodes",
        nargs="+",
        help="Specific node labels to backup (default: all)"
    )
    
    parser.add_argument(
        "--compress",
        action="store_true",
        help="Compress the backup file (JSON format only)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help="Custom output file path"
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
    
    # Create and run the backup utility
    backup_utility = Neo4jBackupUtility(config)
    
    try:
        if args.output:
            # Use custom output path
            if args.format == "json":
                success = backup_utility.export_to_json(args.output, args.nodes, args.compress)
            elif args.format == "cypher":
                success = backup_utility.export_to_cypher(args.output, args.nodes)
            
            return 0 if success else 1
        else:
            # Use default backup location
            backup_file = backup_utility.create_backup(
                format=args.format,
                labels=args.nodes,
                compress=args.compress
            )
            
            return 0 if backup_file else 1
        
    except KeyboardInterrupt:
        logger.info("\nBackup cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
