"""
Small Language Model (SLM) Package
Optimized for Mac Metal using MLX framework
"""

__version__ = "1.0.0"

from .neo4j_data_extractor import (
    Neo4jDataExtractor,
    ConversationNode,
    ConversationSequence,
    TrainingExample
)

from .mlx_slm_model import (
    ConversationSLM,
    SLMConfig
)

from .slm_trainer import (
    SLMTrainer,
    TrainingConfig,
    ConversationTokenizer,
    AnthropicEnhancer
)

from .slm_inference_engine import (
    SLMInferenceEngine,
    InferenceConfig,
    ConversationManager
)

__all__ = [
    "Neo4jDataExtractor",
    "ConversationNode",
    "ConversationSequence",
    "TrainingExample",
    "ConversationSLM",
    "SLMConfig",
    "SLMTrainer",
    "TrainingConfig",
    "ConversationTokenizer",
    "AnthropicEnhancer",
    "SLMInferenceEngine",
    "InferenceConfig",
    "ConversationManager"
]
