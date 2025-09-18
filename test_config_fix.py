#!/usr/bin/env python3
"""
Test script to verify config access fixes in extraction_pipeline.py
"""

import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

def test_config_access():
    """Test that pipeline handles missing config keys gracefully"""
    print("Testing config access fixes...")
    
    try:
        from src.pipelines.extraction_pipeline import ExtractionPipeline
        
        # Test 1: Initialize with empty config
        print("\n1. Testing with empty config...")
        pipeline = ExtractionPipeline({})
        print("✓ Pipeline initialized with empty config")
        
        # Test 2: Initialize with partial config (missing pipeline_config)
        print("\n2. Testing with partial config (no pipeline_config)...")
        partial_config = {
            'extractor_config': {
                'output_dir': 'test_output',
            }
        }
        pipeline = ExtractionPipeline(partial_config)
        print("✓ Pipeline initialized with partial config")
        
        # Test 3: Initialize with None (should use defaults)
        print("\n3. Testing with None config (uses defaults)...")
        pipeline = ExtractionPipeline(None)
        print("✓ Pipeline initialized with None (uses defaults)")
        
        # Verify default config is properly set
        if hasattr(pipeline, 'config'):
            if 'pipeline_config' in pipeline.config:
                print("✓ Default pipeline_config is set")
            else:
                print("⚠ pipeline_config not in default config")
        
        # Test 4: Test with custom config that has pipeline_config
        print("\n4. Testing with complete custom config...")
        complete_config = {
            'extractor_config': {
                'output_dir': 'custom_output',
                'temp_dir': 'custom_temp',
            },
            'processor_config': {
                'enable_llm': True,
                'batch_size': 50,
            },
            'pipeline_config': {
                'save_checkpoints': False,
                'checkpoint_dir': 'custom_checkpoints',
                'continue_on_error': True,
            }
        }
        pipeline = ExtractionPipeline(complete_config)
        print("✓ Pipeline initialized with complete custom config")
        
        return True
        
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_safe_access_methods():
    """Test that all config accesses use safe .get() methods"""
    print("\nChecking for safe config access patterns...")
    
    # Read the extraction_pipeline.py file
    pipeline_file = Path("src/pipelines/extraction_pipeline.py")
    if not pipeline_file.exists():
        print(f"✗ File not found: {pipeline_file}")
        return False
    
    with open(pipeline_file, 'r') as f:
        content = f.read()
    
    # Check for unsafe patterns
    unsafe_patterns = [
        "self.config['pipeline_config']['",
        "self.config['extractor_config']['",
        "self.config['processor_config']['",
        'self.config["pipeline_config"]["',
        'self.config["extractor_config"]["',
        'self.config["processor_config"]["',
    ]
    
    issues_found = []
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        for pattern in unsafe_patterns:
            if pattern in line:
                issues_found.append(f"Line {i}: {line.strip()}")
    
    if issues_found:
        print("✗ Found unsafe config access patterns:")
        for issue in issues_found[:5]:  # Show first 5
            print(f"  {issue}")
        return False
    else:
        print("✓ All config accesses use safe .get() methods")
        return True

def main():
    print("=" * 50)
    print("CONFIG ACCESS FIX VERIFICATION")
    print("=" * 50)
    
    all_passed = True
    
    # Run tests
    if not test_safe_access_methods():
        all_passed = False
    
    if not test_config_access():
        all_passed = False
    
    # Summary
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ ALL TESTS PASSED - Config access fix successful!")
        print("\nYou can now run:")
        print("  python3 src/pipelines/extraction_pipeline.py --limit 100")
        print("  python3 src/pipelines/extraction_pipeline.py --limit 100 --enable-llm")
    else:
        print("❌ SOME TESTS FAILED - Please review the errors above")
    print("=" * 50)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
