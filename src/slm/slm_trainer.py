"""
Training pipeline for Small Language Model using MLX
Optimized for Mac Metal with Anthropic API cost optimization
"""

import os
import json
import math
import time
import logging
from typing import List, Dict, Any, Optional, Tuple, Iterator
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np
from tqdm import tqdm
from datetime import datetime
import hashlib

import mlx.core as mx
import mlx.nn as nn
import mlx.optimizers as optim
from mlx.utils import tree_flatten, tree_unflatten

from .neo4j_data_extractor import Neo4jDataExtractor, TrainingExample
from .mlx_slm_model import ConversationSLM, SLMConfig

# Try importing Anthropic for enhanced training
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    print("Warning: anthropic package not installed. Enhanced training disabled.")

logger = logging.getLogger(__name__)

@dataclass
class TrainingConfig:
    """Training configuration with Anthropic optimization"""
    # Basic training parameters
    batch_size: int = 4
    learning_rate: float = 1e-4
    num_epochs: int = 3
    warmup_steps: int = 1000
    max_grad_norm: float = 1.0
    weight_decay: float = 0.01
    
    # Sequence parameters
    max_sequence_length: int = 512
    context_window: int = 4
    
    # Optimization parameters
    gradient_accumulation_steps: int = 4
    eval_steps: int = 500
    save_steps: int = 1000
    logging_steps: int = 100
    
    # Mac Metal optimizations
    use_mixed_precision: bool = True
    use_gradient_checkpointing: bool = True
    pin_memory: bool = True
    
    # Data parameters
    train_split: float = 0.8
    val_split: float = 0.1
    test_split: float = 0.1
    
    # Anthropic API optimization
    use_anthropic_enhancement: bool = False
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    anthropic_batch_size: int = 10  # Batch multiple requests
    anthropic_cache_system_prompt: bool = True  # Use prompt caching
    anthropic_enhancement_ratio: float = 0.1  # Only enhance 10% of examples
    anthropic_max_retries: int = 3
    anthropic_timeout: int = 30
    
    # Model parameters
    resume_from_checkpoint: Optional[str] = None
    output_dir: str = "slm_outputs"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class AnthropicEnhancer:
    """Enhance training data using Anthropic API with cost optimization"""
    
    def __init__(self, config: TrainingConfig):
        if not HAS_ANTHROPIC:
            raise ImportError("anthropic package required for enhancement")
            
        self.config = config
        self.client = anthropic.Anthropic(api_key=config.anthropic_api_key)
        
        # Cache for system prompts (reduces API costs)
        self.system_prompt_cache = {}
        self.prompt_cache_hits = 0
        self.total_api_calls = 0
        self.total_tokens_used = 0
        
    def _get_system_prompt(self, personality_type: str = None) -> str:
        """Get cached system prompt for personality type"""
        cache_key = personality_type or "default"
        
        if cache_key in self.system_prompt_cache:
            self.prompt_cache_hits += 1
            return self.system_prompt_cache[cache_key]
            
        # Create system prompt with caching markers
        system_prompt = f"""You are helping to enhance conversation training data.
Your task is to make the responses more natural and contextually appropriate.
{f'The speaker has a {personality_type} personality.' if personality_type else ''}

Rules:
1. Keep the same meaning and intent
2. Make the language more natural and conversational
3. Add appropriate emotional nuance
4. Maintain character consistency
5. Keep responses concise (under 100 words)

IMPORTANT: This prompt is cached to reduce API costs. <cache_control><cache_type>ephemeral</cache_type></cache_control>"""
        
        self.system_prompt_cache[cache_key] = system_prompt
        return system_prompt
        
    def enhance_batch(self, examples: List[TrainingExample]) -> List[TrainingExample]:
        """Enhance a batch of examples using Anthropic API"""
        enhanced_examples = []
        
        # Process in batches for efficiency
        batch_size = self.config.anthropic_batch_size
        for i in range(0, len(examples), batch_size):
            batch = examples[i:i+batch_size]
            
            # Create batch request
            batch_messages = []
            for example in batch:
                system_prompt = self._get_system_prompt(example.personality_type)
                
                # Build conversation context
                context = ""
                if example.conversation_history:
                    for msg in example.conversation_history[-3:]:  # Last 3 messages
                        context += f"{msg['speaker']}: {msg['message']}\n"
                        
                user_message = f"""Context:
{context}

Input: {example.input_text}
Original Response: {example.target_text}

Please provide an enhanced version of the response that sounds more natural and appropriate for the context.
Enhanced Response:"""
                
                batch_messages.append({
                    "system": system_prompt,
                    "user": user_message,
                    "metadata": example.example_id
                })
                
            # Process batch with retries
            for message_data in batch_messages:
                try:
                    response = self._call_api_with_retry(
                        message_data["system"],
                        message_data["user"]
                    )
                    
                    # Find corresponding example
                    example_id = message_data["metadata"]
                    original_example = next(e for e in batch if e.example_id == example_id)
                    
                    # Create enhanced example
                    enhanced_example = TrainingExample(
                        example_id=f"{original_example.example_id}_enhanced",
                        input_text=original_example.input_text,
                        target_text=response,
                        speaker_name=original_example.speaker_name,
                        personality_type=original_example.personality_type,
                        emotional_state=original_example.emotional_state,
                        relationship_type=original_example.relationship_type,
                        conversation_history=original_example.conversation_history,
                        metadata={**original_example.metadata, "enhanced": True}
                    )
                    enhanced_examples.append(enhanced_example)
                    
                except Exception as e:
                    logger.warning(f"Failed to enhance example {example_id}: {e}")
                    # Keep original if enhancement fails
                    enhanced_examples.append(original_example)
                    
        return enhanced_examples
        
    def _call_api_with_retry(self, system: str, user: str) -> str:
        """Call Anthropic API with retry logic"""
        for attempt in range(self.config.anthropic_max_retries):
            try:
                self.total_api_calls += 1
                
                # Use messages.create with prompt caching
                message = self.client.messages.create(
                    model=self.config.anthropic_model,
                    max_tokens=150,
                    temperature=0.7,
                    system=system,
                    messages=[{"role": "user", "content": user}],
                    metadata={
                        "cache_control": {"cache_type": "ephemeral"} if self.config.anthropic_cache_system_prompt else None
                    }
                )
                
                # Track token usage
                if hasattr(message, 'usage'):
                    self.total_tokens_used += message.usage.total_tokens
                    
                return message.content[0].text.strip()
                
            except Exception as e:
                if attempt == self.config.anthropic_max_retries - 1:
                    raise
                logger.warning(f"API call failed (attempt {attempt + 1}): {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
                
        return ""
        
    def get_stats(self) -> Dict[str, Any]:
        """Get enhancement statistics"""
        return {
            "total_api_calls": self.total_api_calls,
            "prompt_cache_hits": self.prompt_cache_hits,
            "cache_hit_rate": self.prompt_cache_hits / max(1, self.total_api_calls),
            "total_tokens_used": self.total_tokens_used,
            "estimated_cost": self._estimate_cost()
        }
        
    def _estimate_cost(self) -> float:
        """Estimate API cost based on token usage"""
        # Rough estimates for Claude 3.5 Sonnet
        input_cost_per_1k = 0.003
        output_cost_per_1k = 0.015
        
        # Assume 70% input, 30% output
        estimated_input = self.total_tokens_used * 0.7
        estimated_output = self.total_tokens_used * 0.3
        
        cost = (estimated_input / 1000 * input_cost_per_1k + 
                estimated_output / 1000 * output_cost_per_1k)
        
        # Apply cache discount (cached prompts are ~90% cheaper)
        cache_discount = 0.9 * self.cache_hit_rate
        cost *= (1 - cache_discount * 0.5)  # Apply partial discount
        
        return round(cost, 4)

class ConversationTokenizer:
    """Simple tokenizer for conversation data"""
    
    def __init__(self, vocab_size: int = 32000):
        self.vocab_size = vocab_size
        self.vocab = {}
        self.inverse_vocab = {}
        self.special_tokens = {
            "<pad>": 0,
            "<unk>": 1,
            "<bos>": 2,
            "<eos>": 3,
            "<speaker1>": 4,
            "<speaker2>": 5,
            "<personality>": 6,
            "<emotion>": 7,
            "<relationship>": 8,
        }
        
        # Initialize with special tokens
        for token, idx in self.special_tokens.items():
            self.vocab[token] = idx
            self.inverse_vocab[idx] = token
            
        self.next_idx = len(self.special_tokens)
        
    def fit(self, texts: List[str]):
        """Build vocabulary from texts"""
        word_counts = {}
        
        for text in texts:
            words = text.lower().split()
            for word in words:
                word_counts[word] = word_counts.get(word, 0) + 1
                
        # Add most common words to vocabulary
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        
        for word, _ in sorted_words[:self.vocab_size - len(self.special_tokens)]:
            if word not in self.vocab:
                self.vocab[word] = self.next_idx
                self.inverse_vocab[self.next_idx] = word
                self.next_idx += 1
                
    def encode(self, text: str, max_length: Optional[int] = None) -> List[int]:
        """Encode text to token IDs"""
        words = text.lower().split()
        tokens = []
        
        for word in words:
            if word in self.vocab:
                tokens.append(self.vocab[word])
            else:
                tokens.append(self.vocab["<unk>"])
                
        # Add special tokens
        tokens = [self.vocab["<bos>"]] + tokens + [self.vocab["<eos>"]]
        
        # Truncate or pad
        if max_length:
            if len(tokens) > max_length:
                tokens = tokens[:max_length]
            else:
                tokens += [self.vocab["<pad>"]] * (max_length - len(tokens))
                
        return tokens
        
    def decode(self, token_ids: List[int]) -> str:
        """Decode token IDs to text"""
        words = []
        for token_id in token_ids:
            if token_id in self.inverse_vocab:
                word = self.inverse_vocab[token_id]
                if word not in self.special_tokens:
                    words.append(word)
        return " ".join(words)

class SLMTrainer:
    """Trainer for Small Language Model with Anthropic enhancement"""
    
    def __init__(self, 
                 model: ConversationSLM,
                 tokenizer: ConversationTokenizer,
                 config: TrainingConfig):
        self.model = model
        self.tokenizer = tokenizer
        self.config = config
        
        # Setup optimizer
        self.optimizer = optim.AdamW(
            learning_rate=config.learning_rate,
            weight_decay=config.weight_decay
        )
        
        # Setup enhancer if enabled
        self.enhancer = None
        if config.use_anthropic_enhancement and config.anthropic_api_key:
            try:
                self.enhancer = AnthropicEnhancer(config)
                logger.info("Anthropic enhancement enabled with prompt caching")
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic enhancer: {e}")
                
        # Training state
        self.global_step = 0
        self.best_val_loss = float('inf')
        self.training_history = []
        
        # Setup output directory
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def prepare_dataset(self, examples: List[TrainingExample]) -> Dict[str, List]:
        """Prepare and split dataset"""
        # Enhance subset of examples if enabled
        if self.enhancer and self.config.anthropic_enhancement_ratio > 0:
            num_to_enhance = int(len(examples) * self.config.anthropic_enhancement_ratio)
            examples_to_enhance = np.random.choice(examples, num_to_enhance, replace=False)
            
            logger.info(f"Enhancing {num_to_enhance} examples with Anthropic API...")
            enhanced = self.enhancer.enhance_batch(examples_to_enhance.tolist())
            
            # Combine original and enhanced
            examples = examples + enhanced
            
            # Log enhancement stats
            stats = self.enhancer.get_stats()
            logger.info(f"Enhancement stats: {stats}")
            
        # Shuffle and split
        np.random.shuffle(examples)
        
        n_train = int(len(examples) * self.config.train_split)
        n_val = int(len(examples) * self.config.val_split)
        
        train_examples = examples[:n_train]
        val_examples = examples[n_train:n_train + n_val]
        test_examples = examples[n_train + n_val:]
        
        # Tokenize examples
        train_dataset = self._tokenize_examples(train_examples)
        val_dataset = self._tokenize_examples(val_examples)
        test_dataset = self._tokenize_examples(test_examples)
        
        return {
            "train": train_dataset,
            "val": val_dataset,
            "test": test_dataset
        }
        
    def _tokenize_examples(self, examples: List[TrainingExample]) -> List[Dict]:
        """Tokenize training examples"""
        tokenized = []
        
        for example in examples:
            # Tokenize input and target
            input_ids = self.tokenizer.encode(example.input_text, self.config.max_sequence_length)
            target_ids = self.tokenizer.encode(example.target_text, self.config.max_sequence_length)
            
            # Map personality, emotion, relationship to IDs
            personality_id = hash(example.personality_type or "neutral") % self.model.config.num_personality_types
            emotion_id = hash(example.emotional_state or "neutral") % self.model.config.num_emotion_types
            relationship_id = hash(example.relationship_type or "neutral") % self.model.config.num_relationship_types
            
            tokenized.append({
                "input_ids": input_ids,
                "target_ids": target_ids,
                "personality_id": personality_id,
                "emotion_id": emotion_id,
                "relationship_id": relationship_id,
                "example_id": example.example_id
            })
            
        return tokenized
        
    def train(self, dataset: Dict[str, List]):
        """Train the model"""
        train_data = dataset["train"]
        val_data = dataset["val"]
        
        logger.info(f"Starting training with {len(train_data)} train examples")
        
        for epoch in range(self.config.num_epochs):
            logger.info(f"Epoch {epoch + 1}/{self.config.num_epochs}")
            
            # Training
            train_loss = self._train_epoch(train_data)
            
            # Validation
            val_loss = self._validate(val_data)
            
            # Log metrics
            self.training_history.append({
                "epoch": epoch + 1,
                "train_loss": train_loss,
                "val_loss": val_loss,
                "learning_rate": self.optimizer.learning_rate,
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info(f"Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
            
            # Save best model
            if val_loss < self.best_val_loss:
                self.best_val_loss = val_loss
                self.save_checkpoint("best_model")
                logger.info(f"New best model saved (val_loss: {val_loss:.4f})")
                
        # Save final model
        self.save_checkpoint("final_model")
        
        # Save training history
        history_path = self.output_dir / "training_history.json"
        with open(history_path, 'w') as f:
            json.dump(self.training_history, f, indent=2)
            
        logger.info(f"Training complete. Models saved to {self.output_dir}")
        
    def _train_epoch(self, train_data: List[Dict]) -> float:
        """Train for one epoch"""
        total_loss = 0
        num_batches = 0
        
        # Create batches
        batches = self._create_batches(train_data, self.config.batch_size)
        
        progress_bar = tqdm(batches, desc="Training")
        for batch in progress_bar:
            # Forward pass
            loss = self._compute_loss(batch)
            
            # Backward pass
            loss_value, grads = mx.value_and_grad(self.model, self._loss_fn)(
                self.model.parameters(), batch
            )
            
            # Gradient clipping
            grads = tree_map(lambda g: mx.clip(g, -self.config.max_grad_norm, self.config.max_grad_norm), grads)
            
            # Update weights
            self.optimizer.update(self.model, grads)
            
            # Update metrics
            total_loss += loss_value.item()
            num_batches += 1
            self.global_step += 1
            
            # Update progress bar
            progress_bar.set_postfix({"loss": loss_value.item()})
            
            # Logging
            if self.global_step % self.config.logging_steps == 0:
                logger.debug(f"Step {self.global_step}, Loss: {loss_value.item():.4f}")
                
            # Save checkpoint
            if self.global_step % self.config.save_steps == 0:
                self.save_checkpoint(f"checkpoint_{self.global_step}")
                
        return total_loss / max(1, num_batches)
        
    def _validate(self, val_data: List[Dict]) -> float:
        """Validate the model"""
        total_loss = 0
        num_batches = 0
        
        batches = self._create_batches(val_data, self.config.batch_size)
        
        for batch in tqdm(batches, desc="Validation"):
            loss = self._compute_loss(batch)
            total_loss += loss.item()
            num_batches += 1
            
        return total_loss / max(1, num_batches)
        
    def _compute_loss(self, batch: Dict[str, mx.array]) -> mx.array:
        """Compute loss for a batch"""
        outputs = self.model(
            batch["input_ids"],
            personality_id=batch["personality_id"],
            emotion_id=batch["emotion_id"],
            relationship_id=batch["relationship_id"]
        )
        
        logits = outputs["logits"]
        targets = batch["target_ids"]
        
        # Compute cross-entropy loss
        loss = nn.losses.cross_entropy(
            logits.reshape(-1, logits.shape[-1]),
            targets.reshape(-1),
            reduction="mean"
        )
        
        return loss
        
    def _loss_fn(self, params: Dict, batch: Dict[str, mx.array]) -> mx.array:
        """Loss function for gradient computation"""
        # Update model parameters
        self.model.update(params)
        
        # Compute loss
        return self._compute_loss(batch)
        
    def _create_batches(self, data: List[Dict], batch_size: int) -> Iterator[Dict[str, mx.array]]:
        """Create batches from data"""
        for i in range(0, len(data), batch_size):
            batch_data = data[i:i + batch_size]
            
            # Pad sequences and create arrays
            batch = {
                "input_ids": mx.array([d["input_ids"] for d in batch_data]),
                "target_ids": mx.array([d["target_ids"] for d in batch_data]),
                "personality_id": mx.array([d["personality_id"] for d in batch_data]),
                "emotion_id": mx.array([d["emotion_id"] for d in batch_data]),
                "relationship_id": mx.array([d["relationship_id"] for d in batch_data])
            }
            
            yield batch
            
    def save_checkpoint(self, name: str):
        """Save model checkpoint"""
        checkpoint_dir = self.output_dir / name
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Save model
        self.model.save_pretrained(str(checkpoint_dir))
        
        # Save tokenizer
        tokenizer_path = checkpoint_dir / "tokenizer.json"
        with open(tokenizer_path, 'w') as f:
            json.dump({
                "vocab": self.tokenizer.vocab,
                "vocab_size": self.tokenizer.vocab_size,
                "special_tokens": self.tokenizer.special_tokens
            }, f, indent=2)
            
        # Save training config
        config_path = checkpoint_dir / "training_config.json"
        with open(config_path, 'w') as f:
            json.dump(self.config.to_dict(), f, indent=2)
            
        # Save optimizer state
        optimizer_path = checkpoint_dir / "optimizer.npz"
        mx.savez(str(optimizer_path), **self.optimizer.state)
        
        logger.info(f"Checkpoint saved to {checkpoint_dir}")
        
def tree_map(f, tree):
    """Apply function to all leaves in tree"""
    if isinstance(tree, dict):
        return {k: tree_map(f, v) for k, v in tree.items()}
    elif isinstance(tree, list):
        return [tree_map(f, v) for v in tree]
    elif isinstance(tree, tuple):
        return tuple(tree_map(f, v) for v in tree)
    else:
        return f(tree)

# Example usage
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create config
    config = TrainingConfig(
        batch_size=4,
        num_epochs=3,
        learning_rate=1e-4,
        use_anthropic_enhancement=True,  # Enable enhancement
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        anthropic_enhancement_ratio=0.1,  # Enhance 10% of data
        anthropic_cache_system_prompt=True  # Use prompt caching
    )
    
    # Create model
    model_config = SLMConfig(
        vocab_size=32000,
        hidden_size=512,
        num_hidden_layers=8
    )
    model = ConversationSLM(model_config)
    
    # Create tokenizer
    tokenizer = ConversationTokenizer()
    
    # Create trainer
    trainer = SLMTrainer(model, tokenizer, config)
    
    # Load training data
    with open("training_data.json", 'r') as f:
        data = json.load(f)
        examples = [TrainingExample(**ex) for ex in data["examples"]]
        
    # Fit tokenizer
    all_texts = [ex.input_text + " " + ex.target_text for ex in examples]
    tokenizer.fit(all_texts)
    
    # Prepare dataset
    dataset = trainer.prepare_dataset(examples)
    
    # Train
    trainer.train(dataset)
    
    # Print enhancement stats if used
    if trainer.enhancer:
        stats = trainer.enhancer.get_stats()
        print(f"\nAnthropic Enhancement Statistics:")
        print(f"  Total API calls: {stats['total_api_calls']}")
        print(f"  Cache hit rate: {stats['cache_hit_rate']:.2%}")
        print(f"  Estimated cost: ${stats['estimated_cost']:.2f}")
