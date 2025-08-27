#!/usr/bin/env python3
"""
System Update and Verification Script
=====================================

This script updates the Avatar Engine system to use the correct
Claude model and verifies the configuration.
"""

import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

def update_system():
    """Complete system update and verification"""
    
    print("=" * 60)
    print("🚀 Avatar Engine System Update")
    print("=" * 60)
    print(f"📅 Update started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Step 1: Fix the model configuration
    print("Step 1: Updating model configuration...")
    print("-" * 40)
    
    result = subprocess.run([sys.executable, "fix_model_config.py"], 
                          capture_output=True, text=True)
    
    if result.returncode != 0:
        print("❌ Failed to update configuration")
        print(result.stderr)
        return 1
    
    print(result.stdout)
    print()
    
    # Step 2: Verify the configuration
    print("Step 2: Verifying configuration...")
    print("-" * 40)
    
    config_path = Path.home() / ".avatar-engine" / "avatar_config.json"
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        model = config.get('anthropic', {}).get('model', 'not found')
        api_key_set = bool(config.get('anthropic', {}).get('api_key'))
        
        print(f"✅ Model: {model}")
        print(f"✅ API Key: {'Configured' if api_key_set else '⚠️ NOT SET - Please add your API key'}")
        
        # Check Neo4j configuration
        neo4j_config = config.get('neo4j', {})
        print(f"✅ Neo4j URI: {neo4j_config.get('uri', 'not set')}")
        print(f"✅ Neo4j Username: {neo4j_config.get('username', 'not set')}")
        
    except Exception as e:
        print(f"❌ Error reading configuration: {e}")
        return 1
    
    print()
    
    # Step 3: Test the connection (optional)
    print("Step 3: Testing system...")
    print("-" * 40)
    
    try:
        # Try importing the modules to verify everything is in place
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from config_manager import ConfigManager
        
        config_manager = ConfigManager()
        print(f"✅ Configuration manager loaded successfully")
        print(f"✅ Model set to: {config_manager.anthropic.model}")
        
        if not config_manager.anthropic.api_key:
            print()
            print("⚠️ WARNING: Anthropic API key not configured!")
            print("Please add your API key to the configuration file:")
            print(f"  {config_path}")
            print()
            print("Add this to the 'anthropic' section:")
            print('  "api_key": "your-api-key-here"')
        
    except Exception as e:
        print(f"⚠️ Warning during testing: {e}")
    
    print()
    print("=" * 60)
    print("✨ System update complete!")
    print("=" * 60)
    print()
    
    # Provide next steps
    print("📋 Next steps:")
    print("1. Ensure your Anthropic API key is configured in:")
    print(f"   {config_path}")
    print()
    print("2. Test the system with:")
    print("   python3 enhanced_deployment.py --status")
    print()
    print("3. Try analyzing a person:")
    print('   python3 enhanced_deployment.py --analyze-person "Aisling Murphy" --force')
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(update_system())
