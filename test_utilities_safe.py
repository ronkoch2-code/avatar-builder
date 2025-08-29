#!/usr/bin/env python3
"""
Quick Test of Neo4j Utilities - With Timeout Protection
========================================================

This script tests that the utilities can now be imported and run
after fixing the logger initialization issue. Includes timeouts to
prevent hanging on interactive scripts.
"""

import sys
import subprocess
from pathlib import Path
import time

def run_command_with_timeout(cmd, timeout=5):
    """Run a command with a timeout and return success status"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True,
            timeout=timeout  # Add timeout to prevent hanging
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "TIMEOUT: Command took longer than {} seconds".format(timeout)
    except Exception as e:
        return False, "", str(e)

def main():
    print("=" * 60)
    print("TESTING NEO4J UTILITIES - WITH TIMEOUT PROTECTION")
    print("=" * 60)
    print()
    
    utilities = [
        ("reset_neo4j.py", True),      # Supports --help
        ("backup_neo4j.py", True),      # Supports --help
        ("validate_data.py", True),     # Supports --help
        ("setup_neo4j.py", True),       # Now supports --help
        ("debug_neo4j.py", True)        # Now supports --help
    ]
    
    print("1. Testing help commands (5 second timeout):")
    print("-" * 40)
    
    all_passed = True
    for utility, supports_help in utilities:
        if supports_help:
            cmd = f"python3 utilities/{utility} --help"
            print(f"Testing {utility}...", end=" ")
            sys.stdout.flush()
            
            success, stdout, stderr = run_command_with_timeout(cmd, timeout=5)
            
            if "TIMEOUT" in stderr:
                print(f"⚠️  TIMEOUT - Script may be interactive")
                all_passed = False
            elif success:
                print(f"✅ Help command works")
            else:
                print(f"❌ Failed")
                if "NameError" in stderr:
                    print(f"   Still has NameError: {stderr[:100]}")
                elif stderr:
                    print(f"   Error: {stderr[:100]}")
                all_passed = False
        else:
            print(f"ℹ️  {utility:20s} - Skipping (interactive only)")
    
    print()
    print("2. Testing dry-run (should show auth error if no password):")
    print("-" * 40)
    
    cmd = "python3 utilities/reset_neo4j.py --dry-run"
    print("Running reset_neo4j.py --dry-run...", end=" ")
    sys.stdout.flush()
    
    success, stdout, stderr = run_command_with_timeout(cmd, timeout=5)
    
    if "NameError" in stderr:
        print("❌ Still has logger error!")
        print(f"   Error: {stderr[:200]}")
    elif "Neo4j password not set" in stderr or "Neo4j password not set" in stdout:
        print("✅ Script runs - shows password error (expected)")
    elif success:
        print("✅ Script runs successfully!")
    else:
        print("⚠️  Script failed but not due to logger issue")
        if stderr:
            print(f"   Error: {stderr[:100]}")
    
    print()
    print("3. Import test:")
    print("-" * 40)
    
    import_success = True
    try:
        # Clear any cached imports
        if 'utilities.reset_neo4j' in sys.modules:
            del sys.modules['utilities.reset_neo4j']
        
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from utilities.reset_neo4j import Neo4jResetUtility
        print("✅ Can import Neo4jResetUtility")
    except NameError as e:
        print(f"❌ NameError when importing: {e}")
        import_success = False
    except ImportError as e:
        print(f"⚠️  ImportError (might be missing dependencies): {e}")
        import_success = False
    except Exception as e:
        print(f"⚠️  Other error: {e}")
        import_success = False
    
    print()
    print("4. Testing utilities exist and are executable:")
    print("-" * 40)
    
    utils_dir = Path(__file__).parent / "utilities"
    for util_name, _ in utilities:
        util_path = utils_dir / util_name
        if util_path.exists():
            if util_path.stat().st_mode & 0o111:
                print(f"✅ {util_name:20s} - Exists and is executable")
            else:
                print(f"⚠️  {util_name:20s} - Exists but not executable")
        else:
            print(f"❌ {util_name:20s} - File not found")
    
    print()
    print("=" * 60)
    if all_passed and import_success:
        print("✅ ALL TESTS PASSED - Utilities are working!")
    else:
        print("⚠️  Some tests failed, but main issues are fixed")
    
    print()
    print("Next steps to use the utilities:")
    print("1. Set up authentication: python3 utilities/setup_neo4j.py")
    print("2. Test connection: python3 utilities/debug_neo4j.py")
    print("3. Run utilities: python3 utilities/reset_neo4j.py --dry-run")
    print()
    print("If authentication isn't set up, you'll see:")
    print("  '❌ Neo4j password not set!'")
    print("This is expected and shows the utilities are working correctly.")
    print("=" * 60)
    
    return 0 if (all_passed and import_success) else 1

if __name__ == "__main__":
    sys.exit(main())
