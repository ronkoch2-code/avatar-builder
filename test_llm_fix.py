#!/usr/bin/env python3
"""
Test script for LLM Integration - Debug JSON Parsing Issues
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.llm_integrator import LLMIntegrator, AnalysisRequest, AnalysisType

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_llm_integration():
    """Test the LLM integration with sample data"""
    
    print("=" * 60)
    print("LLM Integration Test - JSON Parsing Fix")
    print("=" * 60)
    
    try:
        # Initialize LLM integrator
        llm = LLMIntegrator(model="claude-sonnet-4-20250514")
        print("✅ LLM Integrator initialized successfully")
        
        # Create sample conversation data
        sample_messages = [
            {
                "body": "Hey! How was your weekend?",
                "isFromMe": True,
                "date": "2025-08-26 10:00",
                "partner_name": "Test Friend"
            },
            {
                "body": "It was great! Went hiking on Saturday and had a BBQ on Sunday. How about yours?",
                "isFromMe": False,
                "date": "2025-08-26 10:05",
                "partner_name": "Test Friend"
            },
            {
                "body": "Sounds fun! I mostly worked on my project and caught up on some reading.",
                "isFromMe": True,
                "date": "2025-08-26 10:10",
                "partner_name": "Test Friend"
            },
            {
                "body": "Nice! What are you reading these days?",
                "isFromMe": False,
                "date": "2025-08-26 10:15",
                "partner_name": "Test Friend"
            },
            {
                "body": "Currently reading 'Atomic Habits' - really insightful book about building good habits.",
                "isFromMe": True,
                "date": "2025-08-26 10:20",
                "partner_name": "Test Friend"
            },
            {
                "body": "Oh I've heard great things about that! I should add it to my list.",
                "isFromMe": False,
                "date": "2025-08-26 10:25",
                "partner_name": "Test Friend"
            },
            {
                "body": "Definitely recommend it! The concepts are really practical and actionable.",
                "isFromMe": True,
                "date": "2025-08-26 10:30",
                "partner_name": "Test Friend"
            },
            {
                "body": "I'll check it out. By the way, are you free for lunch tomorrow?",
                "isFromMe": False,
                "date": "2025-08-26 10:35",
                "partner_name": "Test Friend"
            },
            {
                "body": "Let me check my calendar... Yes, I'm free! Where were you thinking?",
                "isFromMe": True,
                "date": "2025-08-26 10:40",
                "partner_name": "Test Friend"
            },
            {
                "body": "How about that new Thai place downtown? I've been wanting to try it.",
                "isFromMe": False,
                "date": "2025-08-26 10:45",
                "partner_name": "Test Friend"
            }
        ]
        
        print(f"✅ Created sample conversation with {len(sample_messages)} messages")
        
        # Test 1: Personality Analysis
        print("\n" + "-" * 40)
        print("Test 1: Personality Analysis")
        print("-" * 40)
        
        personality_request = AnalysisRequest(
            person_id="test_user_001",
            person_name="Test User",
            analysis_type=AnalysisType.PERSONALITY_PROFILE,
            conversation_data=sample_messages,
            max_messages=10
        )
        
        print("Analyzing personality profile...")
        personality_result = await llm.analyze_personality(personality_request)
        
        if personality_result:
            print("✅ Personality analysis successful!")
            print(f"   Request ID: {personality_result.request_id}")
            print(f"   Cost: ${personality_result.cost:.4f}")
            print(f"   Tokens used: {personality_result.tokens_used}")
            
            if hasattr(personality_result.result, 'big_five_scores'):
                print("\n   Big Five Scores:")
                for trait, score in personality_result.result.big_five_scores.items():
                    print(f"   - {trait.capitalize()}: {score:.2f}")
            
            if hasattr(personality_result.result, 'confidence_score'):
                print(f"\n   Confidence Score: {personality_result.result.confidence_score:.2f}")
        else:
            print("❌ Personality analysis failed")
        
        # Test 2: Relationship Analysis
        print("\n" + "-" * 40)
        print("Test 2: Relationship Analysis")
        print("-" * 40)
        
        relationship_request = AnalysisRequest(
            person_id="test_user_001",
            person_name="Test User",
            analysis_type=AnalysisType.RELATIONSHIP_DYNAMICS,
            conversation_data=sample_messages,
            max_messages=10
        )
        
        print("Analyzing relationship dynamics...")
        relationship_results = await llm.analyze_relationships(relationship_request)
        
        if relationship_results:
            print(f"✅ Relationship analysis successful! Found {len(relationship_results)} relationships")
            for i, result in enumerate(relationship_results, 1):
                print(f"\n   Relationship {i}:")
                print(f"   - Partner: {result.result.partner_name}")
                print(f"   - Type: {result.result.relationship_type}")
                print(f"   - Intimacy Level: {result.result.intimacy_level:.2f}")
                print(f"   - Cost: ${result.cost:.4f}")
        else:
            print("❌ No relationships analyzed")
        
        # Print cost summary
        print("\n" + "=" * 40)
        print("Cost Summary")
        print("=" * 40)
        cost_summary = llm.get_cost_summary()
        print(f"Total cost: ${cost_summary['total_cost']:.4f}")
        print(f"Total tokens: {cost_summary['total_tokens']}")
        print(f"Total analyses: {cost_summary['total_analyses']}")
        
        if cost_summary['cost_by_type']:
            print("\nCost by analysis type:")
            for analysis_type, stats in cost_summary['cost_by_type'].items():
                print(f"  {analysis_type}:")
                print(f"    - Count: {stats['count']}")
                print(f"    - Total Cost: ${stats['total_cost']:.4f}")
                print(f"    - Total Tokens: {stats['total_tokens']}")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        logger.exception("Test error details:")
        return False
    
    return True


async def test_json_extraction():
    """Test the JSON extraction function specifically"""
    
    print("\n" + "=" * 60)
    print("Testing JSON Extraction Function")
    print("=" * 60)
    
    # Initialize a dummy integrator just to test the extraction method
    llm = LLMIntegrator(model="claude-sonnet-4-20250514")
    
    test_cases = [
        # Case 1: Pure JSON
        ('{"test": "value", "number": 42}', True),
        
        # Case 2: JSON in markdown code block
        ('```json\n{"test": "value", "number": 42}\n```', True),
        
        # Case 3: JSON with explanatory text
        ('Here is the analysis:\n\n{"test": "value", "number": 42}\n\nThat should work.', True),
        
        # Case 4: JSON in code block without language specifier
        ('```\n{"test": "value", "number": 42}\n```', True),
        
        # Case 5: Invalid JSON
        ('This is not JSON at all', False),
    ]
    
    for i, (test_input, should_succeed) in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Input: {test_input[:50]}..." if len(test_input) > 50 else f"Input: {test_input}")
        
        try:
            result = llm._extract_json_from_response(test_input)
            if should_succeed:
                print(f"✅ Successfully extracted: {result}")
            else:
                print(f"❌ Unexpectedly succeeded for invalid input")
        except Exception as e:
            if should_succeed:
                print(f"❌ Failed to extract valid JSON: {e}")
            else:
                print(f"✅ Correctly rejected invalid JSON")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    print("Starting LLM Integration Tests...")
    print("Note: This will make actual API calls to Claude and incur costs.\n")
    
    response = input("Do you want to proceed? (yes/no): ").strip().lower()
    
    if response == "yes":
        # Run JSON extraction tests first (no API calls)
        asyncio.run(test_json_extraction())
        
        # Then run full integration tests
        print("\nDo you want to run the full integration tests (will make API calls)?")
        response = input("(yes/no): ").strip().lower()
        
        if response == "yes":
            success = asyncio.run(test_llm_integration())
            sys.exit(0 if success else 1)
        else:
            print("Skipping integration tests.")
    else:
        print("Tests cancelled.")
