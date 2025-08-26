#!/usr/bin/env python3
"""
Enhanced Avatar Engine - Demo Script
===================================

This script demonstrates the enhanced Avatar Engine capabilities including:
- LLM-powered personality analysis
- Relationship dynamics understanding
- Enhanced avatar prompt generation

Prerequisites:
1. Neo4j running with conversation data
2. Anthropic API key set as environment variable
3. Enhanced schema deployed
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config_manager import ConfigManager, CostMonitor
from neo4j import GraphDatabase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def demo_enhanced_avatar_system():
    """
    Comprehensive demo of enhanced Avatar Engine capabilities
    """
    print("🤖 Avatar Engine Enhanced - Demo")
    print("=" * 50)
    
    try:
        # Initialize configuration
        print("\n📋 Loading Configuration...")
        config = ConfigManager()
        
        # Check prerequisites
        if not config.anthropic.api_key:
            print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
            print("   Please set your Claude API key:")
            print("   export ANTHROPIC_API_KEY='your_key_here'")
            return
        
        if not config.neo4j.password:
            print("❌ Error: Neo4j password not configured")
            print("   Run: python src/config_manager.py")
            return
        
        print("✅ Configuration loaded successfully")
        
        # Test database connection
        print("\n🔌 Testing Neo4j Connection...")
        try:
            driver_config = config.get_neo4j_driver_config()
            driver = GraphDatabase.driver(**driver_config)
            
            with driver.session() as session:
                result = session.run("MATCH (p:Person) RETURN count(p) as people").single()
                people_count = result["people"]
                
            print(f"✅ Connected to Neo4j - Found {people_count} people")
            
        except Exception as e:
            print(f"❌ Neo4j connection failed: {e}")
            return
        
        # Initialize enhanced system
        print("\n🚀 Initializing Enhanced Avatar System...")
        try:
            from enhanced_avatar_pipeline import EnhancedAvatarSystemManager
            
            avatar_system = EnhancedAvatarSystemManager(
                neo4j_driver=driver,
                anthropic_api_key=config.anthropic.api_key,
                claude_model=config.anthropic.model,
                enable_llm_analysis=True
            )
            
            print("✅ Enhanced Avatar System initialized")
            
        except Exception as e:
            print(f"❌ Failed to initialize system: {e}")
            return
        
        # Show available people for analysis
        print("\n👥 Finding People for Analysis...")
        people = await get_sample_people(driver, min_messages=100)
        
        if not people:
            print("❌ No people found with sufficient messages for analysis")
            print("   Make sure your Neo4j database has conversation data loaded")
            return
        
        print(f"✅ Found {len(people)} people with sufficient data:")
        for i, person in enumerate(people[:5], 1):
            has_llm = "🧠" if person.get("has_llm_analysis") else "⏳"
            print(f"   {i}. {has_llm} {person['name']} ({person['message_count']} messages)")
        
        # Select person for demo
        if len(people) == 1:
            selected_person = people[0]
        else:
            # Auto-select first person without LLM analysis, or first person
            selected_person = next(
                (p for p in people if not p.get("has_llm_analysis")), 
                people[0]
            )
        
        print(f"\n🎯 Selected for demo: {selected_person['name']}")
        
        # Check cost limits
        cost_monitor = CostMonitor(config)
        current_cost = cost_monitor.get_today_cost()
        daily_limit = config.anthropic.daily_cost_limit
        
        print(f"\n💰 Cost Check:")
        print(f"   Today's cost: ${current_cost:.2f}")
        print(f"   Daily limit: ${daily_limit:.2f}")
        print(f"   Available: ${daily_limit - current_cost:.2f}")
        
        if current_cost >= daily_limit * 0.9:
            print("⚠️  Warning: Near daily cost limit. Consider increasing limit or trying tomorrow.")
            response = input("Continue anyway? (y/N): ").strip().lower()
            if response != 'y':
                print("Demo cancelled.")
                return
        
        # Demonstrate enhanced analysis
        print(f"\n🧠 Starting Enhanced Analysis for {selected_person['name']}...")
        print("   This will analyze personality, relationships, and communication patterns")
        print("   Estimated cost: $3-8 depending on message count")
        
        response = input("Proceed with analysis? (Y/n): ").strip().lower()
        if response == 'n':
            print("Analysis skipped.")
        else:
            try:
                # Run enhanced analysis
                result = await avatar_system.create_enhanced_profile(
                    person_identifier=selected_person['name'],
                    min_messages=50
                )
                
                print("\n✅ Analysis completed!")
                print(f"   Status: {result['status']}")
                print(f"   Messages analyzed: {result.get('message_count', 0)}")
                print(f"   Cost: ${result.get('total_cost', 0):.4f}")
                print(f"   Analysis types: {len(result.get('analysis_results', []))}")
                
                # Show analysis details
                if result.get('analysis_results'):
                    print("\n📊 Analysis Results:")
                    for analysis in result['analysis_results']:
                        confidence = analysis.get('confidence', 0)
                        confidence_icon = "🟢" if confidence > 0.7 else "🟡" if confidence > 0.4 else "🔴"
                        print(f"   {confidence_icon} {analysis['type'].replace('_', ' ').title()}: "
                              f"Confidence {confidence:.1%}, Cost ${analysis['cost']:.3f}")
                
                # Record cost
                if result.get('total_cost', 0) > 0:
                    cost_monitor.record_cost(result['total_cost'])
                
            except Exception as e:
                print(f"❌ Analysis failed: {e}")
        
        # Demonstrate avatar prompt generation
        print(f"\n🎭 Generating Avatar Prompts for {selected_person['name']}...")
        
        try:
            # Generate different types of prompts
            scenarios = [
                {
                    "name": "Casual 1:1 Conversation",
                    "type": "1:1",
                    "partners": ["Ron"],
                    "topic": "weekend plans",
                    "context": None
                },
                {
                    "name": "Professional Meeting",
                    "type": "professional", 
                    "partners": ["Colleagues"],
                    "topic": "project status",
                    "context": "Team standup meeting"
                },
                {
                    "name": "Family Chat",
                    "type": "group",
                    "partners": ["Family"],
                    "topic": "holiday planning",
                    "context": "Planning family gathering"
                }
            ]
            
            for i, scenario in enumerate(scenarios, 1):
                print(f"\n{i}. {scenario['name']}")
                print("-" * 40)
                
                prompt = await avatar_system.generate_enhanced_avatar_prompt(
                    person_identifier=selected_person['name'],
                    conversation_type=scenario['type'],
                    partners=scenario['partners'],
                    topic=scenario['topic'],
                    context=scenario['context']
                )
                
                # Truncate long prompts for display
                if len(prompt) > 300:
                    display_prompt = prompt[:300] + "..."
                else:
                    display_prompt = prompt
                
                print(f"Prompt: {display_prompt}")
                print()
            
            print("✅ Avatar prompts generated successfully!")
            print("   You can now use these prompts with any LLM (Claude, ChatGPT, etc.)")
            
        except Exception as e:
            print(f"❌ Prompt generation failed: {e}")
        
        # Show system statistics
        print("\n📈 System Statistics:")
        try:
            stats = avatar_system.get_system_statistics()
            print(f"   Profiles created: {stats.get('profiles_created', 0)}")
            print(f"   LLM analyses completed: {stats.get('llm_analyses_completed', 0)}")
            print(f"   Total cost: ${stats.get('total_cost', 0):.4f}")
            
            if stats.get('llm_total_cost'):
                print(f"   LLM total tokens: {stats.get('llm_total_tokens', 0):,}")
                print(f"   LLM total cost: ${stats.get('llm_total_cost', 0):.4f}")
        except Exception as e:
            print(f"   Statistics unavailable: {e}")
        
        print("\n🎉 Demo completed successfully!")
        print("\nNext steps:")
        print("1. Analyze more people: python enhanced_deployment.py --analyze-all")
        print("2. Check system status: python enhanced_deployment.py --status")
        print("3. Generate more avatar prompts for your use cases")
        print("4. Integrate with your preferred LLM API")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        logger.exception("Demo error")
        
    finally:
        if 'driver' in locals():
            driver.close()
            print("\n🔌 Database connection closed")


async def get_sample_people(driver, min_messages: int = 100):
    """Get sample people for demo"""
    with driver.session() as session:
        # Get people with sufficient messages
        query = """
        MATCH (p:Person)-[:SENT]->(m:Message)
        WITH p, count(m) as messageCount
        WHERE messageCount >= $min_messages
        OPTIONAL MATCH (p)-[:HAS_COMMUNICATION_PROFILE]->(cp:CommunicationProfile)
        RETURN p.id as person_id,
               p.name as person_name,
               messageCount,
               cp.llmEnhanced as has_llm_analysis
        ORDER BY messageCount DESC
        LIMIT 10
        """
        
        results = session.run(query, min_messages=min_messages).data()
        
        people = []
        for record in results:
            people.append({
                "person_id": record["person_id"],
                "name": record["person_name"], 
                "message_count": record["messageCount"],
                "has_llm_analysis": bool(record.get("has_llm_analysis"))
            })
        
        return people


if __name__ == "__main__":
    print("Starting Enhanced Avatar Engine Demo...")
    print("This demo will show you the key capabilities of the LLM-enhanced system.")
    print()
    
    # Check if running from correct directory
    if not Path("src").exists():
        print("❌ Please run this script from the Avatar-Engine directory:")
        print("   cd /Volumes/FS001/pythonscripts/Avatar-Engine")
        print("   python examples/demo.py")
        sys.exit(1)
    
    # Run the demo
    asyncio.run(demo_enhanced_avatar_system())
