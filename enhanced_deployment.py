#!/usr/bin/env python3
"""
Enhanced Avatar Intelligence System - Deployment and Management
=============================================================

This script handles deployment, management, and monitoring of the
LLM-enhanced Avatar Intelligence System.

Usage:
    python enhanced_deployment.py --deploy          # Deploy enhanced schema
    python enhanced_deployment.py --status          # Check system status
    python enhanced_deployment.py --analyze-all     # Analyze all profiles
    python enhanced_deployment.py --analyze-person "Name"  # Analyze specific person
    python enhanced_deployment.py --costs           # Show cost summary
"""

import argparse
import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from neo4j import GraphDatabase
from src.config_manager import ConfigManager, CostMonitor
from src.enhanced_avatar_pipeline import EnhancedAvatarSystemManager

logger = logging.getLogger(__name__)


class EnhancedSystemDeployment:
    """
    Enhanced Avatar Intelligence System deployment and management
    """
    
    def __init__(self, config: ConfigManager):
        """
        Initialize deployment manager
        
        Args:
            config: Configuration manager instance
        """
        self.config = config
        self.cost_monitor = CostMonitor(config)
        
        # Initialize Neo4j connection
        try:
            driver_config = config.get_neo4j_driver_config()
            self.driver = GraphDatabase.driver(**driver_config)
            logger.info("Connected to Neo4j database")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
        
        # Initialize enhanced avatar system
        try:
            self.avatar_system = EnhancedAvatarSystemManager(
                neo4j_driver=self.driver,
                anthropic_api_key=config.anthropic.api_key,
                claude_model=config.anthropic.model,
                enable_llm_analysis=config.system.enable_llm_analysis
            )
            logger.info("Enhanced Avatar System initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Avatar System: {e}")
            raise
    
    def deploy_enhanced_schema(self):
        """Deploy the enhanced Neo4j schema"""
        logger.info("Deploying enhanced Neo4j schema...")
        
        schema_queries = [
            # Enhanced constraints
            """
            CREATE CONSTRAINT personality_profile_id IF NOT EXISTS 
            FOR (pp:PersonalityProfile) REQUIRE pp.id IS UNIQUE
            """,
            """
            CREATE CONSTRAINT communication_style_id IF NOT EXISTS 
            FOR (cs:CommunicationStyle) REQUIRE cs.id IS UNIQUE
            """,
            """
            CREATE CONSTRAINT relationship_dynamic_id IF NOT EXISTS 
            FOR (rd:RelationshipDynamic) REQUIRE rd.id IS UNIQUE
            """,
            """
            CREATE CONSTRAINT llm_analysis_id IF NOT EXISTS 
            FOR (la:LLMAnalysis) REQUIRE la.id IS UNIQUE
            """,
            
            # Enhanced indexes
            """
            CREATE INDEX personality_big_five_lookup IF NOT EXISTS 
            FOR (pp:PersonalityProfile) ON (pp.openness, pp.conscientiousness, pp.extraversion, pp.agreeableness, pp.neuroticism)
            """,
            """
            CREATE INDEX llm_model_lookup IF NOT EXISTS 
            FOR (la:LLMAnalysis) ON (la.model, la.analysisDate)
            """,
            """
            CREATE INDEX profile_llm_enhanced_lookup IF NOT EXISTS 
            FOR (cp:CommunicationProfile) ON (cp.llmEnhanced, cp.lastLLMAnalysis)
            """,
            
            # System metadata
            """
            MERGE (sys:LLMSystem {id: 'avatar_llm_intelligence_v1'})
            SET sys.version = '1.0',
                sys.supportedModels = ['claude-3-sonnet', 'claude-3-opus', 'claude-3-haiku'],
                sys.deploymentDate = datetime(),
                sys.status = 'active',
                sys.description = 'LLM-Enhanced Avatar Intelligence System'
            """
        ]
        
        with self.driver.session() as session:
            for query in schema_queries:
                try:
                    session.run(query)
                    logger.info("✓ Executed schema query successfully")
                except Exception as e:
                    logger.error(f"✗ Schema query failed: {e}")
                    logger.error(f"Query: {query.strip()}")
        
        logger.info("Enhanced schema deployment completed")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        logger.info("Checking system status...")
        
        status = {
            "timestamp": datetime.now().isoformat(),
            "database_connection": False,
            "llm_integration": False,
            "profiles": {},
            "costs": {},
            "errors": []
        }
        
        try:
            # Test database connection
            with self.driver.session() as session:
                result = session.run("MATCH (n) RETURN count(n) as total").single()
                status["database_connection"] = True
                status["total_nodes"] = result["total"]
                
                # Get profile statistics
                profile_stats = session.run("""
                MATCH (cp:CommunicationProfile)
                RETURN cp.status as status, 
                       cp.llmEnhanced as llmEnhanced,
                       count(*) as count
                """).data()
                
                status["profiles"] = {
                    "total": sum(record["count"] for record in profile_stats),
                    "by_status": {record["status"]: record["count"] for record in profile_stats},
                    "llm_enhanced": sum(record["count"] for record in profile_stats if record.get("llmEnhanced"))
                }
                
                # Get LLM analysis statistics
                llm_stats = session.run("""
                MATCH (la:LLMAnalysis)
                WHERE datetime(la.analysisDate) > datetime() - duration('P30D')
                RETURN la.model as model,
                       count(*) as analysisCount,
                       sum(la.tokensUsed) as totalTokens,
                       sum(la.cost) as totalCost,
                       avg(la.confidenceScore) as avgConfidence
                ORDER BY totalCost DESC
                """).data()
                
                status["llm_analyses"] = llm_stats
                
        except Exception as e:
            status["errors"].append(f"Database error: {str(e)}")
            logger.error(f"Database status check failed: {e}")
        
        try:
            # Test LLM integration
            if self.config.system.enable_llm_analysis and self.config.anthropic.api_key:
                status["llm_integration"] = True
                status["llm_model"] = self.config.anthropic.model
                
                # Get cost information
                status["costs"] = {
                    "today": self.cost_monitor.get_today_cost(),
                    "daily_limit": self.config.anthropic.daily_cost_limit,
                    "remaining_budget": self.config.anthropic.daily_cost_limit - self.cost_monitor.get_today_cost()
                }
        except Exception as e:
            status["errors"].append(f"LLM integration error: {str(e)}")
            logger.error(f"LLM status check failed: {e}")
        
        # Get system statistics from avatar system
        try:
            system_stats = self.avatar_system.get_system_statistics()
            status["system_statistics"] = system_stats
        except Exception as e:
            status["errors"].append(f"System statistics error: {str(e)}")
        
        return status
    
    def list_people_for_analysis(self, min_messages: int = 50) -> List[Dict[str, Any]]:
        """List people available for analysis"""
        logger.info("Finding people for analysis...")
        
        with self.driver.session() as session:
            # Get people with sufficient message counts
            query = """
            MATCH (p:Person)-[:SENT]->(m:Message)
            WITH p, count(m) as messageCount
            WHERE messageCount >= $min_messages
            OPTIONAL MATCH (p)-[:HAS_COMMUNICATION_PROFILE]->(cp:CommunicationProfile)
            RETURN p.id as person_id,
                   p.name as person_name,
                   messageCount,
                   cp.llmEnhanced as has_llm_analysis,
                   cp.lastLLMAnalysis as last_analysis_date
            ORDER BY messageCount DESC
            """
            
            results = session.run(query, min_messages=min_messages).data()
            
            people = []
            for record in results:
                person = {
                    "person_id": record["person_id"],
                    "person_name": record["person_name"],
                    "message_count": record["messageCount"],
                    "has_llm_analysis": bool(record.get("has_llm_analysis")),
                    "last_analysis_date": record.get("last_analysis_date"),
                    "needs_analysis": not bool(record.get("has_llm_analysis"))
                }
                people.append(person)
            
            logger.info(f"Found {len(people)} people with >= {min_messages} messages")
            return people
    
    async def analyze_person(self, person_identifier: str, 
                           force_reanalysis: bool = False) -> Dict[str, Any]:
        """
        Analyze a specific person with LLM
        
        Args:
            person_identifier: Person name or ID
            force_reanalysis: Force analysis even if already done
            
        Returns:
            Analysis results
        """
        logger.info(f"Starting analysis for {person_identifier}")
        
        # Check cost limits
        if not self.cost_monitor.can_afford_analysis():
            return {
                "status": "cost_limit_exceeded",
                "message": f"Daily cost limit would be exceeded. Current: ${self.cost_monitor.get_today_cost():.2f}",
                "person_identifier": person_identifier
            }
        
        try:
            # Check if already analyzed and not forcing
            if not force_reanalysis:
                with self.driver.session() as session:
                    existing = session.run("""
                    MATCH (p:Person)-[:HAS_COMMUNICATION_PROFILE]->(cp:CommunicationProfile)
                    WHERE toLower(p.name) CONTAINS toLower($identifier) OR p.id = $identifier
                    RETURN cp.llmEnhanced as has_analysis
                    """, identifier=person_identifier).single()
                    
                    if existing and existing["has_analysis"]:
                        logger.info(f"{person_identifier} already analyzed. Use --force to reanalyze.")
                        return {
                            "status": "already_analyzed",
                            "message": "Person already has LLM analysis. Use force_reanalysis=True to override.",
                            "person_identifier": person_identifier
                        }
            
            # Perform analysis
            result = await self.avatar_system.create_enhanced_profile(
                person_identifier=person_identifier,
                min_messages=self.config.analysis.min_messages_for_analysis
            )
            
            # Record cost
            if result.get("total_cost", 0) > 0:
                self.cost_monitor.record_cost(result["total_cost"])
            
            logger.info(f"Analysis completed for {person_identifier}")
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed for {person_identifier}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "person_identifier": person_identifier
            }
    
    async def analyze_all_people(self, min_messages: int = None, 
                               max_people: int = 10,
                               force_reanalysis: bool = False) -> List[Dict[str, Any]]:
        """
        Analyze all people with sufficient data
        
        Args:
            min_messages: Minimum messages required (from config if None)
            max_people: Maximum people to analyze in one batch
            force_reanalysis: Force reanalysis of existing profiles
            
        Returns:
            List of analysis results
        """
        if min_messages is None:
            min_messages = self.config.analysis.min_messages_for_analysis
        
        logger.info(f"Starting batch analysis for up to {max_people} people")
        
        # Get people for analysis
        people = self.list_people_for_analysis(min_messages)
        
        if not force_reanalysis:
            # Filter to only those needing analysis
            people = [p for p in people if p["needs_analysis"]]
        
        if not people:
            logger.info("No people need analysis")
            return []
        
        # Limit to max_people
        people_to_analyze = people[:max_people]
        logger.info(f"Analyzing {len(people_to_analyze)} people")
        
        # Check total estimated cost
        estimated_total_cost = len(people_to_analyze) * 3.0  # Rough estimate
        current_cost = self.cost_monitor.get_today_cost()
        
        if current_cost + estimated_total_cost > self.config.anthropic.daily_cost_limit:
            logger.warning(f"Estimated cost ${estimated_total_cost:.2f} would exceed daily limit")
            # Reduce batch size
            affordable_count = int((self.config.anthropic.daily_cost_limit - current_cost) / 3.0)
            people_to_analyze = people_to_analyze[:max(1, affordable_count)]
            logger.info(f"Reduced batch to {len(people_to_analyze)} people due to cost limits")
        
        # Run batch analysis
        person_identifiers = [p["person_name"] for p in people_to_analyze]
        results = await self.avatar_system.batch_create_profiles(
            person_identifiers=person_identifiers,
            min_messages=min_messages,
            max_concurrent=self.config.anthropic.max_concurrent_requests
        )
        
        # Record costs
        total_cost = sum(r.get("total_cost", 0) for r in results)
        if total_cost > 0:
            self.cost_monitor.record_cost(total_cost)
        
        logger.info(f"Batch analysis completed. Total cost: ${total_cost:.4f}")
        return results
    
    def cleanup_old_analyses(self, days_old: int = 30):
        """Clean up old LLM analysis records"""
        logger.info(f"Cleaning up LLM analyses older than {days_old} days")
        
        with self.driver.session() as session:
            result = session.run("""
            MATCH (la:LLMAnalysis)
            WHERE datetime(la.analysisDate) < datetime() - duration('P' + $days + 'D')
              AND la.confidenceScore < 0.5
            SET la.status = 'archived'
            RETURN count(la) as archived
            """, days=str(days_old)).single()
            
            archived_count = result["archived"] if result else 0
            logger.info(f"Archived {archived_count} old analysis records")
    
    def export_profiles(self, output_file: str = None) -> str:
        """Export enhanced profiles to JSON"""
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"avatar_profiles_export_{timestamp}.json"
        
        logger.info(f"Exporting profiles to {output_file}")
        
        with self.driver.session() as session:
            query = """
            MATCH (p:Person)-[:HAS_COMMUNICATION_PROFILE]->(cp:CommunicationProfile)
            OPTIONAL MATCH (p)-[:HAS_PERSONALITY_PROFILE]->(pp:PersonalityProfile)
            OPTIONAL MATCH (p)-[:HAS_RELATIONSHIP_DYNAMIC]->(rd:RelationshipDynamic)
            RETURN p.id as person_id,
                   p.name as person_name,
                   cp,
                   collect(DISTINCT pp) as personality_profiles,
                   collect(DISTINCT rd) as relationship_dynamics
            ORDER BY cp.messageCount DESC
            """
            
            results = session.run(query).data()
            
            # Convert to serializable format
            export_data = []
            for record in results:
                person_data = {
                    "person_id": record["person_id"],
                    "person_name": record["person_name"],
                    "communication_profile": dict(record["cp"]) if record["cp"] else None,
                    "personality_profiles": [dict(pp) for pp in record["personality_profiles"] if pp],
                    "relationship_dynamics": [dict(rd) for rd in record["relationship_dynamics"] if rd]
                }
                export_data.append(person_data)
        
        # Save to file
        import json
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        logger.info(f"Exported {len(export_data)} profiles to {output_file}")
        return output_file
    
    def close(self):
        """Clean up resources"""
        if hasattr(self, 'driver'):
            self.driver.close()
            logger.info("Database connection closed")


