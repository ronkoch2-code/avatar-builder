#!/usr/bin/env python3
"""
Test Claude Model Update
========================

Quick test to verify the Claude model update is working correctly.
"""

import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_model_update():
    """Test that the model has been updated correctly"""
    
    print("🔍 Testing Claude Model Update...")
    print("=" * 50)
    
    # Test 1: Check source code
    print("\n1. Checking source code...")
    try:
        from config_manager import AnthropicConfig
        default_config = AnthropicConfig()
        
        expected_model = "claude-sonnet-4-20250514"
        actual_model = default_config.model
        
        if actual_model == expected_model:
            print(f"✅ Source code model: {actual_model}")
        else:
            print(f"❌ Source code model mismatch!")
            print(f"   Expected: {expected_model}")
            print(f"   Got: {actual_model}")
            return False
    except Exception as e:
        print(f"❌ Error checking source: {e}")
        return False
    
    # Test 2: Check configuration file
    print("\n2. Checking configuration file...")
    config_path = Path.home() / ".avatar-engine" / "avatar_config.json"
    
    if config_path.exists():
        import json
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            config_model = config.get('anthropic', {}).get('model', 'not set')
            print(f"   Current config model: {config_model}")
            
            if config_model == expected_model:
                print(f"✅ Configuration already updated!")
            else:
                print(f"⚠️  Configuration needs update (run fix_model_config.py)")
                print(f"   Current: {config_model}")
                print(f"   Should be: {expected_model}")
        except Exception as e:
            print(f"❌ Error reading config: {e}")
    else:
        print("⚠️  Configuration file doesn't exist yet")
        print(f"   Will be created at: {config_path}")
    
    # Test 3: Try importing with the configuration
    print("\n3. Testing configuration manager...")
    try:
        from config_manager import ConfigManager
        config_mgr = ConfigManager()
        
        print(f"   Loaded model: {config_mgr.anthropic.model}")
        
        if config_mgr.anthropic.model == expected_model:
            print(f"✅ Configuration manager using correct model!")
        else:
            print(f"⚠️  Model mismatch - needs configuration update")
            
        # Check API key
        if config_mgr.anthropic.api_key:
            print(f"✅ API key is configured")
        else:
            print(f"⚠️  API key not set - add to configuration file")
            
    except Exception as e:
        print(f"⚠️  Could not test configuration manager: {e}")
    
    print("\n" + "=" * 50)
    print("📋 Summary:")
    print(f"   Target Model: {expected_model}")
    print(f"   Model Family: Claude Sonnet 4 (Latest)")
    print(f"   Release Date: May 2025")
    print("\n✨ Model update complete in source code!")
    print("\n📝 Next steps:")
    print("1. Run: python3 fix_model_config.py")
    print("2. Run: python3 enhanced_deployment.py --status")
    print("3. Test: python3 enhanced_deployment.py --analyze-person \"Aisling Murphy\" --force")
    
    return True

if __name__ == "__main__":
    success = test_model_update()
    sys.exit(0 if success else 1)
