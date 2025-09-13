#!/usr/bin/env python3
"""
Quick test script to verify our security fixes
"""

import sys
import os
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all imports work correctly"""
    print("Testing imports...")
    
    try:
        # Test PBKDF2HMAC import
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        print("✅ PBKDF2HMAC import successful")
    except ImportError as e:
        print(f"❌ PBKDF2HMAC import failed: {e}")
        return False
    
    try:
        # Test security_utils import
        from src.security_utils import SecurityManager
        print("✅ SecurityManager import successful")
    except ImportError as e:
        print(f"❌ SecurityManager import failed: {e}")
        return False
    
    try:
        # Test secure_database import
        from src.secure_database import SecureNeo4jConnection
        print("✅ SecureNeo4jConnection import successful")
    except ImportError as e:
        print(f"❌ SecureNeo4jConnection import failed: {e}")
        return False
    
    return True

def test_config_manager_fix():
    """Test that ConfigManager initialization works correctly"""
    print("\nTesting ConfigManager fix...")
    
    try:
        from unittest.mock import patch, MagicMock
        
        # Mock GraphDatabase to avoid actual connection
        with patch('src.secure_database.GraphDatabase') as mock_gdb:
            # Mock the driver
            mock_driver = MagicMock()
            mock_gdb.driver.return_value = mock_driver
            
            # Mock session for test connection
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_result.single.return_value = {'test': 1}
            mock_session.run.return_value = mock_result
            mock_driver.session.return_value.__enter__ = lambda self: mock_session
            mock_driver.session.return_value.__exit__ = lambda self, *args: None
            
            # Test without ConfigManager (should use fallback)
            from src.secure_database import SecureNeo4jConnection
            
            # This should not raise an error
            db = SecureNeo4jConnection()
            print("✅ SecureNeo4jConnection creation without ConfigManager successful")
            
            # Test _get_default_config
            config = db._get_default_config()
            assert 'uri' in config
            assert 'auth' in config
            print("✅ Default config fallback working")
            
            return True
    except Exception as e:
        print(f"❌ ConfigManager fix test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("Avatar-Engine Security Fixes Verification")
    print("=" * 60)
    
    all_passed = True
    
    # Test imports
    if not test_imports():
        all_passed = False
    
    # Test ConfigManager fix
    if not test_config_manager_fix():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All fixes verified successfully!")
    else:
        print("❌ Some fixes need attention")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
