#!/usr/bin/env python3
"""
Neo4j Data Validation Utility for Avatar-Engine
===============================================

This utility validates data integrity in the Neo4j database:
- Check for orphaned nodes
- Verify relationship integrity
- Validate required properties
- Generate integrity reports

Author: Avatar-Engine Development Team
Date: 2025-01-10
"""

import argparse
import sys
import os
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Set, Tuple
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Add parent directory to path for module imports
sys.path.append(str(Path(__file__).parent.parent))

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Try multiple locations for .env file
    env_loaded = False
    for env_path in [
        Path.cwd() / ".env",
        Path(__file__).parent.parent / ".env",
        Path.home() / ".avatar-engine" / ".env"
    ]:
        if env_path.exists():
            load_dotenv(env_path)
            env_loaded = True
            logger.debug(f"Loaded .env from {env_path}")
            break
    if not env_loaded:
        load_dotenv()  # Try default location
except ImportError:
    logger.debug("python-dotenv not installed, using system environment variables only")

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
            
            # Debug logging
            if not self.password:
                logger.warning("NEO4J_PASSWORD not found in environment variables")
    
    class ConfigManager:
        def __init__(self):
            self.neo4j = Neo4jConfig()


class Neo4jDataValidator:
    """
    Utility class for validating Neo4j database integrity
    """
    
    # Define required properties for each node type
    REQUIRED_PROPERTIES = {
        "Person": ["name"],
        "Message": ["content", "timestamp"],
        "CommunicationProfile": ["id", "personId"],
        "PersonalityProfile": ["id"],
        "RelationshipPattern": ["partnerId"],
        "LLMAnalysis": ["id", "model", "analysisDate"]
    }
    
    # Define expected relationships
    EXPECTED_RELATIONSHIPS = {
        "Person": {
            "outgoing": ["HAS_COMMUNICATION_PROFILE", "HAS_PERSONALITY_PROFILE", "SENT_MESSAGE"],
            "incoming": ["WITH_PERSON", "RECEIVED_MESSAGE"]
        },
        "CommunicationProfile": {
            "outgoing": ["HAS_STYLE_PATTERN", "HAS_RELATIONSHIP_PATTERN"],
            "incoming": ["HAS_COMMUNICATION_PROFILE"]
        }
    }
    
    def __init__(self, config: Optional[Neo4jConfig] = None):
        """
        Initialize the validation utility
        
        Args:
            config: Optional Neo4j configuration
        """
        if config is None:
            config_manager = ConfigManager()
            config = config_manager.neo4j if hasattr(config_manager, 'neo4j') else Neo4jConfig()
        
        self.config = config
        self.driver = None
        self.validation_results = {
            "timestamp": datetime.now().isoformat(),
            "issues": [],
            "warnings": [],
            "statistics": {},
            "passed": True
        }
    
    def connect(self) -> bool:
        """
        Establish connection to Neo4j database
        
        Returns:
            True if connection successful, False otherwise
        """
        # Check if password is set
        if not self.config.password:
            logger.error("❌ Neo4j password not set!")
            logger.error("")
            logger.error("Please set your Neo4j password using one of these methods:")
            logger.error("1. Set environment variable: export NEO4J_PASSWORD='your_password'")
            logger.error("2. Create .env file: echo 'NEO4J_PASSWORD=your_password' > .env")
            logger.error("3. Pass as argument: --password your_password")
            logger.error("")
            logger.error("For debugging, run: python3 utilities/debug_neo4j.py")
            return False
            
        try:
            logger.debug(f"Attempting connection to {self.config.uri} as {self.config.username}")
            self.driver = GraphDatabase.driver(
                self.config.uri,
                auth=(self.config.username, self.config.password)
            )
            # Test connection
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            logger.info(f"✅ Successfully connected to Neo4j at {self.config.uri}")
            return True
        except AuthError as e:
            logger.error(f"❌ Authentication failed for user '{self.config.username}'")
            logger.error("   Please verify your Neo4j password is correct.")
            logger.error(f"   Error details: {e}")
            return False
        except ServiceUnavailable as e:
            logger.error(f"❌ Neo4j service unavailable at {self.config.uri}")
            logger.error("   Please check:")
            logger.error("   1. Neo4j is running (neo4j status)")
            logger.error("   2. The URI is correct (default: bolt://localhost:7687)")
            logger.error("   3. Port 7687 is not blocked")
            logger.error(f"   Error details: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to connect to Neo4j: {e}")
            logger.error("   Run 'python3 utilities/debug_neo4j.py' for detailed diagnostics")
            return False
    
    def disconnect(self):
        """Close the Neo4j driver connection"""
        if self.driver:
            self.driver.close()
            logger.info("Disconnected from Neo4j")
    
    def add_issue(self, issue_type: str, description: str, severity: str = "ERROR"):
        """
        Add an issue to the validation results
        
        Args:
            issue_type: Type of issue (e.g., "ORPHAN_NODE", "MISSING_PROPERTY")
            description: Description of the issue
            severity: Issue severity ("ERROR" or "WARNING")
        """
        issue = {
            "type": issue_type,
            "description": description,
            "severity": severity
        }
        
        if severity == "ERROR":
            self.validation_results["issues"].append(issue)
            self.validation_results["passed"] = False
        else:
            self.validation_results["warnings"].append(issue)
        
        logger.warning(f"{severity}: {issue_type} - {description}")
    
    def check_orphan_nodes(self) -> Dict[str, int]:
        """
        Check for nodes without any relationships
        
        Returns:
            Dictionary of orphan node counts by label
        """
        orphans = {}
        
        try:
            with self.driver.session() as session:
                # Get all node labels
                result = session.run("CALL db.labels()")
                labels = [record["label"] for record in result]
                
                for label in labels:
                    # Skip system nodes
                    if label in ["AvatarSystem", "LLMSystem"]:
                        continue
                    
                    query = f"""
                    MATCH (n:{label})
                    WHERE NOT EXISTS((n)-[]-())
                    RETURN count(n) as count
                    """
                    result = session.run(query)
                    count = result.single()["count"]
                    
                    if count > 0:
                        orphans[label] = count
                        self.add_issue(
                            "ORPHAN_NODES",
                            f"Found {count} orphan {label} node(s) without relationships",
                            "WARNING"
                        )
                
                logger.info(f"Orphan node check complete: {len(orphans)} types with orphans")
        
        except Exception as e:
            logger.error(f"Error checking orphan nodes: {e}")
        
        return orphans
    
    def check_required_properties(self) -> Dict[str, List[Dict]]:
        """
        Check for nodes missing required properties
        
        Returns:
            Dictionary of nodes with missing properties by label
        """
        missing_props = {}
        
        try:
            with self.driver.session() as session:
                for label, required in self.REQUIRED_PROPERTIES.items():
                    # Check if nodes of this type exist
                    count_query = f"MATCH (n:{label}) RETURN count(n) as count"
                    result = session.run(count_query)
                    total_count = result.single()["count"]
                    
                    if total_count == 0:
                        continue
                    
                    issues = []
                    for prop in required:
                        query = f"""
                        MATCH (n:{label})
                        WHERE n.{prop} IS NULL
                        RETURN id(n) as id, n as node
                        LIMIT 10
                        """
                        result = session.run(query)
                        
                        for record in result:
                            issue = {
                                "node_id": record["id"],
                                "missing_property": prop
                            }
                            issues.append(issue)
                            
                            self.add_issue(
                                "MISSING_PROPERTY",
                                f"{label} node (id: {record['id']}) missing required property: {prop}",
                                "ERROR"
                            )
                    
                    if issues:
                        missing_props[label] = issues
                
                logger.info(f"Property validation complete: {len(missing_props)} types with issues")
        
        except Exception as e:
            logger.error(f"Error checking required properties: {e}")
        
        return missing_props
    
    def check_relationship_integrity(self) -> List[Dict]:
        """
        Check for invalid relationships (e.g., relationships pointing to non-existent nodes)
        
        Returns:
            List of integrity issues
        """
        integrity_issues = []
        
        try:
            with self.driver.session() as session:
                # This should not happen with Neo4j's referential integrity,
                # but we check for logical inconsistencies
                
                # Check for Messages without senders
                query = """
                MATCH (m:Message)
                WHERE NOT EXISTS((m)<-[:SENT_MESSAGE]-(:Person))
                RETURN id(m) as id, m.timestamp as timestamp
                LIMIT 10
                """
                result = session.run(query)
                for record in result:
                    issue = {
                        "type": "MESSAGE_WITHOUT_SENDER",
                        "message_id": record["id"],
                        "timestamp": record["timestamp"]
                    }
                    integrity_issues.append(issue)
                    self.add_issue(
                        "RELATIONSHIP_INTEGRITY",
                        f"Message (id: {record['id']}) has no sender",
                        "ERROR"
                    )
                
                # Check for CommunicationProfiles without Person
                query = """
                MATCH (cp:CommunicationProfile)
                WHERE NOT EXISTS((cp)<-[:HAS_COMMUNICATION_PROFILE]-(:Person))
                RETURN id(cp) as id, cp.personId as personId
                LIMIT 10
                """
                result = session.run(query)
                for record in result:
                    issue = {
                        "type": "PROFILE_WITHOUT_PERSON",
                        "profile_id": record["id"],
                        "person_id": record["personId"]
                    }
                    integrity_issues.append(issue)
                    self.add_issue(
                        "RELATIONSHIP_INTEGRITY",
                        f"CommunicationProfile (id: {record['id']}) not linked to any Person",
                        "ERROR"
                    )
                
                logger.info(f"Relationship integrity check complete: {len(integrity_issues)} issues")
        
        except Exception as e:
            logger.error(f"Error checking relationship integrity: {e}")
        
        return integrity_issues
    
    def check_duplicate_profiles(self) -> List[Dict]:
        """
        Check for duplicate profiles for the same person
        
        Returns:
            List of duplicate profile issues
        """
        duplicates = []
        
        try:
            with self.driver.session() as session:
                # Check for multiple active CommunicationProfiles per person
                query = """
                MATCH (p:Person)-[:HAS_COMMUNICATION_PROFILE]->(cp:CommunicationProfile)
                WHERE cp.status = 'active' OR cp.status IS NULL
                WITH p, count(cp) as profile_count, collect(id(cp)) as profile_ids
                WHERE profile_count > 1
                RETURN p.name as person_name, profile_count, profile_ids
                """
                result = session.run(query)
                
                for record in result:
                    duplicate = {
                        "person": record["person_name"],
                        "profile_count": record["profile_count"],
                        "profile_ids": record["profile_ids"]
                    }
                    duplicates.append(duplicate)
                    self.add_issue(
                        "DUPLICATE_PROFILES",
                        f"Person '{record['person_name']}' has {record['profile_count']} active profiles",
                        "WARNING"
                    )
                
                logger.info(f"Duplicate profile check complete: {len(duplicates)} issues")
        
        except Exception as e:
            logger.error(f"Error checking duplicate profiles: {e}")
        
        return duplicates
    
    def check_data_consistency(self) -> Dict[str, Any]:
        """
        Check for data consistency issues
        
        Returns:
            Dictionary of consistency issues
        """
        consistency_issues = {}
        
        try:
            with self.driver.session() as session:
                # Check for Messages with future timestamps
                query = """
                MATCH (m:Message)
                WHERE m.timestamp > datetime()
                RETURN count(m) as count
                """
                result = session.run(query)
                future_messages = result.single()["count"]
                if future_messages > 0:
                    consistency_issues["future_messages"] = future_messages
                    self.add_issue(
                        "DATA_CONSISTENCY",
                        f"Found {future_messages} messages with future timestamps",
                        "WARNING"
                    )
                
                # Check for invalid confidence scores
                query = """
                MATCH (n)
                WHERE n.confidenceScore IS NOT NULL 
                  AND (n.confidenceScore < 0 OR n.confidenceScore > 1)
                RETURN labels(n)[0] as label, count(n) as count
                """
                result = session.run(query)
                for record in result:
                    if record["count"] > 0:
                        consistency_issues[f"invalid_confidence_{record['label']}"] = record["count"]
                        self.add_issue(
                            "DATA_CONSISTENCY",
                            f"Found {record['count']} {record['label']} nodes with invalid confidence scores",
                            "ERROR"
                        )
                
                logger.info(f"Data consistency check complete: {len(consistency_issues)} issues")
        
        except Exception as e:
            logger.error(f"Error checking data consistency: {e}")
        
        return consistency_issues
    
    def generate_statistics(self) -> Dict[str, Any]:
        """
        Generate database statistics
        
        Returns:
            Dictionary of database statistics
        """
        stats = {}
        
        try:
            with self.driver.session() as session:
                # Count nodes by label
                result = session.run("CALL db.labels()")
                labels = [record["label"] for record in result]
                
                stats["node_counts"] = {}
                for label in labels:
                    query = f"MATCH (n:{label}) RETURN count(n) as count"
                    result = session.run(query)
                    stats["node_counts"][label] = result.single()["count"]
                
                # Count relationships by type
                result = session.run("CALL db.relationshipTypes()")
                rel_types = [record["relationshipType"] for record in result]
                
                stats["relationship_counts"] = {}
                for rel_type in rel_types:
                    query = f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count"
                    result = session.run(query)
                    stats["relationship_counts"][rel_type] = result.single()["count"]
                
                # Total counts
                stats["total_nodes"] = sum(stats["node_counts"].values())
                stats["total_relationships"] = sum(stats["relationship_counts"].values())
                
                logger.info(f"Statistics generated: {stats['total_nodes']} nodes, "
                          f"{stats['total_relationships']} relationships")
        
        except Exception as e:
            logger.error(f"Error generating statistics: {e}")
        
        return stats
    
    def validate(self, checks: Optional[List[str]] = None) -> bool:
        """
        Run validation checks
        
        Args:
            checks: Specific checks to run (None for all)
        
        Returns:
            True if all validations pass, False otherwise
        """
        # Connect to database
        if not self.connect():
            return False
        
        try:
            all_checks = {
                "orphans": self.check_orphan_nodes,
                "properties": self.check_required_properties,
                "relationships": self.check_relationship_integrity,
                "duplicates": self.check_duplicate_profiles,
                "consistency": self.check_data_consistency
            }
            
            # Determine which checks to run
            if checks is None:
                checks_to_run = all_checks
            else:
                checks_to_run = {k: v for k, v in all_checks.items() if k in checks}
            
            # Run checks
            logger.info(f"Running {len(checks_to_run)} validation check(s)...")
            logger.info("=" * 60)
            
            for check_name, check_func in checks_to_run.items():
                logger.info(f"Running {check_name} check...")
                result = check_func()
                self.validation_results[f"{check_name}_details"] = result
            
            # Generate statistics
            self.validation_results["statistics"] = self.generate_statistics()
            
            # Print summary
            logger.info("=" * 60)
            logger.info("VALIDATION SUMMARY:")
            logger.info(f"  Issues found: {len(self.validation_results['issues'])}")
            logger.info(f"  Warnings: {len(self.validation_results['warnings'])}")
            logger.info(f"  Status: {'PASSED' if self.validation_results['passed'] else 'FAILED'}")
            logger.info("=" * 60)
            
            return self.validation_results["passed"]
            
        except Exception as e:
            logger.error(f"Error during validation: {e}")
            return False
        finally:
            self.disconnect()
    
    def save_report(self, output_file: Optional[str] = None) -> str:
        """
        Save validation report to file
        
        Args:
            output_file: Optional output file path
        
        Returns:
            Path to saved report
        """
        if output_file is None:
            reports_dir = Path(__file__).parent / "reports"
            reports_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = str(reports_dir / f"validation_report_{timestamp}.json")
        
        with open(output_file, 'w') as f:
            json.dump(self.validation_results, f, indent=2, default=str)
        
        logger.info(f"Validation report saved to {output_file}")
        return output_file


