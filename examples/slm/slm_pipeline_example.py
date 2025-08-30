#!/usr/bin/env python3
"""
Complete SLM Pipeline Example
==============================
End-to-end example demonstrating the full Avatar SLM pipeline:
1. Extract data from Neo4j
2. Train personalized model
3. Run inference
4. Interactive chat
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from slm.neo4j_data_extractor import Neo4jDataExtractor, ExtractionConfig
from slm.slm_trainer import SLMTrainer, TrainingConfig
from slm.slm_inference_engine import SLMInferenceEngine, InferenceConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AvatarSLMPipeline:
    """Complete pipeline for Avatar SLM system."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize pipeline with configuration.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.extractor = None
        self.trainer = None
        self.inference = None
        
        # Set up directories
        self._setup_directories()
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        default_config = {
            "neo4j": {
                "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                "username": os.getenv("NEO4J_USERNAME", "neo4j"),
                "password": os.getenv("NEO4J_PASSWORD", "password")
            },
            "extraction": {
                "output_dir": "data/extracted",
                "include_metadata": True,
                "max_messages": 10000
            },
            "training": {
                "model_name": "avatar_slm",
                "output_dir": "models",
                "epochs": 10,
                "batch_size": 16,
                "learning_rate": 5e-5,
                "warmup_steps": 100
            },
            "inference": {
                "temperature": 0.8,
                "top_k": 50,
                "top_p": 0.95,
                "max_length": 512
            }
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                # Merge with defaults
                self._merge_configs(default_config, user_config)
        
        return default_config
    
    def _merge_configs(self, base: Dict, update: Dict):
        """Recursively merge configuration dictionaries."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_configs(base[key], value)
            else:
                base[key] = value
    
    def _setup_directories(self):
        """Create necessary directories."""
        dirs = [
            self.config["extraction"]["output_dir"],
            self.config["training"]["output_dir"],
            "logs",
            "checkpoints"
        ]
        
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def extract_data(self, person_name: str) -> str:
        """
        Extract conversation data from Neo4j.
        
        Args:
            person_name: Name of person to extract data for
            
        Returns:
            Path to extracted data
        """
        logger.info(f"📊 Extracting data for {person_name}")
        
        # Initialize extractor
        extraction_config = ExtractionConfig(
            neo4j_uri=self.config["neo4j"]["uri"],
            neo4j_user=self.config["neo4j"]["username"],
            neo4j_password=self.config["neo4j"]["password"],
            output_dir=self.config["extraction"]["output_dir"],
            include_metadata=self.config["extraction"]["include_metadata"]
        )
        
        self.extractor = Neo4jDataExtractor(extraction_config)
        
        # Extract data
        output_path = self.extractor.extract_person_conversations(
            person_name=person_name,
            max_messages=self.config["extraction"]["max_messages"]
        )
        
        # Get statistics
        stats = self.extractor.get_extraction_stats()
        logger.info(f"✅ Extracted {stats['total_messages']} messages")
        logger.info(f"   Conversations: {stats['total_conversations']}")
        logger.info(f"   Date range: {stats['date_range']['start']} to {stats['date_range']['end']}")
        
        return output_path
    
    def train_model(self, data_path: str, model_name: Optional[str] = None) -> str:
        """
        Train SLM on extracted data.
        
        Args:
            data_path: Path to training data
            model_name: Optional model name override
            
        Returns:
            Path to trained model
        """
        model_name = model_name or self.config["training"]["model_name"]
        logger.info(f"🎓 Training model: {model_name}")
        
        # Initialize trainer
        training_config = TrainingConfig(
            model_name=model_name,
            data_path=data_path,
            output_dir=self.config["training"]["output_dir"],
            num_epochs=self.config["training"]["epochs"],
            batch_size=self.config["training"]["batch_size"],
            learning_rate=self.config["training"]["learning_rate"],
            warmup_steps=self.config["training"]["warmup_steps"],
            use_mlx=True,
            gradient_checkpointing=True
        )
        
        self.trainer = SLMTrainer(training_config)
        
        # Train model
        model_path = self.trainer.train()
        
        # Get training metrics
        metrics = self.trainer.get_final_metrics()
        logger.info(f"✅ Training complete!")
        logger.info(f"   Final loss: {metrics.get('loss', 'N/A'):.4f}")
        logger.info(f"   Model saved to: {model_path}")
        
        return model_path
    
    def setup_inference(self, model_path: str):
        """
        Set up inference engine.
        
        Args:
            model_path: Path to trained model
        """
        logger.info(f"🚀 Setting up inference engine")
        
        # Initialize inference engine
        inference_config = InferenceConfig(
            model_path=model_path,
            temperature=self.config["inference"]["temperature"],
            top_k=self.config["inference"]["top_k"],
            top_p=self.config["inference"]["top_p"],
            max_length=self.config["inference"]["max_length"],
            stream=True
        )
        
        self.inference = SLMInferenceEngine(inference_config)
        logger.info("✅ Inference engine ready!")
    
    def chat_demo(self):
        """Run interactive chat demonstration."""
        if not self.inference:
            logger.error("Inference engine not initialized!")
            return
        
        print("\n" + "="*60)
        print("🤖 AVATAR SLM CHAT INTERFACE")
        print("="*60)
        print("Type 'quit' to exit, 'clear' to reset conversation")
        print("="*60 + "\n")
        
        system_prompt = """You are a personalized AI assistant trained on conversation patterns.
        Respond in a natural, conversational style that matches the training data."""
        
        while True:
            try:
                user_input = input("\n👤 You: ")
                
                if user_input.lower() == 'quit':
                    print("\n👋 Goodbye!")
                    break
                
                if user_input.lower() == 'clear':
                    self.inference.clear_conversation()
                    print("🔄 Conversation cleared!")
                    continue
                
                print("🤖 Avatar: ", end="", flush=True)
                
                for chunk in self.inference.chat(
                    user_input,
                    system_prompt=system_prompt,
                    stream=True
                ):
                    print(chunk, end="", flush=True)
                
                print()  # New line after response
                
            except KeyboardInterrupt:
                print("\n\n👋 Chat interrupted. Goodbye!")
                break
            except Exception as e:
                logger.error(f"Chat error: {e}")
                print(f"\n❌ Error: {e}")
    
    def run_full_pipeline(self, person_name: str):
        """
        Run the complete pipeline end-to-end.
        
        Args:
            person_name: Name of person to create avatar for
        """
        print("\n" + "="*60)
        print(f"🚀 AVATAR SLM PIPELINE - {person_name}")
        print("="*60 + "\n")
        
        try:
            # Step 1: Extract data
            print("📊 Step 1: Extracting conversation data...")
            data_path = self.extract_data(person_name)
            print(f"   ✅ Data saved to: {data_path}\n")
            
            # Step 2: Train model
            print("🎓 Step 2: Training personalized model...")
            model_name = f"{person_name.lower().replace(' ', '_')}_avatar"
            model_path = self.train_model(data_path, model_name)
            print(f"   ✅ Model saved to: {model_path}\n")
            
            # Step 3: Setup inference
            print("🚀 Step 3: Setting up inference engine...")
            self.setup_inference(model_path)
            print("   ✅ Ready for chat!\n")
            
            # Step 4: Interactive demo
            print("💬 Step 4: Launching chat interface...")
            self.chat_demo()
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            print(f"\n❌ Pipeline error: {e}")
            raise
    
    def benchmark_model(self, model_path: str, test_prompts: Optional[list] = None):
        """
        Benchmark model performance.
        
        Args:
            model_path: Path to model
            test_prompts: Optional list of test prompts
        """
        if not test_prompts:
            test_prompts = [
                "Hello, how are you?",
                "What's your favorite topic to discuss?",
                "Tell me about your day.",
                "What do you think about AI?",
                "Can you help me with something?"
            ]
        
        print("\n" + "="*60)
        print("📊 MODEL BENCHMARKING")
        print("="*60 + "\n")
        
        # Setup inference if needed
        if not self.inference:
            self.setup_inference(model_path)
        
        results = []
        
        for i, prompt in enumerate(test_prompts, 1):
            print(f"Test {i}/{len(test_prompts)}: {prompt}")
            
            start_time = datetime.now()
            response = self.inference.generate(
                prompt,
                max_new_tokens=100,
                stream=False
            )
            end_time = datetime.now()
            
            duration = (end_time - start_time).total_seconds()
            tokens = len(response.split())
            tokens_per_sec = tokens / duration if duration > 0 else 0
            
            results.append({
                "prompt": prompt,
                "response": response[:100] + "..." if len(response) > 100 else response,
                "duration": duration,
                "tokens": tokens,
                "tokens_per_sec": tokens_per_sec
            })
            
            print(f"   Response: {results[-1]['response']}")
            print(f"   Time: {duration:.2f}s | Tokens/sec: {tokens_per_sec:.1f}\n")
        
        # Summary statistics
        avg_duration = sum(r["duration"] for r in results) / len(results)
        avg_tokens_per_sec = sum(r["tokens_per_sec"] for r in results) / len(results)
        
        print("="*60)
        print("📈 BENCHMARK SUMMARY")
        print(f"   Average response time: {avg_duration:.2f}s")
        print(f"   Average tokens/sec: {avg_tokens_per_sec:.1f}")
        print("="*60 + "\n")
        
        return results


def main():
    """Main entry point for the pipeline example."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Avatar SLM Pipeline - Train personalized language models"
    )
    
    parser.add_argument(
        "command",
        choices=["extract", "train", "chat", "full", "benchmark"],
        help="Command to run"
    )
    
    parser.add_argument(
        "--person",
        type=str,
        help="Person name for data extraction"
    )
    
    parser.add_argument(
        "--data-path",
        type=str,
        help="Path to training data (for train command)"
    )
    
    parser.add_argument(
        "--model-path",
        type=str,
        help="Path to model (for chat/benchmark commands)"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = AvatarSLMPipeline(config_path=args.config)
    
    # Execute command
    if args.command == "full":
        if not args.person:
            parser.error("--person required for full pipeline")
        pipeline.run_full_pipeline(args.person)
    
    elif args.command == "extract":
        if not args.person:
            parser.error("--person required for extraction")
        data_path = pipeline.extract_data(args.person)
        print(f"✅ Data extracted to: {data_path}")
    
    elif args.command == "train":
        if not args.data_path:
            parser.error("--data-path required for training")
        model_path = pipeline.train_model(args.data_path)
        print(f"✅ Model trained: {model_path}")
    
    elif args.command == "chat":
        if not args.model_path:
            parser.error("--model-path required for chat")
        pipeline.setup_inference(args.model_path)
        pipeline.chat_demo()
    
    elif args.command == "benchmark":
        if not args.model_path:
            parser.error("--model-path required for benchmark")
        pipeline.benchmark_model(args.model_path)


if __name__ == "__main__":
    main()
