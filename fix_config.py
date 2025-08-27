#!/usr/bin/env python3
"""
Script to check and fix configuration files for Avatar Engine
"""

import os
import json
from pathlib import Path
import sys

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def check_and_fix_config():
    """Check for existing configuration and fix if needed"""
    
    # The configuration is stored in ~/.avatar-engine/avatar_config.json
    config_dir = Path.home() / ".avatar-engine"
    config_file = config_dir / "avatar_config.json"
    
    print("🔍 Checking for existing configuration files...")
    print("-" * 50)
    
    if config_file.exists():
        print(f"✓ Found configuration file: {config_file}")
        
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            # Check the model setting
            current_model = config_data.get('anthropic', {}).get('model', 'not set')
            print(f"  Current model in config: {current_model}")
            
            # Check if it's one of the outdated models
            outdated_models = [
                "claude-3-sonnet-20240229",
                "claude-3-5-sonnet-20241022",
                "claude-3-sonnet"
            ]
            
            if current_model in outdated_models:
                print(f"  ⚠️  Outdated model detected: {current_model}")
                
                # Update to correct model
                if 'anthropic' not in config_data:
                    config_data['anthropic'] = {}
                
                config_data['anthropic']['model'] = 'claude-3-5-sonnet-20240620'
                
                # Save the updated config
                with open(config_file, 'w') as f:
                    json.dump(config_data, f, indent=2)
                
                print(f"  ✅ Updated model to: claude-3-5-sonnet-20240620")
                print(f"  ✅ Configuration file updated successfully!")
            else:
                print(f"  ✓ Model configuration is already correct")
                
        except Exception as e:
            print(f"  ❌ Error reading/updating config file: {e}")
            print("  💡 You may need to delete the config file and let it regenerate")
            print(f"     Run: rm {config_file}")
    else:
        print(f"ℹ️  No existing configuration file found at {config_file}")
        print("   The default configuration will be used.")
    
    # Also check for environment variable
    env_model = os.getenv('CLAUDE_MODEL')
    if env_model:
        print(f"\n🔍 Environment variable CLAUDE_MODEL is set to: {env_model}")
        if env_model in ["claude-3-sonnet-20240229", "claude-3-5-sonnet-20241022"]:
            print("  ⚠️  This is an outdated model!")
            print("  💡 Update your environment variable:")
            print("     export CLAUDE_MODEL=claude-3-5-sonnet-20240620")
    
    print("\n📋 Correct model names for Anthropic API:")
    print("  • claude-3-5-sonnet-20240620 (recommended - latest Sonnet)")
    print("  • claude-3-opus-20240229")
    print("  • claude-3-haiku-20240307")
    
    # Test the configuration
    print("\n🧪 Testing configuration...")
    from src.config_manager import ConfigManager
    
    try:
        config = ConfigManager()
        print(f"✓ Configuration loaded successfully")
        print(f"  Model being used: {config.anthropic.model}")
        
        if config.anthropic.model == "claude-3-5-sonnet-20240620":
            print("✅ Model configuration is correct!")
            return True
        else:
            print(f"⚠️  Model is not the recommended one: {config.anthropic.model}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Avatar Engine - Configuration Check & Fix")
    print("=" * 50)
    
    success = check_and_fix_config()
    
    if success:
        print("\n✨ Configuration is ready! You can now run:")
        print("   python3 ./enhanced_deployment.py --analyze-all")
    else:
        print("\n⚠️  Please fix the configuration issues above and try again.")
        sys.exit(1)
