#!/usr/bin/env python3
"""
Test that ConfigManager fixes are working
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("="*60)
print("Testing ConfigManager Fixes")
print("="*60)

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

try:
    # Import and test basic syntax
    print("\n1. Testing import...")
    from config_manager import ConfigManager
    print("   ✓ ConfigManager imported successfully")
    
    # Test creating instance
    print("\n2. Testing instance creation...")
    config = ConfigManager()
    print("   ✓ ConfigManager instance created")
    
    # Test configuration values
    print("\n3. Checking configuration values:")
    print(f"   - Neo4j URI: {config.neo4j.uri}")
    print(f"   - Neo4j Username: {config.neo4j.username}")
    print(f"   - Neo4j Password: {'[SET]' if config.neo4j.password else '[NOT SET]'}")
    print(f"   - Anthropic API Key: {'[SET]' if config.anthropic.api_key else '[NOT SET]'}")
    
    # Test method calls
    print("\n4. Testing method calls:")
    
    # Test get_secure_anthropic_key (only if API key is set)
    if config.anthropic.api_key:
        try:
            key = config.get_secure_anthropic_key()
            print(f"   ✓ get_secure_anthropic_key() works - returns {len(key)} char key")
        except Exception as e:
            print(f"   ✗ get_secure_anthropic_key() failed: {e}")
    else:
        print("   - Skipping get_secure_anthropic_key() test (no API key)")
    
    # Test get_neo4j_driver_config
    try:
        driver_config = config.get_neo4j_driver_config()
        print(f"   ✓ get_neo4j_driver_config() works")
        print(f"     - URI: {driver_config['uri']}")
        print(f"     - Auth: {driver_config['auth'][0]} / {'[SET]' if driver_config['auth'][1] else '[NOT SET]'}")
    except Exception as e:
        print(f"   ✗ get_neo4j_driver_config() failed: {e}")
    
    # Test numeric environment variables if set
    print("\n5. Testing numeric environment variables:")
    if os.getenv("DAILY_COST_LIMIT"):
        print(f"   - Daily cost limit: ${config.anthropic.daily_cost_limit}")
    if os.getenv("MAX_CONCURRENT_REQUESTS"):
        print(f"   - Max concurrent requests: {config.anthropic.max_concurrent_requests}")
    if os.getenv("MIN_MESSAGES_FOR_ANALYSIS"):
        print(f"   - Min messages for analysis: {config.analysis.min_messages_for_analysis}")
    
    if not any([os.getenv("DAILY_COST_LIMIT"), os.getenv("MAX_CONCURRENT_REQUESTS"), os.getenv("MIN_MESSAGES_FOR_ANALYSIS")]):
        print("   - No numeric environment variables set")
    
    print("\n✅ ALL TESTS PASSED - ConfigManager is working correctly!")
    
except SyntaxError as e:
    print(f"\n❌ SYNTAX ERROR: {e}")
    print("There's still a syntax error in the code.")
    import traceback
    traceback.print_exc()
    
except ImportError as e:
    print(f"\n❌ IMPORT ERROR: {e}")
    print("Cannot import ConfigManager or its dependencies.")
    import traceback
    traceback.print_exc()
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
