#!/usr/bin/env python3
"""
Test ConfigManager fixes for Neo4j password validation
Tests the fixes applied to config_manager.py on 2025-09-13
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

class TestConfigManagerFixes(unittest.TestCase):
    """Test suite for ConfigManager Neo4j password validation fixes"""
    
    def setUp(self):
        """Set up test environment"""
        # Store original environment variables
        self.original_env = {}
        for key in ['NEO4J_PASSWORD', 'NEO4J_URI', 'NEO4J_USERNAME', 'ANTHROPIC_API_KEY']:
            self.original_env[key] = os.environ.get(key)
    
    def tearDown(self):
        """Restore original environment"""
        for key, value in self.original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    
    @patch('config_manager.logger')
    def test_config_manager_imports(self, mock_logger):
        """Test that ConfigManager can be imported without syntax errors"""
        try:
            from config_manager import ConfigManager
            self.assertTrue(True, "ConfigManager imported successfully")
        except SyntaxError as e:
            self.fail(f"Syntax error in ConfigManager: {e}")
        except ImportError as e:
            self.fail(f"Import error in ConfigManager: {e}")
    
    @patch('config_manager.logger')
    def test_config_manager_instantiation_with_password(self, mock_logger):
        """Test ConfigManager instantiation with Neo4j password set"""
        os.environ['NEO4J_PASSWORD'] = 'TestPassword123!'
        os.environ['ALLOW_EXISTING_PASSWORD'] = 'true'  # Allow test password
        
        from config_manager import ConfigManager
        config = ConfigManager()
        
        self.assertEqual(config.neo4j.password, 'TestPassword123!')
        # Verify secure logging (no password length)
        for call in mock_logger.info.call_args_list:
            self.assertNotIn('chars)', str(call))
    
    @patch('config_manager.load_dotenv')  # Mock load_dotenv to prevent .env file loading
    @patch('config_manager.logger')
    def test_config_manager_no_password_error(self, mock_logger, mock_load_dotenv):
        """Test ConfigManager raises error when no password is provided"""
        # Clear the password from environment
        os.environ.pop('NEO4J_PASSWORD', None)
        
        from config_manager import ConfigManager
        with self.assertRaises(ValueError) as context:
            config = ConfigManager()
        
        self.assertIn("Neo4j password is required", str(context.exception))
    
    @patch('config_manager.logger')
    def test_numeric_env_var_parsing(self, mock_logger):
        """Test that numeric environment variables are parsed correctly"""
        os.environ['NEO4J_PASSWORD'] = 'TestPassword123!'
        os.environ['ALLOW_EXISTING_PASSWORD'] = 'true'
        os.environ['DAILY_COST_LIMIT'] = '100.5'
        os.environ['MAX_CONCURRENT_REQUESTS'] = '5'
        os.environ['MIN_MESSAGES_FOR_ANALYSIS'] = '25'
        
        from config_manager import ConfigManager
        config = ConfigManager()
        
        self.assertEqual(config.anthropic.daily_cost_limit, 100.5)
        self.assertEqual(config.anthropic.max_concurrent_requests, 5)
        self.assertEqual(config.analysis.min_messages_for_analysis, 25)
    
    @patch('config_manager.logger')
    def test_get_secure_anthropic_key_method(self, mock_logger):
        """Test that get_secure_anthropic_key method works correctly"""
        os.environ['NEO4J_PASSWORD'] = 'TestPassword123!'
        os.environ['ALLOW_EXISTING_PASSWORD'] = 'true'
        # Use a non-test API key to avoid security validation rejection
        os.environ['ANTHROPIC_API_KEY'] = 'sk-prod-key-12345678901234567890123456789012345678901234567890'
        
        from config_manager import ConfigManager
        config = ConfigManager()
        
        # Test the method returns the key
        key = config.get_secure_anthropic_key()
        self.assertEqual(key, 'sk-prod-key-12345678901234567890123456789012345678901234567890')
    
    @patch('config_manager.logger')
    def test_reject_test_api_keys(self, mock_logger):
        """Test that test API keys are correctly rejected for security"""
        os.environ['NEO4J_PASSWORD'] = 'TestPassword123!'
        os.environ['ALLOW_EXISTING_PASSWORD'] = 'true'
        # Set a test API key that should be rejected
        os.environ['ANTHROPIC_API_KEY'] = 'sk-test-key-12345678901234567890123456789012345678901234567890'
        
        from config_manager import ConfigManager
        with self.assertRaises(ValueError) as context:
            config = ConfigManager()
        
        self.assertIn("Test API key detected", str(context.exception))
    
    @patch('config_manager.logger')
    def test_security_logging_improvements(self, mock_logger):
        """Test that security-sensitive information is not logged"""
        os.environ['NEO4J_PASSWORD'] = 'SecretPassword123!'
        os.environ['ALLOW_EXISTING_PASSWORD'] = 'true'
        
        from config_manager import ConfigManager
        config = ConfigManager()
        
        # Check that no calls contain the actual password or its length
        all_log_calls = (
            mock_logger.info.call_args_list + 
            mock_logger.warning.call_args_list + 
            mock_logger.error.call_args_list
        )
        
        for call in all_log_calls:
            call_str = str(call)
            self.assertNotIn('SecretPassword123!', call_str, "Password should not be logged")
            self.assertNotIn('18 chars', call_str, "Password length should not be logged")
            self.assertNotIn("password value:", call_str, "Password value prefix should not be logged")


if __name__ == '__main__':
    # Run tests
    print("Running ConfigManager Fix Tests...")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestConfigManagerFixes)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ All tests passed!")
    else:
        print(f"❌ {len(result.failures)} test(s) failed")
        print(f"❌ {len(result.errors)} test(s) had errors")
    
    sys.exit(0 if result.wasSuccessful() else 1)
