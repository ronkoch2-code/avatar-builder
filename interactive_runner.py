#!/usr/bin/env python3
"""
Interactive Avatar Analysis Runner
=================================

Easy-to-use script that avoids command line quote issues.
"""

import sys
import os
from neo4j import GraphDatabase

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from avatar_intelligence_pipeline import AvatarSystemManager

def get_password():
    """Get Neo4j password from user"""
    import getpass
    return getpass.getpass("Enter Neo4j password: ")

def show_menu():
    """Show main menu options"""
    print("\n🤖 Avatar Intelligence Analysis")
    print("=" * 35)
    print("1. Process ALL people (recommended)")
    print("2. Process specific person")
    print("3. Generate AI prompt for someone")
    print("4. Show system statistics")
    print("5. List people in database")
    print("0. Exit")
    print()

def process_all_people(manager):
    """Process all people with sufficient messages"""
    print("\n📊 Message count options:")
    print("1. 25+ messages (more people, less detailed)")
    print("2. 50+ messages (balanced - recommended)")
    print("3. 100+ messages (fewer people, very detailed)")
    
    choice = input("\nChoose option (1-3): ").strip()
    
    min_messages_map = {'1': 25, '2': 50, '3': 100}
    min_messages = min_messages_map.get(choice, 50)
    
    print(f"\n🚀 Processing all people with {min_messages}+ messages...")
    print("This may take a few minutes...")
    
    try:
        stats = manager.initialize_all_people(min_messages=min_messages)
        
        print(f"\n✅ Analysis Complete!")
        print(f"   People found: {stats['found']}")
        print(f"   Successfully processed: {stats['processed']}")
        print(f"   Avatar profiles created: {stats['created']}")
        if stats['errors'] > 0:
            print(f"   Errors: {stats['errors']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return False

def process_specific_person(manager):
    """Process a specific person"""
    print("\n👤 Enter person's name exactly as it appears in your database")
    print("(Use the 'List people' option first if unsure)")
    
    person_name = input("\nPerson name: ").strip()
    
    if not person_name:
        print("❌ No name entered.")
        return
    
    print(f"\n🔍 Processing {person_name}...")
    
    try:
        result = manager.initialize_person(person_name)
        
        if 'error' in result:
            print(f"❌ {result['error']}")
        else:
            print(f"✅ Success!")
            print(f"   Person: {result['person']}")
            print(f"   Messages analyzed: {result['messages_analyzed']}")
            print(f"   Profile created: {result['profile_created']}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def generate_prompt(manager):
    """Generate AI prompt for someone"""
    print("\n🎭 Generate AI Avatar Prompt")
    
    person_name = input("Person name: ").strip()
    if not person_name:
        print("❌ No name entered.")
        return
    
    print("\nOptional parameters (press Enter to skip):")
    partners_input = input("Conversation partners (comma-separated): ").strip()
    topic = input("Topic/context: ").strip()
    
    partners = [p.strip() for p in partners_input.split(',')] if partners_input else None
    topic = topic if topic else None
    
    print(f"\n🎯 Generating prompt for {person_name}...")
    
    try:
        prompt = manager.generate_response(person_name, partners=partners, topic=topic)
        
        print("\n" + "="*60)
        print("🤖 GENERATED AI AVATAR PROMPT:")
        print("="*60)
        print(prompt)
        print("="*60)
        
        # Offer to save to file
        save = input("\nSave prompt to file? (y/n): ").strip().lower()
        if save == 'y':
            filename = f"avatar_prompt_{person_name.replace(' ', '_')}.txt"
            with open(filename, 'w') as f:
                f.write(prompt)
            print(f"✅ Saved to {filename}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def show_stats(manager):
    """Show system statistics"""
    try:
        stats = manager.get_system_stats()
        
        print("\n📊 Avatar Intelligence System Statistics")
        print("=" * 45)
        for key, value in stats.items():
            print(f"   {key.replace('_', ' ').title()}: {value}")
        
    except Exception as e:
        print(f"❌ Error getting stats: {e}")

def list_people(driver):
    """List people in database"""
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (p:Person)-[:SENT]->(m:Message)
                WITH p, count(m) as messageCount
                RETURN p.name as name, messageCount
                ORDER BY messageCount DESC
                LIMIT 20
            """)
            
            people = [dict(record) for record in result]
            
            print("\n👥 Top 20 People by Message Count")
            print("=" * 40)
            
            for i, person in enumerate(people, 1):
                name = person['name'] or '[No Name]'
                count = person['messageCount']
                print(f"  {i:2d}. {name} ({count} messages)")
            
            if not people:
                print("❌ No people with messages found!")
                
    except Exception as e:
        print(f"❌ Error listing people: {e}")

def main():
    """Main interactive loop"""
    print("🤖 Avatar Intelligence System - Interactive Runner")
    print("Avoids command line quote issues!")
    
    # Get password
    try:
        password = get_password()
        driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", password))
        manager = AvatarSystemManager(driver)
        
        print("✅ Connected to Neo4j successfully!")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    try:
        while True:
            show_menu()
            choice = input("Choose option (0-5): ").strip()
            
            if choice == '0':
                print("👋 Goodbye!")
                break
            elif choice == '1':
                process_all_people(manager)
            elif choice == '2':
                process_specific_person(manager)
            elif choice == '3':
                generate_prompt(manager)
            elif choice == '4':
                show_stats(manager)
            elif choice == '5':
                list_people(driver)
            else:
                print("❌ Invalid choice. Please try again.")
            
            input("\nPress Enter to continue...")
    
    finally:
        driver.close()

if __name__ == "__main__":
    main()
