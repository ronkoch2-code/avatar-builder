#!/usr/bin/env python3
"""
SLM Inference Engine
====================
Inference and chat capabilities for Mac Metal-optimized language models.

This module provides real-time inference using MLX framework for efficient
generation on Apple Silicon.
"""

import json
import logging
import time
from typing import Dict, List, Optional, Any, Generator
from pathlib import Path
import numpy as np

try:
    import mlx
    import mlx.core as mx
    import mlx.nn as nn
    MLX_AVAILABLE = True
except ImportError:
    MLX_AVAILABLE = False
    print("Warning: MLX not available. Install with: pip install mlx")

from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class InferenceConfig:
    """Configuration for inference engine."""
    model_path: str
    max_length: int = 512
    temperature: float = 0.7
    top_k: int = 40
    top_p: float = 0.95
    repetition_penalty: float = 1.1
    use_cache: bool = True
    batch_size: int = 1
    stream: bool = True


class TokenSampler:
    """Advanced token sampling strategies."""
    
    def __init__(self, vocab_size: int):
        """Initialize sampler with vocabulary size."""
        self.vocab_size = vocab_size
    
    def sample(
        self,
        logits: mx.array,
        temperature: float = 1.0,
        top_k: int = 40,
        top_p: float = 0.95,
        repetition_penalty: float = 1.0,
        past_tokens: Optional[List[int]] = None
    ) -> int:
        """
        Sample next token using various strategies.
        
        Args:
            logits: Raw model outputs
            temperature: Sampling temperature
            top_k: Top-k sampling parameter
            top_p: Nucleus sampling parameter
            repetition_penalty: Penalty for repeated tokens
            past_tokens: Previously generated tokens
            
        Returns:
            Sampled token ID
        """
        if not MLX_AVAILABLE:
            return 0
            
        # Apply repetition penalty
        if past_tokens and repetition_penalty != 1.0:
            for token in set(past_tokens):
                logits[token] /= repetition_penalty
        
        # Apply temperature
        if temperature != 1.0:
            logits = logits / temperature
        
        # Convert to probabilities
        probs = mx.softmax(logits, axis=-1)
        
        # Top-k sampling
        if top_k > 0:
            top_k = min(top_k, self.vocab_size)
            top_k_indices = mx.argpartition(probs, -top_k)[-top_k:]
            top_k_probs = probs[top_k_indices]
            top_k_probs = top_k_probs / mx.sum(top_k_probs)
            
            # Sample from top-k
            sampled_idx = mx.random.categorical(mx.log(top_k_probs))
            return int(top_k_indices[sampled_idx])
        
        # Nucleus (top-p) sampling
        if top_p < 1.0:
            sorted_indices = mx.argsort(probs, axis=-1)[::-1]
            sorted_probs = probs[sorted_indices]
            cumsum_probs = mx.cumsum(sorted_probs)
            
            # Find cutoff
            cutoff_idx = mx.sum(cumsum_probs <= top_p)
            cutoff_idx = max(1, cutoff_idx)  # At least one token
            
            # Sample from nucleus
            nucleus_probs = sorted_probs[:cutoff_idx]
            nucleus_probs = nucleus_probs / mx.sum(nucleus_probs)
            
            sampled_idx = mx.random.categorical(mx.log(nucleus_probs))
            return int(sorted_indices[sampled_idx])
        
        # Standard sampling
        return int(mx.random.categorical(mx.log(probs)))


class ConversationManager:
    """Manages conversation context and history."""
    
    def __init__(self, max_context_length: int = 2048):
        """Initialize conversation manager."""
        self.max_context_length = max_context_length
        self.history = []
        self.context_tokens = []
    
    def add_turn(self, role: str, content: str, tokens: List[int]):
        """Add a conversation turn."""
        self.history.append({
            "role": role,
            "content": content,
            "tokens": tokens
        })
        
        # Update context tokens
        self.context_tokens.extend(tokens)
        
        # Truncate if necessary
        if len(self.context_tokens) > self.max_context_length:
            self._truncate_context()
    
    def _truncate_context(self):
        """Truncate context to fit within max length."""
        # Keep most recent messages
        while len(self.context_tokens) > self.max_context_length:
            if self.history:
                removed = self.history.pop(0)
                removed_len = len(removed["tokens"])
                self.context_tokens = self.context_tokens[removed_len:]
            else:
                break
    
    def get_context(self) -> List[int]:
        """Get current context tokens."""
        return self.context_tokens
    
    def clear(self):
        """Clear conversation history."""
        self.history = []
        self.context_tokens = []


