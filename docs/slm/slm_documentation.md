# Avatar SLM (Small Language Model) Documentation

## 🚀 Overview

The Avatar SLM feature enables training personalized language models directly from Neo4j conversation data, optimized for Apple Silicon using the MLX framework. This creates AI avatars that can mimic communication styles and patterns from your conversation history.

## 📋 Table of Contents

1. [Installation](#installation)
2. [Architecture](#architecture)
3. [Components](#components)
4. [Usage Guide](#usage-guide)
5. [API Reference](#api-reference)
6. [Configuration](#configuration)
7. [Performance Optimization](#performance-optimization)
8. [Troubleshooting](#troubleshooting)

## 🔧 Installation

### Prerequisites

- **Hardware**: Mac with Apple Silicon (M1, M2, M3, or newer)
- **OS**: macOS 13.3 or later
- **Python**: 3.9 or later
- **Neo4j**: Running instance with conversation data

### Install Dependencies

```bash
# Install MLX framework
pip install mlx mlx-lm

# Install other requirements
pip install -r requirements.txt

# For development
pip install -e .
```

### Verify Installation

```python
python3 -c "import mlx; print(f'MLX version: {mlx.__version__}')"
```

## 🏗️ Architecture

```
┌─────────────────┐
│    Neo4j DB     │
│ (Conversations) │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Data Extractor │ ← Extracts and formats conversation data
└────────┬────────┘
         │
         v
┌─────────────────┐
│   SLM Trainer   │ ← Trains personalized model using MLX
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Inference Engine│ ← Generates responses in avatar's style
└────────┬────────┘
         │
         v
┌─────────────────┐
│   Chat/API      │ ← User interaction interface
└─────────────────┘
```

## 📦 Components

### 1. Neo4j Data Extractor (`neo4j_data_extractor.py`)

Extracts conversation data from Neo4j and prepares it for training.

**Key Features:**
- Person-specific data extraction
- Conversation threading
- Metadata preservation
- Data cleaning and formatting

**Example:**
```python
from slm.neo4j_data_extractor import Neo4jDataExtractor, ExtractionConfig

config = ExtractionConfig(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="password",
    output_dir="data/extracted"
)

extractor = Neo4jDataExtractor(config)
data_path = extractor.extract_person_conversations("John Doe")
```

### 2. MLX SLM Model (`mlx_slm_model.py`)

Transformer-based model architecture optimized for Apple Silicon.

**Key Features:**
- Multi-head attention
- Positional encoding
- Layer normalization
- MLX optimization

**Architecture:**
```python
- Embedding dimension: 512
- Hidden dimension: 2048
- Attention heads: 8
- Layers: 6
- Vocabulary size: 50,000
```

### 3. SLM Trainer (`slm_trainer.py`)

Training pipeline with MLX acceleration.

**Key Features:**
- Adaptive learning rate
- Gradient accumulation
- Checkpointing
- Mixed precision training
- Progress tracking

**Example:**
```python
from slm.slm_trainer import SLMTrainer, TrainingConfig

config = TrainingConfig(
    model_name="john_avatar",
    data_path="data/extracted/john_doe.jsonl",
    num_epochs=10,
    batch_size=16,
    learning_rate=5e-5
)

trainer = SLMTrainer(config)
model_path = trainer.train()
```

### 4. Inference Engine (`slm_inference_engine.py`)

Real-time text generation with various sampling strategies.

**Key Features:**
- Temperature sampling
- Top-k/Top-p sampling
- Repetition penalty
- Streaming generation
- Conversation management

**Example:**
```python
from slm.slm_inference_engine import SLMInferenceEngine, InferenceConfig

config = InferenceConfig(
    model_path="models/john_avatar",
    temperature=0.8,
    top_k=50,
    stream=True
)

engine = SLMInferenceEngine(config)

# Generate text
response = engine.generate("Hello, how are you?")

# Interactive chat
for chunk in engine.chat("Tell me about your day", stream=True):
    print(chunk, end="", flush=True)
```

## 📘 Usage Guide

### Quick Start

1. **Extract conversation data:**
```bash
python3 examples/slm/slm_pipeline_example.py extract --person "John Doe"
```

2. **Train personalized model:**
```bash
python3 examples/slm/slm_pipeline_example.py train \
    --data-path data/extracted/john_doe.jsonl
```

3. **Start interactive chat:**
```bash
python3 examples/slm/slm_pipeline_example.py chat \
    --model-path models/john_avatar
```

### Full Pipeline

Run the complete pipeline with one command:

```bash
python3 examples/slm/slm_pipeline_example.py full --person "John Doe"
```

### Python API

```python
from examples.slm.slm_pipeline_example import AvatarSLMPipeline

# Initialize pipeline
pipeline = AvatarSLMPipeline()

# Run complete pipeline
pipeline.run_full_pipeline("John Doe")

# Or run steps individually
data_path = pipeline.extract_data("John Doe")
model_path = pipeline.train_model(data_path)
pipeline.setup_inference(model_path)
pipeline.chat_demo()
```

## 🔧 Configuration

### Configuration File Format

Create a `config.json` file:

```json
{
  "neo4j": {
    "uri": "bolt://localhost:7687",
    "username": "neo4j",
    "password": "password"
  },
  "extraction": {
    "output_dir": "data/extracted",
    "include_metadata": true,
    "max_messages": 10000,
    "date_range": {
      "start": "2023-01-01",
      "end": "2024-12-31"
    }
  },
  "training": {
    "model_name": "avatar_slm",
    "output_dir": "models",
    "epochs": 10,
    "batch_size": 16,
    "learning_rate": 5e-5,
    "warmup_steps": 100,
    "gradient_accumulation": 4,
    "max_sequence_length": 512
  },
  "inference": {
    "temperature": 0.8,
    "top_k": 50,
    "top_p": 0.95,
    "max_length": 512,
    "repetition_penalty": 1.1
  }
}
```

### Environment Variables

```bash
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USERNAME="neo4j"
export NEO4J_PASSWORD="password"
export MLX_DEVICE="gpu"  # Use Metal GPU
```

## ⚡ Performance Optimization

### Training Optimization

1. **Batch Size**: Larger batches improve GPU utilization
   ```python
   config.batch_size = 32  # Increase if memory allows
   ```

2. **Gradient Accumulation**: Simulate larger batches
   ```python
   config.gradient_accumulation_steps = 4
   ```

3. **Mixed Precision**: Faster training with minimal quality loss
   ```python
   config.use_mixed_precision = True
   ```

### Inference Optimization

1. **Caching**: Enable KV-cache for faster generation
   ```python
   config.use_cache = True
   ```

2. **Batch Processing**: Process multiple prompts efficiently
   ```python
   from slm.slm_inference_engine import BatchInferenceEngine
   
   batch_engine = BatchInferenceEngine(config)
   responses = batch_engine.process_batch(prompts)
   ```

3. **Streaming**: Reduce perceived latency
   ```python
   for chunk in engine.generate(prompt, stream=True):
       print(chunk, end="", flush=True)
   ```

### Memory Management

Monitor and optimize memory usage:

```python
import mlx.core as mx

# Check memory usage
print(f"Memory used: {mx.metal.get_peak_memory() / 1e9:.2f} GB")

# Clear cache
mx.metal.clear_cache()
```

## 🐛 Troubleshooting

### Common Issues

#### 1. MLX Not Found
```
ImportError: No module named 'mlx'
```
**Solution:**
```bash
pip install mlx mlx-lm
```

#### 2. Neo4j Connection Failed
```
Neo4j connection failed: Unable to connect
```
**Solution:**
- Verify Neo4j is running: `neo4j status`
- Check credentials in config
- Ensure network connectivity

#### 3. Out of Memory During Training
```
RuntimeError: Metal out of memory
```
**Solution:**
- Reduce batch size
- Enable gradient checkpointing
- Use gradient accumulation
- Clear MLX cache between epochs

#### 4. Slow Training Speed
**Solutions:**
- Ensure using Metal GPU: `export MLX_DEVICE=gpu`
- Increase batch size if memory allows
- Use mixed precision training
- Disable unnecessary logging

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set environment variable
export LOG_LEVEL=DEBUG
```

### Performance Profiling

```python
from slm.utils import profile_model

# Profile training
profile_model(trainer, num_steps=100)

# Profile inference
profile_model(engine, num_generations=50)
```

## 📊 Benchmarks

### Training Performance (M2 Max)

| Metric | Value |
|--------|-------|
| Training speed | ~500 tokens/sec |
| Memory usage | 8-12 GB |
| Time per epoch (10k samples) | ~5 minutes |
| Model size | ~200 MB |

### Inference Performance (M2 Max)

| Metric | Value |
|--------|-------|
| Generation speed | ~100 tokens/sec |
| First token latency | <100ms |
| Memory usage | 2-4 GB |
| Concurrent sessions | 5-10 |

## 🔗 API Reference

### ExtractionConfig

```python
@dataclass
class ExtractionConfig:
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    output_dir: str = "data/extracted"
    include_metadata: bool = True
    max_messages: int = 10000
    date_range: Optional[Dict[str, str]] = None
```

### TrainingConfig

```python
@dataclass
class TrainingConfig:
    model_name: str
    data_path: str
    output_dir: str = "models"
    num_epochs: int = 10
    batch_size: int = 16
    learning_rate: float = 5e-5
    warmup_steps: int = 100
    max_sequence_length: int = 512
    use_mlx: bool = True
```

### InferenceConfig

```python
@dataclass
class InferenceConfig:
    model_path: str
    max_length: int = 512
    temperature: float = 0.7
    top_k: int = 40
    top_p: float = 0.95
    repetition_penalty: float = 1.1
    use_cache: bool = True
    stream: bool = True
```

## 📚 Additional Resources

- [MLX Documentation](https://ml-explore.github.io/mlx/)
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)
- [Transformer Architecture](https://arxiv.org/abs/1706.03762)
- [Avatar Engine Main Documentation](../README.md)

## 📄 License

This feature is part of the Avatar Engine project and follows the same license terms.

## 🤝 Contributing

Contributions are welcome! Please see the main project's contributing guidelines.

## 📮 Support

For issues or questions:
- Open an issue on GitHub
- Check existing documentation
- Contact the development team

---

*Last updated: 2025-08-30*
