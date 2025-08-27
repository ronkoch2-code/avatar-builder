#!/usr/bin/env python3
"""
LLM Integration Module for Avatar Intelligence System
====================================================

This module provides comprehensive LLM-powered analysis for personality profiling,
relationship dynamics, communication patterns, and conversation insights.

Key Features:
- Claude API integration for deep personality analysis
- Async processing for batch analysis
- Cost monitoring and rate limiting
- Structured output with validation
- Conversation context understanding
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum

import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential
import pandas as pd
from pydantic import BaseModel, Field, ValidationError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AnalysisType(Enum):
    """Types of LLM analysis available"""
    PERSONALITY_PROFILE = "personality_profile"
    RELATIONSHIP_DYNAMICS = "relationship_dynamics"
    COMMUNICATION_STYLE = "communication_style"
    TOPIC_EXPERTISE = "topic_expertise"
    EMOTIONAL_PROFILE = "emotional_profile"
    CONVERSATION_SUMMARY = "conversation_summary"


class PersonalityProfile(BaseModel):
    """Structured personality profile from LLM analysis"""
    big_five_scores: Dict[str, float] = Field(description="Big Five personality scores (0-1)")
    personality_insights: List[str] = Field(description="Key personality insights")
    communication_preferences: Dict[str, Any] = Field(description="Preferred communication styles")
    behavioral_patterns: List[str] = Field(description="Observed behavioral patterns")
    confidence_score: float = Field(ge=0, le=1, description="Analysis confidence")
    

class RelationshipDynamic(BaseModel):
    """Relationship dynamics analysis"""
    partner_name: str = Field(description="Name of conversation partner")
    relationship_type: str = Field(description="Inferred relationship type")
    intimacy_level: float = Field(ge=0, le=1, description="Communication intimacy level")
    communication_pattern: str = Field(description="Communication pattern description")
    emotional_dynamics: Dict[str, Any] = Field(description="Emotional interaction patterns")
    key_topics: List[str] = Field(description="Main conversation topics")
    confidence_score: float = Field(ge=0, le=1, description="Analysis confidence")


class CommunicationStyle(BaseModel):
    """Communication style analysis"""
    formality_level: float = Field(ge=0, le=1, description="Formality score")
    directness_score: float = Field(ge=0, le=1, description="Communication directness")
    emotional_expressiveness: float = Field(ge=0, le=1, description="Emotional expression level")
    humor_usage: float = Field(ge=0, le=1, description="Frequency of humor usage")
    preferred_topics: List[str] = Field(description="Preferred conversation topics")
    communication_patterns: List[str] = Field(description="Observed communication patterns")
    confidence_score: float = Field(ge=0, le=1, description="Analysis confidence")


class TopicExpertise(BaseModel):
    """Topic expertise and interest analysis"""
    topic_category: str = Field(description="Main topic category")
    expertise_level: float = Field(ge=0, le=1, description="Demonstrated expertise level")
    engagement_level: float = Field(ge=0, le=1, description="Engagement with topic")
    key_insights: List[str] = Field(description="Key insights about their knowledge")
    related_topics: List[str] = Field(description="Related topics of interest")
    conversation_frequency: int = Field(description="Number of conversations on this topic")


class EmotionalProfile(BaseModel):
    """Emotional expression and patterns"""
    overall_valence: float = Field(ge=-1, le=1, description="Overall emotional valence")
    emotional_range: float = Field(ge=0, le=1, description="Range of emotional expression")
    emotional_triggers: List[str] = Field(description="Topics that trigger emotional responses")
    emotional_patterns: Dict[str, Any] = Field(description="Emotional expression patterns")
    stress_indicators: List[str] = Field(description="Signs of stress or anxiety")
    confidence_score: float = Field(ge=0, le=1, description="Analysis confidence")


@dataclass
class AnalysisRequest:
    """Request for LLM analysis"""
    person_id: str
    person_name: str
    analysis_type: AnalysisType
    conversation_data: List[Dict[str, Any]]
    context: Optional[Dict[str, Any]] = None
    max_messages: int = 500
    priority: int = 1  # 1 (high) to 5 (low)


@dataclass
class AnalysisResult:
    """Result from LLM analysis"""
    request_id: str
    person_id: str
    analysis_type: AnalysisType
    result: Union[PersonalityProfile, RelationshipDynamic, CommunicationStyle, TopicExpertise, EmotionalProfile]
    metadata: Dict[str, Any]
    tokens_used: int
    cost: float
    processing_time: float
    timestamp: datetime


class LLMIntegrator:
    """Main class for LLM integration with Avatar Intelligence System"""
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 model: str = "claude-3-sonnet-20240229",
                 max_concurrent: int = 5,
                 rate_limit_per_minute: int = 100):
        """
        Initialize LLM integrator
        
        Args:
            api_key: Anthropic API key (or from environment)
            model: Claude model to use
            max_concurrent: Maximum concurrent API calls
            rate_limit_per_minute: Rate limit for API calls
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key required. Set ANTHROPIC_API_KEY environment variable.")
            
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model
        self.max_concurrent = max_concurrent
        self.rate_limit_per_minute = rate_limit_per_minute
        
        # Cost tracking
        self.total_tokens = 0
        self.total_cost = 0.0
        self.analysis_history = []
        
        # Pricing (per 1K tokens) - update as needed
        self.pricing = {
            "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
            "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
            "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125}
        }
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _call_llm(self, system_prompt: str, user_prompt: str) -> Tuple[str, Dict[str, Any]]:
        """
        Make API call to Claude with retry logic
        
        Returns:
            Tuple of (response_text, metadata)
        """
        try:
            start_time = datetime.now()
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.1,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Calculate cost
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost = self._calculate_cost(input_tokens, output_tokens)
            
            # Update tracking
            self.total_tokens += input_tokens + output_tokens
            self.total_cost += cost
            
            metadata = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "cost": cost,
                "processing_time": processing_time,
                "model": self.model,
                "timestamp": datetime.now().isoformat()
            }
            
            return response.content[0].text, metadata
            
        except Exception as e:
            logger.error(f"LLM API call failed: {str(e)}")
            raise
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for API call based on token usage"""
        pricing = self.pricing.get(self.model, {"input": 0.003, "output": 0.015})
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        return input_cost + output_cost
    
    def _prepare_conversation_context(self, messages: List[Dict[str, Any]], max_messages: int = 500) -> str:
        """
        Prepare conversation data for LLM analysis
        
        Args:
            messages: List of message dictionaries
            max_messages: Maximum number of messages to include
            
        Returns:
            Formatted conversation context string
        """
        # Sort messages by date
        sorted_messages = sorted(messages, key=lambda x: x.get('date', ''))
        
        # Limit to max_messages, taking most recent
        if len(sorted_messages) > max_messages:
            sorted_messages = sorted_messages[-max_messages:]
        
        context = []
        for msg in sorted_messages:
            sender = "USER" if msg.get('isFromMe', False) else "PERSON"
            date = msg.get('date', 'Unknown')
            body = msg.get('body', '').strip()
            
            if body:  # Only include messages with content
                context.append(f"[{date}] {sender}: {body}")
        
        return "\n".join(context)
    
    async def analyze_personality(self, request: AnalysisRequest) -> AnalysisResult:
        """
        Analyze personality traits from conversation data
        
        Args:
            request: Analysis request with conversation data
            
        Returns:
            AnalysisResult with PersonalityProfile
        """
        system_prompt = """You are an expert personality psychologist analyzing communication patterns to create detailed personality profiles. 