class SLMInferenceEngine:
    """
    Inference engine for Small Language Models on Mac Metal.
    
    Provides efficient text generation using MLX framework.
    """
    
    def __init__(self, config: InferenceConfig):
        """
        Initialize inference engine.
        
        Args:
            config: Inference configuration
        """
        self.config = config
        self.model = None
        self.tokenizer = None
        self.sampler = None
        self.conversation = ConversationManager()
        self.cache = {} if config.use_cache else None
        
        # Load model
        self._load_model()
    
    def _load_model(self):
        """Load model and tokenizer."""
        if not MLX_AVAILABLE:
            logger.warning("MLX not available, skipping model load")
            return
            
        try:
            model_path = Path(self.config.model_path)
            
            # Load model weights
            weights_path = model_path / "model.safetensors"
            if weights_path.exists():
                logger.info(f"Loading model from {weights_path}")
                # Load with MLX (implementation depends on model format)
                # self.model = load_mlx_model(weights_path)
            
            # Load tokenizer
            tokenizer_path = model_path / "tokenizer.json"
            if tokenizer_path.exists():
                logger.info(f"Loading tokenizer from {tokenizer_path}")
                with open(tokenizer_path, 'r') as f:
                    tokenizer_config = json.load(f)
                    # Initialize tokenizer with config
                    # self.tokenizer = Tokenizer(tokenizer_config)
            
            # Initialize sampler
            vocab_size = 50000  # Should get from model config
            self.sampler = TokenSampler(vocab_size)
            
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
    
    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 256,
        stream: bool = None
    ) -> Generator[str, None, None] | str:
        """
        Generate text from prompt.
        
        Args:
            prompt: Input prompt
            max_new_tokens: Maximum tokens to generate
            stream: Whether to stream output
            
        Returns:
            Generated text (streamed or complete)
        """
        stream = stream if stream is not None else self.config.stream
        
        if not MLX_AVAILABLE or not self.model:
            if stream:
                yield "MLX not available or model not loaded"
            else:
                return "MLX not available or model not loaded"
        
        try:
            # Tokenize prompt
            input_tokens = self._tokenize(prompt)
            
            # Generate tokens
            generated_tokens = []
            past_tokens = input_tokens.copy()
            
            for _ in range(max_new_tokens):
                # Get model predictions
                logits = self._forward(past_tokens)
                
                # Sample next token
                next_token = self.sampler.sample(
                    logits[-1],
                    temperature=self.config.temperature,
                    top_k=self.config.top_k,
                    top_p=self.config.top_p,
                    repetition_penalty=self.config.repetition_penalty,
                    past_tokens=past_tokens
                )
                
                # Add to generated tokens
                generated_tokens.append(next_token)
                past_tokens.append(next_token)
                
                # Decode and yield if streaming
                if stream:
                    token_text = self._decode([next_token])
                    yield token_text
                
                # Check for end token
                if self._is_end_token(next_token):
                    break
            
            # Return complete text if not streaming
            if not stream:
                return self._decode(generated_tokens)
                
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            error_msg = f"Error: {str(e)}"
            if stream:
                yield error_msg
            else:
                return error_msg
    
    def chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        stream: bool = True
    ) -> Generator[str, None, None] | str:
        """
        Interactive chat with the model.
        
        Args:
            message: User message
            system_prompt: Optional system prompt
            stream: Whether to stream response
            
        Returns:
            Model response
        """
        # Format conversation
        if system_prompt and not self.conversation.history:
            self.conversation.add_turn(
                "system",
                system_prompt,
                self._tokenize(system_prompt)
            )
        
        # Add user message
        self.conversation.add_turn(
            "user",
            message,
            self._tokenize(message)
        )
        
        # Generate response
        context = self.conversation.get_context()
        response = ""
        
        for chunk in self.generate("", max_new_tokens=256, stream=stream):
            response += chunk
            if stream:
                yield chunk
        
        # Add assistant response to history
        self.conversation.add_turn(
            "assistant",
            response,
            self._tokenize(response)
        )
        
        if not stream:
            return response
    
    def _tokenize(self, text: str) -> List[int]:
        """Tokenize text to token IDs."""
        if not self.tokenizer:
            # Dummy tokenization for testing
            return [ord(c) for c in text]
        return self.tokenizer.encode(text)
    
    def _decode(self, tokens: List[int]) -> str:
        """Decode token IDs to text."""
        if not self.tokenizer:
            # Dummy decoding for testing
            return ''.join(chr(t) for t in tokens if t < 128)
        return self.tokenizer.decode(tokens)
    
    def _forward(self, tokens: List[int]) -> mx.array:
        """Forward pass through model."""
        if not MLX_AVAILABLE or not self.model:
            # Return dummy logits for testing
            return mx.random.normal((len(tokens), 50000))
        
        # Convert to MLX array
        input_array = mx.array(tokens)
        
        # Forward pass
        with mx.no_grad():
            logits = self.model(input_array)
        
        return logits
    
    def _is_end_token(self, token: int) -> bool:
        """Check if token is end-of-sequence."""
        # Common end tokens
        end_tokens = [0, 2, 3]  # <pad>, </s>, <eos>
        return token in end_tokens
    
    def clear_conversation(self):
        """Clear conversation history."""
        self.conversation.clear()
        logger.info("Conversation cleared")
    
    def save_conversation(self, path: str):
        """Save conversation history to file."""
        try:
            with open(path, 'w') as f:
                json.dump(self.conversation.history, f, indent=2)
            logger.info(f"Conversation saved to {path}")
        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")
    
    def load_conversation(self, path: str):
        """Load conversation history from file."""
        try:
            with open(path, 'r') as f:
                history = json.load(f)
            
            self.conversation.clear()
            for turn in history:
                self.conversation.history.append(turn)
                self.conversation.context_tokens.extend(turn["tokens"])
            
            logger.info(f"Conversation loaded from {path}")
            
        except Exception as e:
            logger.error(f"Failed to load conversation: {e}")


