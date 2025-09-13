#!/usr/bin/env python3
"""
LLM Integration Module for Avatar Intelligence System (FIXED VERSION)
====================================================

This module provides comprehensive LLM-powered analysis for personality profiling,
relationship dynamics, communication patterns, and conversation insights.

Key Features:
- Claude API integration for deep personality analysis
- Async processing for batch analysis
- Cost monitoring and rate limiting
- Structured output with validation
- Conversation context understanding
- FIXED: Robust JSON parsing for LLM responses
"""

import asyncio
import json
import logging
import os
import uuid
import re
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
                 model: str = "claude-sonnet-4-20250514",
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
        
        # Updated pricing for newer models
        self.pricing = {
            "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
            "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
            "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
            "claude-sonnet-4-20250514": {"input": 0.003, "output": 0.015}  # Adjust based on actual pricing
        }
    
    def _extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
        """
        Extract JSON from LLM response with improved parsing and security
        
        Args:
            response_text: Raw response from LLM
            
        Returns:
            Parsed JSON dictionary
            
        Raises:
            ValueError: If no valid JSON can be extracted
        """
        # Log the raw response for debugging (truncated for security)
        logger.debug(f"Raw LLM response length: {len(response_text)} chars")
        
        # Try direct JSON parsing first
        try:
            return json.loads(response_text.strip())
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from markdown code blocks
        markdown_patterns = [
            r'```json\s*\n([^`]+)\n```',  # JSON code block
            r'```\s*\n(\{[^`]+\})\n```',  # Generic code block with JSON
        ]
        
        for pattern in markdown_patterns:
            matches = re.findall(pattern, response_text, re.MULTILINE | re.DOTALL)
            if matches:
                for match in matches:
                    try:
                        parsed = json.loads(match)
                        # Validate it's a dictionary
                        if isinstance(parsed, dict):
                            return parsed
                    except json.JSONDecodeError:
                        continue
        
        # Try to find well-formed JSON objects using a more precise pattern
        # This handles nested objects better
        json_object_pattern = r'(\{(?:[^{}]|\{[^{}]*\})*\})'
        matches = re.finditer(json_object_pattern, response_text)
        
        json_candidates = []
        for match in matches:
            try:
                parsed = json.loads(match.group(1))
                if isinstance(parsed, dict):
                    json_candidates.append(parsed)
            except json.JSONDecodeError:
                continue
        
        # Return the largest valid JSON object (likely the most complete)
        if json_candidates:
            return max(json_candidates, key=lambda x: len(json.dumps(x)))
        
        # Try to extract JSON arrays if no objects found
        json_array_pattern = r'(\[(?:[^\[\]]|\[[^\[\]]*\])*\])'
        matches = re.finditer(json_array_pattern, response_text)
        
        for match in matches:
            try:
                parsed = json.loads(match.group(1))
                # Wrap array in object if needed
                if isinstance(parsed, list):
                    return {"data": parsed}
            except json.JSONDecodeError:
                continue
        
        # If all else fails, log error with limited info
        logger.error(f"Could not extract JSON from response. Response length: {len(response_text)}")
        
        # Try to provide helpful error information without exposing full response
        if '{' not in response_text:
            raise ValueError("No JSON object found in LLM response")
        elif '}' not in response_text:
            raise ValueError("Incomplete JSON object in LLM response")
        else:
            raise ValueError("Failed to parse JSON from LLM response - invalid format")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _call_llm(self, 
                       system_prompt: str, 
                       user_prompt: str,
                       max_tokens: Optional[int] = None,
                       temperature: Optional[float] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Make API call to Claude with retry logic and error handling
        
        Args:
            system_prompt: System instructions for the model
            user_prompt: User's input prompt
            max_tokens: Maximum tokens for response (default: 4000)
            temperature: Temperature for response (default: 0.1)
            
        Returns:
            Tuple of (response_text, metadata)
            
        Raises:
            anthropic.APIError: For API-related errors
            ValueError: For invalid responses
        """
        try:
            start_time = datetime.now()
            
            # Use provided values or defaults
            max_tokens = max_tokens or 4000
            temperature = temperature or 0.1
            
            # Validate inputs
            if not system_prompt or not user_prompt:
                raise ValueError("System prompt and user prompt are required")
            
            # Make API call with timeout
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
                timeout=30.0  # 30 second timeout
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
            
            # Log successful call (without sensitive data)
            logger.info(f"LLM call successful: {input_tokens} input, {output_tokens} output tokens")
            
            return response.content[0].text, metadata
            
        except anthropic.RateLimitError as e:
            logger.error(f"Rate limit exceeded: {e}")
            raise
        except anthropic.APIConnectionError as e:
            logger.error(f"API connection error: {e}")
            raise
        except anthropic.APIStatusError as e:
            logger.error(f"API status error: {e.status_code} - {e.message}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in LLM call: {type(e).__name__}: {e}")
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

IMPORTANT: Respond ONLY with a valid JSON object. Do not include any explanatory text, markdown formatting, or code blocks. 
The response must be a single JSON object that can be directly parsed.

Required JSON structure:
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
}"""
        
        conversation_context = self._prepare_conversation_context(
            request.conversation_data, 
            request.max_messages
        )
        
        user_prompt = f"""Analyze the personality of {request.person_name} based on the following conversation data:

{conversation_context}

Remember to respond ONLY with a valid JSON object following the specified format. No additional text or formatting."""
        
        try:
            response_text, metadata = await self._call_llm(system_prompt, user_prompt)
            
            # Parse JSON response with robust extraction
            analysis_data = self._extract_json_from_response(response_text)
            
            # Validate and create PersonalityProfile
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
            
        except (json.JSONDecodeError, ValidationError, ValueError) as e:
            logger.error(f"Failed to parse LLM response for personality analysis: {str(e)}")
            # Return a default profile with error indication
            default_profile = PersonalityProfile(
                big_five_scores={
                    "openness": 0.5,
                    "conscientiousness": 0.5,
                    "extraversion": 0.5,
                    "agreeableness": 0.5,
                    "neuroticism": 0.5
                },
                personality_insights=["Analysis failed - insufficient data or parsing error"],
                communication_preferences={"error": str(e)},
                behavioral_patterns=["Error in analysis"],
                confidence_score=0.0
            )
            
            result = AnalysisResult(
                request_id=str(uuid.uuid4()),
                person_id=request.person_id,
                analysis_type=AnalysisType.PERSONALITY_PROFILE,
                result=default_profile,
                metadata={"error": str(e), "cost": 0.0},
                tokens_used=0,
                cost=0.0,
                processing_time=0.0,
                timestamp=datetime.now()
            )
            return result
            
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

IMPORTANT: Respond ONLY with a valid JSON object. Do not include any explanatory text, markdown formatting, or code blocks.

Required JSON structure:
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

Remember to respond ONLY with a valid JSON object following the specified format."""
            
            try:
                response_text, metadata = await self._call_llm(system_prompt, user_prompt)
                
                # Parse JSON response with robust extraction
                analysis_data = self._extract_json_from_response(response_text)
                
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
                
            except (json.JSONDecodeError, ValidationError, ValueError) as e:
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
        """
        # First check for partner_name field
        if 'partner_name' in message:
            return message['partner_name']
        
        # Then check partners list
        partners = message.get('partners', [])
        if partners and len(partners) == 1:
            return partners[0]
        
        # Check group chat name
        group_name = message.get('group_chat_name')
        if group_name:
            return group_name
            
        # Default to Unknown if can't identify
        return message.get('group_chat_id', 'Unknown')
    
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
        llm = LLMIntegrator(model="claude-sonnet-4-20250514")
        
        # Example conversation data
        sample_messages = [
            {"body": "Hey, how was your day?", "isFromMe": True, "date": "2025-08-26"},
            {"body": "Pretty good! Just finished a great workout. How about you?", "isFromMe": False, "date": "2025-08-26"}
        ]
        
        # Create analysis request
        request = AnalysisRequest(
            person_id="test_001",
            person_name="Test User",
            analysis_type=AnalysisType.PERSONALITY_PROFILE,
            conversation_data=sample_messages
        )
        
        # Run analysis
        result = await llm.analyze_personality(request)
        print(f"Analysis complete: {result}")
        
        # Get cost summary
        print(f"Cost summary: {llm.get_cost_summary()}")
    
    asyncio.run(main())
