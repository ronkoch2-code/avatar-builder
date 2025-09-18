#!/usr/bin/env python3
"""
Test script to verify extraction_pipeline import fix
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

def test_imports():
    """Test that all imports work correctly"""
    print("Testing imports...")
    
    try:
        # Test the fixed import
        from src.pipelines.extraction_pipeline import ExtractionPipeline
        print("✓ ExtractionPipeline import successful")
        
        # Test the AvatarSystemManager import
        from src.avatar_intelligence_pipeline import AvatarSystemManager
        print("✓ AvatarSystemManager import successful")
        
        # Test MessageDataLoader import
        from src.message_data_loader import MessageDataLoader
        print("✓ MessageDataLoader import successful")
        
        # Test ConfigManager import
        from src.config_manager import ConfigManager
        print("✓ ConfigManager import successful")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_class_methods():
    """Test that expected methods exist"""
    print("\nTesting class methods...")
    
    try:
        from src.avatar_intelligence_pipeline import AvatarSystemManager
        from src.message_data_loader import MessageDataLoader
        
        # Check AvatarSystemManager methods
        methods = ['initialize_all_people', 'initialize_person', 'generate_response', 'get_system_stats']
        for method in methods:
            if hasattr(AvatarSystemManager, method):
                print(f"✓ AvatarSystemManager.{method} exists")
            else:
                print(f"✗ AvatarSystemManager.{method} missing")
        
        # Check MessageDataLoader methods  
        methods = ['load_from_json', 'load_from_sqlite']
        for method in methods:
            if hasattr(MessageDataLoader, method):
                print(f"✓ MessageDataLoader.{method} exists")
            else:
                print(f"✗ MessageDataLoader.{method} missing")
        
        return True
        
    except Exception as e:
        print(f"✗ Error checking methods: {e}")
        return False

def test_pipeline_initialization():
    """Test that ExtractionPipeline can be initialized"""
    print("\nTesting pipeline initialization...")
    
    try:
        from src.pipelines.extraction_pipeline import ExtractionPipeline
        
        # Try to create an instance
        pipeline = ExtractionPipeline()
        print("✓ ExtractionPipeline initialized successfully")
        
        # Check that state is initialized
        if hasattr(pipeline, 'state'):
            print("✓ Pipeline state initialized")
        else:
            print("✗ Pipeline state not initialized")
        
        # Check that config_manager is initialized
        if hasattr(pipeline, 'config_manager'):
            print("✓ ConfigManager initialized")
        else:
            print("✗ ConfigManager not initialized")
        
        return True
        
    except Exception as e:
        print(f"✗ Error initializing pipeline: {e}")
        return False

def main():
    print("=" * 50)
    print("EXTRACTION PIPELINE IMPORT FIX VERIFICATION")
    print("=" * 50)
    
    all_passed = True
    
    # Run tests
    if not test_imports():
        all_passed = False
    
    if not test_class_methods():
        all_passed = False
    
    if not test_pipeline_initialization():
        all_passed = False
    
    # Summary
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ ALL TESTS PASSED - Import fix successful!")
        print("\nYou can now run:")
        print("  python3 src/pipelines/extraction_pipeline.py --limit 100")
    else:
        print("❌ SOME TESTS FAILED - Please review the errors above")
    print("=" * 50)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
