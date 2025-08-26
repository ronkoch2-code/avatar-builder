#!/usr/bin/env python3
"""
Avatar System Cleanup Utility
=============================

This script helps clean up partial or problematic Avatar Intelligence System deployments.
Use this if you're having deployment issues.
"""

import sys
import os
from neo4j import GraphDatabase

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def clean_avatar_system():
    """Clean up Avatar Intelligence System data"""
    
    NEO4J_URI = "bolt://localhost:7687"
    NEO4J_USERNAME = "neo4j"
    NEO4J_PASSWORD = input("Enter Neo4j password: ")
    
    print("🧹 Avatar Intelligence System - Cleanup Utility")
    print("=" * 50)
    print("⚠️  WARNING: This will remove all Avatar Intelligence System data!")
    print("   (Your original Person/Message data will NOT be affected)")
    
    confirm = input("\nAre you sure you want to continue? (type 'yes' to confirm): ")
    if confirm.lower() != 'yes':
        print("❌ Cleanup cancelled.")
        return
    
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        
        with driver.session() as session:
            print("\n🔍 Checking current Avatar system data...")
            
            # Check what exists
            results = {}
            queries = {
                'AvatarSystem': 'MATCH (n:AvatarSystem) RETURN count(n) as count',
                'CommunicationProfile': 'MATCH (n:CommunicationProfile) RETURN count(n) as count',
                'RelationshipPattern': 'MATCH (n:RelationshipPattern) RETURN count(n) as count',
                'SignaturePhrase': 'MATCH (n:SignaturePhrase) RETURN count(n) as count',
                'StylePattern': 'MATCH (n:StylePattern) RETURN count(n) as count',
                'TopicPreference': 'MATCH (n:TopicPreference) RETURN count(n) as count',
                'EmotionalExpression': 'MATCH (n:EmotionalExpression) RETURN count(n) as count',
                'TemporalPattern': 'MATCH (n:TemporalPattern) RETURN count(n) as count',
                'ContextTrigger': 'MATCH (n:ContextTrigger) RETURN count(n) as count'
            }
            
            for node_type, query in queries.items():
                result = session.run(query).single()
                count = result['count'] if result else 0
                results[node_type] = count
                if count > 0:
                    print(f"   Found {count} {node_type} nodes")
            
            total_avatar_nodes = sum(results.values())
            
            if total_avatar_nodes == 0:
                print("✅ No Avatar Intelligence System data found. Nothing to clean.")
                return
            
            print(f"\n📊 Total Avatar system nodes to remove: {total_avatar_nodes}")
            
            # Perform cleanup
            print("\n🧹 Starting cleanup...")
            
            cleanup_queries = [
                # Remove relationships first
                'MATCH (cp:CommunicationProfile)-[r]-() DELETE r',
                'MATCH (rp:RelationshipPattern)-[r]-() DELETE r', 
                'MATCH (sp:SignaturePhrase)-[r]-() DELETE r',
                'MATCH (stp:StylePattern)-[r]-() DELETE r',
                'MATCH (tp:TopicPreference)-[r]-() DELETE r',
                'MATCH (ee:EmotionalExpression)-[r]-() DELETE r',
                'MATCH (tmp:TemporalPattern)-[r]-() DELETE r',
                'MATCH (ct:ContextTrigger)-[r]-() DELETE r',
                
                # Remove nodes
                'MATCH (n:AvatarSystem) DELETE n',
                'MATCH (n:CommunicationProfile) DELETE n',
                'MATCH (n:RelationshipPattern) DELETE n',
                'MATCH (n:SignaturePhrase) DELETE n',
                'MATCH (n:StylePattern) DELETE n',
                'MATCH (n:TopicPreference) DELETE n',
                'MATCH (n:EmotionalExpression) DELETE n',
                'MATCH (n:TemporalPattern) DELETE n',
                'MATCH (n:ContextTrigger) DELETE n'
            ]
            
            for query in cleanup_queries:
                try:
                    result = session.run(query)
                    print(f"   ✅ Executed: {query[:50]}...")
                except Exception as e:
                    print(f"   ⚠️  Warning executing {query[:30]}...: {e}")
            
            print("\n🔍 Verifying cleanup...")
            
            # Verify cleanup
            remaining = 0
            for node_type, query in queries.items():
                result = session.run(query).single()
                count = result['count'] if result else 0
                remaining += count
                if count > 0:
                    print(f"   ⚠️  {count} {node_type} nodes still remain")
            
            if remaining == 0:
                print("✅ Cleanup completed successfully!")
                print("\n🚀 You can now run a fresh deployment:")
                print("   python3 examples/basic_usage.py")
                print("   OR")
                print("   python3 src/avatar_system_deployment.py --password your_password --command deploy")
            else:
                print(f"⚠️  Cleanup partially completed. {remaining} nodes still remain.")
                print("   You may need to run this cleanup again or check for constraint issues.")
        
        driver.close()
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    clean_avatar_system()
