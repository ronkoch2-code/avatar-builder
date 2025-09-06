"""
MLX-based Small Language Model for Conversation
Optimized for Mac Metal with personality and emotional context
"""

import json
import math
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np

import mlx.core as mx
import mlx.nn as nn
from mlx.utils import tree_flatten, tree_unflatten

@dataclass
class SLMConfig:
    """Configuration for the Small Language Model"""
    # Model dimensions
    vocab_size: int = 32000
    hidden_size: int = 512
    intermediate_size: int = 2048
    num_hidden_layers: int = 8
    num_attention_heads: int = 8
    num_key_value_heads: Optional[int] = None  # For GQA
    
    # Context embeddings
    num_personality_types: int = 10
    num_emotion_types: int = 8
    num_relationship_types: int = 5
    context_embedding_dim: int = 64
    
    # Sequence parameters
    max_position_embeddings: int = 512
    rope_theta: float = 10000.0
    rope_scaling: Optional[Dict[str, Any]] = None
    
    # Regularization
    hidden_dropout_prob: float = 0.1
    attention_probs_dropout_prob: float = 0.1
    layer_norm_eps: float = 1e-6
    
    # Activation
    hidden_act: str = "silu"  # SiLU/Swish activation
    
    # Training optimizations
    use_cache: bool = True
    tie_word_embeddings: bool = True
    gradient_checkpointing: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
        
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "SLMConfig":
        return cls(**config_dict)

class RMSNorm(nn.Module):
    """Root Mean Square Layer Normalization"""
    
    def __init__(self, dims: int, eps: float = 1e-6):
        super().__init__()
        self.weight = mx.ones((dims,))
        self.eps = eps
        
    def _norm(self, x):
        return x * mx.rsqrt(x.square().mean(-1, keepdims=True) + self.eps)
        
    def __call__(self, x):
        return self._norm(x.astype(mx.float32)).astype(x.dtype) * self.weight

class RotaryEmbedding(nn.Module):
    """Rotary Position Embedding"""
    
    def __init__(self, dims: int, max_position: int = 512, base: float = 10000):
        super().__init__()
        self.dims = dims
        self.max_position = max_position
        self.base = base
        self._set_cos_sin_cache()
        
    def _set_cos_sin_cache(self):
        inv_freq = 1.0 / (self.base ** (mx.arange(0, self.dims, 2).astype(mx.float32) / self.dims))
        t = mx.arange(self.max_position).astype(mx.float32)
        
        freqs = mx.outer(t, inv_freq)
        self.cos_cached = mx.cos(freqs)
        self.sin_cached = mx.sin(freqs)
        
    def __call__(self, x, position_ids):
        # x: [batch_size, num_heads, seq_len, head_dim]
        batch_size, num_heads, seq_len, head_dim = x.shape
        
        cos = self.cos_cached[position_ids].reshape(batch_size, 1, seq_len, -1)
        sin = self.sin_cached[position_ids].reshape(batch_size, 1, seq_len, -1)
        
        x1, x2 = mx.split(x, 2, axis=-1)
        
        # Apply rotation
        rotated = mx.concatenate([-x2, x1], axis=-1)
        x_rotated = (x * cos) + (rotated * sin)
        
        return x_rotated

