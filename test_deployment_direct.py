#!/usr/bin/env python3
"""
Direct System Deployment Test
============================

This script directly tests the deployment system to diagnose issues.
"""

import sys
import os
from neo4j import GraphDatabase

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from avatar_system_deployment import AvatarSystemDeployment

def test_deployment():
    """Test deployment system directly"""
    
    NEO4J_URI = "bolt://localhost:7687"
    NEO4J_USERNAME = "neo4j"
    NEO4J_PASSWORD = input("Enter Neo4j password: ")
    
    print("🔧 Avatar Intelligence System - Deployment Diagnostics")
    print("=" * 55)
    
    try:
        deployment = AvatarSystemDeployment(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
        
        print("1. Testing database connection...")
        driver = deployment.driver
        with driver.session() as session:
            result = session.run("RETURN 1 as test").single()
            print(f"   ✅ Connection successful: {result['test']}")
        
        print("\n2. Checking existing deployment...")
        existing = deployment._check_existing_deployment()
        print(f"   Existing deployment found: {existing}")
        
        print("\n3. Getting system status...")
        status = deployment.get_system_status()
        print(f"   Total profiles: {status['total_profiles']}")
        print(f"   Active profiles: {status['active_profiles']}")
        print(f"   Total artifacts: {status['total_artifacts']}")
        print(f"   System health: {status['deployment_status']}")
        
        print("\n4. Checking for AvatarSystem metadata...")
        with driver.session() as session:
            result = session.run("""
                MATCH (sys:AvatarSystem {id: 'avatar_intelligence_v1'})
                RETURN sys.status as status, sys.version as version
            """).single()
            
            if result:
                print(f"   ✅ System metadata found: status={result['status']}, version={result['version']}")
            else:
                print("   ❌ No system metadata found")
        
        print("\n5. Testing deployment with force rebuild...")
        success = deployment.deploy_system(force_rebuild=True)
        
        if success:
            print("   ✅ Force deployment successful!")
            
            # Check status again
            new_status = deployment.get_system_status()
            print(f"   Updated status: {new_status['deployment_status']}")
        else:
            print("   ❌ Force deployment failed!")
        
        print("\n6. Final verification...")
        verified = deployment._verify_deployment()
        print(f"   System verification: {'✅ PASSED' if verified else '❌ FAILED'}")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_deployment()
