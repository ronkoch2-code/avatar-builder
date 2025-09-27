#!/usr/bin/env python3
"""Test script to verify the import fix works."""

import sys
from pathlib import Path

# Add source to path
sys.path.insert(0, str(Path(__file__).parent))

def test_import():
    """Test if the imports work correctly."""
    print("Testing SLM module imports...")
    
    try:
        # Test importing from __init__.py
        from src.slm import (
            SLMInferenceEngine,
            InferenceConfig,
            ConversationManager
        )
        print("✓ Successfully imported from src.slm:")
        print("  - SLMInferenceEngine")
        print("  - InferenceConfig")
        print("  - ConversationManager")
        
        # Test importing from the module directly
        from src.slm.slm_inference_engine import (
            SLMInferenceEngine as Engine2,
            InferenceConfig as Config2,
            ConversationManager as Manager2
        )
        print("\n✓ Successfully imported directly from slm_inference_engine.py")
        
        # Verify they're the same classes
        assert SLMInferenceEngine == Engine2
        assert InferenceConfig == Config2
        assert ConversationManager == Manager2
        print("\n✓ Classes match between imports")
        
        return True
        
    except ImportError as e:
        print(f"\n✗ Import error: {e}")
        return False

if __name__ == "__main__":
    success = test_import()
    if success:
        print("\n✅ All imports working correctly!")
        print("\nYou should now be able to run:")
        print("  python3 src/slm/inference/chat.py --model Keifth_Zotti_fallback_model")
    else:
        print("\n❌ Import issues remain - check error messages above")
    
    sys.exit(0 if success else 1)
