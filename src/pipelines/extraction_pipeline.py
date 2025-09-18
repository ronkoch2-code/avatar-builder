#!/usr/bin/env python3
"""
Message Extraction Pipeline for Avatar-Engine
==============================================

Orchestrates the complete message extraction and processing pipeline:
1. Extract messages from iMessage database
2. Process extracted JSON through Avatar-Engine
3. Generate personality profiles and avatars

Author: Avatar-Engine Team
Date: 2025-09-07
Version: 1.0.0
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import argparse
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import extraction and processing modules
from imessage_extractor import IMessageExtractor
from message_data_loader import MessageDataLoader
from avatar_intelligence_pipeline import AvatarSystemManager
from config_manager import ConfigManager
from security_utils import SecureLogger

# Configure logging
logger = SecureLogger(__name__, log_file="logs/extraction_pipeline.log")


class ExtractionPipeline:
    """Orchestrates the complete extraction and processing pipeline"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the extraction pipeline
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or self._get_default_config()
        self.logger = logger
        
        # Initialize components
        self.extractor = IMessageExtractor(self.config.get('extractor_config', {}))
        self.config_manager = ConfigManager()
        
        # Track pipeline state
        self.state = {
            'started_at': None,
            'completed_at': None,
            'stages_completed': [],
            'extracted_file': None,
            'messages_processed': 0,
            'profiles_generated': 0,
            'errors': []
        }
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default pipeline configuration"""
        return {
            'extractor_config': {
                'output_dir': 'data/extracted',
                'temp_dir': 'data/temp',
                'anonymize_phones': True,
                'human_readable_dates': True,
                'cleanup_temp': True
            },
            'processor_config': {
                'enable_llm': False,  # Start without LLM for testing
                'batch_size': 100,
                'neo4j_config': None  # Will be loaded from config_manager
            },
            'pipeline_config': {
                'save_checkpoints': True,
                'checkpoint_dir': 'data/checkpoints',
                'continue_on_error': False,
                'max_retries': 3
            }
        }
    
    def run_stage_1_extraction(self, message_limit: Optional[int] = None) -> str:
        """
        Stage 1: Extract messages from iMessage database
        
        Args:
            message_limit: Maximum number of messages to extract
            
        Returns:
            Path to extracted JSON file
        """
        self.logger.log_event("pipeline_stage", {
            "stage": 1,
            "name": "extraction",
            "status": "starting",
            "limit": message_limit
        })
        
        try:
            # Run extraction
            output_file = self.extractor.run_extraction_pipeline(message_limit)
            
            # Update state
            self.state['extracted_file'] = output_file
            self.state['stages_completed'].append('extraction')
            
            # Count messages
            with open(output_file, 'r') as f:
                messages = json.load(f)
                self.state['messages_processed'] = len(messages)
            
            self.logger.log_event("pipeline_stage", {
                "stage": 1,
                "name": "extraction",
                "status": "completed",
                "output": output_file,
                "message_count": self.state['messages_processed']
            })
            
            # Save checkpoint if configured
            if self.config.get('pipeline_config', {}).get('save_checkpoints', True):
                self._save_checkpoint('stage_1_complete')
            
            return output_file
            
        except Exception as e:
            self.logger.log_event("pipeline_stage", {
                "stage": 1,
                "name": "extraction",
                "status": "failed",
                "error": str(e)
            }, level="error")
            
            self.state['errors'].append({
                'stage': 'extraction',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            
            if not self.config.get('pipeline_config', {}).get('continue_on_error', False):
                raise
            
            return None
    
    def run_stage_2_processing(self, json_file: str) -> Dict[str, Any]:
        """
        Stage 2: Process extracted JSON through Avatar-Engine
        
        Args:
            json_file: Path to extracted JSON file
            
        Returns:
            Processing results dictionary
        """
        self.logger.log_event("pipeline_stage", {
            "stage": 2,
            "name": "processing",
            "status": "starting",
            "input": json_file
        })
        
        try:
            # Initialize data loader with Neo4j driver
            from neo4j import GraphDatabase
            
            driver = GraphDatabase.driver(
                self.config_manager.neo4j.uri,
                auth=(self.config_manager.neo4j.username, self.config_manager.neo4j.password)
            )
            
            loader = MessageDataLoader(driver)
            
            # Load messages from JSON file into Neo4j
            stats = loader.load_from_json(json_file, limit=None)
            total_processed = stats.get('messages_created', 0)
            
            # Update state
            self.state['stages_completed'].append('processing')
            
            results = {
                'messages_loaded': total_processed,
                'neo4j_status': 'connected',
                'timestamp': datetime.now().isoformat(),
                'loader_stats': stats
            }
            
            # Clean up driver
            driver.close()
            
            self.logger.log_event("pipeline_stage", {
                "stage": 2,
                "name": "processing",
                "status": "completed",
                "results": results
            })
            
            # Save checkpoint
            if self.config.get('pipeline_config', {}).get('save_checkpoints', True):
                self._save_checkpoint('stage_2_complete')
            
            return results
            
        except Exception as e:
            self.logger.log_event("pipeline_stage", {
                "stage": 2,
                "name": "processing",
                "status": "failed",
                "error": str(e)
            }, level="error")
            
            self.state['errors'].append({
                'stage': 'processing',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            
            if not self.config.get('pipeline_config', {}).get('continue_on_error', False):
                raise
            
            return {'status': 'failed', 'error': str(e)}
    
    def run_stage_3_profiling(self) -> Dict[str, Any]:
        """
        Stage 3: Generate personality profiles from processed data
        
        Returns:
            Profiling results dictionary
        """
        self.logger.log_event("pipeline_stage", {
            "stage": 3,
            "name": "profiling",
            "status": "starting"
        })
        
        try:
            # Initialize Avatar System Manager
            from neo4j import GraphDatabase
            
            # Create Neo4j driver
            driver = GraphDatabase.driver(
                self.config_manager.neo4j.uri,
                auth=(self.config_manager.neo4j.username, self.config_manager.neo4j.password)
            )
            
            # Initialize the avatar system manager
            avatar_manager = AvatarSystemManager(driver)
            
            # Generate profiles for all people with sufficient data
            stats = avatar_manager.initialize_all_people(min_messages=50)
            
            # Get the actual profile count from stats
            profiles_count = stats.get('created', 0)
            
            # Save profile statistics
            output_dir = Path(self.config.get('extractor_config', {}).get('output_dir', 'data/extracted')) / 'profiles'
            output_dir.mkdir(parents=True, exist_ok=True, mode=0o750)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            stats_file = output_dir / f"profile_generation_stats_{timestamp}.json"
            
            with open(stats_file, 'w') as f:
                json.dump(stats, f, indent=2)
            
            # Update state
            self.state['profiles_generated'] = profiles_count
            self.state['stages_completed'].append('profiling')
            
            results = {
                'profiles_generated': profiles_count,
                'output_file': str(stats_file),
                'stats': stats,
                'timestamp': datetime.now().isoformat()
            }
            
            # Clean up driver
            driver.close()
            
            self.logger.log_event("pipeline_stage", {
                "stage": 3,
                "name": "profiling",
                "status": "completed",
                "results": results
            })
            
            # Save checkpoint
            if self.config.get('pipeline_config', {}).get('save_checkpoints', True):
                self._save_checkpoint('stage_3_complete')
            
            return results
            
        except Exception as e:
            self.logger.log_event("pipeline_stage", {
                "stage": 3,
                "name": "profiling",
                "status": "failed",
                "error": str(e)
            }, level="error")
            
            self.state['errors'].append({
                'stage': 'profiling',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            
            if not self.config.get('pipeline_config', {}).get('continue_on_error', False):
                raise
            
            return {'status': 'failed', 'error': str(e)}
    
    def run_complete_pipeline(self, message_limit: Optional[int] = None, 
                            skip_extraction: bool = False,
                            existing_json: Optional[str] = None) -> Dict[str, Any]:
        """
        Run the complete extraction and processing pipeline
        
        Args:
            message_limit: Maximum number of messages to extract
            skip_extraction: Skip extraction and use existing JSON
            existing_json: Path to existing JSON file (if skip_extraction=True)
            
        Returns:
            Pipeline results dictionary
        """
        self.state['started_at'] = datetime.now().isoformat()
        
        self.logger.log_event("pipeline", {
            "status": "starting",
            "config": {
                "message_limit": message_limit,
                "skip_extraction": skip_extraction,
                "existing_json": existing_json
            }
        })
        
        try:
            # Stage 1: Extraction (optional)
            if skip_extraction and existing_json:
                json_file = existing_json
                self.logger.log_event("pipeline", {
                    "note": "Skipping extraction, using existing JSON",
                    "file": json_file
                })
            else:
                json_file = self.run_stage_1_extraction(message_limit)
                if not json_file:
                    raise ValueError("Extraction failed, cannot continue")
            
            # Stage 2: Processing
            processing_results = self.run_stage_2_processing(json_file)
            
            # Stage 3: Profiling
            profiling_results = self.run_stage_3_profiling()
            
            # Complete
            self.state['completed_at'] = datetime.now().isoformat()
            
            # Generate summary
            summary = {
                'status': 'completed',
                'started_at': self.state['started_at'],
                'completed_at': self.state['completed_at'],
                'stages_completed': self.state['stages_completed'],
                'messages_processed': self.state['messages_processed'],
                'profiles_generated': self.state['profiles_generated'],
                'extracted_file': self.state['extracted_file'],
                'errors': self.state['errors'],
                'results': {
                    'extraction': {'file': json_file} if json_file else None,
                    'processing': processing_results,
                    'profiling': profiling_results
                }
            }
            
            # Save final summary
            self._save_pipeline_summary(summary)
            
            self.logger.log_event("pipeline", {
                "status": "completed",
                "summary": summary
            })
            
            print("\n" + "="*50)
            print("🎉 PIPELINE COMPLETE!")
            print("="*50)
            print(f"📊 Messages Processed: {self.state['messages_processed']}")
            print(f"👤 Profiles Generated: {self.state['profiles_generated']}")
            print(f"⏱️  Duration: {self._calculate_duration()}")
            print(f"📁 Output: {self.state['extracted_file']}")
            
            return summary
            
        except Exception as e:
            self.state['completed_at'] = datetime.now().isoformat()
            
            error_summary = {
                'status': 'failed',
                'error': str(e),
                'started_at': self.state['started_at'],
                'completed_at': self.state['completed_at'],
                'stages_completed': self.state['stages_completed'],
                'errors': self.state['errors']
            }
            
            self.logger.log_event("pipeline", {
                "status": "failed",
                "summary": error_summary
            }, level="error")
            
            print("\n" + "="*50)
            print("❌ PIPELINE FAILED")
            print("="*50)
            print(f"Error: {e}")
            print(f"Stages Completed: {', '.join(self.state['stages_completed'])}")
            
            raise
    
    def _save_checkpoint(self, checkpoint_name: str):
        """Save pipeline checkpoint for recovery"""
        checkpoint_dir = Path(self.config.get('pipeline_config', {}).get('checkpoint_dir', 'data/checkpoints'))
        checkpoint_dir.mkdir(parents=True, exist_ok=True, mode=0o750)
        
        checkpoint_file = checkpoint_dir / f"{checkpoint_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(checkpoint_file, 'w') as f:
            json.dump(self.state, f, indent=2)
        
        self.logger.log_event("checkpoint", {
            "name": checkpoint_name,
            "file": str(checkpoint_file)
        })
    
    def _save_pipeline_summary(self, summary: Dict[str, Any]):
        """Save pipeline execution summary"""
        output_dir = Path(self.config.get('extractor_config', {}).get('output_dir', 'data/extracted')) / 'summaries'
        output_dir.mkdir(parents=True, exist_ok=True, mode=0o750)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = output_dir / f"pipeline_summary_{timestamp}.json"
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        os.chmod(summary_file, 0o640)
    
    def _calculate_duration(self) -> str:
        """Calculate pipeline execution duration"""
        if not self.state['started_at'] or not self.state['completed_at']:
            return "Unknown"
        
        start = datetime.fromisoformat(self.state['started_at'])
        end = datetime.fromisoformat(self.state['completed_at'])
        duration = end - start
        
        hours, remainder = divmod(duration.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        elif minutes > 0:
            return f"{int(minutes)}m {int(seconds)}s"
        else:
            return f"{int(seconds)}s"


def main():
    """Command-line interface for extraction pipeline"""
    parser = argparse.ArgumentParser(
        description="Run the complete iMessage extraction and processing pipeline"
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        help='Maximum number of messages to extract'
    )
    parser.add_argument(
        '--skip-extraction',
        action='store_true',
        help='Skip extraction stage and use existing JSON'
    )
    parser.add_argument(
        '--json-file',
        type=str,
        help='Path to existing JSON file (when skipping extraction)'
    )
    parser.add_argument(
        '--enable-llm',
        action='store_true',
        help='Enable LLM enhancement for personality profiling'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to pipeline configuration JSON file'
    )
    parser.add_argument(
        '--stage',
        choices=['all', 'extract', 'process', 'profile'],
        default='all',
        help='Run specific pipeline stage or all stages'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = {}
    if args.config:
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    # Override with command-line arguments
    if args.enable_llm:
        if 'processor_config' not in config:
            config['processor_config'] = {}
        config['processor_config']['enable_llm'] = True
    
    # Initialize pipeline
    pipeline = ExtractionPipeline(config)
    
    # Run requested stages
    if args.stage == 'extract':
        result = pipeline.run_stage_1_extraction(args.limit)
        print(f"Extraction complete: {result}")
    elif args.stage == 'process':
        if not args.json_file:
            print("Error: --json-file required for process stage")
            return 1
        result = pipeline.run_stage_2_processing(args.json_file)
        print(f"Processing complete: {result}")
    elif args.stage == 'profile':
        result = pipeline.run_stage_3_profiling()
        print(f"Profiling complete: {result}")
    else:  # all
        pipeline.run_complete_pipeline(
            message_limit=args.limit,
            skip_extraction=args.skip_extraction,
            existing_json=args.json_file
        )
    
    return 0


if __name__ == "__main__":
    exit(main())
