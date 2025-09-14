#!/usr/bin/env python3
"""
Test script for LocalStorageManager integration with IMessageExtractor
Tests network volume detection and automatic local storage usage
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, '/Volumes/FS001/pythonscripts/Avatar-Engine/src')

from storage_manager import LocalStorageManager
from imessage_extractor import IMessageExtractor
import logging

def test_network_volume_detection():
    """Test if network volume detection works correctly"""
    print("\n" + "="*60)
    print("Testing Network Volume Detection")
    print("="*60)
    
    manager = LocalStorageManager()
    
    test_paths = [
        Path('/tmp/test'),
        Path('/Volumes/FS001/test'),
        Path('/Users/test'),
        Path.home() / 'test',
        Path.cwd()
    ]
    
    for path in test_paths:
        is_network = manager.is_network_volume(path)
        print(f"{path}: {'NETWORK' if is_network else 'LOCAL'}")
    
    # Test current project path
    project_path = Path('/Volumes/FS001/pythonscripts/Avatar-Engine')
    is_network = manager.is_network_volume(project_path)
    print(f"\nProject path ({project_path}): {'NETWORK' if is_network else 'LOCAL'}")
    
    return is_network

def test_extraction_with_storage_manager():
    """Test extraction using the enhanced IMessageExtractor"""
    print("\n" + "="*60)
    print("Testing IMessage Extraction with Storage Manager")
    print("="*60)
    
    # Configure for network volume (should trigger local storage)
    config = {
        'temp_dir': '/Volumes/FS001/pythonscripts/Avatar-Engine/data/temp',
        'output_dir': '/Volumes/FS001/pythonscripts/Avatar-Engine/data/extracted',
        'message_limit': 10,  # Small test
        'cleanup_temp': True
    }
    
    print("\nConfiguration:")
    print(f"  Temp dir: {config['temp_dir']}")
    print(f"  Output dir: {config['output_dir']}")
    print(f"  Message limit: {config['message_limit']}")
    
    try:
        # Initialize extractor
        extractor = IMessageExtractor(config)
        
        print("\n✅ IMessageExtractor initialized successfully")
        
        # Test database copy (this should detect network and use local)
        print("\nTesting database copy...")
        chat_db, addressbook_db = extractor.copy_databases_secure()
        
        print(f"✅ Databases copied:")
        print(f"  Chat DB: {chat_db}")
        print(f"  AddressBook: {addressbook_db}")
        
        # Check if local storage was used
        if hasattr(extractor, '_storage_manager') and extractor._storage_manager:
            print("\n✅ LocalStorageManager was activated (network volume detected)")
            stats = extractor._storage_manager.get_storage_stats()
            print(f"  Temp files: {stats['temp_files_count']}")
            print(f"  Temp size: {stats['total_temp_size_mb']:.2f} MB")
        else:
            print("\n📍 Direct local storage used (no network volume)")
        
        # Clean up test
        if hasattr(extractor, '_storage_manager') and extractor._storage_manager:
            extractor._storage_manager.cleanup(force=True)
            
        return True
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_full_extraction_pipeline():
    """Test the complete extraction pipeline with network volume handling"""
    print("\n" + "="*60)
    print("Testing Full Extraction Pipeline")
    print("="*60)
    
    # Use network volume paths to trigger LocalStorageManager
    config = {
        'temp_dir': '/Volumes/FS001/pythonscripts/Avatar-Engine/data/temp',
        'output_dir': '/Volumes/FS001/pythonscripts/Avatar-Engine/data/extracted',
        'message_limit': 50,  # Moderate test
        'cleanup_temp': True
    }
    
    print("\nRunning extraction with network volume paths...")
    print("This should automatically use local storage for SQLite operations")
    
    try:
        extractor = IMessageExtractor(config)
        output_file = extractor.run_extraction_pipeline(message_limit=50)
        
        print(f"\n✅ SUCCESS! Extraction completed")
        print(f"Output file: {output_file}")
        
        # Verify file exists on network volume
        if Path(output_file).exists():
            size = Path(output_file).stat().st_size
            print(f"File size: {size:,} bytes")
            print("\n✅ File successfully synced to network volume")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*60)
    print("LocalStorageManager Integration Test Suite")
    print("="*60)
    
    results = []
    
    # Test 1: Network volume detection
    print("\nTest 1: Network Volume Detection")
    is_network = test_network_volume_detection()
    results.append(("Network Detection", is_network))
    
    # Test 2: Storage manager integration
    print("\nTest 2: Storage Manager Integration")
    success = test_extraction_with_storage_manager()
    results.append(("Storage Integration", success))
    
    # Test 3: Full pipeline
    print("\nTest 3: Full Pipeline Execution")
    success = test_full_extraction_pipeline()
    results.append(("Full Pipeline", success))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    # Overall result
    all_passed = all(r for _, r in results)
    print("\n" + "="*60)
    if all_passed:
        print("✅ All tests passed! Network volume handling is working.")
    else:
        print("❌ Some tests failed. Check the output above for details.")
    print("="*60)

if __name__ == "__main__":
    main()