def main():
    """Main entry point for the validation utility"""
    parser = argparse.ArgumentParser(
        description="Validate Neo4j database integrity for Avatar-Engine project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all validation checks
  python3 validate_data.py
  
  # Run specific checks
  python3 validate_data.py --checks orphans relationships
  
  # Generate detailed report
  python3 validate_data.py --report
  
  # Save report to specific location
  python3 validate_data.py --report --output /path/to/report.json
  
Available checks:
  orphans       - Check for nodes without relationships
  properties    - Validate required properties
  relationships - Check relationship integrity
  duplicates    - Find duplicate profiles
  consistency   - Check data consistency
        """
    )
    
    parser.add_argument(
        "--checks",
        nargs="+",
        choices=["orphans", "properties", "relationships", "duplicates", "consistency"],
        help="Specific validation checks to run (default: all)"
    )
    
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate detailed validation report"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help="Custom output file path for report"
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
    
    # Create and run the validation utility
    validator = Neo4jDataValidator(config)
    
    try:
        # Run validation
        passed = validator.validate(args.checks)
        
        # Save report if requested
        if args.report:
            report_file = validator.save_report(args.output)
            logger.info(f"Report saved: {report_file}")
        
        return 0 if passed else 1
        
    except KeyboardInterrupt:
        logger.info("\nValidation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
