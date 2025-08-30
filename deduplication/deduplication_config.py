"""
Configuration settings for person entity deduplication.

This module contains all configurable parameters for the deduplication process,
allowing for easy tuning without code changes.
"""

import os
from typing import Dict, List


class DeduplicationConfig:
    """Configuration class for person entity deduplication parameters."""
    
    # Database Configuration
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
    
    # Matching Thresholds
    NAME_SIMILARITY_THRESHOLD = 0.8
    AUTO_MERGE_THRESHOLD = 0.9
    MINIMUM_CONFIDENCE_THRESHOLD = 0.6
    
    # Matching Weights
    NAME_MATCH_WEIGHT = 0.7
    EMAIL_EXACT_MATCH_WEIGHT = 0.9
    RELATIONSHIP_SIMILARITY_WEIGHT = 0.3
    
    # Fuzzy Matching Configuration
    FUZZY_MATCHING_ALGORITHMS = [
        'ratio',           # Basic similarity
        'partial_ratio',   # Partial string matching
        'token_sort_ratio', # Token-based sorting
        'token_set_ratio'   # Token-based sets
    ]
    
    # Property Merge Rules
    PROPERTY_MERGE_STRATEGY = {
        # How to handle conflicting properties during merge
        'name': 'prefer_longer',           # Keep the longer name
        'email': 'prefer_non_null',        # Keep the non-null email
        'phone': 'prefer_non_null',        # Keep the non-null phone
        'address': 'prefer_most_complete', # Keep most complete address
        'bio': 'concatenate',              # Combine biographies
        'created_date': 'prefer_earlier',  # Keep earlier creation date
        'last_updated': 'prefer_later'     # Keep later update date
    }
    
    # Relationship Handling
    RELATIONSHIP_MERGE_RULES = {
        'WORKS_FOR': 'consolidate_duplicates',  # Remove duplicate work relationships
        'KNOWS': 'consolidate_duplicates',      # Remove duplicate knows relationships
        'FAMILY_OF': 'preserve_all',            # Keep all family relationships
        'MENTOR_OF': 'preserve_all',            # Keep all mentor relationships
        'FRIEND_OF': 'consolidate_duplicates'   # Remove duplicate friendships
    }
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = "person_deduplication.log"
    
    # Performance Settings
    BATCH_SIZE = 1000  # Number of entities to process in each batch
    MAX_COMPARISON_PAIRS = 10000  # Maximum number of entity pairs to compare
    
    # Interactive Mode Settings
    INTERACTIVE_MODE = True
    REQUIRE_USER_CONFIRMATION_FOR_HIGH_CONFIDENCE = False
    SHOW_DETAILED_MATCH_REASONS = True
    
    # Backup and Recovery
    CREATE_BACKUP_BEFORE_MERGE = True
    BACKUP_RETENTION_DAYS = 30
    
    # Audit and Tracking
    ENABLE_DETAILED_AUDIT_LOG = True
    TRACK_MERGE_STATISTICS = True
    
    # Advanced Matching Features
    USE_PHONETIC_MATCHING = True  # Use Soundex/Metaphone for name matching
    USE_NICKNAME_EXPANSION = True  # Expand nicknames (Bob -> Robert)
    USE_CONTEXTUAL_MATCHING = True  # Consider relationship context
    
    # Nickname mappings for name normalization
    NICKNAME_MAPPINGS = {
        'bob': 'robert',
        'rob': 'robert',
        'bobby': 'robert',
        'bill': 'william',
        'billy': 'william',
        'will': 'william',
        'willie': 'william',
        'dick': 'richard',
        'rick': 'richard',
        'richie': 'richard',
        'mike': 'michael',
        'mickey': 'michael',
        'mick': 'michael',
        'jim': 'james',
        'jimmy': 'james',
        'jamie': 'james',
        'tom': 'thomas',
        'tommy': 'thomas',
        'dave': 'david',
        'davie': 'david',
        'dan': 'daniel',
        'danny': 'daniel',
        'chris': 'christopher',
        'steve': 'stephen',
        'stevie': 'stephen',
        'matt': 'matthew',
        'tony': 'anthony',
        'joe': 'joseph',
        'joey': 'joseph'
    }
    
    @classmethod
    def get_matching_config(cls) -> Dict:
        """Returns matching configuration as a dictionary."""
        return {
            'name_threshold': cls.NAME_SIMILARITY_THRESHOLD,
            'auto_merge_threshold': cls.AUTO_MERGE_THRESHOLD,
            'min_confidence': cls.MINIMUM_CONFIDENCE_THRESHOLD,
            'name_weight': cls.NAME_MATCH_WEIGHT,
            'email_weight': cls.EMAIL_EXACT_MATCH_WEIGHT,
            'relationship_weight': cls.RELATIONSHIP_SIMILARITY_WEIGHT,
            'use_phonetic': cls.USE_PHONETIC_MATCHING,
            'use_nicknames': cls.USE_NICKNAME_EXPANSION,
            'use_context': cls.USE_CONTEXTUAL_MATCHING
        }
    
    @classmethod
    def get_database_config(cls) -> Dict:
        """Returns database configuration as a dictionary."""
        return {
            'uri': cls.NEO4J_URI,
            'user': cls.NEO4J_USER,
            'password': cls.NEO4J_PASSWORD
        }
    
    @classmethod
    def validate_config(cls) -> List[str]:
        """
        Validates configuration settings and returns list of issues found.
        
        Returns:
            List[str]: List of configuration validation errors
        """
        issues = []
        
        # Check thresholds are in valid range
        if not 0 <= cls.NAME_SIMILARITY_THRESHOLD <= 1:
            issues.append("NAME_SIMILARITY_THRESHOLD must be between 0 and 1")
        
        if not 0 <= cls.AUTO_MERGE_THRESHOLD <= 1:
            issues.append("AUTO_MERGE_THRESHOLD must be between 0 and 1")
        
        if not 0 <= cls.MINIMUM_CONFIDENCE_THRESHOLD <= 1:
            issues.append("MINIMUM_CONFIDENCE_THRESHOLD must be between 0 and 1")
        
        # Check that auto merge threshold is higher than minimum confidence
        if cls.AUTO_MERGE_THRESHOLD <= cls.MINIMUM_CONFIDENCE_THRESHOLD:
            issues.append("AUTO_MERGE_THRESHOLD should be higher than MINIMUM_CONFIDENCE_THRESHOLD")
        
        # Check weights sum to reasonable values
        total_weight = cls.NAME_MATCH_WEIGHT + cls.EMAIL_EXACT_MATCH_WEIGHT + cls.RELATIONSHIP_SIMILARITY_WEIGHT
        if total_weight > 2.0:  # Allow some flexibility for overlapping matches
            issues.append("Combined matching weights exceed reasonable threshold (2.0)")
        
        # Check batch size is reasonable
        if cls.BATCH_SIZE <= 0:
            issues.append("BATCH_SIZE must be positive")
        
        if cls.BATCH_SIZE > 10000:
            issues.append("BATCH_SIZE is very large and may cause memory issues")
        
        return issues


