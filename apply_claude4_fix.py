#!/usr/bin/env python3
"""
Apply Claude Sonnet 4 Model Update - v1.0.2
============================================

This script applies the correct Claude Sonnet 4 model identifier
to fix all 404 API errors.
"""

import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# The correct Claude Sonnet 4 model as of August 2025
CORRECT_MODEL = "claude-sonnet-4-20250514"

def apply_model_fix():
    """Apply the model fix to the configuration"""
    
    print("=" * 60)
    print("🚀 Avatar Engine - Claude Sonnet 4 Model Update")
    print("=" * 60)
    print(f"📅 Update started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Target Model: {CORRECT_MODEL}")
    print()
    
    # Path to configuration file
    config_dir = Path.home() / ".avatar-engine"
    config_path = config_dir / "avatar_config.json"
    
    print(f"📁 Configuration location: {config_path}")
    print()
    
    # Step 1: Update or create configuration
    print("Step 1: Updating configuration file...")
    print("-" * 40)
    
    try:
        if config_path.exists():
            # Read existing configuration
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            old_model = config.get('anthropic', {}).get('model', 'not set')
            print(f"   Current model: {old_model}")
            
            # Update the model
            if 'anthropic' not in config:
                config['anthropic'] = {}
            
            config['anthropic']['model'] = CORRECT_MODEL
            
            # Write updated configuration
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"✅ Updated model to: {CORRECT_MODEL}")
            
        else:
            # Create new configuration
            print("   Creating new configuration...")
            
            config = {
                "anthropic": {
                    "model": CORRECT_MODEL,
                    "api_key": "",  # User needs to add this
                    "max_tokens": 4000,
                    "temperature": 0.1,
                    "max_concurrent_requests": 3,
                    "rate_limit_per_minute": 50,
                    "daily_cost_limit": 50.0,
                    "cost_alert_threshold": 20.0
                },
                "neo4j": {
                    "uri": "bolt://localhost:7687",
                    "username": "neo4j",
                    "password": "",  # User needs to add this
                    "database": "neo4j",
                    "max_connection_pool_size": 50,
                    "connection_timeout": 30.0
                },
                "analysis": {
                    "min_messages_for_analysis": 50,
                    "max_messages_per_analysis": 1000,
                    "personality_analysis_enabled": True,
                    "relationship_analysis_enabled": True,
                    "topic_analysis_enabled": True,
                    "emotional_analysis_enabled": True,
                    "min_confidence_score": 0.3,
                    "high_confidence_threshold": 0.7
                },
                "system": {
                    "log_level": "INFO",
                    "enable_llm_analysis": True,
                    "enable_cost_monitoring": True,
                    "backup_enabled": True,
                    "backup_interval_hours": 24,
                    "async_processing": True,
                    "batch_size": 10,
                    "retry_attempts": 3
                }
            }
            
            # Create directory if needed
            config_dir.mkdir(exist_ok=True)
            
            # Write configuration
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"✅ Created configuration with model: {CORRECT_MODEL}")
            
    except Exception as e:
        print(f"❌ Error updating configuration: {e}")
        return False
    
    print()
    
    # Step 2: Verify the configuration
    print("Step 2: Verifying configuration...")
    print("-" * 40)
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Check model
        model = config.get('anthropic', {}).get('model')
        if model == CORRECT_MODEL:
            print(f"✅ Model verified: {model}")
        else:
            print(f"❌ Model mismatch: {model}")
            return False
        
        # Check API key
        api_key = config.get('anthropic', {}).get('api_key', '')
        if api_key:
            print(f"✅ API key is configured")
        else:
            print(f"⚠️  API key not set")
            print(f"   Please add your Anthropic API key to:")
            print(f"   {config_path}")
            print(f"   In the 'anthropic' section, add:")
            print(f'   "api_key": "your-api-key-here"')
        
        # Check Neo4j password
        neo4j_pass = config.get('neo4j', {}).get('password', '')
        if neo4j_pass:
            print(f"✅ Neo4j password is configured")
        else:
            print(f"⚠️  Neo4j password not set")
            print(f"   Add to the 'neo4j' section if needed")
        
    except Exception as e:
        print(f"❌ Error verifying configuration: {e}")
        return False
    
    print()
    
    # Step 3: Test the system
    print("Step 3: Testing the update...")
    print("-" * 40)
    
    try:
        # Add src to path
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        
        from config_manager import ConfigManager
        
        config_mgr = ConfigManager()
        
        if config_mgr.anthropic.model == CORRECT_MODEL:
            print(f"✅ Configuration manager loaded successfully")
            print(f"   Model: {config_mgr.anthropic.model}")
            print(f"   API Key: {'Configured' if config_mgr.anthropic.api_key else 'NOT SET'}")
        else:
            print(f"❌ Model mismatch in configuration manager")
            return False
            
    except Exception as e:
        print(f"⚠️  Could not test configuration manager: {e}")
    
    print()
    print("=" * 60)
    print("✨ Model update complete!")
    print("=" * 60)
    print()
    
    # Display summary
    print("📋 Update Summary:")
    print(f"   ✅ Model updated to: {CORRECT_MODEL}")
    print(f"   ✅ Configuration saved to: {config_path}")
    print(f"   ✅ Version: 1.0.2")
    print()
    
    print("📝 Model Information:")
    print(f"   Model: Claude Sonnet 4")
    print(f"   Identifier: {CORRECT_MODEL}")
    print(f"   Release: May 2025")
    print(f"   Status: Current Production Model")
    print()
    
    if not api_key:
        print("⚠️  IMPORTANT: Add your Anthropic API key before testing!")
        print(f"   Edit: {config_path}")
        print()
    
    print("🧪 Test the fix with:")
    print('   python3 enhanced_deployment.py --analyze-person "Aisling Murphy" --force')
    print()
    print("📦 Push to GitHub with:")
    print("   ./git_push_ready.sh")
    print("   git push origin main")
    print()
    
    return True

if __name__ == "__main__":
    success = apply_model_fix()
    sys.exit(0 if success else 1)
