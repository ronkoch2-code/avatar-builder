#!/usr/bin/env python3
"""
LLM Integration Fix for Extraction Pipeline
===========================================

This module contains the updated run_stage_3_profiling method that properly
integrates LLM capabilities through the EnhancedAvatarSystemManager.
"""

import asyncio
from typing import Dict, Any

def run_stage_3_profiling_with_llm(self) -> Dict[str, Any]:
    """
    Stage 3: Generate personality profiles from processed data with LLM support
    
    Returns:
        Profiling results dictionary
    """
    self.logger.log_event("pipeline_stage", {
        "stage": 3,
        "name": "profiling",
        "status": "starting"
    })
    
    # Capture token balance before profiling
    self._capture_token_balance("profiling", "before")
    
    try:
        # Initialize Avatar System Manager
        from neo4j import GraphDatabase
        import os
        
        # Create Neo4j driver
        driver = GraphDatabase.driver(
            self.config_manager.neo4j.uri,
            auth=(self.config_manager.neo4j.username, self.config_manager.neo4j.password)
        )
        
        # Check if LLM is enabled and use appropriate manager
        enable_llm = self.config.get('processor_config', {}).get('enable_llm', False)
        
        if enable_llm:
            # Get API key from environment or config
            api_key = os.getenv('ANTHROPIC_API_KEY')
            
            if not api_key:
                self.logger.log_event("pipeline_stage", {
                    "stage": 3,
                    "warning": "LLM enabled but ANTHROPIC_API_KEY not set, falling back to basic analysis"
                }, level="warning")
                print("\n⚠️  WARNING: LLM analysis requested but ANTHROPIC_API_KEY environment variable not set!")
                print("   Falling back to basic analysis without LLM enhancement.")
                print("   To enable LLM analysis, set: export ANTHROPIC_API_KEY='your-api-key'\n")
                
                # Fall back to basic analysis
                from avatar_intelligence_pipeline import AvatarSystemManager
                avatar_manager = AvatarSystemManager(driver)
                stats = avatar_manager.initialize_all_people(min_messages=50)
                
            else:
                # Use enhanced avatar manager with LLM
                self.logger.log_event("pipeline_stage", {
                    "stage": 3,
                    "note": "Using Enhanced Avatar Manager with LLM integration"
                })
                print("\n🤖 LLM Integration Active:")
                print(f"   - API Key: {'*' * 8}{api_key[-4:]}")
                print(f"   - Model: claude-sonnet-4-20250514")
                print(f"   - Token Monitoring: Enabled\n")
                
                from enhanced_avatar_pipeline import EnhancedAvatarSystemManager
                
                # Initialize enhanced manager
                avatar_manager = EnhancedAvatarSystemManager(
                    neo4j_driver=driver,
                    anthropic_api_key=api_key,
                    claude_model="claude-sonnet-4-20250514",
                    enable_llm_analysis=True
                )
                
                # Get list of people to analyze
                with driver.session() as session:
                    result = session.run("""
                    MATCH (p:Person)-[:SENT|RECEIVED]-(m:Message)
                    WITH p, COUNT(m) AS message_count
                    WHERE message_count >= $min_messages
                    RETURN p.id AS person_id, p.name AS name, message_count
                    ORDER BY message_count DESC
                    """, min_messages=50)
                    
                    people_to_analyze = [
                        {"id": record["person_id"], "name": record["name"], "messages": record["message_count"]}
                        for record in result
                    ]
                
                print(f"📊 Found {len(people_to_analyze)} people with sufficient data for analysis")
                
                if people_to_analyze:
                    # Run async batch processing
                    async def run_llm_analysis():
                        identifiers = [p["name"] for p in people_to_analyze[:5]]  # Limit to 5 for cost control
                        
                        print(f"🔍 Analyzing top {len(identifiers)} people with LLM enhancement...")
                        for i, person in enumerate(people_to_analyze[:5], 1):
                            print(f"   {i}. {person['name']} ({person['messages']} messages)")
                        
                        results = await avatar_manager.batch_create_profiles(
                            person_identifiers=identifiers,
                            min_messages=50,
                            max_concurrent=2  # Conservative for cost management
                        )
                        
                        return results
                    
                    # Run the async analysis
                    llm_results = asyncio.run(run_llm_analysis())
                    
                    # Process results
                    successful = sum(1 for r in llm_results if r.get("status") == "success")
                    failed = len(llm_results) - successful
                    total_cost = sum(r.get("total_cost", 0.0) for r in llm_results)
                    
                    stats = {
                        "created": successful,
                        "failed": failed,
                        "total": len(llm_results),
                        "llm_enhanced": True,
                        "total_cost": total_cost,
                        "details": llm_results
                    }
                    
                    print(f"\n✅ LLM Analysis Complete:")
                    print(f"   - Profiles Created: {successful}")
                    print(f"   - Failed: {failed}")
                    print(f"   - Total Cost: ${total_cost:.4f}")
                    
                    # Also run basic analysis for remaining people
                    if len(people_to_analyze) > 5:
                        print(f"\n📝 Running basic analysis for remaining {len(people_to_analyze) - 5} people...")
                        from avatar_intelligence_pipeline import AvatarSystemManager
                        basic_manager = AvatarSystemManager(driver)
                        basic_stats = basic_manager.initialize_all_people(min_messages=50)
                        stats["basic_analysis"] = basic_stats
                else:
                    stats = {"created": 0, "message": "No people with sufficient messages"}
                    
        else:
            # Use basic avatar manager
            print("\n📝 Running basic personality analysis (LLM disabled)")
            from avatar_intelligence_pipeline import AvatarSystemManager
            avatar_manager = AvatarSystemManager(driver)
            stats = avatar_manager.initialize_all_people(min_messages=50)
        
        # Get the actual profile count from stats
        profiles_count = stats.get('created', 0)
        
        # Save profile statistics
        from pathlib import Path
        import json
        from datetime import datetime
        
        output_dir = Path(self.config.get('extractor_config', {}).get('output_dir', 'data/extracted')) / 'profiles'
        output_dir.mkdir(parents=True, exist_ok=True, mode=0o750)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stats_file = output_dir / f"profile_generation_stats_{timestamp}.json"
        
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
        # Update state
        self.state['profiles_generated'] = profiles_count
        self.state['stages_completed'].append('profiling')
        
        # Capture token balance after profiling
        self._capture_token_balance("profiling", "after")
        
        # Display token usage delta
        self._display_token_usage_delta("profiling")
        
        results = {
            'profiles_generated': profiles_count,
            'output_file': str(stats_file),
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        }
        
        # Add token usage to results if available
        if self.token_monitor:
            session_summary = self.token_monitor.get_session_summary(format="compact")
            results['token_usage'] = session_summary
        
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
