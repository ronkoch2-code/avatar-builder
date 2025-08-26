#!/usr/bin/env python3
"""
Enhanced Avatar Intelligence Pipeline with LLM Integration
=========================================================

This module extends the original Avatar Intelligence System with deep LLM-powered analysis
for comprehensive personality profiling, relationship understanding, and conversation insights.

Key Enhancements:
- Claude-powered personality analysis
- Deep relationship dynamics understanding
- Semantic conversation clustering
- Advanced emotional intelligence profiling
- Context-aware avatar response generation
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from collections import Counter, defaultdict
import uuid

import pandas as pd
from neo4j import GraphDatabase

from llm_integrator import (
    LLMIntegrator, AnalysisRequest, AnalysisResult, AnalysisType,
    PersonalityProfile, RelationshipDynamic, CommunicationStyle
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EnhancedAvatarSystemManager:
    """
    Enhanced Avatar System Manager with LLM integration
    
    Extends the original system with deep personality analysis,
    relationship understanding, and intelligent avatar generation.
    """
    
    def __init__(self, 
                 neo4j_driver,
                 anthropic_api_key: Optional[str] = None,
                 claude_model: str = "claude-3-sonnet-20240229",
                 enable_llm_analysis: bool = True):
        """
        Initialize Enhanced Avatar System
        
        Args:
            neo4j_driver: Neo4j database driver
            anthropic_api_key: Anthropic API key for Claude
            claude_model: Claude model to use
            enable_llm_analysis: Whether to enable LLM analysis
        """
        self.driver = neo4j_driver
        self.enable_llm_analysis = enable_llm_analysis
        
        if self.enable_llm_analysis and anthropic_api_key:
            self.llm_integrator = LLMIntegrator(
                api_key=anthropic_api_key,
                model=claude_model,
                max_concurrent=3,  # Conservative to manage costs
                rate_limit_per_minute=50
            )
            logger.info(f"LLM integration enabled with model: {claude_model}")
        else:
            self.llm_integrator = None
            if enable_llm_analysis:
                logger.warning("LLM analysis requested but API key not provided - disabled")
            else:
                logger.info("LLM integration disabled")
        
        # System statistics
        self.stats = {
            "profiles_created": 0,
            "llm_analyses_completed": 0,
            "total_cost": 0.0,
            "last_analysis_date": None
        }
    
    def get_conversation_data(self, person_identifier: str, identifier_type: str = "name", 
                            max_messages: int = 1000) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Retrieve conversation data for a person from Neo4j
        
        Args:
            person_identifier: Person name, ID, or phone number
            identifier_type: Type of identifier ('name', 'id', 'phone')
            max_messages: Maximum messages to retrieve
            
        Returns:
            Tuple of (person_id, conversation_messages)
        """
        with self.driver.session() as session:
            # Get person information
            if identifier_type == "name":
                person_query = """
                MATCH (p:Person) 
                WHERE toLower(p.name) CONTAINS toLower($identifier)
                RETURN p.id as person_id, p.name as person_name
                LIMIT 1
                """
            elif identifier_type == "id":
                person_query = """
                MATCH (p:Person {id: $identifier})
                RETURN p.id as person_id, p.name as person_name
                """
            else:  # phone
                person_query = """
                MATCH (p:Person {phone: $identifier})
                RETURN p.id as person_id, p.name as person_name
                """
            
            person_result = session.run(person_query, identifier=person_identifier).single()
            if not person_result:
                raise ValueError(f"Person not found: {person_identifier}")
            
            person_id = person_result["person_id"]
            person_name = person_result["person_name"]
            
            # Get conversation messages - improved query to capture conversation partners
            messages_query = f"""
            MATCH (p:Person {{id: $person_id}})-[:SENT]->(m:Message)
            OPTIONAL MATCH (m)-[:SENT_TO]->(gc:GroupChat)
            OPTIONAL MATCH (gc)<-[:MEMBER_OF]-(partner:Person)
            WHERE partner.id <> $person_id
            WITH m, gc, collect(DISTINCT partner.name) as partners
            RETURN m.id as message_id,
                   m.body as body,
                   m.date as date,
                   m.isFromMe as isFromMe,
                   m.groupChat as group_chat_id,
                   gc.name as group_chat_name,
                   partners
            ORDER BY m.date DESC
            LIMIT {max_messages}
            """
            
            messages_result = session.run(messages_query, person_id=person_id)
            messages = []
            
            for record in messages_result:
                # Extract conversation partner info
                partners = record["partners"] or []
                group_chat_name = record["group_chat_name"] or record["group_chat_id"]
                
                # Determine conversation partner
                if len(partners) == 1:
                    partner_name = partners[0]
                elif len(partners) > 1:
                    partner_name = group_chat_name or "Group"
                else:
                    partner_name = "Unknown"
                
                message_data = {
                    "id": record["message_id"],
                    "body": record["body"],
                    "date": record["date"],
                    "isFromMe": record["isFromMe"],
                    "group_chat_id": record["group_chat_id"],
                    "group_chat_name": group_chat_name,
                    "partners": partners,
                    "partner_name": partner_name
                }
                messages.append(message_data)
            
            logger.info(f"Retrieved {len(messages)} messages for {person_name}")
            return person_id, messages
    
    async def create_enhanced_profile(self, person_identifier: str, 
                                    identifier_type: str = "name",
                                    min_messages: int = 50) -> Dict[str, Any]:
        """
        Create comprehensive personality profile with LLM analysis
        
        Args:
            person_identifier: Person identifier
            identifier_type: Type of identifier
            min_messages: Minimum messages required for analysis
            
        Returns:
            Dictionary with profile creation results
        """
        try:
            # Get conversation data
            person_id, messages = self.get_conversation_data(
                person_identifier, identifier_type, max_messages=1000
            )
            
            if len(messages) < min_messages:
                logger.warning(f"Insufficient messages ({len(messages)}) for {person_identifier}")
                return {
                    "status": "insufficient_data",
                    "message_count": len(messages),
                    "required": min_messages,
                    "person_identifier": person_identifier
                }
            
            # Get person name for analysis
            person_name = self._get_person_name(person_id)
            
            results = {
                "person_id": person_id,
                "person_name": person_name,
                "message_count": len(messages),
                "analysis_results": [],
                "total_cost": 0.0
            }
            
            if self.enable_llm_analysis and self.llm_integrator:
                # Create analysis requests
                requests = []
                
                # Personality analysis
                requests.append(AnalysisRequest(
                    person_id=person_id,
                    person_name=person_name,
                    analysis_type=AnalysisType.PERSONALITY_PROFILE,
                    conversation_data=messages,
                    max_messages=500
                ))
                
                # Relationship dynamics analysis
                requests.append(AnalysisRequest(
                    person_id=person_id,
                    person_name=person_name,
                    analysis_type=AnalysisType.RELATIONSHIP_DYNAMICS,
                    conversation_data=messages,
                    max_messages=800
                ))
                
                # Run LLM analysis
                logger.info(f"Starting LLM analysis for {person_name}")
                analysis_results = await self.llm_integrator.batch_analyze(requests)
                
                # Store results in Neo4j
                for analysis_result in analysis_results:
                    await self._store_llm_analysis(analysis_result)
                    results["analysis_results"].append({
                        "type": analysis_result.analysis_type.value,
                        "cost": analysis_result.cost,
                        "tokens": analysis_result.tokens_used,
                        "confidence": getattr(analysis_result.result, 'confidence_score', 0.0)
                    })
                    results["total_cost"] += analysis_result.cost
                
                # Update system statistics
                self.stats["llm_analyses_completed"] += len(analysis_results)
                self.stats["total_cost"] += results["total_cost"]
                self.stats["last_analysis_date"] = datetime.now().isoformat()
                
                logger.info(f"Completed LLM analysis for {person_name}. Cost: ${results['total_cost']:.4f}")
            else:
                logger.info(f"LLM analysis disabled, creating basic profile for {person_name}")
            
            # Create or update communication profile
            profile_id = await self._create_enhanced_communication_profile(person_id, person_name, messages, results)
            results["profile_id"] = profile_id
            
            self.stats["profiles_created"] += 1
            results["status"] = "success"
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to create enhanced profile for {person_identifier}: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "person_identifier": person_identifier
            }
    
    def _get_person_name(self, person_id: str) -> str:
        """Get person name from ID"""
        with self.driver.session() as session:
            result = session.run("MATCH (p:Person {id: $person_id}) RETURN p.name", person_id=person_id).single()
            return result["p.name"] if result else "Unknown"
    
    async def _store_llm_analysis(self, analysis_result: AnalysisResult):
        """Store LLM analysis results in Neo4j"""
        with self.driver.session() as session:
            # Store LLM analysis record
            session.run("""
            CREATE (la:LLMAnalysis {
                id: $analysis_id,
                personId: $person_id,
                analysisType: $analysis_type,
                model: $model,
                tokensUsed: $tokens_used,
                cost: $cost,
                processingTime: $processing_time,
                confidenceScore: $confidence_score,
                analysisDate: datetime($timestamp),
                version: '1.0'
            })
            """, {
                "analysis_id": analysis_result.request_id,
                "person_id": analysis_result.person_id,
                "analysis_type": analysis_result.analysis_type.value,
                "model": analysis_result.metadata.get("model", "unknown"),
                "tokens_used": analysis_result.tokens_used,
                "cost": analysis_result.cost,
                "processing_time": analysis_result.processing_time,
                "confidence_score": getattr(analysis_result.result, 'confidence_score', 0.0),
                "timestamp": analysis_result.timestamp.isoformat()
            })
            
            # Store specific analysis results based on type
            if analysis_result.analysis_type == AnalysisType.PERSONALITY_PROFILE:
                await self._store_personality_profile(session, analysis_result)
            elif analysis_result.analysis_type == AnalysisType.RELATIONSHIP_DYNAMICS:
                await self._store_relationship_dynamics(session, analysis_result)
    
    async def _store_personality_profile(self, session, analysis_result: AnalysisResult):
        """Store personality profile in Neo4j"""
        profile = analysis_result.result
        profile_id = str(uuid.uuid4())
        
        # Create personality profile node
        session.run("""
        MATCH (p:Person {id: $person_id})
        CREATE (p)-[:HAS_PERSONALITY_PROFILE]->(pp:PersonalityProfile {
            id: $profile_id,
            openness: $openness,
            conscientiousness: $conscientiousness,
            extraversion: $extraversion,
            agreeableness: $agreeableness,
            neuroticism: $neuroticism,
            personalityInsights: $insights,
            communicationPreferences: $comm_prefs,
            behavioralPatterns: $behavioral_patterns,
            confidenceScore: $confidence_score,
            llmGenerated: true,
            analysisDate: datetime(),
            analysisId: $analysis_id
        })
        """, {
            "person_id": analysis_result.person_id,
            "profile_id": profile_id,
            "openness": profile.big_five_scores.get("openness", 0.5),
            "conscientiousness": profile.big_five_scores.get("conscientiousness", 0.5),
            "extraversion": profile.big_five_scores.get("extraversion", 0.5),
            "agreeableness": profile.big_five_scores.get("agreeableness", 0.5),
            "neuroticism": profile.big_five_scores.get("neuroticism", 0.5),
            "insights": profile.personality_insights,
            "comm_prefs": json.dumps(profile.communication_preferences),
            "behavioral_patterns": profile.behavioral_patterns,
            "confidence_score": profile.confidence_score,
            "analysis_id": analysis_result.request_id
        })
        
        logger.info(f"Stored personality profile for {analysis_result.person_id}")
    
    async def _store_relationship_dynamics(self, session, analysis_result: AnalysisResult):
        """Store relationship dynamics in Neo4j"""
        if isinstance(analysis_result.result, list):
            relationships = analysis_result.result
        else:
            relationships = [analysis_result.result]
        
        for relationship in relationships:
            relationship_id = str(uuid.uuid4())
            
            # Find or create partner
            partner_result = session.run("""
            MATCH (p:Person) 
            WHERE toLower(p.name) = toLower($partner_name)
            RETURN p.id as partner_id
            LIMIT 1
            """, partner_name=relationship.partner_name).single()
            
            partner_id = partner_result["partner_id"] if partner_result else f"unknown_{relationship.partner_name}"
            
            # Create relationship dynamic node
            session.run("""
            MATCH (p:Person {id: $person_id})
            CREATE (p)-[:HAS_RELATIONSHIP_DYNAMIC]->(rd:RelationshipDynamic {
                id: $relationship_id,
                partnerId: $partner_id,
                partnerName: $partner_name,
                relationshipType: $relationship_type,
                intimacyLevel: $intimacy_level,
                communicationPattern: $communication_pattern,
                emotionalDynamics: $emotional_dynamics,
                keyTopics: $key_topics,
                confidenceScore: $confidence_score,
                llmGenerated: true,
                analysisDate: datetime(),
                analysisId: $analysis_id
            })
            """, {
                "person_id": analysis_result.person_id,
                "relationship_id": relationship_id,
                "partner_id": partner_id,
                "partner_name": relationship.partner_name,
                "relationship_type": relationship.relationship_type,
                "intimacy_level": relationship.intimacy_level,
                "communication_pattern": relationship.communication_pattern,
                "emotional_dynamics": json.dumps(relationship.emotional_dynamics),
                "key_topics": relationship.key_topics,
                "confidence_score": relationship.confidence_score,
                "analysis_id": analysis_result.request_id
            })
        
        logger.info(f"Stored {len(relationships)} relationship dynamics for {analysis_result.person_id}")
    
    async def _create_enhanced_communication_profile(self, person_id: str, person_name: str, 
                                                   messages: List[Dict], analysis_results: Dict) -> str:
        """Create enhanced communication profile with LLM insights"""
        profile_id = str(uuid.uuid4())
        
        # Calculate basic metrics
        total_messages = len(messages)
        avg_message_length = sum(len(msg.get("body", "")) for msg in messages if msg.get("body")) / max(1, total_messages)
        
        # Determine status
        status = "active" if total_messages >= 100 else "limited_data"
        
        with self.driver.session() as session:
            # Create or update communication profile
            session.run("""
            MATCH (p:Person {id: $person_id})
            MERGE (p)-[:HAS_COMMUNICATION_PROFILE]->(cp:CommunicationProfile {personId: $person_id})
            SET cp.id = $profile_id,
                cp.personName = $person_name,
                cp.messageCount = $message_count,
                cp.avgMessageLength = $avg_message_length,
                cp.status = $status,
                cp.llmEnhanced = $llm_enhanced,
                cp.lastLLMAnalysis = $last_analysis,
                cp.analysisVersion = '2.0',
                cp.totalCost = $total_cost,
                cp.lastAnalysis = datetime()
            """, {
                "person_id": person_id,
                "profile_id": profile_id,
                "person_name": person_name,
                "message_count": total_messages,
                "avg_message_length": avg_message_length,
                "status": status,
                "llm_enhanced": self.enable_llm_analysis and self.llm_integrator is not None,
                "last_analysis": datetime.now().isoformat() if self.enable_llm_analysis else None,
                "total_cost": analysis_results.get("total_cost", 0.0)
            })
        
        return profile_id
    
    async def generate_enhanced_avatar_prompt(self, person_identifier: str,
                                           conversation_type: str = "1:1",
                                           partners: Optional[List[str]] = None,
                                           topic: Optional[str] = None,
                                           context: Optional[str] = None) -> str:
        """
        Generate enhanced avatar prompt using LLM-powered insights
        
        Args:
            person_identifier: Person to generate avatar for
            conversation_type: Type of conversation ("1:1", "group", "professional")
            partners: Names of conversation partners
            topic: Specific topic or context
            context: Additional context for the conversation
            
        Returns:
            Enhanced avatar prompt string
        """
        try:
            # Get person data and LLM insights
            person_data = await self._get_enhanced_person_data(person_identifier)
            
            if not person_data:
                return "Unable to generate avatar prompt: person not found or insufficient data"
            
            # Build context-aware prompt
            prompt_parts = []
            
            # Base personality context
            prompt_parts.append(f"You are role-playing as {person_data['name']}.")
            
            # Add personality insights if available
            if person_data.get("personality_profile"):
                pp = person_data["personality_profile"]
                if pp.get('personality_insights'):
                    prompt_parts.append(f"Personality: {' '.join(pp.get('personality_insights', []))}")
                
                # Add Big Five context
                big_five = pp.get('big_five_scores', {})
                personality_desc = []
                if big_five.get('extraversion', 0.5) > 0.6:
                    personality_desc.append("outgoing and social")
                elif big_five.get('extraversion', 0.5) < 0.4:
                    personality_desc.append("more reserved and introspective")
                
                if big_five.get('agreeableness', 0.5) > 0.6:
                    personality_desc.append("cooperative and considerate")
                
                if big_five.get('openness', 0.5) > 0.6:
                    personality_desc.append("curious and open to new experiences")
                
                if personality_desc:
                    prompt_parts.append(f"You are {', '.join(personality_desc)}.")
            
            # Add relationship context
            if partners and person_data.get("relationships"):
                for partner in partners:
                    rel = person_data["relationships"].get(partner.lower())
                    if rel:
                        prompt_parts.append(
                            f"Your relationship with {partner} is {rel.get('relationship_type', 'friendly')}. "
                            f"Communication pattern: {rel.get('communication_pattern', 'casual and friendly')}."
                        )
            
            # Add communication style
            if person_data.get("communication_style"):
                cs = person_data["communication_style"]
                formality = cs.get('formality_level', 0.5)
                directness = cs.get('directness_score', 0.5)
                
                style_desc = []
                if formality > 0.6:
                    style_desc.append("formal and professional")
                elif formality < 0.4:
                    style_desc.append("casual and relaxed")
                
                if directness > 0.6:
                    style_desc.append("direct and straightforward")
                elif directness < 0.4:
                    style_desc.append("gentle and diplomatic")
                
                if style_desc:
                    prompt_parts.append(f"Communication style: {', '.join(style_desc)}.")
            
            # Add topic-specific context
            if topic and person_data.get("topic_interests"):
                if topic.lower() in person_data["topic_interests"]:
                    topic_data = person_data["topic_interests"][topic.lower()]
                    expertise = topic_data.get("expertise_level", 0.5)
                    if expertise > 0.6:
                        prompt_parts.append(f"You have significant knowledge and interest in {topic}.")
                    elif expertise > 0.3:
                        prompt_parts.append(f"You have some familiarity with {topic}.")
            
            # Add conversation type context
            if conversation_type == "professional":
                prompt_parts.append("Maintain a professional tone appropriate for work settings.")
            elif conversation_type == "group":
                prompt_parts.append("Engage naturally in group conversation dynamics.")
            
            # Add signature phrases or expressions
            if person_data.get("signature_phrases"):
                common_phrases = person_data["signature_phrases"][:3]  # Top 3 phrases
                if common_phrases:
                    prompt_parts.append(
                        f"You sometimes use expressions like: {', '.join([f'\"{phrase}\"' for phrase in common_phrases])}"
                    )
            
            # Additional context
            if context:
                prompt_parts.append(f"Context: {context}")
            
            # Final instructions
            prompt_parts.append(
                "Respond naturally as this person would, maintaining their personality, "
                "communication style, and relationship dynamics. Keep responses conversational and authentic."
            )
            
            return " ".join(prompt_parts)
            
        except Exception as e:
            logger.error(f"Failed to generate enhanced avatar prompt: {str(e)}")
            return f"Error generating avatar prompt: {str(e)}"
    
    async def _get_enhanced_person_data(self, person_identifier: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive person data including LLM insights"""
        with self.driver.session() as session:
            # Get person and basic data
            person_result = session.run("""
            MATCH (p:Person) 
            WHERE toLower(p.name) CONTAINS toLower($identifier) OR p.id = $identifier
            OPTIONAL MATCH (p)-[:HAS_PERSONALITY_PROFILE]->(pp:PersonalityProfile)
            OPTIONAL MATCH (p)-[:HAS_COMMUNICATION_STYLE]->(cs:CommunicationStyle)
            OPTIONAL MATCH (p)-[:HAS_RELATIONSHIP_DYNAMIC]->(rd:RelationshipDynamic)
            OPTIONAL MATCH (p)-[:USES_PHRASE]->(sp:SignaturePhrase)
            RETURN p.id as person_id, p.name as name,
                   pp, cs,
                   collect(DISTINCT rd) as relationships,
                   collect(DISTINCT sp.phrase) as signature_phrases
            LIMIT 1
            """, identifier=person_identifier).single()
            
            if not person_result:
                return None
            
            person_data = {
                "person_id": person_result["person_id"],
                "name": person_result["name"],
                "signature_phrases": [p for p in person_result["signature_phrases"] if p]
            }
            
            # Add personality profile if available
            if person_result["pp"]:
                pp = dict(person_result["pp"])
                person_data["personality_profile"] = {
                    "big_five_scores": {
                        "openness": pp.get("openness", 0.5),
                        "conscientiousness": pp.get("conscientiousness", 0.5),
                        "extraversion": pp.get("extraversion", 0.5),
                        "agreeableness": pp.get("agreeableness", 0.5),
                        "neuroticism": pp.get("neuroticism", 0.5)
                    },
                    "personality_insights": pp.get("personalityInsights", [])
                }
            
            # Add communication style if available
            if person_result["cs"]:
                cs = dict(person_result["cs"])
                person_data["communication_style"] = {
                    "formality_level": cs.get("formalityLevel", 0.5),
                    "directness_score": cs.get("directnessScore", 0.5)
                }
            
            # Add relationship dynamics
            if person_result["relationships"]:
                relationships = {}
                for rd in person_result["relationships"]:
                    if rd:
                        rd_dict = dict(rd)
                        partner_name = rd_dict.get("partnerName", "").lower()
                        relationships[partner_name] = {
                            "relationship_type": rd_dict.get("relationshipType"),
                            "communication_pattern": rd_dict.get("communicationPattern"),
                            "intimacy_level": rd_dict.get("intimacyLevel", 0.5)
                        }
                person_data["relationships"] = relationships
            
            return person_data
    
    async def batch_create_profiles(self, person_identifiers: List[str],
                                  min_messages: int = 50,
                                  max_concurrent: int = 2) -> List[Dict[str, Any]]:
        """
        Create enhanced profiles for multiple people concurrently
        
        Args:
            person_identifiers: List of person identifiers
            min_messages: Minimum messages required
            max_concurrent: Maximum concurrent analyses (to manage costs)
            
        Returns:
            List of profile creation results
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def create_profile_with_semaphore(identifier: str) -> Dict[str, Any]:
            async with semaphore:
                return await self.create_enhanced_profile(identifier, min_messages=min_messages)
        
        logger.info(f"Starting batch profile creation for {len(person_identifiers)} people")
        
        results = await asyncio.gather(
            *[create_profile_with_semaphore(identifier) for identifier in person_identifiers],
            return_exceptions=True
        )
        
        # Process results
        successful = 0
        failed = 0
        total_cost = 0.0
        
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Profile creation failed for {person_identifiers[i]}: {str(result)}")
                processed_results.append({
                    "person_identifier": person_identifiers[i],
                    "status": "error",
                    "error": str(result)
                })
                failed += 1
            else:
                if result.get("status") == "success":
                    successful += 1
                    total_cost += result.get("total_cost", 0.0)
                else:
                    failed += 1
                processed_results.append(result)
        
        logger.info(f"Batch processing completed: {successful} successful, {failed} failed. Total cost: ${total_cost:.4f}")
        
        return processed_results
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        stats = self.stats.copy()
        
        if self.enable_llm_analysis and self.llm_integrator:
            llm_stats = self.llm_integrator.get_cost_summary()
            stats.update({
                "llm_total_tokens": llm_stats["total_tokens"],
                "llm_total_cost": llm_stats["total_cost"],
                "llm_analyses_by_type": llm_stats["cost_by_type"]
            })
        
        # Add Neo4j statistics
        with self.driver.session() as session:
            # Count profiles by status
            profile_counts = session.run("""
            MATCH (cp:CommunicationProfile)
            RETURN cp.status as status, count(*) as count
            """).data()
            
            stats["profiles_by_status"] = {record["status"]: record["count"] for record in profile_counts}
            
            # Count LLM-enhanced profiles
            llm_enhanced = session.run("""
            MATCH (cp:CommunicationProfile {llmEnhanced: true})
            RETURN count(*) as count
            """).single()
            
            stats["llm_enhanced_profiles"] = llm_enhanced["count"] if llm_enhanced else 0
        
        return stats


# Usage example and testing
async def main():
    """Example usage of Enhanced Avatar System"""
    # Initialize Neo4j connection
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
    
    # Initialize enhanced system
    avatar_system = EnhancedAvatarSystemManager(
        neo4j_driver=driver,
        anthropic_api_key=None,  # Will use environment variable
        enable_llm_analysis=True
    )
    
    try:
        # Create enhanced profile for a person
        result = await avatar_system.create_enhanced_profile(
            person_identifier="Claire Russell",
            min_messages=100
        )
        
        print(f"Profile creation result: {result}")
        
        # Generate enhanced avatar prompt
        if result.get("status") == "success":
            prompt = await avatar_system.generate_enhanced_avatar_prompt(
                person_identifier="Claire Russell",
                conversation_type="1:1",
                partners=["Ron"],
                topic="health"
            )
            
            print(f"Generated prompt: {prompt}")
        
        # Get system statistics
        stats = avatar_system.get_system_statistics()
        print(f"System statistics: {stats}")
        
    finally:
        driver.close()


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())