# Environment-specific configurations
class DevelopmentConfig(DeduplicationConfig):
    """Development environment configuration."""
    LOG_LEVEL = "DEBUG"
    INTERACTIVE_MODE = True
    CREATE_BACKUP_BEFORE_MERGE = True
    ENABLE_DETAILED_AUDIT_LOG = True


class ProductionConfig(DeduplicationConfig):
    """Production environment configuration."""
    LOG_LEVEL = "INFO"
    INTERACTIVE_MODE = False
    AUTO_MERGE_THRESHOLD = 0.95  # Higher threshold for production
    CREATE_BACKUP_BEFORE_MERGE = True
    ENABLE_DETAILED_AUDIT_LOG = True
    BATCH_SIZE = 500  # Smaller batches for production stability


class TestingConfig(DeduplicationConfig):
    """Testing environment configuration."""
    LOG_LEVEL = "WARNING"
    INTERACTIVE_MODE = False
    CREATE_BACKUP_BEFORE_MERGE = False
    ENABLE_DETAILED_AUDIT_LOG = False
    BATCH_SIZE = 100


# Configuration factory
def get_config(environment: str = None) -> DeduplicationConfig:
    """
    Factory function to get appropriate configuration based on environment.
    
    Args:
        environment: Environment name ('development', 'production', 'testing')
        
    Returns:
        DeduplicationConfig: Appropriate configuration class
    """
    if environment is None:
        environment = os.getenv('AVATAR_ENGINE_ENV', 'development')
    
    config_map = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig
    }
    
    return config_map.get(environment.lower(), DeduplicationConfig)()
