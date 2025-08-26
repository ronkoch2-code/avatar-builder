#!/usr/bin/env python3
"""
List People in Database
======================

Shows all people in your Neo4j database with their message counts.
Use this to get exact names for avatar analysis.
"""

import sys
import os
from neo4j import GraphDatabase

def list_people():
    """List all people in the database with message counts"""
    
    NEO4J_URI = "bolt://localhost:7687"
    NEO4J_USERNAME = "neo4j"
    NEO4J_PASSWORD = input("Enter Neo4j password: ")
    
    print("👥 People in Your Database")
    print("=" * 50)
    
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        
        with driver.session() as session:
            # Get all people with message counts
            result = session.run("""
                MATCH (p:Person)-[:SENT]->(m:Message)
                WITH p, count(m) as messageCount
                RETURN p.name as name, p.id as personId, p.phone as phone, messageCount
                ORDER BY messageCount DESC
                LIMIT 50
            """)
            
            people = [dict(record) for record in result]
            
            if not people:
                print("❌ No people with messages found!")
                return
            
            print(f"Found {len(people)} people with messages:\n")
            
            # Show people grouped by message count ranges
            high_volume = [p for p in people if p['messageCount'] >= 100]
            medium_volume = [p for p in people if 25 <= p['messageCount'] < 100]
            low_volume = [p for p in people if 10 <= p['messageCount'] < 25]
            
            print("🔥 HIGH VOLUME (100+ messages) - Best for avatar analysis:")
            for i, person in enumerate(high_volume[:10], 1):
                name = person['name'] or '[No Name]'
                print(f"  {i:2d}. {name} ({person['messageCount']} messages)")
            
            if medium_volume:
                print(f"\n📊 MEDIUM VOLUME (25-99 messages) - Good for analysis:")
                for i, person in enumerate(medium_volume[:10], 1):
                    name = person['name'] or '[No Name]'
                    print(f"  {i:2d}. {name} ({person['messageCount']} messages)")
            
            if low_volume:
                print(f"\n📉 LOW VOLUME (10-24 messages) - Limited analysis:")
                for i, person in enumerate(low_volume[:5], 1):
                    name = person['name'] or '[No Name]'
                    print(f"  {i:2d}. {name} ({person['messageCount']} messages)")
            
            print("\n" + "="*60)
            print("💡 COPY/PASTE COMMANDS:")
            print("="*60)
            
            # Show exact commands for top people
            top_people = people[:5]
            for person in top_people:
                name = person['name']
                if name and name.strip():
                    # Show command without quotes first
                    print(f"\n# Process {name}:")
                    print(f"python3 src/avatar_intelligence_pipeline.py --password YOUR_PASSWORD --command init-person --person {name}")
                    
                    # If name has spaces, show alternative with quotes
                    if ' ' in name:
                        print(f"# Alternative if spaces cause issues:")
                        print(f'python3 src/avatar_intelligence_pipeline.py --password YOUR_PASSWORD --command init-person --person "{name}"')
            
            print(f"\n🚀 PROCESS ALL HIGH-VOLUME PEOPLE:")
            print(f"python3 src/avatar_intelligence_pipeline.py --password YOUR_PASSWORD --command init-all --min-messages 100")
            print(f"\n🎯 PROCESS ALL MEDIUM+ VOLUME PEOPLE:")
            print(f"python3 src/avatar_intelligence_pipeline.py --password YOUR_PASSWORD --command init-all --min-messages 25")
            
        driver.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    list_people()
