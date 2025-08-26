#!/usr/bin/env python3
"""
Avatar Intelligence System - Basic Usage Example
===============================================

This example shows how to use the Avatar Intelligence System to:
1. Deploy the system
2. Test database connectivity
3. Check system status

Run this after setting up the system:
    python examples/basic_usage.py

For full functionality, you need the complete avatar_intelligence_pipeline.py file.
"""

import sys
import os
from neo4j import GraphDatabase

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from avatar_system_deployment import AvatarSystemDeployment
except ImportError:
    print("Error: Could not import avatar_system_deployment")
    print("Make sure the src/avatar_system_deployment.py file exists.")
    sys.exit(1)


def test_database_connection(uri, username, password):
    """Test basic database connectivity"""
    try:
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        with driver.session() as session:
            # Test basic connection
            result = session.run("MATCH (n) RETURN count(n) as total_nodes").single()
            total_nodes = result['total_nodes']
            print(f"✓ Connected! Database has {total_nodes} total nodes")
            
            # Check for conversation data
            person_result = session.run("MATCH (p:Person) RETURN count(p) as people").single()
            total_people = person_result['people'] if person_result else 0
            
            message_result = session.run("MATCH (m:Message) RETURN count(m) as messages").single()
            total_messages = message_result['messages'] if message_result else 0
            
            print(f"📊 Conversation data: {total_people} people, {total_messages} messages")
            
            if total_people == 0:
                print("⚠️  No Person nodes found. Please load your conversation data first.")
                return False, driver
            
            if total_messages == 0:
                print("⚠️  No Message nodes found. Please load your conversation data first.")
                return False, driver
            
            return True, driver
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False, None


def main():
    """Basic system test"""
    
    print("🤖 Avatar Intelligence System - Basic Test")
    print("=" * 50)
    
    # Configuration
    NEO4J_URI = "bolt://localhost:7687"
    NEO4J_USERNAME = "neo4j"
    NEO4J_PASSWORD = input("Enter Neo4j password: ")
    
    print(f"\n📡 Testing connection to Neo4j at {NEO4J_URI}...")
    
    # Test database connection
    connected, driver = test_database_connection(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
    
    if not connected:
        print("\n❌ Cannot proceed without database connection.")
        print("💡 Make sure Neo4j is running and your credentials are correct.")
        return
    
    try:
        # Test system deployment
        print(f"\n🚀 Testing Avatar Intelligence System deployment...")
        deployment = AvatarSystemDeployment(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
        
        # Check if system is already deployed
        status = deployment.get_system_status()
        
        # Check if we need to deploy or redeploy
        needs_deployment = False
        
        if status['active_profiles'] == 0 and status['total_profiles'] == 0:
            print("📦 System not yet deployed. Deploying now...")
            needs_deployment = True
        elif status['total_profiles'] > 0 and status['active_profiles'] == 0:
            print("🔧 System partially deployed but no active profiles. This is normal.")
            print("✓ System schema is ready for profile creation.")
        else:
            print(f"✓ System already deployed with {status['active_profiles']} active profiles")
        
        # Deploy if needed
        if needs_deployment:
            try:
                success = deployment.deploy_system()
                
                if success:
                    print("✓ System deployed successfully!")
                else:
                    # Try force rebuild if initial deployment failed
                    print("🔧 Initial deployment failed, trying force rebuild...")
                    success = deployment.deploy_system(force_rebuild=True)
                    
                    if success:
                        print("✓ System deployed successfully with force rebuild!")
                    else:
                        print("❌ System deployment failed even with force rebuild!")
                        return
            except Exception as e:
                print(f"❌ Error during deployment: {e}")
                return
        
        # Show system status
        print(f"\n📊 System Status:")
        print(f"   Version: {status['system_version']}")
        print(f"   Total profiles: {status['total_profiles']}")
        print(f"   Active profiles: {status['active_profiles']}")
        print(f"   Total artifacts: {status['total_artifacts']}")
        print(f"   Health: {status['deployment_status']}")
        
        # Check for people with sufficient message data
        print(f"\n👥 Checking for people with conversation data...")
        
        with driver.session() as session:
            result = session.run("""
                MATCH (p:Person)-[:SENT]->(m:Message)
                WITH p, count(m) as messageCount
                WHERE messageCount >= 10
                RETURN p.name as name, messageCount
                ORDER BY messageCount DESC
                LIMIT 10
            """)
            
            candidates = [dict(record) for record in result]
            
            if candidates:
                print(f"Found {len(candidates)} people with 10+ messages:")
                for i, person in enumerate(candidates, 1):
                    print(f"  {i:2d}. {person['name']} ({person['messageCount']} messages)")
                
                print(f"\n🎯 Ready for full avatar analysis!")
                print(f"💡 To process these people and create avatar profiles:")
                print(f"   1. Get the complete avatar_intelligence_pipeline.py")
                print(f"   2. Run: python -c \"from src.avatar_intelligence_pipeline import AvatarSystemManager; \\")
                print(f"      manager = AvatarSystemManager(driver); \\")
                print(f"      stats = manager.initialize_all_people(min_messages=50)\"")
            else:
                print("❌ No people found with sufficient conversation data (10+ messages)")
                print("💡 Please check your conversation data loading.")
        
        print(f"\n🎉 Basic test completed successfully!")
        print(f"📝 Next steps:")
        print(f"   1. Install full pipeline: Copy complete avatar_intelligence_pipeline.py")  
        print(f"   2. Process your data: Run the full analysis system")
        print(f"   3. Generate avatars: Create personalized AI prompts")
        
        driver.close()
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        if driver:
            driver.close()


if __name__ == "__main__":
    main()
