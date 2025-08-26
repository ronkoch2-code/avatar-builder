#!/usr/bin/env python3
"""
Complete Setup Verification for Avatar Intelligence System
=========================================================

This script verifies that your Avatar Intelligence System is properly set up.
Run this after installation to make sure everything works.
"""

import subprocess
import sys
import os
import importlib
from pathlib import Path

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f"🔍 {title}")
    print("="*60)

def print_success(message):
    """Print a success message"""
    print(f"✅ {message}")

def print_warning(message):
    """Print a warning message"""
    print(f"⚠️  {message}")

def print_error(message):
    """Print an error message"""
    print(f"❌ {message}")

def check_python_executable():
    """Check which Python executable is being used"""
    print_header("Python Executable Detection")
    
    python_cmd = None
    
    # Check python3
    try:
        result = subprocess.run(['python3', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"python3: {result.stdout.strip()}")
            python_cmd = 'python3'
    except FileNotFoundError:
        print_warning("python3 command not found")
    
    # Check python
    try:
        result = subprocess.run(['python', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"python: {result.stdout.strip()}")
            if python_cmd is None:
                python_cmd = 'python'
    except FileNotFoundError:
        print_warning("python command not found")
    
    if python_cmd:
        print_success(f"Recommended Python command: {python_cmd}")
        return python_cmd
    else:
        print_error("No Python executable found!")
        return None

def check_dependencies(python_cmd):
    """Check if required dependencies are installed"""
    print_header("Dependency Check")
    
    required_packages = {
        'neo4j': 'Neo4j Python driver',
        'pandas': 'Data manipulation library',
        'numpy': 'Numerical computing library',
        'pytest': 'Testing framework'
    }
    
    missing_packages = []
    
    for package, description in required_packages.items():
        try:
            importlib.import_module(package)
            print_success(f"{package}: {description}")
        except ImportError:
            print_error(f"{package}: {description} - NOT INSTALLED")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 To install missing packages:")
        print(f"   {python_cmd} -m pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_project_structure():
    """Check if project structure is correct"""
    print_header("Project Structure Check")
    
    expected_files = [
        'src/avatar_intelligence_pipeline.py',
        'src/avatar_system_deployment.py',
        'src/__init__.py',
        'tests/test_deployment.py',
        'examples/basic_usage.py',
        'requirements.txt',
        'setup.py',
        'pyproject.toml',
        'README.md',
        'QUICKSTART.md',
        'Makefile'
    ]
    
    missing_files = []
    
    for file_path in expected_files:
        if Path(file_path).exists():
            print_success(f"{file_path}")
        else:
            print_error(f"{file_path} - MISSING")
            missing_files.append(file_path)
    
    if missing_files:
        print_error(f"Missing files: {missing_files}")
        return False
    
    return True

def test_makefile(python_cmd):
    """Test Makefile functionality"""
    print_header("Makefile Test")
    
    try:
        # Test make help
        result = subprocess.run(['make', 'help'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print_success("make help works")
            
            # Look for Python detection
            if f"Detected Python:" in result.stdout:
                print_success("Python detection in Makefile works")
            else:
                print_warning("Python detection not visible in make help")
            
            return True
        else:
            print_error(f"make help failed: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print_error("make command not found")
        print("💡 On macOS, install with: xcode-select --install")
        return False
    except subprocess.TimeoutExpired:
        print_error("make help timed out")
        return False

def test_python_imports():
    """Test that our modules can be imported"""
    print_header("Module Import Test")
    
    sys.path.insert(0, 'src')
    
    modules_to_test = [
        'avatar_system_deployment',
        'avatar_intelligence_pipeline'
    ]
    
    success = True
    
    for module_name in modules_to_test:
        try:
            module = importlib.import_module(module_name)
            print_success(f"{module_name} imported successfully")
        except ImportError as e:
            print_error(f"{module_name} import failed: {e}")
            success = False
    
    return success

def run_basic_tests(python_cmd):
    """Run the basic test suite"""
    print_header("Basic Test Suite")
    
    try:
        result = subprocess.run([python_cmd, 'run_tests.py'], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print_success("All tests passed!")
            return True
        else:
            print_error("Some tests failed")
            print(f"Output: {result.stdout[-500:]}")  # Show last 500 chars
            return False
            
    except subprocess.TimeoutExpired:
        print_error("Tests timed out")
        return False
    except Exception as e:
        print_error(f"Error running tests: {e}")
        return False

def main():
    """Main verification function"""
    print("🤖 Avatar Intelligence System - Setup Verification")
    print("=" * 60)
    print("This script will verify your Avatar Intelligence System setup.")
    print("Run from the Avatar-Engine directory.")
    
    # Change to correct directory
    try:
        os.chdir('/Volumes/FS001/pythonscripts/Avatar-Engine/')
        print_success(f"Working directory: {os.getcwd()}")
    except FileNotFoundError:
        print_error("Avatar-Engine directory not found!")
        sys.exit(1)
    
    success_count = 0
    total_checks = 6
    
    # Run all checks
    checks = [
        ("Python Executable", check_python_executable),
        ("Project Structure", check_project_structure),
        ("Module Imports", test_python_imports),
    ]
    
    python_cmd = None
    
    for check_name, check_func in checks:
        try:
            if check_name == "Python Executable":
                python_cmd = check_func()
                if python_cmd:
                    success_count += 1
            else:
                if check_func():
                    success_count += 1
        except Exception as e:
            print_error(f"{check_name} check failed: {e}")
    
    # Only run dependency and advanced checks if we have Python
    if python_cmd:
        advanced_checks = [
            ("Dependencies", lambda: check_dependencies(python_cmd)),
            ("Makefile", lambda: test_makefile(python_cmd)),
            ("Basic Tests", lambda: run_basic_tests(python_cmd)),
        ]
        
        for check_name, check_func in advanced_checks:
            try:
                if check_func():
                    success_count += 1
                total_checks += 1
            except Exception as e:
                print_error(f"{check_name} check failed: {e}")
                total_checks += 1
    
    # Final summary
    print_header("Verification Summary")
    
    if success_count == total_checks:
        print_success(f"All {total_checks} checks passed! 🎉")
        print("\n✨ Your Avatar Intelligence System is ready to use!")
        print("\nNext steps:")
        print("  1. Make sure Neo4j is running")
        print("  2. Run: make deploy-system NEO4J_PASSWORD=your_password")  
        print("  3. Process your conversation data")
        print("  4. Generate AI avatars!")
        
    elif success_count > total_checks * 0.7:
        print_warning(f"Most checks passed ({success_count}/{total_checks})")
        print("🔧 System should work but may need minor fixes")
        
    else:
        print_error(f"Several checks failed ({success_count}/{total_checks})")
        print("🚨 System needs setup before use")
        print("\n💡 Try:")
        if not python_cmd:
            print("  - Install Python 3.7+")
        print("  - Run: pip install -e .")
        print("  - Check the QUICKSTART.md guide")
    
    print(f"\n📊 Final Score: {success_count}/{total_checks}")

if __name__ == "__main__":
    main()
