#!/usr/bin/env python3
"""
Fix Model Configuration Script
==============================

This script updates the Claude model identifier in the configuration file
to use the current valid model name.
"""

import json
import os
from pathlib import Path
import sys

def fix_model_config():
    """Update the model name in the configuration file"""
    
    # Path to configuration file
    config_dir = Path.home() / ".avatar-engine"
    config_path = config_dir / "avatar_config.json"
    
    print(f"🔧 Updating configuration at: {config_path}")
    
    try:
        # Read existing configuration
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Update the model name
            old_model = config.get('anthropic', {}).get('model', 'not found')
            new_model = "claude-sonnet-4-20250514"
            
            if 'anthropic' not in config:
                config['anthropic'] = {}
            
            config['anthropic']['model'] = new_model
            
            # Write updated configuration
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"✅ Successfully updated model from '{old_model}' to '{new_model}'")
            print(f"📝 Configuration saved to: {config_path}")
            
            # Display the updated anthropic section
            print("\n📋 Updated Anthropic Configuration:")
            print(json.dumps(config.get('anthropic', {}), indent=2))
            
        else:
            print(f"⚠️ Configuration file not found at {config_path}")
            print("Creating default configuration with correct model...")
            
            # Create default config with correct model
            default_config = {
                "anthropic": {
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 4000,
                    "temperature": 0.1
                },
                "neo4j": {
                    "uri": "bolt://localhost:7687",
                    "username": "neo4j",
                    "database": "neo4j"
                }
            }
            
            config_dir.mkdir(exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            print(f"✅ Created new configuration with correct model")
            print(f"📝 Configuration saved to: {config_path}")
            print("\n⚠️ Note: You'll need to add your Anthropic API key to the configuration")
            
    except Exception as e:
        print(f"❌ Error updating configuration: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(fix_model_config())
