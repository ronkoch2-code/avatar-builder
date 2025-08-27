#!/usr/bin/env python3
"""
Comprehensive diagnostic script for Avatar Engine model configuration
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def run_diagnostics():
    """Run complete diagnostics on the Avatar Engine configuration"""
    
    print("🔬 Avatar Engine - Complete Diagnostics")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # 1. Check Python version
    print("1️⃣  Python Environment:")
    print(f"   Python version: {sys.version}")
    print(f"   Executable: {sys.executable}")
    print()
    
    # 2. Check environment variables
    print("2️⃣  Environment Variables:")
    important_vars = ['ANTHROPIC_API_KEY', 'CLAUDE_MODEL', 'NEO4J_PASSWORD']
    for var in important_vars:
        value = os.getenv(var)
        if var == 'ANTHROPIC_API_KEY' and value:
            # Mask API key for security
            masked = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
            print(f"   {var}: {masked}")
        elif var == 'NEO4J_PASSWORD' and value:
            print(f"   {var}: ***SET***")
        else:
            print(f"   {var}: {value if value else 'NOT SET'}")
    print()
    
    # 3. Check configuration files
    print("3️⃣  Configuration Files:")
    config_locations = [
        Path.home() / ".avatar-engine" / "avatar_config.json",
        Path.cwd() / "avatar_config.json",
        Path.cwd() / ".env"
    ]
    
    for config_path in config_locations:
        if config_path.exists():
            print(f"   ✓ Found: {config_path}")
            if config_path.suffix == '.json':
                try:
                    with open(config_path, 'r') as f:
                        data = json.load(f)
                        model = data.get('anthropic', {}).get('model', 'not specified')
                        print(f"     Model in file: {model}")
                except Exception as e:
                    print(f"     ⚠️  Error reading: {e}")
        else:
            print(f"   ✗ Not found: {config_path}")
    print()
    
    # 4. Load and check actual configuration
    print("4️⃣  Active Configuration:")
    try:
        from src.config_manager import ConfigManager
        config = ConfigManager()
        
        print(f"   ✓ Configuration loaded successfully")
        print(f"   Active model: {config.anthropic.model}")
        print(f"   API key set: {'Yes' if config.anthropic.api_key else 'No'}")
        print(f"   Max tokens: {config.anthropic.max_tokens}")
        print(f"   Temperature: {config.anthropic.temperature}")
        print(f"   Daily cost limit: ${config.anthropic.daily_cost_limit}")
        
        # Check if model is correct
        valid_models = [
            "claude-3-5-sonnet-20240620",
            "claude-3-opus-20240229", 
            "claude-3-haiku-20240307"
        ]
        
        if config.anthropic.model in valid_models:
            print(f"   ✅ Model is valid!")
        else:
            print(f"   ❌ Invalid model! Should be one of: {', '.join(valid_models)}")
            
    except Exception as e:
        print(f"   ❌ Failed to load configuration: {e}")
        import traceback
        traceback.print_exc()
    print()
    
    # 5. Test Anthropic API connection (without actually calling it)
    print("5️⃣  Anthropic API Setup:")
    try:
        import anthropic
        print(f"   ✓ Anthropic library installed: {anthropic.__version__}")
    except ImportError:
        print(f"   ✗ Anthropic library not installed")
        print(f"     Run: pip install anthropic")
    
    try:
        from src.config_manager import ConfigManager
        config = ConfigManager()
        if config.anthropic.api_key:
            # Just check if we can create a client
            from anthropic import Anthropic
            client = Anthropic(api_key=config.anthropic.api_key)
            print(f"   ✓ Anthropic client initialized")
            print(f"   📌 Model to use: {config.anthropic.model}")
        else:
            print(f"   ⚠️  No API key configured")
    except Exception as e:
        print(f"   ❌ Failed to initialize Anthropic client: {e}")
    print()
    
    # 6. Check Neo4j connection
    print("6️⃣  Neo4j Database:")
    try:
        from src.config_manager import ConfigManager
        from neo4j import GraphDatabase
        
        config = ConfigManager()
        driver_config = config.get_neo4j_driver_config()
        
        print(f"   URI: {driver_config['uri']}")
        print(f"   Username: {driver_config['auth'][0]}")
        print(f"   Database: {driver_config.get('database', 'neo4j')}")
        
        # Try to connect
        try:
            driver = GraphDatabase.driver(**driver_config)
            with driver.session() as session:
                result = session.run("RETURN 1 as test")
                if result.single()['test'] == 1:
                    print(f"   ✅ Neo4j connection successful!")
            driver.close()
        except Exception as e:
            print(f"   ❌ Neo4j connection failed: {e}")
            
    except Exception as e:
        print(f"   ❌ Failed to check Neo4j: {e}")
    print()
    
    # 7. Summary and recommendations
    print("7️⃣  Recommendations:")
    print("-" * 50)
    
    recommendations = []
    
    # Check for common issues
    try:
        from src.config_manager import ConfigManager
        config = ConfigManager()
        
        if config.anthropic.model not in ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229", "claude-3-haiku-20240307"]:
            recommendations.append(f"Update model to 'claude-3-5-sonnet-20240620' (current: {config.anthropic.model})")
        
        if not config.anthropic.api_key:
            recommendations.append("Set ANTHROPIC_API_KEY environment variable")
            
        if not config.neo4j.password:
            recommendations.append("Set NEO4J_PASSWORD in configuration")
            
    except:
        recommendations.append("Fix configuration loading issues first")
    
    # Check for old config file
    old_config = Path.home() / ".avatar-engine" / "avatar_config.json"
    if old_config.exists():
        try:
            with open(old_config, 'r') as f:
                data = json.load(f)
                if data.get('anthropic', {}).get('model') != "claude-3-5-sonnet-20240620":
                    recommendations.append(f"Update or delete config file: {old_config}")
        except:
            pass
    
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    else:
        print("   ✅ Everything looks good! Ready to run:")
        print("      python3 ./enhanced_deployment.py --analyze-all")
    
    print()
    print("=" * 50)
    print("Diagnostics complete!")

if __name__ == "__main__":
    try:
        run_diagnostics()
    except KeyboardInterrupt:
        print("\n⚠️  Diagnostics interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
