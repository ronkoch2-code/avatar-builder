#!/usr/bin/env python3
"""
Debug Neo4j Connection Issues
============================

This script helps diagnose Neo4j authentication problems.
"""

import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

def debug_connection():
    print("=" * 60)
    print("NEO4J CONNECTION DEBUGGER")
    print("=" * 60)

    # Check environment variables
    print("\n1. Environment Variables:")
    print("-" * 40)
    neo4j_vars = {
        "NEO4J_URI": os.getenv("NEO4J_URI"),
        "NEO4J_USERNAME": os.getenv("NEO4J_USERNAME"),
        "NEO4J_PASSWORD": os.getenv("NEO4J_PASSWORD"),
        "NEO4J_DATABASE": os.getenv("NEO4J_DATABASE")
    }

    for var, value in neo4j_vars.items():
        if value:
            if "PASSWORD" in var:
                # Mask password for security
                masked_value = value[:2] + "*" * (len(value) - 4) + value[-2:] if len(value) > 4 else "*" * len(value)
                print(f"  {var}: {masked_value} (length: {len(value)})")
            else:
                print(f"  {var}: {value}")
        else:
            print(f"  {var}: NOT SET ❌")

    # Check for .env file
    print("\n2. .env File:")
    print("-" * 40)
    env_paths = [
        Path.cwd() / ".env",
        Path(__file__).parent.parent / ".env",
        Path.home() / ".avatar-engine" / ".env"
    ]

    env_found = False
    for env_path in env_paths:
        if env_path.exists():
            print(f"  ✓ Found: {env_path}")
            env_found = True
            # Check if it contains Neo4j settings
            with open(env_path, 'r') as f:
                content = f.read()
                if "NEO4J" in content:
                    print("    Contains Neo4j settings")
        else:
            print(f"  ✗ Not found: {env_path}")

    if not env_found:
        print("  ⚠️  No .env file found")

    # Try loading config manager
    print("\n3. Config Manager:")
    print("-" * 40)
    try:
        from src.config_manager import ConfigManager
        config = ConfigManager()
        
        print(f"  Neo4j URI: {config.neo4j.uri}")
        print(f"  Neo4j Username: {config.neo4j.username}")
        if config.neo4j.password:
            masked = config.neo4j.password[:2] + "*" * (len(config.neo4j.password) - 4) + config.neo4j.password[-2:] if len(config.neo4j.password) > 4 else "*" * len(config.neo4j.password)
            print(f"  Neo4j Password: {masked} (length: {len(config.neo4j.password)})")
        else:
            print(f"  Neo4j Password: NOT SET ❌")
        print(f"  Neo4j Database: {config.neo4j.database}")
    except ImportError as e:
        print(f"  ❌ Failed to import ConfigManager: {e}")
    except ValueError as e:
        print(f"  ⚠️  ConfigManager validation error: {e}")
    except Exception as e:
        print(f"  ❌ Error loading ConfigManager: {e}")

    # Try direct Neo4j connection
    print("\n4. Direct Neo4j Connection Test:")
    print("-" * 40)
    try:
        from neo4j import GraphDatabase
        
        # Get connection parameters
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        username = os.getenv("NEO4J_USERNAME", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "")
        
        if not password:
            print("  ⚠️  No password found in environment")
            print("\n  To set the password, use one of these methods:")
            print("  Method 1: Export environment variable")
            print("    export NEO4J_PASSWORD='your_password'")
            print("\n  Method 2: Create .env file")
            print("    echo 'NEO4J_PASSWORD=your_password' > .env")
            print("\n  Method 3: Pass password as argument")
            print("    python3 utilities/reset_neo4j.py --password your_password")
        else:
            print(f"  Attempting connection to {uri}")
            print(f"  Username: {username}")
            
            try:
                driver = GraphDatabase.driver(uri, auth=(username, password))
                with driver.session() as session:
                    result = session.run("RETURN 1 as test")
                    result.single()
                print("  ✅ CONNECTION SUCCESSFUL!")
                driver.close()
            except Exception as conn_error:
                print(f"  ❌ Connection failed: {conn_error}")
                print("\n  Common issues:")
                print("  - Wrong password")
                print("  - Neo4j not running")
                print("  - Wrong URI (should be bolt://localhost:7687)")
                print("  - Firewall blocking port 7687")
                
    except ImportError:
        print("  ❌ neo4j driver not installed")
        print("  Run: pip install neo4j")
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")

    # Provide recommendations
    print("\n5. Recommendations:")
    print("-" * 40)
    
    if not neo4j_vars["NEO4J_PASSWORD"]:
        print("📌 Set the NEO4J_PASSWORD environment variable:")
        print("   export NEO4J_PASSWORD='your_actual_password'")
        print("\n📌 Or create a .env file in the project root:")
        print("   echo 'NEO4J_PASSWORD=your_actual_password' > /Volumes/FS001/pythonscripts/Avatar-Engine/.env")
        print("\n📌 Or pass it directly to the utility:")
        print("   python3 utilities/reset_neo4j.py --password 'your_actual_password'")
    else:
        print("✓ Password is set in environment")
        print("  If connection still fails, verify:")
        print("  - The password is correct")
        print("  - Neo4j is running (check with: neo4j status)")
        print("  - The URI is correct (default: bolt://localhost:7687)")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Debug Neo4j connection issues for Avatar-Engine utilities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script helps diagnose Neo4j authentication problems by checking:
  1. Environment variables
  2. .env file locations
  3. Config manager settings
  4. Direct connection test
  5. Providing specific recommendations

Example:
  python3 debug_neo4j.py
        """
    )
    
    # Parse arguments (mainly for --help)
    args = parser.parse_args()
    
    # Run the debug
    debug_connection()
