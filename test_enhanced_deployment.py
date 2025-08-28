#!/usr/bin/env python3
"""
Test script for enhanced_deployment.py fixes
"""

import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import argparse
        print("✅ argparse imported")
    except ImportError as e:
        print(f"❌ Failed to import argparse: {e}")
        return False
    
    try:
        import asyncio
        print("✅ asyncio imported")
    except ImportError as e:
        print(f"❌ Failed to import asyncio: {e}")
        return False
    
    try:
        import logging
        print("✅ logging imported")
    except ImportError as e:
        print(f"❌ Failed to import logging: {e}")
        return False
    
    try:
        from neo4j import GraphDatabase
        print("✅ neo4j imported")
    except ImportError as e:
        print(f"⚠️  neo4j not installed (optional for testing): {e}")
    
    try:
        from src.config_manager import ConfigManager, CostMonitor
        print("✅ config_manager imported")
    except ImportError as e:
        print(f"❌ Failed to import config_manager: {e}")
        return False
    
    try:
        from src.enhanced_avatar_pipeline import EnhancedAvatarSystemManager
        print("✅ enhanced_avatar_pipeline imported")
    except ImportError as e:
        print(f"❌ Failed to import enhanced_avatar_pipeline: {e}")
        return False
    
    return True

def test_script_syntax():
    """Test that the enhanced_deployment.py script has correct syntax"""
    print("\nTesting enhanced_deployment.py syntax...")
    
    script_path = Path(__file__).parent / "enhanced_deployment.py"
    
    try:
        with open(script_path, 'r') as f:
            code = f.read()
        
        # Try to compile the code
        compile(code, str(script_path), 'exec')
        print("✅ Script syntax is valid")
        
        # Check for async/sync issues
        if "async def main()" in code:
            print("❌ main() is still async - needs to be sync")
            return False
        
        if "asyncio.run(main())" in code:
            print("❌ Still using asyncio.run(main()) - should call main() directly")
            return False
        
        if "loop.run_until_complete" in code:
            print("✅ Using proper event loop management for async functions")
        
        return True
        
    except SyntaxError as e:
        print(f"❌ Syntax error in script: {e}")
        return False
    except Exception as e:
        print(f"❌ Error checking script: {e}")
        return False

def test_main_function():
    """Test that the main function can be called"""
    print("\nTesting main function structure...")
    
    try:
        # Import the script module
        import enhanced_deployment
        
        # Check if main is not async
        import inspect
        if inspect.iscoroutinefunction(enhanced_deployment.main):
            print("❌ main() is still an async function")
            return False
        
        print("✅ main() is a regular function (not async)")
        return True
        
    except Exception as e:
        print(f"❌ Error testing main function: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Enhanced Deployment Script Fixes")
    print("=" * 60)
    
    all_passed = True
    
    # Run tests
    if not test_imports():
        all_passed = False
    
    if not test_script_syntax():
        all_passed = False
    
    if not test_main_function():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests passed! The enhanced_deployment.py script should work now.")
        print("\nYou can now run:")
        print("  python3 enhanced_deployment.py --help")
        print("  python3 enhanced_deployment.py --status")
        print("  python3 enhanced_deployment.py --deploy")
    else:
        print("❌ Some tests failed. Please review the errors above.")
    print("=" * 60)

if __name__ == "__main__":
    main()
