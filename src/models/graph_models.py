"""
Graph database models for Avatar-Engine
Handles Person and Nickname entities with Neo4j relationships
Last Updated: September 29, 2025
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from loguru import logger


class NicknameSource(str, Enum):
    """Source of nickname identification"""
    ADDRESS_BOOK = "addressbook"
    CONVERSATION = "conversation"
    SELF_REFERENCE = "self_reference"
    MANUAL = "manual"
    INFERRED = "inferred"


class NicknameType(str, Enum):
    """Types of nicknames"""
    GIVEN = "given"           # Explicitly given nickname
    DIMINUTIVE = "diminutive" # Shortened version (Alex from Alexander)
    FORMAL = "formal"         # Formal version (Robert from Bob)
    INITIALS = "initials"     # Initial-based (JS from John Smith)
    CULTURAL = "cultural"     # Cultural variations
    PROFESSIONAL = "professional"  # Work-related names
    FAMILY = "family"         # Family nicknames
    SOCIAL = "social"         # Social media handles


class Nickname(BaseModel):
    """Nickname entity model"""
    name: str = Field(..., description="The actual nickname")
    source: NicknameSource = Field(..., description="Where the nickname came from")
    nickname_type: Optional[NicknameType] = Field(None, description="Type of nickname")
    confidence: float = Field(
        1.0, 
        ge=0.0, 
        le=1.0, 
        description="Confidence score for inferred nicknames"
    )
    first_seen: datetime = Field(
        default_factory=datetime.now,
        description="When nickname was first encountered"
    )
    last_used: Optional[datetime] = Field(
        None,
        description="Most recent usage in conversations"
    )
    frequency: int = Field(0, description="Usage count in conversations")
    context: Optional[str] = Field(None, description="Context where nickname is used")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator('name')
    def validate_name(cls, v):
        """Ensure nickname is not empty and properly formatted"""
        if not v or not v.strip():
            raise ValueError("Nickname cannot be empty")
        return v.strip()

    def to_neo4j_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Neo4j node creation"""
        return {
            "name": self.name,
            "source": self.source.value,
            "nickname_type": self.nickname_type.value if self.nickname_type else None,
            "confidence": self.confidence,
            "first_seen": self.first_seen.isoformat(),
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "frequency": self.frequency,
            "context": self.context,
            "metadata": str(self.metadata) if self.metadata else None
        }


class Person(BaseModel):
    """Person entity model with nickname relationships"""
    id: Optional[str] = Field(None, description="Unique identifier")
    full_name: str = Field(..., description="Full legal name")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    middle_name: Optional[str] = Field(None, description="Middle name")
    
    # Contact information
    email: Optional[List[str]] = Field(default_factory=list)
    phone: Optional[List[str]] = Field(default_factory=list)
    
    # Nicknames
    nicknames: List[Nickname] = Field(
        default_factory=list,
        description="List of associated nicknames"
    )
    primary_nickname: Optional[str] = Field(
        None,
        description="Most commonly used nickname"
    )
    
    # Additional metadata
    organization: Optional[str] = Field(None)
    job_title: Optional[str] = Field(None)
    address_book_id: Optional[str] = Field(None, description="ID from Address Book")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Relationships tracking
    relationships: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Related persons and relationship types"
    )

    @validator('full_name')
    def validate_full_name(cls, v):
        """Ensure full name is not empty"""
        if not v or not v.strip():
            raise ValueError("Full name cannot be empty")
        return v.strip()

    def add_nickname(self, nickname: Nickname) -> None:
        """Add a nickname to the person"""
        # Check for duplicates
        existing = next(
            (n for n in self.nicknames if n.name.lower() == nickname.name.lower()),
            None
        )
        
        if existing:
            # Update existing nickname if confidence is higher
            if nickname.confidence > existing.confidence:
                existing.confidence = nickname.confidence
                existing.last_used = nickname.last_used or existing.last_used
                existing.frequency += 1
                logger.debug(f"Updated existing nickname '{nickname.name}' for {self.full_name}")
        else:
            self.nicknames.append(nickname)
            logger.debug(f"Added new nickname '{nickname.name}' for {self.full_name}")
            
        # Update primary nickname if needed
        self._update_primary_nickname()
    
    def _update_primary_nickname(self) -> None:
        """Update primary nickname based on frequency and confidence"""
        if not self.nicknames:
            self.primary_nickname = None
            return
            
        # Sort by frequency and confidence
        sorted_nicknames = sorted(
            self.nicknames,
            key=lambda n: (n.frequency, n.confidence),
            reverse=True
        )
        
        self.primary_nickname = sorted_nicknames[0].name
    
    def get_all_names(self) -> List[str]:
        """Get all names associated with this person"""
        names = [self.full_name]
        
        if self.first_name:
            names.append(self.first_name)
        if self.last_name:
            names.append(self.last_name)
            
        names.extend([n.name for n in self.nicknames])
        
        return list(set(names))  # Remove duplicates
    
    def to_neo4j_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Neo4j node creation"""
        return {
            "id": self.id,
            "full_name": self.full_name,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "middle_name": self.middle_name,
            "email": self.email,
            "phone": self.phone,
            "primary_nickname": self.primary_nickname,
            "organization": self.organization,
            "job_title": self.job_title,
            "address_book_id": self.address_book_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class NicknameRelationship(BaseModel):
    """Represents the KNOWN_AS relationship between Person and Nickname"""
    person_id: str
    nickname_name: str
    relationship_type: str = "KNOWN_AS"
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def to_neo4j_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Neo4j relationship creation"""
        return {
            "created_at": self.created_at.isoformat(),
            "metadata": str(self.metadata) if self.metadata else None
        }
