"""
SLM Inference Module
====================
Provides inference capabilities for trained Small Language Models.

This module includes:
- Interactive chat interface
- Model loading and management
- Streaming text generation
- Conversation history management
"""

from .chat import (
    ChatInterface,
    ModelLoader,
    FallbackModel
)

__all__ = [
    'ChatInterface',
    'ModelLoader',
    'FallbackModel'
]

__version__ = '1.0.0'