class ConversationAttention(nn.Module):
    """Multi-head attention with conversation context"""
    
    def __init__(self, config: SLMConfig):
        super().__init__()
        self.config = config
        self.hidden_size = config.hidden_size
        self.num_heads = config.num_attention_heads
        self.head_dim = self.hidden_size // self.num_heads
        self.num_key_value_heads = config.num_key_value_heads or self.num_heads
        self.num_key_value_groups = self.num_heads // self.num_key_value_heads
        
        self.q_proj = nn.Linear(self.hidden_size, self.num_heads * self.head_dim, bias=False)
        self.k_proj = nn.Linear(self.hidden_size, self.num_key_value_heads * self.head_dim, bias=False)
        self.v_proj = nn.Linear(self.hidden_size, self.num_key_value_heads * self.head_dim, bias=False)
        self.o_proj = nn.Linear(self.num_heads * self.head_dim, self.hidden_size, bias=False)
        
        self.rotary_emb = RotaryEmbedding(self.head_dim, config.max_position_embeddings)
        self.dropout = nn.Dropout(config.attention_probs_dropout_prob)
        
    def __call__(self, 
                 hidden_states: mx.array,
                 attention_mask: Optional[mx.array] = None,
                 position_ids: Optional[mx.array] = None,
                 past_key_value: Optional[Tuple[mx.array]] = None,
                 use_cache: bool = False) -> Tuple[mx.array, Optional[Tuple[mx.array]]]:
        
        batch_size, seq_len, _ = hidden_states.shape
        
        # Compute queries, keys, values
        queries = self.q_proj(hidden_states)
        keys = self.k_proj(hidden_states)
        values = self.v_proj(hidden_states)
        
        # Reshape for multi-head attention
        queries = queries.reshape(batch_size, seq_len, self.num_heads, self.head_dim).transpose(0, 2, 1, 3)
        keys = keys.reshape(batch_size, seq_len, self.num_key_value_heads, self.head_dim).transpose(0, 2, 1, 3)
        values = values.reshape(batch_size, seq_len, self.num_key_value_heads, self.head_dim).transpose(0, 2, 1, 3)
        
        # Apply rotary embeddings
        if position_ids is None:
            position_ids = mx.arange(seq_len).reshape(1, -1).broadcast_to((batch_size, seq_len))
            
        queries = self.rotary_emb(queries, position_ids)
        keys = self.rotary_emb(keys, position_ids)
        
        # Handle key-value caching
        if past_key_value is not None:
            keys = mx.concatenate([past_key_value[0], keys], axis=2)
            values = mx.concatenate([past_key_value[1], values], axis=2)
            
        present_key_value = (keys, values) if use_cache else None
        
        # Repeat keys and values for grouped query attention
        if self.num_key_value_groups > 1:
            keys = mx.repeat(keys, self.num_key_value_groups, axis=1)
            values = mx.repeat(values, self.num_key_value_groups, axis=1)
            
        # Compute attention scores
        attn_weights = mx.matmul(queries, keys.transpose(0, 1, 3, 2)) / math.sqrt(self.head_dim)
        
        # Apply attention mask
        if attention_mask is not None:
            attn_weights = attn_weights + attention_mask
            
        # Softmax
        attn_weights = mx.softmax(attn_weights, axis=-1)
        attn_weights = self.dropout(attn_weights)
        
        # Apply attention to values
        attn_output = mx.matmul(attn_weights, values)
        
        # Reshape and project output
        attn_output = attn_output.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, self.hidden_size)
        attn_output = self.o_proj(attn_output)
        
        return attn_output, present_key_value

class ConversationMLP(nn.Module):
    """Feed-forward network with SiLU activation"""
    
    def __init__(self, config: SLMConfig):
        super().__init__()
        self.config = config
        self.gate_proj = nn.Linear(config.hidden_size, config.intermediate_size, bias=False)
        self.up_proj = nn.Linear(config.hidden_size, config.intermediate_size, bias=False)
        self.down_proj = nn.Linear(config.intermediate_size, config.hidden_size, bias=False)
        self.dropout = nn.Dropout(config.hidden_dropout_prob)
        
    def __call__(self, x: mx.array) -> mx.array:
        # SiLU activation with gating
        gate = nn.silu(self.gate_proj(x))
        up = self.up_proj(x)
        x = gate * up
        x = self.down_proj(x)
        x = self.dropout(x)
        return x

class ConversationLayer(nn.Module):
    """Transformer layer with conversation context"""
    
    def __init__(self, config: SLMConfig):
        super().__init__()
        self.config = config
        self.self_attn = ConversationAttention(config)
        self.mlp = ConversationMLP(config)
        self.input_layernorm = RMSNorm(config.hidden_size, eps=config.layer_norm_eps)
        self.post_attention_layernorm = RMSNorm(config.hidden_size, eps=config.layer_norm_eps)
        
    def __call__(self,
                 hidden_states: mx.array,
                 attention_mask: Optional[mx.array] = None,
                 position_ids: Optional[mx.array] = None,
                 past_key_value: Optional[Tuple[mx.array]] = None,
                 use_cache: bool = False) -> Tuple[mx.array, Optional[Tuple[mx.array]]]:
        
        # Self-attention with residual
        residual = hidden_states
        hidden_states = self.input_layernorm(hidden_states)
        hidden_states, present_key_value = self.self_attn(
            hidden_states,
            attention_mask=attention_mask,
            position_ids=position_ids,
            past_key_value=past_key_value,
            use_cache=use_cache
        )
        hidden_states = residual + hidden_states
        
        # MLP with residual
        residual = hidden_states
        hidden_states = self.post_attention_layernorm(hidden_states)
        hidden_states = self.mlp(hidden_states)
        hidden_states = residual + hidden_states
        
        return hidden_states, present_key_value

