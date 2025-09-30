"""
Nickname inference engine for Avatar-Engine
Analyzes conversations to detect and infer nicknames
Last Updated: September 29, 2025
"""

import re
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
from collections import defaultdict, Counter
from loguru import logger

# Try to import spaCy - it's optional but recommended
try:
    import spacy
    SPACY_AVAILABLE = True
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        logger.warning("spaCy model 'en_core_web_sm' not found. Run: python3 -m spacy download en_core_web_sm")
        SPACY_AVAILABLE = False
        nlp = None
except ImportError:
    SPACY_AVAILABLE = False
    nlp = None
    logger.info("spaCy not available. Install with: pip3 install spacy")

# Try to import textdistance for similarity calculations
try:
    import textdistance
    TEXTDISTANCE_AVAILABLE = True
except ImportError:
    TEXTDISTANCE_AVAILABLE = False
    logger.info("textdistance not available. Install with: pip3 install textdistance")

from models.graph_models import Person, Nickname, NicknameSource, NicknameType


class NicknameInferenceEngine:
    """Infer nicknames from conversation data"""
    
    def __init__(self):
        """Initialize the inference engine"""
        self.nlp = nlp if SPACY_AVAILABLE else None
        
        # Name variation patterns
        self.name_variations = {}
        
        # Track name usage across conversations
        self.name_usage_stats = defaultdict(lambda: {
            'count': 0,
            'contexts': [],
            'associated_names': Counter(),
            'self_references': 0
        })
        
        # Confidence thresholds
        self.MIN_CONFIDENCE = 0.3
        self.HIGH_CONFIDENCE = 0.8
        
        # String similarity threshold
        self.SIMILARITY_THRESHOLD = 0.85

    def analyze_conversation(
        self, 
        messages: List[Dict[str, Any]], 
        known_persons: List[Person] = None
    ) -> Dict[str, List[Nickname]]:
        """
        Analyze a conversation to infer nicknames
        
        Args:
            messages: List of message dictionaries with 'sender', 'text', 'timestamp'
            known_persons: List of already known Person objects
        
        Returns:
            Dictionary mapping person identifiers to inferred nicknames
        """
        if not messages:
            return {}
        
        known_persons = known_persons or []
        inferred_nicknames = defaultdict(list)
        
        # Step 1: Extract all names mentioned in conversation
        all_names = self._extract_names_from_messages(messages)
        
        # Step 2: Identify self-references
        self_references = self._identify_self_references(messages)
        
        # Step 3: Build name co-occurrence matrix
        cooccurrence = self._build_cooccurrence_matrix(messages, all_names)
        
        # Step 4: Match names to known persons
        name_to_person = self._match_names_to_persons(all_names, known_persons)
        
        # Step 5: Infer nickname relationships
        for name in all_names:
            # Check if this might be a nickname
            potential_nicknames = self._infer_nickname_relationships(
                name, 
                all_names, 
                cooccurrence,
                self_references,
                known_persons
            )
            
            for nickname_data in potential_nicknames:
                person_id = nickname_data['person_id']
                nickname = nickname_data['nickname']
                inferred_nicknames[person_id].append(nickname)
        
        # Step 6: Process greeting patterns
        greeting_nicknames = self._extract_greeting_nicknames(messages)
        for person_id, nicknames in greeting_nicknames.items():
            inferred_nicknames[person_id].extend(nicknames)
        
        return dict(inferred_nicknames)

    def _extract_names_from_messages(self, messages: List[Dict[str, Any]]) -> Set[str]:
        """Extract all person names from messages using NER"""
        names = set()
        
        for msg in messages:
            text = msg.get('text', '')
            
            # Use spaCy NER if available
            if self.nlp:
                try:
                    doc = self.nlp(text)
                    for ent in doc.ents:
                        if ent.label_ == "PERSON":
                            names.add(ent.text)
                except Exception as e:
                    logger.debug(f"spaCy processing error: {e}")
            
            # Also use regex patterns for common name patterns
            # Pattern for capitalized words that might be names
            potential_names = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
            for name in potential_names:
                # Filter out common words that aren't names
                if self._is_likely_name(name):
                    names.add(name)
            
            # Extract @mentions
            mentions = re.findall(r'@(\w+)', text)
            names.update(mentions)
            
            # Update usage statistics
            sender = msg.get('sender', '')
            for name in names:
                self.name_usage_stats[name]['count'] += 1
                self.name_usage_stats[name]['contexts'].append({
                    'sender': sender,
                    'timestamp': msg.get('timestamp'),
                    'text_snippet': text[:100]
                })
        
        return names

    def _is_likely_name(self, text: str) -> bool:
        """Check if text is likely a person's name"""
        # Common words that are capitalized but not names
        non_names = {
            'The', 'This', 'That', 'These', 'Those', 'What', 'Where', 'When',
            'Why', 'How', 'Yes', 'No', 'Monday', 'Tuesday', 'Wednesday', 
            'Thursday', 'Friday', 'Saturday', 'Sunday', 'January', 'February',
            'March', 'April', 'May', 'June', 'July', 'August', 'September',
            'October', 'November', 'December', 'I', 'You', 'He', 'She', 'It',
            'We', 'They', 'Me', 'Him', 'Her', 'Us', 'Them'
        }
        
        words = text.split()
        
        # Single word checks
        if len(words) == 1:
            return (
                len(text) > 2 and 
                text not in non_names and
                not text.isupper() and  # Avoid acronyms
                text[0].isupper()
            )
        
        # Multi-word checks (likely full names)
        return all(
            word[0].isupper() and word not in non_names 
            for word in words
        )

    def _identify_self_references(self, messages: List[Dict[str, Any]]) -> Dict[str, Set[str]]:
        """Identify when senders refer to themselves by name"""
        self_references = defaultdict(set)
        
        patterns = [
            r"(?:I'm|I am|My name is|Call me|It's|This is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:here|speaking|talking)",
            r"-\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)$",  # Sign-offs
        ]
        
        for msg in messages:
            sender = msg.get('sender', '')
            text = msg.get('text', '')
            
            for pattern in patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    if self._is_likely_name(match):
                        self_references[sender].add(match)
                        self.name_usage_stats[match]['self_references'] += 1
                        
                        # Create high-confidence nickname
                        logger.debug(f"Self-reference detected: {sender} -> {match}")
        
        return self_references

    def _build_cooccurrence_matrix(
        self, 
        messages: List[Dict[str, Any]], 
        names: Set[str]
    ) -> Dict[Tuple[str, str], int]:
        """Build a matrix of how often names appear together"""
        cooccurrence = defaultdict(int)
        
        for msg in messages:
            text = msg.get('text', '')
            mentioned_names = [name for name in names if name in text]
            
            # Count pairs of names that appear in same message
            for i, name1 in enumerate(mentioned_names):
                for name2 in mentioned_names[i+1:]:
                    key = tuple(sorted([name1, name2]))
                    cooccurrence[key] += 1
                    
                    # Update associated names
                    self.name_usage_stats[name1]['associated_names'][name2] += 1
                    self.name_usage_stats[name2]['associated_names'][name1] += 1
        
        return cooccurrence

    def _match_names_to_persons(
        self, 
        names: Set[str], 
        known_persons: List[Person]
    ) -> Dict[str, Person]:
        """Match extracted names to known persons"""
        name_to_person = {}
        
        for name in names:
            best_match = None
            best_score = 0
            
            for person in known_persons:
                # Check exact matches
                all_person_names = person.get_all_names()
                
                for person_name in all_person_names:
                    # Calculate similarity score
                    score = self._calculate_name_similarity(name, person_name)
                    
                    if score > best_score and score >= self.SIMILARITY_THRESHOLD:
                        best_score = score
                        best_match = person
                
                # Check if name matches any existing nicknames
                for nickname in person.nicknames:
                    if nickname.name.lower() == name.lower():
                        best_match = person
                        best_score = 1.0
                        break
            
            if best_match:
                name_to_person[name] = best_match
                logger.debug(f"Matched '{name}' to person '{best_match.full_name}' (score: {best_score:.2f})")
        
        return name_to_person

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two names"""
        name1_lower = name1.lower()
        name2_lower = name2.lower()
        
        # Exact match
        if name1_lower == name2_lower:
            return 1.0
        
        # One name contains the other (e.g., "Bob" in "Bob Smith")
        if name1_lower in name2_lower or name2_lower in name1_lower:
            return 0.9
        
        # Use textdistance if available
        if TEXTDISTANCE_AVAILABLE:
            scores = [
                textdistance.jaro_winkler(name1_lower, name2_lower),
                textdistance.levenshtein.normalized_similarity(name1_lower, name2_lower),
                textdistance.jaccard.normalized_similarity(name1_lower.split(), name2_lower.split())
            ]
            return max(scores)
        else:
            # Simple fallback similarity
            # Check if they share first letters
            if name1_lower[0] == name2_lower[0]:
                return 0.3
            return 0.0

    def _infer_nickname_relationships(
        self,
        name: str,
        all_names: Set[str],
        cooccurrence: Dict[Tuple[str, str], int],
        self_references: Dict[str, Set[str]],
        known_persons: List[Person]
    ) -> List[Dict[str, Any]]:
        """Infer if a name is a nickname and who it belongs to"""
        nickname_relationships = []
        
        # Check if this name is a self-reference
        for sender, refs in self_references.items():
            if name in refs:
                # Try to find the person by sender ID or create new
                person_id = sender  # Use sender as person ID for now
                
                nickname = Nickname(
                    name=name,
                    source=NicknameSource.SELF_REFERENCE,
                    nickname_type=NicknameType.GIVEN,
                    confidence=0.95,  # High confidence for self-references
                    frequency=self.name_usage_stats[name]['count']
                )
                
                nickname_relationships.append({
                    'person_id': person_id,
                    'nickname': nickname
                })
        
        # Check co-occurrence patterns
        stats = self.name_usage_stats[name]
        if stats['associated_names']:
            most_common_associate = stats['associated_names'].most_common(1)[0]
            associate_name, count = most_common_associate
            
            # If names frequently appear together, might be same person
            if count >= 3:  # Threshold for co-occurrence
                # Check if associate is a known person
                for person in known_persons:
                    if associate_name in person.get_all_names():
                        confidence = min(0.7, count * 0.1)  # Cap at 0.7
                        
                        nickname = Nickname(
                            name=name,
                            source=NicknameSource.CONVERSATION,
                            nickname_type=NicknameType.INFERRED,
                            confidence=confidence,
                            frequency=stats['count'],
                            context=f"Often mentioned with {associate_name}"
                        )
                        
                        nickname_relationships.append({
                            'person_id': person.id or person.full_name,
                            'nickname': nickname
                        })
        
        return nickname_relationships

    def _extract_greeting_nicknames(self, messages: List[Dict[str, Any]]) -> Dict[str, List[Nickname]]:
        """Extract nicknames from greeting patterns"""
        greeting_nicknames = defaultdict(list)
        
        greeting_patterns = [
            r"(?:Hey|Hi|Hello|Morning|Evening),?\s+([A-Z][a-z]+)",
            r"(?:Thanks|Thank you|Cheers),?\s+([A-Z][a-z]+)",
            r"(?:Dear|Hi there),?\s+([A-Z][a-z]+)",
        ]
        
        for msg in messages:
            text = msg.get('text', '')
            sender = msg.get('sender', '')
            
            for pattern in greeting_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    if self._is_likely_name(match):
                        # This might be addressing someone
                        nickname = Nickname(
                            name=match,
                            source=NicknameSource.CONVERSATION,
                            nickname_type=NicknameType.SOCIAL,
                            confidence=0.6,
                            frequency=1,
                            context="Used in greeting"
                        )
                        
                        # For now, associate with the message recipient (not sender)
                        # In a real system, you'd need to determine the recipient
                        greeting_nicknames[f"recipient_of_{sender}"].append(nickname)
        
        return greeting_nicknames

    def calculate_confidence_score(
        self,
        name: str,
        usage_count: int,
        self_reference: bool,
        cooccurrence_count: int
    ) -> float:
        """Calculate confidence score for a nickname inference"""
        base_confidence = 0.3
        
        # Boost for self-references
        if self_reference:
            base_confidence = 0.9
        
        # Boost for frequency
        if usage_count > 10:
            base_confidence += 0.2
        elif usage_count > 5:
            base_confidence += 0.1
        
        # Boost for co-occurrence
        if cooccurrence_count > 5:
            base_confidence += 0.15
        elif cooccurrence_count > 2:
            base_confidence += 0.05
        
        return min(1.0, base_confidence)

    def merge_nickname_inferences(
        self,
        existing_nicknames: List[Nickname],
        new_nicknames: List[Nickname]
    ) -> List[Nickname]:
        """Merge new nickname inferences with existing ones"""
        merged = {n.name.lower(): n for n in existing_nicknames}
        
        for new_nick in new_nicknames:
            key = new_nick.name.lower()
            
            if key in merged:
                # Update existing if new confidence is higher
                existing = merged[key]
                if new_nick.confidence > existing.confidence:
                    existing.confidence = new_nick.confidence
                    existing.source = new_nick.source
                
                # Update frequency
                existing.frequency += new_nick.frequency
                existing.last_used = new_nick.last_used or existing.last_used
            else:
                merged[key] = new_nick
        
        return list(merged.values())