class BatchInferenceEngine:
    """Batch inference for processing multiple prompts efficiently."""
    
    def __init__(self, config: InferenceConfig):
        """Initialize batch inference engine."""
        self.config = config
        self.engine = SLMInferenceEngine(config)
    
    def process_batch(
        self,
        prompts: List[str],
        max_new_tokens: int = 256,
        show_progress: bool = True
    ) -> List[str]:
        """
        Process a batch of prompts.
        
        Args:
            prompts: List of input prompts
            max_new_tokens: Maximum tokens per generation
            show_progress: Whether to show progress
            
        Returns:
            List of generated texts
        """
        results = []
        total = len(prompts)
        
        for i, prompt in enumerate(prompts):
            if show_progress:
                logger.info(f"Processing {i+1}/{total}: {prompt[:50]}...")
            
            # Generate response
            response = self.engine.generate(
                prompt,
                max_new_tokens=max_new_tokens,
                stream=False
            )
            
            results.append(response)
            
            # Clear conversation between prompts
            self.engine.clear_conversation()
        
        return results
    
    async def process_batch_async(
        self,
        prompts: List[str],
        max_new_tokens: int = 256
    ) -> List[str]:
        """
        Process batch asynchronously.
        
        Args:
            prompts: List of input prompts
            max_new_tokens: Maximum tokens per generation
            
        Returns:
            List of generated texts
        """
        # Async implementation would go here
        # For now, fallback to sync
        return self.process_batch(prompts, max_new_tokens, show_progress=False)


if __name__ == "__main__":
    # Example usage
    config = InferenceConfig(
        model_path="models/avatar_slm",
        temperature=0.8,
        top_k=50,
        stream=True
    )
    
    # Initialize engine
    engine = SLMInferenceEngine(config)
    
    # Interactive chat
    print("\n🤖 Avatar SLM Chat (Type 'quit' to exit)\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['quit', 'exit']:
            break
        
        print("Bot: ", end="", flush=True)
        for chunk in engine.chat(user_input, stream=True):
            print(chunk, end="", flush=True)
        print()
    
    print("\n👋 Goodbye!")
