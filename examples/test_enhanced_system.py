#!/usr/bin/env python3
"""
Enhanced Avatar Engine - Quick Test
===================================

Quick test script to verify the enhanced Avatar Engine setup without using LLM analysis.
This tests database connectivity, configuration, and basic functionality.
"""

import sys
import logging
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config_manager import ConfigManager
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


def test_enhanced_avatar_system():
    """
    Quick test of enhanced Avatar Engine setup
    """
    print("🧪 Avatar Engine Enhanced - Quick Test")
    print("=" * 50)
    
    test_results = {
        "config": False,
        "database": False,
        "schema": False,
        "data": False
    }
    
    # Test 1: Configuration
    print("\n1. Testing Configuration...")
    try:
        config = ConfigManager()
        print(f"✅ Configuration loaded")
        print(f"   Neo4j URI: {config.neo4j.uri}")
        print(f"   Claude Model: {config.anthropic.model}")
        print(f"   LLM Analysis: {'Enabled' if config.system.enable_llm_analysis else 'Disabled'}")
        
        if config.anthropic.api_key:
            print(f"   API Key: {'*' * 20} (Set)")
        else:
            print(f"   API Key: Not set (LLM analysis will be disabled)")
        
        test_results["config"] = True
        
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
        return test_results
    
    # Test 2: Database Connection
    print("\n2. Testing Database Connection...")
    try:
        driver_config = config.get_neo4j_driver_config()
        driver = GraphDatabase.driver(**driver_config)
        
        with driver.session() as session:
            # Test basic connectivity
            result = session.run("RETURN 1 as test").single()
            assert result["test"] == 1
            
        print("✅ Neo4j connection successful")
        test_results["database"] = True
        
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        print("   Check your Neo4j password and service status")
        return test_results
    
    # Test 3: Schema Check
    print("\n3. Checking Database Schema...")
    try:
        with driver.session() as session:
            # Check for basic nodes
            person_count = session.run("MATCH (p:Person) RETURN count(p) as count").single()["count"]
            message_count = session.run("MATCH (m:Message) RETURN count(m) as count").single()["count"] 
            profile_count = session.run("MATCH (cp:CommunicationProfile) RETURN count(cp) as count").single()["count"]
            
            print(f"✅ Schema check passed")
            print(f"   People: {person_count:,}")
            print(f"   Messages: {message_count:,}")
            print(f"   Profiles: {profile_count:,}")
            
            # Check for enhanced schema elements
            enhanced_nodes = [
                "PersonalityProfile",
                "RelationshipDynamic", 
                "LLMAnalysis",
                "LLMSystem"
            ]
            
            enhanced_present = []
            for node_type in enhanced_nodes:
                count = session.run(f"MATCH (n:{node_type}) RETURN count(n) as count").single()["count"]
                if count > 0:
                    enhanced_present.append(f"{node_type}: {count}")
            
            if enhanced_present:
                print("   Enhanced nodes found:")
                for node_info in enhanced_present:
                    print(f"     {node_info}")
            else:
                print("   Enhanced schema not yet deployed (run --deploy)")
            
            test_results["schema"] = True
            
    except Exception as e:
        print(f"❌ Schema check failed: {e}")
        return test_results
    
    # Test 4: Data Quality Check
    print("\n4. Checking Data Quality...")
    try:
        with driver.session() as session:
            # Find people with sufficient messages for analysis
            result = session.run("""
            MATCH (p:Person)-[:SENT]->(m:Message)
            WITH p, count(m) as messageCount
            WHERE messageCount >= 50
            RETURN count(p) as analyzable_people,
                   max(messageCount) as max_messages,
                   avg(messageCount) as avg_messages
            """).single()
            
            analyzable_people = result["analyzable_people"]
            max_messages = result["max_messages"]
            avg_messages = result["avg_messages"]
            
            print(f"✅ Data quality check passed")
            print(f"   People with 50+ messages: {analyzable_people}")
            print(f"   Maximum messages per person: {max_messages:,.0f}")
            print(f"   Average messages per person: {avg_messages:,.0f}")
            
            if analyzable_people == 0:
                print("   ⚠️  No people have sufficient messages for LLM analysis")
                print("      Minimum 50 messages required per person")
            
            test_results["data"] = True
            
    except Exception as e:
        print(f"❌ Data quality check failed: {e}")
        return test_results
    
    finally:
        if 'driver' in locals():
            driver.close()
    
    # Summary
    print("\n📊 Test Summary:")
    print("-" * 30)
    
    passed = sum(test_results.values())
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.title():<12}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your enhanced Avatar Engine is ready.")
        print("\nNext steps:")
        print("1. Set your Anthropic API key: export ANTHROPIC_API_KEY='your_key'")
        print("2. Deploy enhanced schema: python enhanced_deployment.py --deploy") 
        print("3. Run a demo: python examples/enhanced_demo.py")
        print("4. Analyze people: python enhanced_deployment.py --analyze-person 'Name'")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above before proceeding.")
        
        if not test_results["config"]:
            print("   → Run: python src/config_manager.py")
        if not test_results["database"]:
            print("   → Check Neo4j service and password")
        if not test_results["schema"]:
            print("   → Your data looks good for enhancement!")
        if not test_results["data"]:
            print("   → Make sure conversation data is loaded")
    
    return test_results


if __name__ == "__main__":
    # Check if running from correct directory
    if not Path("src").exists():
        print("❌ Please run this script from the Avatar-Engine directory:")
        print("   cd /Volumes/FS001/pythonscripts/Avatar-Engine")
        print("   python examples/test_enhanced_system.py")
        sys.exit(1)
    
    # Run the test
    test_enhanced_avatar_system()
