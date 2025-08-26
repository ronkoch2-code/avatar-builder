#!/usr/bin/env python3
"""
Avatar System Deployment & Management
====================================

Handles deployment, setup, and maintenance of the Avatar Intelligence System.

Usage:
    python avatar_system_deployment.py --password NEO4J_PASSWORD --command deploy
    python avatar_system_deployment.py --password NEO4J_PASSWORD --command bulk-init --min-messages 50
    python avatar_system_deployment.py --password NEO4J_PASSWORD --command status
"""

import argparse
import logging
from datetime import datetime
from neo4j import GraphDatabase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AvatarSystemDeployment:
    """Handles system deployment, setup, and maintenance"""
    
    def __init__(self, neo4j_uri: str, username: str, password: str):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(username, password))
        self.system_version = "1.0"
        self.deployment_date = datetime.now()
        
    def deploy_system(self, force_rebuild: bool = False) -> bool:
        """Complete system deployment"""
        logger.info("Starting Avatar Intelligence System deployment...")
        
        try:
            # Step 1: Verify existing schema
            if not force_rebuild and self._check_existing_deployment():
                logger.info("System already deployed. Use force_rebuild=True to redeploy.")
                return False
            
            # Step 2: Create schema and constraints
            self._create_schema()
            
            # Step 3: Create indexes for performance
            self._create_indexes()
            
            # Step 4: Set up system metadata
            self._initialize_system_metadata()
            
            # Step 5: Verify deployment
            if self._verify_deployment():
                logger.info("✓ Avatar Intelligence System deployed successfully")
                return True
            else:
                logger.error("✗ System deployment verification failed")
                return False
                
        except Exception as e:
            logger.error(f"Deployment failed: {str(e)}")
            return False
    
    def _create_schema(self):
        """Create Neo4j schema for avatar intelligence"""
        
        schema_commands = [
            # Constraints
            "CREATE CONSTRAINT avatar_profile_id IF NOT EXISTS FOR (cp:CommunicationProfile) REQUIRE cp.id IS UNIQUE",
            "CREATE CONSTRAINT style_pattern_id IF NOT EXISTS FOR (sp:StylePattern) REQUIRE sp.id IS UNIQUE", 
            "CREATE CONSTRAINT relationship_pattern_id IF NOT EXISTS FOR (rp:RelationshipPattern) REQUIRE rp.id IS UNIQUE",
            "CREATE CONSTRAINT signature_phrase_id IF NOT EXISTS FOR (sp:SignaturePhrase) REQUIRE sp.id IS UNIQUE",
            "CREATE CONSTRAINT topic_preference_id IF NOT EXISTS FOR (tp:TopicPreference) REQUIRE tp.id IS UNIQUE",
            "CREATE CONSTRAINT emotional_expression_id IF NOT EXISTS FOR (ee:EmotionalExpression) REQUIRE ee.id IS UNIQUE",
            "CREATE CONSTRAINT temporal_pattern_id IF NOT EXISTS FOR (tp:TemporalPattern) REQUIRE tp.id IS UNIQUE",
            "CREATE CONSTRAINT context_trigger_id IF NOT EXISTS FOR (ct:ContextTrigger) REQUIRE ct.id IS UNIQUE",
        ]
        
        with self.driver.session() as session:
            for command in schema_commands:
                try:
                    session.run(command)
                    logger.info(f"✓ {command}")
                except Exception as e:
                    if "already exists" in str(e).lower():
                        logger.info(f"- {command} (already exists)")
                    else:
                        logger.warning(f"⚠ {command} failed: {e}")
    
    def _create_indexes(self):
        """Create performance indexes"""
        
        index_commands = [
            "CREATE INDEX profile_person_lookup IF NOT EXISTS FOR (cp:CommunicationProfile) ON (cp.personId)",
            "CREATE INDEX profile_status_lookup IF NOT EXISTS FOR (cp:CommunicationProfile) ON (cp.status)",
            "CREATE INDEX style_context_lookup IF NOT EXISTS FOR (sp:StylePattern) ON (sp.contextType)",
            "CREATE INDEX relationship_partner_lookup IF NOT EXISTS FOR (rp:RelationshipPattern) ON (rp.partnerId)",
            "CREATE INDEX phrase_frequency_lookup IF NOT EXISTS FOR (sp:SignaturePhrase) ON (sp.frequency)",
            "CREATE INDEX topic_lookup IF NOT EXISTS FOR (tp:TopicPreference) ON (tp.topic)",
            "CREATE INDEX emotion_type_lookup IF NOT EXISTS FOR (ee:EmotionalExpression) ON (ee.emotion)",
            "CREATE INDEX temporal_timeframe_lookup IF NOT EXISTS FOR (tp:TemporalPattern) ON (tp.timeFrame)",
        ]
        
        with self.driver.session() as session:
            for command in index_commands:
                try:
                    session.run(command)
                    logger.info(f"✓ {command}")
                except Exception as e:
                    if "already exists" in str(e).lower():
                        logger.info(f"- {command} (already exists)")
                    else:
                        logger.warning(f"⚠ {command} failed: {e}")
    
    def _initialize_system_metadata(self):
        """Initialize system metadata and versioning"""
        
        with self.driver.session() as session:
            session.run("""
                MERGE (sys:AvatarSystem {id: 'avatar_intelligence_v1'})
                SET sys.version = $version,
                    sys.deploymentDate = $deployment_date,
                    sys.status = 'active',
                    sys.lastMaintenance = $deployment_date,
                    sys.totalProfiles = 0,
                    sys.totalArtifacts = 0
            """, 
            version=self.system_version,
            deployment_date=self.deployment_date.isoformat())
    
    def get_system_status(self) -> dict:
        """Get comprehensive system health metrics"""
        
        with self.driver.session() as session:
            # Get profile counts
            profile_result = session.run("""
                MATCH (cp:CommunicationProfile)
                RETURN count(cp) as total,
                       sum(CASE WHEN cp.status = 'active' THEN 1 ELSE 0 END) as active
            """).single()
            
            # Get artifact counts if profiles exist
            total_artifacts = 0
            if profile_result and profile_result['active'] > 0:
                artifact_result = session.run("""
                    MATCH (artifact) 
                    WHERE artifact:StylePattern OR artifact:RelationshipPattern 
                       OR artifact:SignaturePhrase OR artifact:TopicPreference
                    RETURN count(artifact) as totalArtifacts
                """).single()
                total_artifacts = artifact_result['totalArtifacts'] if artifact_result else 0
            
            total_profiles = profile_result['total'] or 0
            active_profiles = profile_result['active'] or 0
            
            # Calculate system health
            health = "healthy"
            if active_profiles == 0:
                health = "no_profiles"
            elif total_artifacts < active_profiles * 3:  # Each profile should have at least 3 artifacts
                health = "incomplete_artifacts"
            elif active_profiles < total_profiles * 0.8:  # Most profiles should be active
                health = "degraded"
            
            return {
                'total_profiles': total_profiles,
                'active_profiles': active_profiles,
                'total_artifacts': total_artifacts,
                'last_update': datetime.now().isoformat(),
                'system_version': self.system_version,
                'deployment_status': health
            }
    
    def _check_existing_deployment(self) -> bool:
        """Check if system is already deployed"""
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (sys:AvatarSystem {id: 'avatar_intelligence_v1'})
                RETURN sys.status as status
            """).single()
            
            return result and result['status'] == 'active'
    
    def _verify_deployment(self) -> bool:
        """Verify system deployment is successful"""
        
        with self.driver.session() as session:
            # Check constraints exist
            try:
                constraints_result = session.run("SHOW CONSTRAINTS").data()
                avatar_constraints = [c for c in constraints_result if 'CommunicationProfile' in c.get('description', '')]
            except:
                avatar_constraints = []  # Some Neo4j versions might not support SHOW CONSTRAINTS
            
            # Check system metadata
            system_result = session.run("""
                MATCH (sys:AvatarSystem {id: 'avatar_intelligence_v1'})
                RETURN sys
            """).single()
            
            verification_passed = system_result is not None
            
            logger.info(f"Verification: {len(avatar_constraints)} constraints, system metadata: {'✓' if system_result else '✗'}")
            
            return verification_passed


def main():
    """Command line interface for system management"""
    
    parser = argparse.ArgumentParser(description="Avatar Intelligence System Management")
    parser.add_argument("--neo4j-uri", default="bolt://localhost:7687", help="Neo4j URI")
    parser.add_argument("--username", default="neo4j", help="Neo4j username") 
    parser.add_argument("--password", required=True, help="Neo4j password")
    parser.add_argument("--command", required=True, choices=[
        'deploy', 'status', 'help'
    ], help="Command to execute")
    parser.add_argument("--force", action="store_true", help="Force rebuild/overwrite")
    
    args = parser.parse_args()
    
    if args.command == 'help':
        print_help()
        return
    
    # Initialize deployment system
    deployment = AvatarSystemDeployment(args.neo4j_uri, args.username, args.password)
    
    if args.command == 'deploy':
        success = deployment.deploy_system(force_rebuild=args.force)
        print(f"Deployment {'successful' if success else 'failed'}")
        
        if success:
            print("\n🎉 Avatar Intelligence System deployed successfully!")
            print("\nNext steps:")
            print("1. Install dependencies: pip install -r requirements.txt")
            print("2. Run the full analysis pipeline to process your conversation data")  
            print("3. Use: python examples/basic_usage.py to get started")
            
    elif args.command == 'status':
        status = deployment.get_system_status()
        print(f"=== Avatar Intelligence System Status ===")
        print(f"System version: {status['system_version']}")
        print(f"Total profiles: {status['total_profiles']}")
        print(f"Active profiles: {status['active_profiles']}")
        print(f"Total artifacts: {status['total_artifacts']}")
        print(f"Status: {status['deployment_status']}")
        print(f"Last update: {status['last_update']}")
        
    deployment.driver.close()


def print_help():
    """Print detailed help information"""
    
    print("""
Avatar Intelligence System - Help
=================================

COMMANDS:
  deploy    Deploy the system schema and initialize
  status    Show system health and statistics
  help      Show this help message

EXAMPLES:
  # Deploy the system
  python avatar_system_deployment.py --password YOUR_PASSWORD --command deploy

  # Check system status
  python avatar_system_deployment.py --password YOUR_PASSWORD --command status

  # Force redeploy (overwrites existing)  
  python avatar_system_deployment.py --password YOUR_PASSWORD --command deploy --force

SYSTEM REQUIREMENTS:
  - Neo4j 5.0+ with conversation data loaded
  - Python 3.7+
  - neo4j-python-driver
  - Access to your conversation database

For complete functionality, you need the main avatar_intelligence_pipeline.py file.
""")


if __name__ == "__main__":
    main()