Your task is to analyze conversation data and provide insights into:
- Big Five personality traits (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism)
- Communication preferences and behavioral patterns
- Key personality insights based on conversation style and content

Provide your analysis as a structured JSON response with the following format:
{
    "big_five_scores": {
        "openness": 0.0-1.0,
        "conscientiousness": 0.0-1.0, 
        "extraversion": 0.0-1.0,
        "agreeableness": 0.0-1.0,
        "neuroticism": 0.0-1.0
    },
    "personality_insights": ["insight1", "insight2", ...],
    "communication_preferences": {
        "preferred_style": "description",
        "response_patterns": "description",
        "topic_preferences": ["topic1", "topic2"]
    },
    "behavioral_patterns": ["pattern1", "pattern2", ...],
    "confidence_score": 0.0-1.0
}

Base your analysis on observable communication patterns, word choice, topic engagement, emotional expression, and interaction styles."""
        
        conversation_context = self._prepare_conversation_context(
            request.conversation_data, 
            request.max_messages
        )
        
        user_prompt = f"""Analyze the personality of {request.person_name} based on the following conversation data:

{conversation_context}

Please provide a comprehensive personality analysis following the specified JSON format. Focus on patterns you can observe in their communication style, topics they engage with, how they express emotions, and their interaction patterns with others."""
        
        try:
            response_text, metadata = await self._call_llm(system_prompt, user_prompt)
            
            # Parse JSON response
            analysis_data = json.loads(response_text.strip())
            personality_profile = PersonalityProfile(**analysis_data)
            
            result = AnalysisResult(
                request_id=str(uuid.uuid4()),
                person_id=request.person_id,
                analysis_type=AnalysisType.PERSONALITY_PROFILE,
                result=personality_profile,
                metadata=metadata,
                tokens_used=metadata["total_tokens"],
                cost=metadata["cost"],
                processing_time=metadata["processing_time"],
                timestamp=datetime.now()
            )
            
            self.analysis_history.append(result)
            logger.info(f"Completed personality analysis for {request.person_name}")
            
            return result
            
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Failed to parse LLM response for personality analysis: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Personality analysis failed: {str(e)}")
            raise
    
    async def analyze_relationships(self, request: AnalysisRequest) -> List[AnalysisResult]:
        """
        Analyze relationship dynamics from conversation data
        
        Args:
            request: Analysis request with conversation data
            
        Returns:
            List of AnalysisResult with RelationshipDynamic for each partner
        """
        # Group messages by conversation partner
        partner_conversations = {}
        
        for msg in request.conversation_data:
            # Determine partner based on group chat or direct message context
            partner = self._identify_conversation_partner(msg, request.person_name)
            if partner:
                if partner not in partner_conversations:
                    partner_conversations[partner] = []
                partner_conversations[partner].append(msg)
        
        results = []
        
        for partner_name, messages in partner_conversations.items():
            if len(messages) < 10:  # Skip partners with too few messages
                continue
                
            system_prompt = f"""You are an expert in relationship dynamics and interpersonal communication. 

