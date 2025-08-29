#!/usr/bin/env python3
"""
Quick fix for Neo4j password loading issue
==========================================

This script installs python-dotenv if missing and tests the password loading.
"""

import subprocess
import sys
import os
from pathlib import Path

def check_and_install_dotenv():
    """Check if python-dotenv is installed, install if not"""
    try:
        import dotenv
        print("✅ python-dotenv is already installed")
        return True
    except ImportError:
        print("❌ python-dotenv is NOT installed")
        response = input("Install python-dotenv? (y/N): ")
        if response.lower() == 'y':
            try:
                print("Installing python-dotenv...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dotenv"])
                print("✅ python-dotenv installed successfully")
                return True
            except subprocess.CalledProcessError:
                print("❌ Failed to install python-dotenv")
                print("Try manually: pip install python-dotenv")
                return False
        else:
            print("⚠️  Without python-dotenv, .env files won't be loaded")
            return False

def test_password_loading():
    """Test if password loads correctly"""
    print("\n" + "=" * 60)
    print("Testing password loading...")
    print("=" * 60)
    
    # Check .env file
    env_file = Path.cwd() / ".env"
    if env_file.exists():
        print(f"✅ Found .env file: {env_file}")
        with open(env_file, 'r') as f:
            lines = f.readlines()
            for line in lines:
                if 'NEO4J_PASSWORD' in line:
                    print(f"   Contains: {line.strip()}")
    else:
        print(f"❌ No .env file found at {env_file}")
        print("Creating one now...")
        password = input("Enter your Neo4j password: ")
        with open(env_file, 'w') as f:
            f.write(f"NEO4J_PASSWORD={password}\n")
        print(f"✅ Created .env file")
    
    # Load environment
    try:
        from dotenv import load_dotenv
        load_dotenv(override=True)  # Force reload
        print("✅ Loaded .env file with dotenv")
    except ImportError:
        print("❌ Can't load .env - python-dotenv not available")
        return False
    
    # Check if password is now set
    password = os.getenv("NEO4J_PASSWORD")
    if password:
        masked = password[:2] + "*" * (len(password) - 4) + password[-2:] if len(password) > 4 else "*" * len(password)
        print(f"✅ NEO4J_PASSWORD is set: {masked}")
        return True
    else:
        print("❌ NEO4J_PASSWORD is still not set")
        return False

def main():
    print("NEO4J PASSWORD LOADING FIX")
    print("=" * 60)
    
    # Step 1: Check python-dotenv
    if not check_and_install_dotenv():
        print("\n⚠️  python-dotenv is required for .env file support")
        print("Install it manually: pip install python-dotenv")
        return 1
    
    # Step 2: Test password loading
    if not test_password_loading():
        print("\n⚠️  Password loading failed")
        print("Try setting it manually:")
        print("  export NEO4J_PASSWORD='your_password'")
        return 1
    
    # Step 3: Test with actual utility
    print("\n" + "=" * 60)
    print("Testing with reset_neo4j.py...")
    print("=" * 60)
    
    result = subprocess.run(
        ["python3", "utilities/reset_neo4j.py", "--dry-run"],
        capture_output=True,
        text=True
    )
    
    if "Neo4j password not set" in result.stderr:
        print("❌ Utility still reports password not set")
        print("\nDebugging info:")
        print("STDERR:", result.stderr[:500])
    elif "Successfully connected" in result.stdout or "No data nodes found" in result.stdout:
        print("✅ Utility can now connect!")
    else:
        print("⚠️  Utility ran but connection status unclear")
        if result.stderr:
            print("STDERR:", result.stderr[:500])
        if result.stdout:
            print("STDOUT:", result.stdout[:500])
    
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("1. If python-dotenv was just installed, try again:")
    print("   python3 utilities/reset_neo4j.py --dry-run")
    print("\n2. If still failing, use direct password argument:")
    print("   python3 utilities/reset_neo4j.py --password 'your_password' --dry-run")
    print("\n3. For more debugging:")
    print("   python3 test_env_loading.py")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