class ConversationSLM(nn.Module):
    """Small Language Model for Conversation with personality and emotional context"""
    
    def __init__(self, config: SLMConfig):
        super().__init__()
        self.config = config
        
        # Token embeddings
        self.embed_tokens = nn.Embedding(config.vocab_size, config.hidden_size)
        
        # Context embeddings
        self.personality_embedding = nn.Embedding(config.num_personality_types, config.context_embedding_dim)
        self.emotion_embedding = nn.Embedding(config.num_emotion_types, config.context_embedding_dim)
        self.relationship_embedding = nn.Embedding(config.num_relationship_types, config.context_embedding_dim)
        
        # Context projection
        self.context_proj = nn.Linear(config.context_embedding_dim * 3, config.hidden_size)
        
        # Transformer layers
        self.layers = [ConversationLayer(config) for _ in range(config.num_hidden_layers)]
        
        # Output
        self.norm = RMSNorm(config.hidden_size, eps=config.layer_norm_eps)
        self.lm_head = nn.Linear(config.hidden_size, config.vocab_size, bias=False)
        
        # Tie embeddings
        if config.tie_word_embeddings:
            self.lm_head.weight = self.embed_tokens.weight
            
    def get_input_embeddings(self):
        return self.embed_tokens
        
    def set_input_embeddings(self, value):
        self.embed_tokens = value
        
    def __call__(self,
                 input_ids: mx.array,
                 attention_mask: Optional[mx.array] = None,
                 position_ids: Optional[mx.array] = None,
                 personality_id: Optional[mx.array] = None,
                 emotion_id: Optional[mx.array] = None,
                 relationship_id: Optional[mx.array] = None,
                 past_key_values: Optional[List[Tuple[mx.array]]] = None,
                 use_cache: bool = False,
                 return_dict: bool = True) -> Dict[str, Any]:
        
        batch_size, seq_len = input_ids.shape
        
        # Get token embeddings
        hidden_states = self.embed_tokens(input_ids)
        
        # Add context embeddings if provided
        if personality_id is not None or emotion_id is not None or relationship_id is not None:
            context_embeds = []
            
            if personality_id is not None:
                context_embeds.append(self.personality_embedding(personality_id))
            else:
                context_embeds.append(mx.zeros((batch_size, self.config.context_embedding_dim)))
                
            if emotion_id is not None:
                context_embeds.append(self.emotion_embedding(emotion_id))
            else:
                context_embeds.append(mx.zeros((batch_size, self.config.context_embedding_dim)))
                
            if relationship_id is not None:
                context_embeds.append(self.relationship_embedding(relationship_id))
            else:
                context_embeds.append(mx.zeros((batch_size, self.config.context_embedding_dim)))
                
            # Concatenate and project context
            context = mx.concatenate(context_embeds, axis=-1)
            context = self.context_proj(context)
            context = context.reshape(batch_size, 1, -1).broadcast_to((batch_size, seq_len, -1))
            
            # Add context to embeddings
            hidden_states = hidden_states + context
            
        # Create attention mask
        if attention_mask is None:
            attention_mask = mx.ones((batch_size, seq_len))
            
        # Convert to proper shape for attention
        attention_mask = self._prepare_attention_mask(attention_mask, seq_len)
        
        # Process through transformer layers
        present_key_values = [] if use_cache else None
        
        for i, layer in enumerate(self.layers):
            past_key_value = past_key_values[i] if past_key_values else None
            
            hidden_states, present_key_value = layer(
                hidden_states,
                attention_mask=attention_mask,
                position_ids=position_ids,
                past_key_value=past_key_value,
                use_cache=use_cache
            )
            
            if use_cache:
                present_key_values.append(present_key_value)
                
        # Final normalization
        hidden_states = self.norm(hidden_states)
        
        # Language model head
        logits = self.lm_head(hidden_states)
        
        if return_dict:
            return {
                "logits": logits,
                "past_key_values": present_key_values,
                "hidden_states": hidden_states
            }
        else:
            return logits, present_key_values
            
    def _prepare_attention_mask(self, attention_mask: mx.array, seq_len: int) -> mx.array:
        """Prepare causal attention mask"""
        batch_size = attention_mask.shape[0]
        
        # Create causal mask
        causal_mask = mx.triu(mx.ones((seq_len, seq_len)) * float('-inf'), k=1)
        causal_mask = causal_mask.reshape(1, 1, seq_len, seq_len)
        causal_mask = causal_mask.broadcast_to((batch_size, 1, seq_len, seq_len))
        
        # Combine with padding mask
        if attention_mask is not None:
            padding_mask = (1.0 - attention_mask[:, None, None, :]) * float('-inf')
            causal_mask = causal_mask + padding_mask
            
        return causal_mask
        
    def generate(self,
                 input_ids: mx.array,
                 max_new_tokens: int = 100,
                 temperature: float = 0.7,
                 top_p: float = 0.9,
                 personality_id: Optional[mx.array] = None,
                 emotion_id: Optional[mx.array] = None,
                 relationship_id: Optional[mx.array] = None) -> mx.array:
        """Generate text using the model"""
        
        batch_size = input_ids.shape[0]
        past_key_values = None
        
        for _ in range(max_new_tokens):
            # Get model predictions
            outputs = self(
                input_ids[:, -1:] if past_key_values else input_ids,
                personality_id=personality_id,
                emotion_id=emotion_id,
                relationship_id=relationship_id,
                past_key_values=past_key_values,
                use_cache=True
            )
            
            logits = outputs["logits"]
            past_key_values = outputs["past_key_values"]
            
            # Get next token logits
            next_token_logits = logits[:, -1, :]
            
            # Apply temperature
            if temperature > 0:
                next_token_logits = next_token_logits / temperature
                
            # Apply top-p sampling
            if top_p < 1.0:
                sorted_logits, sorted_indices = mx.sort(next_token_logits, axis=-1)
                cumulative_probs = mx.cumsum(mx.softmax(sorted_logits, axis=-1), axis=-1)
                
                # Remove tokens with cumulative probability above threshold
                sorted_indices_to_remove = cumulative_probs > top_p
                sorted_indices_to_remove[:, 1:] = sorted_indices_to_remove[:, :-1]
                sorted_indices_to_remove[:, 0] = False
                
                indices_to_remove = mx.scatter(sorted_indices_to_remove, sorted_indices, axis=-1)
                next_token_logits = mx.where(indices_to_remove, float('-inf'), next_token_logits)
                
            # Sample next token
            probs = mx.softmax(next_token_logits, axis=-1)
            next_token = mx.random.categorical(mx.log(probs))
            
            # Append to sequence
            input_ids = mx.concatenate([input_ids, next_token.reshape(batch_size, 1)], axis=1)
            
            # Check for EOS token (assuming 3 is EOS)
            if mx.any(next_token == 3):
                break
                
        return input_ids
        
    def save_pretrained(self, save_directory: str):
        """Save model weights and configuration"""
        save_path = Path(save_directory)
        save_path.mkdir(parents=True, exist_ok=True)
        
        # Save configuration
        config_path = save_path / "config.json"
        with open(config_path, 'w') as f:
            json.dump(self.config.to_dict(), f, indent=2)
            
        # Save weights
        weights = dict(tree_flatten(self.parameters()))
        weights_path = save_path / "model.safetensors"
        mx.save_safetensors(str(weights_path), weights)
        
        print(f"Model saved to {save_directory}")
        
    @classmethod
    def from_pretrained(cls, model_directory: str) -> "ConversationSLM":
        """Load model from saved weights"""
        model_path = Path(model_directory)
        
        # Load configuration
        config_path = model_path / "config.json"
        with open(config_path, 'r') as f:
            config_dict = json.load(f)
        config = SLMConfig.from_dict(config_dict)
        
        # Create model
        model = cls(config)
        
        # Load weights
        weights_path = model_path / "model.safetensors"
        weights = mx.load(str(weights_path))
        model.update(tree_unflatten(list(weights.items())))
        
        print(f"Model loaded from {model_directory}")
        return model

# Example usage
if __name__ == "__main__":
    # Create configuration
    config = SLMConfig(
        vocab_size=32000,
        hidden_size=512,
        num_hidden_layers=8,
        num_attention_heads=8,
        intermediate_size=2048
    )
    
    # Create model
    model = ConversationSLM(config)
    
    # Test forward pass
    batch_size = 2
    seq_len = 10
    input_ids = mx.random.randint(0, config.vocab_size, (batch_size, seq_len))
    personality_id = mx.array([0, 1])
    emotion_id = mx.array([2, 3])
    relationship_id = mx.array([0, 1])
    
    outputs = model(
        input_ids,
        personality_id=personality_id,
        emotion_id=emotion_id,
        relationship_id=relationship_id
    )
    
    print(f"Output shape: {outputs['logits'].shape}")
    
    # Test generation
    generated = model.generate(
        input_ids[:, :5],
        max_new_tokens=20,
        personality_id=personality_id,
        emotion_id=emotion_id,
        relationship_id=relationship_id
    )
    
    print(f"Generated shape: {generated.shape}")
    
    # Save and load test
    model.save_pretrained("test_model")
    loaded_model = ConversationSLM.from_pretrained("test_model")
    print("Model loaded successfully")
