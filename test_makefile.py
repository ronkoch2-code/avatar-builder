#!/usr/bin/env python3
"""
Test the Makefile Python detection
"""
import subprocess
import sys
import os

def test_makefile_python():
    """Test the Makefile Python detection"""
    print("🔧 Testing Makefile Python Detection")
    print("=" * 40)
    
    try:
        # Change to the correct directory
        os.chdir('/Volumes/FS001/pythonscripts/Avatar-Engine/')
        
        # Run make help to see the detected Python
        result = subprocess.run(['make', 'help'], capture_output=True, text=True)
        
        print("Make help output (first few lines):")
        lines = result.stdout.split('\n')[:8]
        for line in lines:
            print(f"  {line}")
        
        # Look for the detected Python line
        for line in lines:
            if "Detected Python:" in line:
                print(f"\n✅ {line}")
                break
        else:
            print("\n⚠️  Could not find Python detection in make help")
        
        return result.returncode == 0
        
    except FileNotFoundError:
        print("❌ make command not found")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_makefile_python()
