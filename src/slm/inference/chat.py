#!/usr/bin/env python3
"""
SLM Interactive Chat Interface
================================
Command-line interface for chatting with trained Avatar language models.

This module provides an interactive CLI for loading and chatting with
trained SLM models, supporting both MLX and fallback implementations.
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any, Generator
import time
from datetime import datetime
import readline  # For better input handling

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from src.config_manager import ConfigManager
except ImportError:
    print("Warning: ConfigManager not available")
    ConfigManager = None

try:
    import mlx
    import mlx.core as mx
    MLX_AVAILABLE = True
except ImportError:
    MLX_AVAILABLE = False
    print("Info: MLX not available. Will use fallback mode.")

# Import SLM modules
from src.slm.slm_inference_engine import (
    SLMInferenceEngine,
    InferenceConfig,
    ConversationManager
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelLoader:
    """Handles loading and management of trained models."""
    
    def __init__(self, models_dir: Path = None):
        """
        Initialize model loader.
        
        Args:
            models_dir: Directory containing trained models
        """
        if models_dir is None:
            models_dir = Path(__file__).parent.parent.parent.parent / "slm_models"
        self.models_dir = Path(models_dir)
        self.available_models = self._scan_models()
    
    def _scan_models(self) -> Dict[str, Dict]:
        """Scan for available models."""
        models = {}
        
        if not self.models_dir.exists():
            logger.warning(f"Models directory not found: {self.models_dir}")
            return models
        
        # Scan for model directories
        for model_path in self.models_dir.iterdir():
            if model_path.is_dir():
                config_path = model_path / "config.json"
                if config_path.exists():
                    try:
                        with open(config_path, 'r') as f:
                            config = json.load(f)
                        
                        models[model_path.name] = {
                            "path": model_path,
                            "config": config,
                            "type": config.get("framework", "unknown")
                        }
                    except Exception as e:
                        logger.warning(f"Failed to load config for {model_path.name}: {e}")
        
        return models
    
    def list_models(self) -> List[str]:
        """Get list of available model names."""
        return list(self.available_models.keys())
    
    def get_model_info(self, model_name: str) -> Optional[Dict]:
        """Get information about a specific model."""
        return self.available_models.get(model_name)
    
    def load_model(self, model_name: str) -> Optional[Any]:
        """
        Load a specific model.
        
        Args:
            model_name: Name of the model to load
            
        Returns:
            Loaded model or None if failed
        """
        model_info = self.get_model_info(model_name)
        if not model_info:
            logger.error(f"Model not found: {model_name}")
            return None
        
        model_type = model_info["type"]
        model_path = model_info["path"]
        
        logger.info(f"Loading {model_type} model: {model_name}")
        
        if model_type == "mlx":
            return self._load_mlx_model(model_path, model_info["config"])
        elif model_type == "fallback":
            return self._load_fallback_model(model_path, model_info["config"])
        else:
            logger.error(f"Unknown model type: {model_type}")
            return None
    
    def _load_mlx_model(self, model_path: Path, config: Dict) -> Optional[Any]:
        """Load MLX model."""
        if not MLX_AVAILABLE:
            logger.error("MLX not available, cannot load MLX model")
            return None
        
        try:
            # Create inference configuration
            inference_config = InferenceConfig(
                model_path=str(model_path),
                max_length=config.get("max_length", 512),
                temperature=0.7,
                top_k=40,
                top_p=0.95
            )
            
            # Create inference engine
            engine = SLMInferenceEngine(inference_config)
            return engine
        except Exception as e:
            logger.error(f"Failed to load MLX model: {e}")
            return None
    
    def _load_fallback_model(self, model_path: Path, config: Dict) -> Optional[Any]:
        """Load fallback model."""
        try:
            # Load samples for fallback mode
            samples_path = model_path / "samples.json"
            if samples_path.exists():
                with open(samples_path, 'r') as f:
                    samples = json.load(f)
                
                # Create simple fallback model
                return FallbackModel(config, samples)
            else:
                logger.warning("No samples found for fallback model")
                return None
        except Exception as e:
            logger.error(f"Failed to load fallback model: {e}")
            return None


class FallbackModel:
    """Simple fallback model for when MLX is not available."""
    
    def __init__(self, config: Dict, samples: List[str]):
        """Initialize fallback model."""
        self.config = config
        self.samples = samples
        self.person_name = config.get("person_name", "Avatar")
        self.conversation = ConversationManager()
    
    def generate(self, prompt: str, max_new_tokens: int = 256, stream: bool = False) -> str:
        """Generate response using samples."""
        import random
        
        # Simple response selection from samples
        if self.samples:
            response = random.choice(self.samples)
            
            # Truncate to max length
            words = response.split()
            if len(words) > max_new_tokens // 4:  # Rough estimate
                response = " ".join(words[:max_new_tokens // 4]) + "..."
            
            if stream:
                # Simulate streaming
                for char in response:
                    yield char
                    time.sleep(0.01)  # Small delay for effect
            else:
                return response
        else:
            fallback_response = f"Hello! I'm {self.person_name}. How can I help you today?"
            if stream:
                for char in fallback_response:
                    yield char
                    time.sleep(0.01)
            else:
                return fallback_response
    
    def chat(self, message: str, stream: bool = True) -> str:
        """Chat interface for fallback model."""
        return self.generate(message, stream=stream)


class ChatInterface:
    """Interactive chat interface for SLM models."""
    
    def __init__(self):
        """Initialize chat interface."""
        self.model = None
        self.model_name = None
        self.loader = ModelLoader()
        self.conversation_history = []
        self.session_start = datetime.now()
    
    def print_header(self):
        """Print welcome header."""
        print("\n" + "="*60)
        print("  Avatar Engine - SLM Chat Interface")
        print("  MLX Status: " + ("✓ Available" if MLX_AVAILABLE else "✗ Not Available"))
        print("="*60 + "\n")
    
    def print_models(self):
        """Print available models."""
        models = self.loader.list_models()
        if not models:
            print("No models found in slm_models directory.")
            return
        
        print("Available models:")
        for i, model_name in enumerate(models, 1):
            model_info = self.loader.get_model_info(model_name)
            model_type = model_info["config"].get("framework", "unknown")
            person = model_info["config"].get("person_name", "Unknown")
            examples = model_info["config"].get("training_examples", 0)
            
            status = "✓" if (model_type == "fallback" or MLX_AVAILABLE) else "✗"
            print(f"  {i}. {status} {model_name}")
            print(f"     Person: {person}, Type: {model_type}, Examples: {examples}")
    
    def select_model(self) -> bool:
        """Select and load a model."""
        models = self.loader.list_models()
        if not models:
            print("No models available.")
            return False
        
        self.print_models()
        print()
        
        # Get user selection
        while True:
            try:
                choice = input("Select model (number or name, 'q' to quit): ").strip()
                
                if choice.lower() == 'q':
                    return False
                
                # Try as number
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(models):
                        model_name = models[idx]
                    else:
                        print("Invalid selection. Try again.")
                        continue
                else:
                    # Try as name
                    if choice in models:
                        model_name = choice
                    else:
                        print("Model not found. Try again.")
                        continue
                
                # Load the model
                print(f"\nLoading {model_name}...")
                self.model = self.loader.load_model(model_name)
                
                if self.model:
                    self.model_name = model_name
                    model_info = self.loader.get_model_info(model_name)
                    person = model_info["config"].get("person_name", "Avatar")
                    print(f"✓ Model loaded successfully!")
                    print(f"  You're now chatting with {person}")
                    return True
                else:
                    print(f"✗ Failed to load model: {model_name}")
                    return False
                    
            except KeyboardInterrupt:
                return False
            except Exception as e:
                print(f"Error: {e}")
                continue
    
    def chat_loop(self):
        """Main chat interaction loop."""
        if not self.model:
            print("No model loaded.")
            return
        
        print("\n" + "-"*60)
        print("Chat started. Commands:")
        print("  /help    - Show help")
        print("  /clear   - Clear conversation")
        print("  /save    - Save conversation")
        print("  /switch  - Switch model")
        print("  /exit    - Exit chat")
        print("-"*60 + "\n")
        
        while True:
            try:
                # Get user input
                user_input = input("\nYou: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith("/"):
                    if not self._handle_command(user_input):
                        break
                    continue
                
                # Add to history
                self.conversation_history.append({
                    "role": "user",
                    "content": user_input,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Generate response
                print("\nAvatar: ", end="", flush=True)
                
                # Check if model supports streaming
                if hasattr(self.model, 'chat'):
                    response_gen = self.model.chat(user_input, stream=True)
                else:
                    response_gen = self.model.generate(user_input, stream=True)
                
                # Handle streaming or non-streaming response
                full_response = ""
                if isinstance(response_gen, (Generator, type(iter([])))):
                    for chunk in response_gen:
                        print(chunk, end="", flush=True)
                        full_response += chunk
                else:
                    print(response_gen)
                    full_response = response_gen
                
                print()  # New line after response
                
                # Add to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": full_response,
                    "timestamp": datetime.now().isoformat()
                })
                
            except KeyboardInterrupt:
                print("\n\nChat interrupted.")
                break
            except Exception as e:
                print(f"\nError: {e}")
                continue
    
    def _handle_command(self, command: str) -> bool:
        """
        Handle chat commands.
        
        Returns:
            True to continue chat, False to exit
        """
        cmd = command.lower().split()[0]
        
        if cmd == "/exit" or cmd == "/quit":
            return False
        
        elif cmd == "/help":
            print("\nAvailable commands:")
            print("  /help    - Show this help")
            print("  /clear   - Clear conversation history")
            print("  /save    - Save conversation to file")
            print("  /switch  - Switch to different model")
            print("  /exit    - Exit chat")
        
        elif cmd == "/clear":
            self.conversation_history = []
            if hasattr(self.model, 'conversation'):
                self.model.conversation.clear()
            print("Conversation cleared.")
        
        elif cmd == "/save":
            self._save_conversation()
        
        elif cmd == "/switch":
            if self.select_model():
                self.conversation_history = []
                print("Switched to new model. Conversation cleared.")
            else:
                print("Model switch cancelled.")
        
        else:
            print(f"Unknown command: {command}")
        
        return True
    
    def _save_conversation(self):
        """Save conversation to file."""
        if not self.conversation_history:
            print("No conversation to save.")
            return
        
        # Create filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chat_{self.model_name}_{timestamp}.json"
        
        # Save to file
        try:
            output_dir = Path("chat_logs")
            output_dir.mkdir(exist_ok=True)
            
            output_path = output_dir / filename
            
            with open(output_path, 'w') as f:
                json.dump({
                    "model": self.model_name,
                    "session_start": self.session_start.isoformat(),
                    "session_end": datetime.now().isoformat(),
                    "messages": self.conversation_history
                }, f, indent=2)
            
            print(f"Conversation saved to: {output_path}")
        except Exception as e:
            print(f"Failed to save conversation: {e}")
    
    def run(self):
        """Run the chat interface."""
        self.print_header()
        
        # Select and load model
        if not self.select_model():
            print("No model selected. Exiting.")
            return
        
        # Start chat loop
        self.chat_loop()
        
        # Exit message
        print("\nThank you for chatting! Goodbye.")
        
        # Offer to save conversation
        if self.conversation_history:
            save = input("Save conversation? (y/n): ").strip().lower()
            if save == 'y':
                self._save_conversation()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Interactive chat interface for Avatar SLM models"
    )
    parser.add_argument(
        "--model",
        type=str,
        help="Specific model to load (skips selection)"
    )
    parser.add_argument(
        "--models-dir",
        type=str,
        help="Directory containing trained models"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and run interface
    interface = ChatInterface()
    
    # Override models directory if specified
    if args.models_dir:
        interface.loader.models_dir = Path(args.models_dir)
        interface.loader.available_models = interface.loader._scan_models()
    
    # Auto-load model if specified
    if args.model:
        interface.model = interface.loader.load_model(args.model)
        if interface.model:
            interface.model_name = args.model
            interface.print_header()
            print(f"Loaded model: {args.model}")
            interface.chat_loop()
        else:
            print(f"Failed to load model: {args.model}")
    else:
        # Run normal interface
        interface.run()


if __name__ == "__main__":
    main()
