#!/usr/bin/env python3
"""
Simple test runner for Avatar Intelligence System
================================================

Run this script to test the system without needing make or complex setup.
"""

import subprocess
import sys
import os

def run_tests():
    """Run all tests with proper path setup"""
    
    # Change to the project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    
    print("🧪 Running Avatar Intelligence System Tests")
    print("=" * 50)
    print(f"Project directory: {project_dir}")
    print()
    
    try:
        # Run pytest with verbose output
        cmd = [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr)
        
        print(f"\nReturn code: {result.returncode}")
        
        if result.returncode == 0:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed or had errors.")
            
        return result.returncode == 0
        
    except FileNotFoundError:
        print("❌ pytest not found. Please install with: pip install pytest")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False


def check_dependencies():
    """Check if required dependencies are available"""
    
    print("📦 Checking dependencies...")
    
    required_packages = ['pytest', 'neo4j', 'pandas', 'numpy']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} - OK")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    else:
        print("✅ All dependencies available")
        return True


def main():
    """Main test runner"""
    
    print("Avatar Intelligence System Test Runner")
    print("=" * 40)
    print()
    
    # Check dependencies first
    if not check_dependencies():
        print("\n❌ Please install missing dependencies before running tests.")
        sys.exit(1)
    
    print()
    
    # Run tests
    success = run_tests()
    
    if success:
        print("\n🎉 Test suite completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Test suite failed. Check output above for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
