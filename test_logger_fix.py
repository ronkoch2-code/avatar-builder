#!/usr/bin/env python3
"""
Quick Test of Neo4j Utilities After Logger Fix
==============================================

This script tests that the utilities can now be imported and run
after fixing the logger initialization issue.
"""

import sys
import subprocess
from pathlib import Path

def run_command(cmd):
    """Run a command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    print("=" * 60)
    print("TESTING NEO4J UTILITIES - LOGGER FIX")
    print("=" * 60)
    print()
    
    utilities = [
        "reset_neo4j.py",
        "backup_neo4j.py", 
        "validate_data.py",
        "setup_neo4j.py",
        "debug_neo4j.py"
    ]
    
    print("1. Testing help commands for all utilities:")
    print("-" * 40)
    
    all_passed = True
    for utility in utilities:
        cmd = f"python3 utilities/{utility} --help"
        success, stdout, stderr = run_command(cmd)
        
        if success:
            print(f"✅ {utility:20s} - Help command works")
        else:
            print(f"❌ {utility:20s} - Failed")
            if "NameError" in stderr:
                print(f"   Still has NameError: {stderr[:100]}")
            all_passed = False
    
    print()
    print("2. Testing dry-run (will show auth error if no password):")
    print("-" * 40)
    
    cmd = "python3 utilities/reset_neo4j.py --dry-run"
    success, stdout, stderr = run_command(cmd)
    
    if "NameError" in stderr:
        print("❌ Still has logger error!")
        print(f"   Error: {stderr[:200]}")
    elif "Neo4j password not set" in stderr or "Neo4j password not set" in stdout:
        print("✅ Script runs correctly - shows password not set error (expected)")
    elif success:
        print("✅ Script runs successfully!")
    else:
        print("⚠️  Script failed but not due to logger issue")
    
    print()
    print("3. Import test:")
    print("-" * 40)
    
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from utilities.reset_neo4j import Neo4jResetUtility
        print("✅ Can import Neo4jResetUtility")
    except NameError as e:
        print(f"❌ NameError when importing: {e}")
    except ImportError as e:
        print(f"⚠️  ImportError (might be missing dependencies): {e}")
    except Exception as e:
        print(f"⚠️  Other error: {e}")
    
    print()
    print("=" * 60)
    if all_passed:
        print("✅ ALL UTILITIES FIXED - No more logger errors!")
    else:
        print("⚠️  Some utilities still have issues")
    
    print()
    print("Next steps:")
    print("1. Set up authentication: python3 utilities/setup_neo4j.py")
    print("2. Test connection: python3 utilities/debug_neo4j.py")
    print("3. Run utilities: python3 utilities/reset_neo4j.py --dry-run")
    print("=" * 60)

if __name__ == "__main__":
    main()