Analyze the relationship between {request.person_name} and {partner_name} based on their conversation patterns.

Provide insights into:
- Relationship type (family, friend, colleague, romantic, etc.)
- Communication intimacy level
- Emotional dynamics and interaction patterns
- Main conversation topics and shared interests

Respond with structured JSON:
{{
    "partner_name": "{partner_name}",
    "relationship_type": "type",
    "intimacy_level": 0.0-1.0,
    "communication_pattern": "description",
    "emotional_dynamics": {{
        "primary_emotions": ["emotion1", "emotion2"],
        "interaction_style": "description",
        "conflict_resolution": "description"
    }},
    "key_topics": ["topic1", "topic2", ...],
    "confidence_score": 0.0-1.0
}}"""
            
            conversation_context = self._prepare_conversation_context(messages, 300)
            
            user_prompt = f"""Analyze the relationship dynamics between {request.person_name} and {partner_name} based on these conversations:

{conversation_context}

Focus on communication patterns, emotional undertones, topics discussed, and the nature of their interaction."""
            
            try:
                response_text, metadata = await self._call_llm(system_prompt, user_prompt)
                analysis_data = json.loads(response_text.strip())
                relationship_dynamic = RelationshipDynamic(**analysis_data)
                
                result = AnalysisResult(
                    request_id=str(uuid.uuid4()),
                    person_id=request.person_id,
                    analysis_type=AnalysisType.RELATIONSHIP_DYNAMICS,
                    result=relationship_dynamic,
                    metadata=metadata,
                    tokens_used=metadata["total_tokens"],
                    cost=metadata["cost"],
                    processing_time=metadata["processing_time"],
                    timestamp=datetime.now()
                )
                
                results.append(result)
                self.analysis_history.append(result)
                
            except (json.JSONDecodeError, ValidationError) as e:
                logger.error(f"Failed to parse relationship analysis for {partner_name}: {str(e)}")
                continue
            except Exception as e:
                logger.error(f"Relationship analysis failed for {partner_name}: {str(e)}")
                continue
        
        logger.info(f"Completed relationship analysis for {request.person_name}: {len(results)} relationships")
        return results
    
    def _identify_conversation_partner(self, message: Dict[str, Any], person_name: str) -> Optional[str]:
        """
        Identify conversation partner from message context
        
        This is a simplified implementation - you may need to enhance based on your data structure
        """
        # This would need to be implemented based on your specific data structure
        # For now, returning a placeholder
        return message.get('partner_name') or message.get('group_chat', 'Unknown')
    
    async def batch_analyze(self, requests: List[AnalysisRequest]) -> List[AnalysisResult]:
        """
        Process multiple analysis requests concurrently
        
        Args:
            requests: List of analysis requests
            
        Returns:
            List of analysis results
        """
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def process_request(request: AnalysisRequest) -> AnalysisResult:
            async with semaphore:
                if request.analysis_type == AnalysisType.PERSONALITY_PROFILE:
                    return await self.analyze_personality(request)
                elif request.analysis_type == AnalysisType.RELATIONSHIP_DYNAMICS:
                    return await self.analyze_relationships(request)
                else:
                    raise ValueError(f"Unsupported analysis type: {request.analysis_type}")
        
        results = await asyncio.gather(*[process_request(req) for req in requests], return_exceptions=True)
        
        # Filter out exceptions and log them
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Analysis request {i} failed: {str(result)}")
            else:
                if isinstance(result, list):
                    valid_results.extend(result)
                else:
                    valid_results.append(result)
        
        return valid_results
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get summary of API costs and usage"""
        return {
            "total_tokens": self.total_tokens,
            "total_cost": round(self.total_cost, 4),
            "total_analyses": len(self.analysis_history),
            "average_cost_per_analysis": round(self.total_cost / max(1, len(self.analysis_history)), 4),
            "cost_by_type": self._get_cost_by_analysis_type()
        }
    
    def _get_cost_by_analysis_type(self) -> Dict[str, Dict[str, Any]]:
        """Get cost breakdown by analysis type"""
        costs_by_type = {}
        
        for analysis in self.analysis_history:
            analysis_type = analysis.analysis_type.value
            if analysis_type not in costs_by_type:
                costs_by_type[analysis_type] = {"count": 0, "total_cost": 0.0, "total_tokens": 0}
            
            costs_by_type[analysis_type]["count"] += 1
            costs_by_type[analysis_type]["total_cost"] += analysis.cost
            costs_by_type[analysis_type]["total_tokens"] += analysis.tokens_used
        
        return costs_by_type


# Example usage
if __name__ == "__main__":
    async def main():
        # Initialize LLM integrator
        llm = LLMIntegrator(model="claude-3-sonnet-20240229")
        
        # Example conversation data
        sample_messages = [
            {"body": "Hey, how was your day?", "isFromMe": True, "date": "2025-08-26"},
            {"body": "Pretty good! Just finished a great workout. How about you?", "isFromMe": False, "date": "2025-08-26"}
        ]
        
        # Create analysis request
        request = AnalysisRequest(
            person_id="person_test",
            person_name="Test Person",
            analysis_type=AnalysisType.PERSONALITY_PROFILE,
            conversation_data=sample_messages
        )
        
        # Run analysis
        result = await llm.analyze_personality(request)
        print(f"Analysis completed: {result.result}")
        print(f"Cost: ${result.cost:.4f}")
    
    # Run example
    # asyncio.run(main())
