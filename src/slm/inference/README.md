# SLM Chat Interface

## Overview
Interactive command-line interface for chatting with trained Avatar Small Language Models (SLMs).

## Features
- ✓ Interactive CLI with model selection
- ✓ Support for both MLX and fallback models
- ✓ Conversation history management
- ✓ Streaming text generation
- ✓ Save/load conversations
- ✓ Model switching during chat

## Usage

### Basic Usage
```bash
# Start interactive chat interface
python3 src/slm/inference/chat.py

# Load specific model directly
python3 src/slm/inference/chat.py --model Keifth_Zotti_fallback_model

# Enable debug logging
python3 src/slm/inference/chat.py --debug
```

### Chat Commands
During chat, you can use these commands:
- `/help` - Show available commands
- `/clear` - Clear conversation history
- `/save` - Save conversation to file
- `/switch` - Switch to a different model
- `/exit` - Exit the chat

## Available Models

The interface automatically detects models in the `slm_models/` directory:

| Model | Person | Type | Status |
|-------|--------|------|--------|
| Keifth_Zotti_fallback_model | Keifth Zotti | fallback | ✓ Ready |
| Keifth_Zotti_mlx_model | Keifth Zotti | mlx | Requires MLX |
| Virginia_Koch_fallback_model | Virginia Koch | fallback | ✓ Ready |
| Jay_Houghton_mlx_model | Jay Houghton | mlx | Requires MLX |

## Testing

Run the test script to verify installation:
```bash
python3 test_chat_interface.py
```

## Requirements

### Core Requirements
- Python 3.8+
- Avatar Engine modules

### Optional Requirements
- MLX framework (for MLX models on Apple Silicon)
- Neo4j database (for training new models)

## Model Types

### Fallback Models
- Work without MLX framework
- Use pre-generated responses
- Good for testing and development

### MLX Models
- Require Apple Silicon Mac with MLX
- Full generative capabilities
- Better response quality

## Conversation Logs

Conversations are saved to `chat_logs/` directory with timestamps:
```
chat_logs/
├── chat_Keifth_Zotti_20250927_143022.json
└── chat_Virginia_Koch_20250927_150135.json
```

## Troubleshooting

### MLX Not Available
If you see "MLX not available", fallback models will still work. To use MLX models:
1. Ensure you're on Apple Silicon Mac
2. Install MLX: `pip install mlx mlx-lm`
3. Check MLX status in the interface header

### No Models Found
If no models are detected:
1. Check `slm_models/` directory exists
2. Verify model directories have `config.json`
3. For fallback models, ensure `samples.json` exists

## Next Steps
1. Train more models using `src/slm/train_model.py`
2. Fine-tune generation parameters in chat
3. Implement web interface (coming soon)
