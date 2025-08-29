#!/usr/bin/env python3
"""
Test environment variable loading
"""
import os
import sys
from pathlib import Path

print("Testing environment variable loading...")
print("=" * 60)

# Check if .env file exists
env_file = Path.cwd() / ".env"
print(f"1. Checking .env file at: {env_file}")
if env_file.exists():
    print(f"   ✓ .env file exists")
    with open(env_file, 'r') as f:
        content = f.read()
        print(f"   Content: {repr(content)}")
else:
    print(f"   ✗ .env file not found")

# Check environment variable BEFORE loading dotenv
print("\n2. NEO4J_PASSWORD before loading .env:")
password_before = os.getenv("NEO4J_PASSWORD")
if password_before:
    print(f"   ✓ Already set: {password_before[:2]}...{password_before[-2:]}")
else:
    print(f"   ✗ Not set")

# Try to load dotenv
print("\n3. Loading .env with python-dotenv:")
try:
    from dotenv import load_dotenv
    result = load_dotenv()
    print(f"   load_dotenv() returned: {result}")
    
    # Try explicit path
    if env_file.exists():
        result2 = load_dotenv(env_file)
        print(f"   load_dotenv(explicit path) returned: {result2}")
except ImportError:
    print("   ✗ python-dotenv not installed!")
    print("   Run: pip install python-dotenv")
    sys.exit(1)

# Check environment variable AFTER loading dotenv
print("\n4. NEO4J_PASSWORD after loading .env:")
password_after = os.getenv("NEO4J_PASSWORD")
if password_after:
    print(f"   ✓ Set: {password_after[:2]}...{password_after[-2:]}")
    print(f"   Length: {len(password_after)}")
else:
    print(f"   ✗ Still not set!")

# Try the actual config loading logic from reset_neo4j.py
print("\n5. Testing actual config loading:")
sys.path.append(str(Path(__file__).parent.parent))

try:
    from src.config_manager import ConfigManager
    config = ConfigManager()
    if hasattr(config, 'neo4j'):
        print(f"   Using ConfigManager")
        print(f"   Password set: {bool(config.neo4j.password)}")
        if config.neo4j.password:
            print(f"   Password: {config.neo4j.password[:2]}...{config.neo4j.password[-2:]}")
    else:
        print("   ConfigManager has no neo4j attribute")
except ImportError:
    print("   ConfigManager not found, using fallback")
    class Neo4jConfig:
        def __init__(self):
            self.password = os.getenv("NEO4J_PASSWORD", "")
            print(f"   Neo4jConfig password: {bool(self.password)}")
            if self.password:
                print(f"   Password: {self.password[:2]}...{self.password[-2:]}")
    
    config = Neo4jConfig()

print("\n" + "=" * 60)
print("Diagnosis:")
if password_after:
    print("✅ Environment variable is being loaded correctly")
    print("   The issue might be in how the config object is being created")
else:
    print("❌ Environment variable is NOT being loaded from .env")
    print("   Check that python-dotenv is installed: pip install python-dotenv")
