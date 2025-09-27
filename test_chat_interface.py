#!/usr/bin/env python3
"""Test the SLM chat interface."""

import sys
import os
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

# Test imports
print("Testing SLM Chat Interface...")
print("-" * 60)

try:
    from src.slm.inference.chat import ChatInterface, ModelLoader, FallbackModel
    print("✓ Chat interface imports successful")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

# Test model loader
try:
    loader = ModelLoader()
    print(f"✓ ModelLoader initialized")
    
    models = loader.list_models()
    print(f"✓ Found {len(models)} models:")
    for model_name in models:
        info = loader.get_model_info(model_name)
        model_type = info["config"].get("framework", "unknown")
        person = info["config"].get("person_name", "Unknown")
        print(f"  - {model_name}: {person} ({model_type})")
    
except Exception as e:
    print(f"✗ Error loading models: {e}")
    sys.exit(1)

print("-" * 60)
print("✓ All tests passed!")
print("\nTo run the chat interface:")
print("  python3 src/slm/inference/chat.py")
print("\nOr with a specific model:")
print("  python3 src/slm/inference/chat.py --model Keifth_Zotti_fallback_model")