async def main():
    """Main deployment script"""
    parser = argparse.ArgumentParser(description="Enhanced Avatar Intelligence System Deployment")
    
    parser.add_argument("--deploy", action="store_true", help="Deploy enhanced schema")
    parser.add_argument("--status", action="store_true", help="Show system status")
    parser.add_argument("--analyze-all", action="store_true", help="Analyze all people")
    parser.add_argument("--analyze-person", type=str, help="Analyze specific person")
    parser.add_argument("--list-people", action="store_true", help="List people available for analysis")
    parser.add_argument("--costs", action="store_true", help="Show cost summary")
    parser.add_argument("--export", action="store_true", help="Export profiles to JSON")
    parser.add_argument("--cleanup", type=int, help="Clean up old analyses (days)")
    parser.add_argument("--force", action="store_true", help="Force reanalysis of existing profiles")
    parser.add_argument("--max-people", type=int, default=5, help="Maximum people to analyze (default: 5)")
    parser.add_argument("--config", type=str, help="Configuration file path")
    
    args = parser.parse_args()
    
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    # Initialize configuration
    try:
        config = ConfigManager(args.config)
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print("Run 'python src/config_manager.py' to set up configuration")
        return
    
    # Initialize deployment manager
    try:
        deployment = EnhancedSystemDeployment(config)
    except Exception as e:
        print(f"❌ Failed to initialize system: {e}")
        return
    
    try:
        # Execute commands
        if args.deploy:
            print("🚀 Deploying enhanced schema...")
            deployment.deploy_enhanced_schema()
            print("✅ Schema deployment completed")
        
        if args.status:
            print("📊 System Status Check")
            print("=" * 50)
            status = deployment.get_system_status()
            
            print(f"Database Connection: {'✅' if status['database_connection'] else '❌'}")
            print(f"LLM Integration: {'✅' if status['llm_integration'] else '❌'}")
            
            if status.get('profiles'):
                profiles = status['profiles']
                print(f"\nProfiles:")
                print(f"  Total: {profiles['total']}")
                print(f"  LLM Enhanced: {profiles['llm_enhanced']}")
                print(f"  By Status: {profiles['by_status']}")
            
            if status.get('costs'):
                costs = status['costs']
                print(f"\nCosts:")
                print(f"  Today: ${costs['today']:.2f}")
                print(f"  Daily Limit: ${costs['daily_limit']:.2f}")
                print(f"  Remaining: ${costs['remaining_budget']:.2f}")
            
            if status.get('errors'):
                print(f"\n⚠️ Errors:")
                for error in status['errors']:
                    print(f"  - {error}")
        
        if args.list_people:
            print("👥 People Available for Analysis")
            print("=" * 50)
            people = deployment.list_people_for_analysis()
            
            for person in people[:20]:  # Show top 20
                status_icon = "✅" if person["has_llm_analysis"] else "⏳"
                print(f"{status_icon} {person['person_name']:<25} {person['message_count']:>6} messages")
            
            if len(people) > 20:
                print(f"... and {len(people) - 20} more")
            
            need_analysis = sum(1 for p in people if p["needs_analysis"])
            print(f"\nSummary: {need_analysis} people need analysis")
        
        if args.analyze_person:
            print(f"🧠 Analyzing {args.analyze_person}...")
            result = await deployment.analyze_person(args.analyze_person, args.force)
            
            if result["status"] == "success":
                print(f"✅ Analysis completed!")
                print(f"   Messages analyzed: {result['message_count']}")
                print(f"   Cost: ${result['total_cost']:.4f}")
                print(f"   Analysis types: {len(result['analysis_results'])}")
            elif result["status"] == "already_analyzed":
                print(f"ℹ️ {result['message']}")
            else:
                print(f"❌ Analysis failed: {result.get('message', result.get('error', 'Unknown error'))}")
        
        if args.analyze_all:
            print(f"🧠 Analyzing up to {args.max_people} people...")
            results = await deployment.analyze_all_people(
                max_people=args.max_people,
                force_reanalysis=args.force
            )
            
            successful = sum(1 for r in results if r.get("status") == "success")
            total_cost = sum(r.get("total_cost", 0) for r in results)
            
            print(f"✅ Batch analysis completed!")
            print(f"   Successful: {successful}/{len(results)}")
            print(f"   Total cost: ${total_cost:.4f}")
        
        if args.costs:
            print("💰 Cost Summary")
            print("=" * 50)
            cost_monitor = CostMonitor(config)
            
            today_cost = cost_monitor.get_today_cost()
            daily_limit = config.anthropic.daily_cost_limit
            
            print(f"Today's cost: ${today_cost:.2f}")
            print(f"Daily limit: ${daily_limit:.2f}")
            print(f"Remaining budget: ${daily_limit - today_cost:.2f}")
            
            if today_cost > daily_limit * 0.8:
                print("⚠️ Warning: Approaching daily cost limit!")
        
        if args.export:
            print("📤 Exporting profiles...")
            output_file = deployment.export_profiles()
            print(f"✅ Profiles exported to {output_file}")
        
        if args.cleanup:
            print(f"🧹 Cleaning up analyses older than {args.cleanup} days...")
            deployment.cleanup_old_analyses(args.cleanup)
            print("✅ Cleanup completed")
    
    except KeyboardInterrupt:
        print("\n🛑 Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.exception("Deployment error")
    finally:
        deployment.close()


if __name__ == "__main__":
    asyncio.run(main())
