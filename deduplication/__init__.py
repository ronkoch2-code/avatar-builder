"""
Person Entity Deduplication Package

This package provides comprehensive functionality for identifying, merging,
and tracking duplicate person entities in Neo4j knowledge graphs.

Main modules:
- person_entity_deduplication: Core deduplication logic
- deduplication_config: Configuration management
- deduplication_cli: Command-line interface

Usage:
    from deduplication import PersonDeduplicationEngine
    engine = PersonDeduplicationEngine(uri, user, password)
    results = engine.run_deduplication()
"""

from .person_entity_deduplication import (
    PersonEntity,
    MergeCandidate, 
    PersonEntityMatcher,
    PersonEntityMerger,
    PersonDeduplicationEngine
)

from .deduplication_config import (
    DeduplicationConfig,
    DevelopmentConfig,
    ProductionConfig,
    TestingConfig,
    get_config
)

__version__ = "1.0.0"
__author__ = "Avatar-Engine Project"

# Module-level convenience functions
def create_engine(environment='development'):
    """Create a deduplication engine with environment-specific config."""
    config = get_config(environment)
    db_config = config.get_database_config()
    
    return PersonDeduplicationEngine(
        db_config['uri'],
        db_config['user'], 
        db_config['password']
    )

def quick_deduplication(environment='development', interactive=True):
    """Run a quick deduplication with default settings."""
    engine = create_engine(environment)
    try:
        return engine.run_deduplication(interactive_mode=interactive)
    finally:
        engine.close()
