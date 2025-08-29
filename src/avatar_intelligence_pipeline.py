#!/usr/bin/env python3
"""
Avatar Intelligence Pipeline - Core System
==========================================

Complete avatar analysis system with:
- Nickname detection engine
- Relationship inference engine  
- Linguistic analysis
- Avatar generation pipeline
- Runtime system for fast queries

Usage:
    from src.avatar_intelligence_pipeline import AvatarSystemManager
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
    avatar_system = AvatarSystemManager(driver)
    
    # Process all people with sufficient conversation data
    stats = avatar_system.initialize_all_people(min_messages=50)
    
    # Generate avatar response
    prompt = avatar_system.generate_response(
        person_identifier="John Doe",
        conversation_type="1:1",
        partners=["Jane Smith"],
        topic="travel"
    )
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
from collections import Counter, defaultdict
import pandas as pd
from neo4j import GraphDatabase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class NicknameDetector:
    """Advanced nickname detection for conversation participants"""
    
    def __init__(self):
        self.common_nicknames = {
            'mom', 'dad', 'babe', 'baby', 'honey', 'sweetie', 'love', 'dear',
            'buddy', 'dude', 'bro', 'sis', 'sister', 'brother', 'bestie',
            'sweetheart', 'darling', 'hun', 'gorgeous', 'beautiful', 'handsome'
        }
    
    def extract_nicknames(self, messages: List[Dict], person_name: str) -> Dict[str, int]:
        """Extract nicknames used for a person from message content"""
        nicknames = Counter()
        
        # Get messages sent TO this person (looking for what they're called)
        for msg in messages:
            if not msg.get('body'):
                continue
                
            body = msg['body'].lower()
            
            # Look for direct address patterns
            patterns = [
                r'\b(?:hey|hi|hello)\s+([a-zA-Z]+)\b',
                r'\b([a-zA-Z]+),?\s+(?:how|what|where|when|why)',
                r'\bthanks?\s+([a-zA-Z]+)\b',
                r'\bye\s+([a-zA-Z]+)\b',
                r'\bgoodnight\s+([a-zA-Z]+)\b',
                r'\bgood\s+morning\s+([a-zA-Z]+)\b',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, body, re.IGNORECASE)
                for match in matches:
                    if len(match) > 1 and match.lower() not in ['you', 'me', 'us', 'we']:
                        nicknames[match.lower()] += 1
        
        # Filter out unlikely nicknames
        filtered_nicknames = {}
        for nickname, count in nicknames.items():
            if (count >= 2 and 
                len(nickname) <= 15 and 
                nickname.isalpha() and
                nickname.lower() != person_name.lower()):
                filtered_nicknames[nickname] = count
        
        return filtered_nicknames


class RelationshipInferrer:
    """Infers relationship types between conversation participants"""
    
    def __init__(self):
        self.relationship_indicators = {
            'romantic': {
                'keywords': ['love', 'babe', 'baby', 'honey', 'sweetheart', 'darling', 'gorgeous', 'beautiful', 'handsome'],
                'patterns': [r'\bi love you\b', r'\bmiss you\b', r'\bkiss\b', r'\bdate night\b']
            },
            'family': {
                'keywords': ['mom', 'dad', 'mother', 'father', 'son', 'daughter', 'brother', 'sister', 'grandma', 'grandpa'],
                'patterns': [r'\bfamily dinner\b', r'\bhome for\b', r'\bparents\b']
            },
            'friend': {
                'keywords': ['buddy', 'dude', 'bro', 'bestie', 'friend'],
                'patterns': [r'\bhang out\b', r'\bcatch up\b', r'\bgrab a drink\b', r'\bmeet up\b']
            },
            'professional': {
                'keywords': ['meeting', 'project', 'deadline', 'work', 'office', 'client', 'boss', 'colleague'],
                'patterns': [r'\bwork on\b', r'\bmeeting\b', r'\bdeadline\b', r'\boffice\b']
            }
        }
    
    def infer_relationship(self, messages: List[Dict], person1: str, person2: str) -> Dict[str, Any]:
        """Infer relationship type between two people based on their messages"""
        
        relationship_scores = defaultdict(int)
        total_messages = len(messages)
        
        if total_messages == 0:
            return {'type': 'unknown', 'confidence': 0.0, 'evidence': []}
        
        evidence = []
        
        for msg in messages:
            body = msg.get('body', '').lower()
            if not body:
                continue
                
            for rel_type, indicators in self.relationship_indicators.items():
                # Check keywords
                for keyword in indicators['keywords']:
                    if keyword in body:
                        relationship_scores[rel_type] += 1
                        evidence.append(f"{rel_type}: '{keyword}' found")
                
                # Check patterns
                for pattern in indicators['patterns']:
                    if re.search(pattern, body, re.IGNORECASE):
                        relationship_scores[rel_type] += 2  # Patterns worth more
                        evidence.append(f"{rel_type}: pattern '{pattern}' matched")
        
        if not relationship_scores:
            return {'type': 'unknown', 'confidence': 0.0, 'evidence': []}
        
        # Determine most likely relationship
        best_type = max(relationship_scores, key=relationship_scores.get)
        confidence = min(relationship_scores[best_type] / total_messages, 1.0)
        
        return {
            'type': best_type,
            'confidence': confidence,
            'evidence': evidence[:10],  # Limit evidence examples
            'all_scores': dict(relationship_scores)
        }


class LinguisticAnalyzer:
    """Analyzes linguistic patterns and communication styles"""
    
    def analyze_communication_style(self, messages: List[Dict]) -> Dict[str, Any]:
        """Analyze comprehensive communication style from messages"""
        
        if not messages:
            return self._empty_style_analysis()
        
        analysis = {
            'message_patterns': self._analyze_message_patterns(messages),
            'linguistic_features': self._analyze_linguistic_features(messages),
            'emotional_expressions': self._analyze_emotional_expressions(messages),
            'topic_preferences': self._analyze_topic_preferences(messages),
            'temporal_patterns': self._analyze_temporal_patterns(messages)
        }
        
        return analysis
    
    def _analyze_message_patterns(self, messages: List[Dict]) -> Dict[str, Any]:
        """Analyze message length, frequency, and timing patterns"""
        lengths = [len(msg.get('body', '')) for msg in messages if msg.get('body')]
        
        return {
            'avg_message_length': sum(lengths) / len(lengths) if lengths else 0,
            'total_messages': len(messages),
            'short_messages': sum(1 for l in lengths if l < 20),
            'long_messages': sum(1 for l in lengths if l > 100),
            'response_style': 'concise' if sum(lengths) / len(lengths) < 50 else 'detailed' if lengths else 'unknown'
        }
    
    def _analyze_linguistic_features(self, messages: List[Dict]) -> Dict[str, Any]:
        """Analyze language patterns, formality, punctuation"""
        all_text = ' '.join([msg.get('body', '') for msg in messages if msg.get('body')])
        
        return {
            'exclamation_usage': all_text.count('!') / len(messages) if messages else 0,
            'question_usage': all_text.count('?') / len(messages) if messages else 0,
            'capitalization_style': self._analyze_capitalization(all_text),
            'emoji_usage': len(re.findall(r'[😀-🙏]', all_text)) / len(messages) if messages else 0,
            'formal_language': self._detect_formal_language(all_text),
        }
    
    def _analyze_emotional_expressions(self, messages: List[Dict]) -> Dict[str, int]:
        """Detect emotional expressions and sentiment indicators"""
        emotions = Counter()
        
        emotion_patterns = {
            'excitement': [r'\b(amazing|awesome|fantastic|great|wonderful)\b', r'!+'],
            'affection': [r'\b(love|miss|care|sweet|dear)\b'],
            'humor': [r'\b(lol|haha|funny|joke)\b'],
            'concern': [r'\b(worried|concerned|hope|careful)\b'],
            'gratitude': [r'\b(thanks|thank you|grateful|appreciate)\b']
        }
        
        for msg in messages:
            body = msg.get('body', '').lower()
            if not body:
                continue
                
            for emotion, patterns in emotion_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, body, re.IGNORECASE):
                        emotions[emotion] += 1
        
        return dict(emotions)
    
    def _analyze_topic_preferences(self, messages: List[Dict]) -> Dict[str, int]:
        """Identify commonly discussed topics"""
        topics = Counter()
        
        topic_keywords = {
            'work': ['work', 'job', 'office', 'meeting', 'project', 'deadline'],
            'family': ['family', 'mom', 'dad', 'kids', 'children', 'parents'],
            'health': ['doctor', 'hospital', 'sick', 'healthy', 'exercise', 'fitness'],
            'travel': ['trip', 'vacation', 'travel', 'flight', 'hotel'],
            'food': ['dinner', 'lunch', 'restaurant', 'cook', 'eat', 'food'],
            'entertainment': ['movie', 'show', 'music', 'book', 'game']
        }
        
        for msg in messages:
            body = msg.get('body', '').lower()
            if not body:
                continue
                
            for topic, keywords in topic_keywords.items():
                for keyword in keywords:
                    if keyword in body:
                        topics[topic] += 1
        
        return dict(topics)
    
    def _analyze_temporal_patterns(self, messages: List[Dict]) -> Dict[str, Any]:
        """Analyze when person typically communicates"""
        
        # This would need actual timestamp analysis
        # For now, return placeholder structure
        return {
            'preferred_hours': 'evening',  # Would be calculated from timestamps
            'response_speed': 'moderate',   # Would be calculated from conversation threads
            'communication_frequency': 'regular'  # Would be calculated from message spacing
        }
    
    def _analyze_capitalization(self, text: str) -> str:
        """Analyze capitalization patterns"""
        if not text:
            return 'unknown'
            
        sentences = re.split(r'[.!?]+', text)
        properly_capitalized = sum(1 for s in sentences if s.strip() and s.strip()[0].isupper())
        
        if len(sentences) == 0:
            return 'unknown'
        elif properly_capitalized / len(sentences) > 0.8:
            return 'proper'
        elif properly_capitalized / len(sentences) < 0.3:
            return 'lowercase'
        else:
            return 'mixed'
    
    def _detect_formal_language(self, text: str) -> float:
        """Detect formal language usage (0.0 to 1.0)"""
        formal_indicators = ['please', 'thank you', 'would you', 'could you', 'appreciate']
        informal_indicators = ['gonna', 'wanna', 'yeah', 'nah', 'sup']
        
        formal_count = sum(text.lower().count(indicator) for indicator in formal_indicators)
        informal_count = sum(text.lower().count(indicator) for indicator in informal_indicators)
        
        total = formal_count + informal_count
        return formal_count / total if total > 0 else 0.5
    
    def _empty_style_analysis(self) -> Dict[str, Any]:
        """Return empty analysis structure"""
        return {
            'message_patterns': {'avg_message_length': 0, 'total_messages': 0, 'response_style': 'unknown'},
            'linguistic_features': {'exclamation_usage': 0, 'question_usage': 0, 'capitalization_style': 'unknown'},
            'emotional_expressions': {},
            'topic_preferences': {},
            'temporal_patterns': {'preferred_hours': 'unknown', 'response_speed': 'unknown'}
        }


class AvatarSystemManager:
    """
    Main system manager for avatar intelligence operations
    
    FIXED VERSION - Addresses:
    - Schema mismatch errors in get_system_stats()
    - Cypher syntax issues with ORDER BY after WITH DISTINCT
    - Property name corrections for GroupChat (using gc.id instead of gc.chat_identifier)
    - Proper error handling and graceful degradation
    """
    
    def __init__(self, driver: GraphDatabase.driver):
        self.driver = driver
        self.nickname_detector = NicknameDetector()
        self.relationship_inferrer = RelationshipInferrer()
        self.linguistic_analyzer = LinguisticAnalyzer()
    
    def initialize_all_people(self, min_messages: int = 50) -> Dict[str, int]:
        """Initialize avatar profiles for all people with sufficient message data"""
        
        logger.info(f"Starting avatar profile initialization for people with {min_messages}+ messages")
        
        with self.driver.session() as session:
            # Get people with enough messages
            result = session.run("""
                MATCH (p:Person)-[:SENT]->(m:Message)
                WITH p, count(m) as messageCount
                WHERE messageCount >= $min_messages
                RETURN p.name as name, p.id as personId, messageCount
                ORDER BY messageCount DESC
            """, min_messages=min_messages)
            
            candidates = [dict(record) for record in result]
            
        if not candidates:
            logger.warning(f"No people found with {min_messages}+ messages")
            return {'found': 0, 'processed': 0, 'created': 0, 'errors': 0}
        
        logger.info(f"Found {len(candidates)} people to process")
        
        stats = {'found': len(candidates), 'processed': 0, 'created': 0, 'errors': 0}
        
        for person in candidates:
            try:
                result = self.initialize_person(person['name'], identifier_type='name')
                if result.get('created'):
                    stats['created'] += 1
                stats['processed'] += 1
                
                if stats['processed'] % 10 == 0:
                    logger.info(f"Processed {stats['processed']}/{stats['found']} people")
                    
            except Exception as e:
                logger.error(f"Error processing {person['name']}: {e}")
                stats['errors'] += 1
        
        logger.info(f"Initialization complete: {stats}")
        return stats
    
    def initialize_person(self, person_identifier: str, identifier_type: str = 'name') -> Dict[str, Any]:
        """Initialize comprehensive avatar profile for a single person"""
        
        logger.info(f"Initializing avatar profile for: {person_identifier}")
        
        with self.driver.session() as session:
            # Get person's messages and basic info
            if identifier_type == 'name':
                person_query = """
                    MATCH (p:Person {name: $identifier})
                    OPTIONAL MATCH (p)-[:SENT]->(m:Message)
                    RETURN p.name as name, p.id as personId, p.phone as phone,
                           collect(m) as messages
                """
            else:  # phone or id
                person_query = """
                    MATCH (p:Person) 
                    WHERE p.phone = $identifier OR p.id = $identifier
                    OPTIONAL MATCH (p)-[:SENT]->(m:Message)
                    RETURN p.name as name, p.id as personId, p.phone as phone,
                           collect(m) as messages
                """
            
            result = session.run(person_query, identifier=person_identifier).single()
            
            if not result:
                return {'error': f'Person not found: {person_identifier}'}
            
            person_info = {
                'name': result['name'],
                'personId': result['personId'],
                'phone': result['phone']
            }
            
            messages = [dict(m) for m in result['messages'] if m]
            
            if len(messages) < 10:
                return {'error': f'Insufficient message data for {person_info["name"]} ({len(messages)} messages)'}
            
            # Perform comprehensive analysis
            profile_data = self._create_comprehensive_profile(session, person_info, messages)
            
            # Store profile in database
            created = self._store_avatar_profile(session, person_info, profile_data)
            
            return {
                'person': person_info['name'],
                'messages_analyzed': len(messages),
                'profile_created': created,
                'created': created
            }
    
    def _create_comprehensive_profile(self, session, person_info: Dict, messages: List[Dict]) -> Dict[str, Any]:
        """Create comprehensive avatar profile from person's messages"""
        
        # Analyze communication style
        style_analysis = self.linguistic_analyzer.analyze_communication_style(messages)
        
        # Extract nicknames
        nicknames = self.nickname_detector.extract_nicknames(messages, person_info['name'])
        
        # Get conversation partners and analyze relationships
        relationships = self._analyze_relationships(session, person_info, messages)
        
        # Extract signature phrases
        signature_phrases = self._extract_signature_phrases(messages)
        
        return {
            'communication_style': style_analysis,
            'nicknames': nicknames,
            'relationships': relationships,
            'signature_phrases': signature_phrases,
            'last_analysis': datetime.now().isoformat(),
            'message_count': len(messages)
        }
    
    def _analyze_relationships(self, session, person_info: Dict, messages: List[Dict]) -> List[Dict[str, Any]]:
        """Analyze relationships with conversation partners"""
        
        # FIXED: Updated query to work with actual schema and fix ORDER BY issue
        partner_query = """
            MATCH (person:Person {name: $person_name})-[:SENT]->(m:Message)-[:SENT_TO]->(gc:GroupChat)
            MATCH (partner:Person)-[:MEMBER_OF]->(gc)
            WHERE partner.name <> $person_name
            WITH partner, gc, count(m) as messageCount
            RETURN partner.name as partnerName, partner.id as partnerId, messageCount,
                   collect({chatId: gc.id, messages: messageCount}) as conversations
            ORDER BY messageCount DESC
            LIMIT 20
        """
        
        result = session.run(partner_query, person_name=person_info['name'])
        
        relationships = []
        for record in result:
            partner_name = record['partnerName']
            
            # Get messages between these two people
            conversation_query = """
                MATCH (p1:Person {name: $person1})-[:SENT]->(m:Message)-[:SENT_TO]->(gc:GroupChat)
                MATCH (p2:Person {name: $person2})-[:MEMBER_OF]->(gc)
                RETURN m.body as body, m.date as date, m.isFromMe as isFromMe
                ORDER BY m.date DESC
                LIMIT 100
            """
            
            conv_result = session.run(conversation_query, person1=person_info['name'], person2=partner_name)
            partner_messages = [dict(record) for record in conv_result]
            
            if partner_messages:
                # Infer relationship
                relationship_analysis = self.relationship_inferrer.infer_relationship(
                    partner_messages, person_info['name'], partner_name
                )
                
                relationships.append({
                    'partner_name': partner_name,
                    'partner_id': record['partnerId'],
                    'relationship_type': relationship_analysis['type'],
                    'confidence': relationship_analysis['confidence'],
                    'message_count': len(partner_messages),
                    'evidence': relationship_analysis.get('evidence', [])[:5]  # Limit evidence
                })
        
        return relationships
    
    def _extract_signature_phrases(self, messages: List[Dict]) -> List[Dict[str, Any]]:
        """Extract characteristic phrases this person uses"""
        
        phrase_patterns = [
            r'\b(?:lol|haha|hehe)\b',
            r'\bthanks?\s+(?:so\s+much|a\s+lot|again)\b',
            r'\bhave\s+a\s+(?:good|great|nice)\s+\w+\b',
            r'\btalk\s+to\s+you\s+(?:later|soon)\b',
            r'\bsounds?\s+good\b',
            r'\bno\s+worries?\b',
            r'\byeah\s+(?:definitely|totally|for\s+sure)\b'
        ]
        
        all_text = ' '.join([msg.get('body', '').lower() for msg in messages if msg.get('body')])
        
        signature_phrases = []
        for pattern in phrase_patterns:
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            if matches:
                unique_matches = list(set(matches))
                for match in unique_matches:
                    frequency = all_text.count(match.lower())
                    if frequency >= 3:  # Must appear at least 3 times
                        signature_phrases.append({
                            'phrase': match,
                            'frequency': frequency,
                            'context': 'conversational'
                        })
        
        return sorted(signature_phrases, key=lambda x: x['frequency'], reverse=True)[:10]
    
    def _store_avatar_profile(self, session, person_info: Dict, profile_data: Dict) -> bool:
        """Store comprehensive avatar profile in Neo4j"""
        
        try:
            # Create or update communication profile
            profile_query = """
                MERGE (p:Person {name: $person_name})
                MERGE (cp:CommunicationProfile {id: $profile_id})
                SET cp.personId = $person_id,
                    cp.personName = $person_name,
                    cp.status = 'active',
                    cp.lastAnalysis = $last_analysis,
                    cp.messageCount = $message_count,
                    cp.avgMessageLength = $avg_length,
                    cp.responseStyle = $response_style,
                    cp.formalityScore = $formality_score,
                    cp.emotionalExpressions = $emotional_expressions
                MERGE (p)-[:HAS_PROFILE]->(cp)
            """
            
            style = profile_data['communication_style']
            session.run(profile_query,
                person_name=person_info['name'],
                profile_id=f"profile_{person_info['personId']}",
                person_id=person_info['personId'],
                last_analysis=profile_data['last_analysis'],
                message_count=profile_data['message_count'],
                avg_length=style['message_patterns']['avg_message_length'],
                response_style=style['message_patterns']['response_style'],
                formality_score=style['linguistic_features'].get('formal_language', 0.5),
                emotional_expressions=str(style['emotional_expressions'])  # Convert to string for storage
            )
            
            # Store relationships
            for rel in profile_data['relationships']:
                rel_query = """
                    MATCH (cp:CommunicationProfile {id: $profile_id})
                    MERGE (rp:RelationshipPattern {id: $rel_id})
                    SET rp.partnerId = $partner_id,
                        rp.partnerName = $partner_name,
                        rp.relationshipType = $rel_type,
                        rp.confidence = $confidence,
                        rp.messageCount = $message_count
                    MERGE (cp)-[:HAS_RELATIONSHIP]->(rp)
                """
                
                session.run(rel_query,
                    profile_id=f"profile_{person_info['personId']}",
                    rel_id=f"rel_{person_info['personId']}_{rel['partner_id']}",
                    partner_id=rel['partner_id'],
                    partner_name=rel['partner_name'],
                    rel_type=rel['relationship_type'],
                    confidence=rel['confidence'],
                    message_count=rel['message_count']
                )
            
            # Store signature phrases
            for phrase in profile_data['signature_phrases']:
                phrase_query = """
                    MATCH (cp:CommunicationProfile {id: $profile_id})
                    MERGE (sp:SignaturePhrase {id: $phrase_id})
                    SET sp.phrase = $phrase,
                        sp.frequency = $frequency,
                        sp.context = $context
                    MERGE (cp)-[:USES_PHRASE]->(sp)
                """
                
                phrase_id = f"phrase_{person_info['personId']}_{hash(phrase['phrase']) % 10000}"
                session.run(phrase_query,
                    profile_id=f"profile_{person_info['personId']}",
                    phrase_id=phrase_id,
                    phrase=phrase['phrase'],
                    frequency=phrase['frequency'],
                    context=phrase['context']
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing profile for {person_info['name']}: {e}")
            return False
    
    def generate_response(self, person_identifier: str, conversation_type: str = "1:1", 
                         partners: List[str] = None, topic: str = None) -> str:
        """Generate personalized AI avatar response prompt"""
        
        # Debug logging to see what we're actually searching for
        logger.info(f"Searching for person with identifier: '{person_identifier}' (length: {len(person_identifier)})")
        logger.info(f"Identifier repr: {repr(person_identifier)}")
        
        with self.driver.session() as session:
            # Get person's communication profile
            profile_query = """
                MATCH (p:Person)
                WHERE p.name = $identifier OR p.phone = $identifier OR p.id = $identifier
                MATCH (p)-[:HAS_PROFILE]->(cp:CommunicationProfile)
                OPTIONAL MATCH (cp)-[:HAS_RELATIONSHIP]->(rp:RelationshipPattern)
                OPTIONAL MATCH (cp)-[:USES_PHRASE]->(sp:SignaturePhrase)
                RETURN p.name as name, cp, 
                       collect(DISTINCT rp) as relationships,
                       collect(DISTINCT sp) as phrases
            """
            
            result = session.run(profile_query, identifier=person_identifier).single()
            
            if not result:
                return f"Error: No person found for '{person_identifier}'. Please check the name and try again."
            
            if not result['cp']:
                return f"Error: No avatar profile found for '{person_identifier}'. Please run initialization first."
            
            profile = dict(result['cp'])
            relationships = [dict(r) for r in result['relationships'] if r]
            phrases = [dict(p) for p in result['phrases'] if p]
            
            # Build personalized prompt
            prompt_parts = [
                f"You are communicating as {result['name']}, responding in their authentic voice and style.",
                "",
                "COMMUNICATION STYLE:",
                f"- Response style: {profile.get('responseStyle', 'moderate')} messages",
                f"- Formality level: {self._format_formality(profile.get('formalityScore', 0.5))}",
                f"- Average message length: ~{int(profile.get('avgMessageLength', 50))} characters"
            ]
            
            # Add emotional tendencies
            if profile.get('emotionalExpressions'):
                try:
                    emotions = eval(profile['emotionalExpressions']) if isinstance(profile['emotionalExpressions'], str) else profile['emotionalExpressions']
                    if emotions:
                        top_emotions = sorted(emotions.items(), key=lambda x: x[1], reverse=True)[:3]
                        prompt_parts.append(f"- Emotional expressions: {', '.join([e[0] for e in top_emotions])}")
                except:
                    pass  # Skip if emotion parsing fails
            
            # Add relationship context
            if partners and relationships:
                partner_relations = [r for r in relationships if r['partnerName'] in partners]
                if partner_relations:
                    prompt_parts.extend(["", "RELATIONSHIP CONTEXT:"])
                    for rel in partner_relations:
                        prompt_parts.append(f"- {rel['partnerName']}: {rel['relationshipType']} relationship (confidence: {rel['confidence']:.2f})")
            
            # Add signature phrases
            if phrases:
                top_phrases = sorted(phrases, key=lambda x: x['frequency'], reverse=True)[:5]
                prompt_parts.extend(["", "CHARACTERISTIC PHRASES:"])
                for phrase in top_phrases:
                    prompt_parts.append(f"- \"{phrase['phrase']}\" (used {phrase['frequency']} times)")
            
            # Add conversation context
            if conversation_type:
                prompt_parts.extend(["", f"CONVERSATION TYPE: {conversation_type}"])
            
            if topic:
                prompt_parts.extend([f"TOPIC: {topic}"])
            
            prompt_parts.extend([
                "",
                "Respond naturally as this person would, matching their communication style, emotional tendencies, and relationship dynamics. Use their characteristic phrases when appropriate but don't overuse them."
            ])
            
            return "\n".join(prompt_parts)
    
    def _format_formality(self, score: float) -> str:
        """Format formality score as human readable"""
        if score >= 0.7:
            return "formal"
        elif score >= 0.4:
            return "moderate"
        else:
            return "casual/informal"
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics - FIXED to eliminate all warnings"""
        
        with self.driver.session() as session:
            try:
                # First, check if CommunicationProfile nodes exist at all
                check_profiles_query = """
                    MATCH (cp:CommunicationProfile)
                    RETURN count(cp) as profile_count
                    LIMIT 1
                """
                
                try:
                    profile_check = session.run(check_profiles_query).single()
                    profiles_exist = profile_check and profile_check['profile_count'] > 0
                except:
                    profiles_exist = False
                
                if profiles_exist:
                    # Avatar profiles exist, get full avatar system stats
                    avatar_stats_query = """
                        MATCH (cp:CommunicationProfile)
                        OPTIONAL MATCH (cp)-[:HAS_RELATIONSHIP]->(rp:RelationshipPattern)
                        OPTIONAL MATCH (cp)-[:USES_PHRASE]->(sp:SignaturePhrase)
                        RETURN count(DISTINCT cp) as profiles,
                               count(DISTINCT rp) as relationships,
                               count(DISTINCT sp) as phrases,
                               avg(cp.messageCount) as avgMessages
                    """
                    
                    result = session.run(avatar_stats_query).single()
                    
                    return {
                        'avatar_profiles_created': result['profiles'] or 0,
                        'relationship_patterns': result['relationships'] or 0,
                        'signature_phrases': result['phrases'] or 0,
                        'avg_messages_per_profile': int(result['avgMessages'] or 0),
                        'system_status': 'active',
                        'last_check': datetime.now().isoformat()
                    }
                else:
                    # No avatar profiles exist, get basic database stats
                    basic_stats_query = """
                        MATCH (p:Person)
                        OPTIONAL MATCH (p)-[:SENT]->(m:Message)
                        WITH p, count(m) as messageCount
                        RETURN count(p) as total_people,
                               sum(messageCount) as total_messages,
                               avg(messageCount) as avg_messages_per_person,
                               max(messageCount) as max_messages_per_person
                    """
                    
                    basic_result = session.run(basic_stats_query).single()
                    
                    return {
                        'total_people': basic_result['total_people'] or 0,
                        'total_messages': basic_result['total_messages'] or 0,
                        'avg_messages_per_person': int(basic_result['avg_messages_per_person'] or 0),
                        'max_messages_per_person': basic_result['max_messages_per_person'] or 0,
                        'avatar_profiles_created': 0,
                        'system_status': 'ready_for_initialization',
                        'last_check': datetime.now().isoformat()
                    }
                    
            except Exception as e:
                logger.error(f"Error getting system stats: {e}")
                return {
                    'error': f"Could not retrieve system statistics: {e}",
                    'system_status': 'error',
                    'last_check': datetime.now().isoformat()
                }


def main():
    """Command line interface for the avatar intelligence pipeline"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Avatar Intelligence Pipeline")
    parser.add_argument("--neo4j-uri", default="bolt://localhost:7687", help="Neo4j URI")
    parser.add_argument("--username", default="neo4j", help="Neo4j username")
    parser.add_argument("--password", required=True, help="Neo4j password")
    parser.add_argument("--command", required=True, choices=[
        'init-all', 'init-person', 'generate', 'stats'
    ], help="Command to execute")
    parser.add_argument("--person", nargs='*', help="Person identifier (can be multiple words)")
    parser.add_argument("--min-messages", type=int, default=50, help="Minimum messages for init-all")
    parser.add_argument("--partners", nargs='+', help="Conversation partners for generation")
    parser.add_argument("--topic", nargs='*', help="Conversation topic (can be multiple words)")
    
    args = parser.parse_args()
    
    # Initialize system
    driver = GraphDatabase.driver(args.neo4j_uri, auth=(args.username, args.password))
    manager = AvatarSystemManager(driver)
    
    # Handle multi-word arguments
    person_name = ' '.join(args.person) if args.person else None
    topic_text = ' '.join(args.topic) if args.topic else None
    
    # Debug logging
    if args.command == 'generate':
        logger.info(f"Raw args.person: {args.person}")
        logger.info(f"Processed person_name: '{person_name}'")
        logger.info(f"Person name repr: {repr(person_name)}")
        if args.partners:
            logger.info(f"Raw args.partners: {args.partners}")
    
    try:
        if args.command == 'init-all':
            stats = manager.initialize_all_people(min_messages=args.min_messages)
            print(f"Initialized {stats['created']} avatar profiles")
            
        elif args.command == 'init-person':
            if not person_name:
                print("Error: --person required for init-person command")
                return
            result = manager.initialize_person(person_name)
            print(f"Initialized profile for {person_name}: {result}")
            
        elif args.command == 'generate':
            if not person_name:
                print("Error: --person required for generate command")
                return
            prompt = manager.generate_response(person_name, partners=args.partners, topic=topic_text)
            print("Generated Avatar Prompt:")
            print("=" * 50)
            print(prompt)
            
        elif args.command == 'stats':
            stats = manager.get_system_stats()
            print("System Statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
    
    finally:
        driver.close()


if __name__ == "__main__":
    main()
