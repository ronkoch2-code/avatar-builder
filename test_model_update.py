#!/usr/bin/env python3
"""
Test script to verify Claude model update works
"""

import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_model_configuration():
    """Test that the updated model configuration works"""
    from src.config_manager import ConfigManager
    
    print("🧪 Testing Claude model configuration...")
    print("-" * 50)
    
    # Initialize configuration
    config = ConfigManager()
    
    # Check model name
    print(f"✓ Current model: {config.anthropic.model}")
    
    # Verify it's not the old model
    assert config.anthropic.model != "claude-3-sonnet-20240229", "Still using old model!"
    assert config.anthropic.model == "claude-3-5-sonnet-20240620", "Model not updated correctly!"
    
    print("✅ Model configuration is correct!")
    
    # Show other relevant settings
    print("\n📊 Configuration Summary:")
    print(f"  Model: {config.anthropic.model}")
    print(f"  Max Tokens: {config.anthropic.max_tokens}")
    print(f"  Temperature: {config.anthropic.temperature}")
    print(f"  Daily Cost Limit: ${config.anthropic.daily_cost_limit}")
    print(f"  Min Messages for Analysis: {config.analysis.min_messages_for_analysis}")
    
    return True

if __name__ == "__main__":
    try:
        test_model_configuration()
        print("\n✨ All tests passed! The model update fix is working.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
