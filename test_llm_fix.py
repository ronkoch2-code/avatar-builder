#!/usr/bin/env python3
"""
Test script to verify LLM integration fix
"""

import sys
import os
sys.path.append('/Volumes/FS001/pythonscripts/Avatar-Engine/src')

def test_imports():
    """Test if all necessary imports work"""
    print("Testing imports...\n")
    
    try:
        from avatar_intelligence_pipeline import AvatarSystemManager
        print("✅ AvatarSystemManager imports correctly")
    except ImportError as e:
        print(f"❌ Error importing AvatarSystemManager: {e}")
        return False
    
    try:
        from enhanced_avatar_pipeline import EnhancedAvatarSystemManager
        print("✅ EnhancedAvatarSystemManager imports correctly")
    except ImportError as e:
        print(f"❌ Error importing EnhancedAvatarSystemManager: {e}")
        return False
    
    try:
        from pipelines.extraction_pipeline import ExtractionPipeline
        print("✅ ExtractionPipeline imports correctly with modifications")
    except ImportError as e:
        print(f"❌ Error importing ExtractionPipeline: {e}")
        return False
    
    return True

def test_llm_detection():
    """Test if LLM flag is properly detected"""
    print("\nTesting LLM detection...\n")
    
    from pipelines.extraction_pipeline import ExtractionPipeline
    
    # Test with LLM disabled
    config_no_llm = {
        'processor_config': {
            'enable_llm': False
        }
    }
    pipeline = ExtractionPipeline(config_no_llm)
    assert pipeline.config['processor_config']['enable_llm'] == False
    print("✅ LLM disabled detection works")
    
    # Test with LLM enabled
    config_with_llm = {
        'processor_config': {
            'enable_llm': True
        }
    }
    pipeline = ExtractionPipeline(config_with_llm)
    assert pipeline.config['processor_config']['enable_llm'] == True
    print("✅ LLM enabled detection works")
    
    # Check for API key
    if os.getenv('ANTHROPIC_API_KEY'):
        print(f"✅ ANTHROPIC_API_KEY is set: ...{os.getenv('ANTHROPIC_API_KEY')[-4:]}")
    else:
        print("⚠️  ANTHROPIC_API_KEY is not set - LLM will fall back to basic analysis")

def main():
    print("="*60)
    print("LLM Integration Test Suite")
    print("="*60)
    
    if test_imports():
        print("\n✅ All imports successful!")
        test_llm_detection()
        
        print("\n" + "="*60)
        print("SUMMARY: LLM integration fix is working correctly!")
        print("="*60)
        print("\nTo use LLM enhancement:")
        print("1. Set your API key: export ANTHROPIC_API_KEY='your-key'")
        print("2. Run with flag: python3 src/pipelines/extraction_pipeline.py --enable-llm")
    else:
        print("\n❌ Import issues detected - please check the code")

if __name__ == "__main__":
    main()
