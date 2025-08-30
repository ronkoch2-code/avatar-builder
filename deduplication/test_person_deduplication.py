"""
Unit tests for person entity deduplication functionality.

Tests cover:
- Entity matching algorithms
- Merge operations
- Mapping preservation
- Configuration validation
- Error handling

Run with: python3 -m pytest test_person_deduplication.py -v
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import uuid
from datetime import datetime

# Import our modules
from person_entity_deduplication import (
    PersonEntity, MergeCandidate, PersonEntityMatcher, 
    PersonEntityMerger, PersonDeduplicationEngine
)
from deduplication_config import DeduplicationConfig, get_config


class TestPersonEntity:
    """Test PersonEntity data class."""
    
    def test_person_entity_creation(self):
        """Test basic PersonEntity creation."""
        entity = PersonEntity(
            node_id="test_123",
            name="John Doe",
            email="john@example.com"
        )
        
        assert entity.node_id == "test_123"
        assert entity.name == "John Doe"
        assert entity.email == "john@example.com"
        assert entity.properties == {}
        assert entity.relationships == set()
    
    def test_person_entity_with_properties(self):
        """Test PersonEntity with additional properties."""
        properties = {"age": 30, "city": "New York"}
        relationships = {"WORKS_FOR", "KNOWS"}
        
        entity = PersonEntity(
            node_id="test_456",
            name="Jane Smith",
            properties=properties,
            relationships=relationships
        )
        
        assert entity.properties == properties
        assert entity.relationships == relationships


class TestMergeCandidate:
    """Test MergeCandidate data class."""
    
    def test_merge_candidate_creation(self):
        """Test basic MergeCandidate creation."""
        entity1 = PersonEntity("1", "John Doe")
        entity2 = PersonEntity("2", "John D. Doe")
        
        candidate = MergeCandidate(
            entity1=entity1,
            entity2=entity2,
            confidence_score=0.85,
            match_reasons=["name_similarity_0.85"]
        )
        
        assert candidate.confidence_score == 0.85
        assert candidate.match_reasons == ["name_similarity_0.85"]
    
    def test_high_confidence_property(self):
        """Test high confidence property calculation."""
        entity1 = PersonEntity("1", "John Doe")
        entity2 = PersonEntity("2", "John D. Doe")
        
        # High confidence candidate
        high_confidence = MergeCandidate(
            entity1, entity2, 0.9, ["name_similarity"]
        )
        assert high_confidence.is_high_confidence is True
        
        # Low confidence candidate
        low_confidence = MergeCandidate(
            entity1, entity2, 0.7, ["name_similarity"]
        )
        assert low_confidence.is_high_confidence is False


class TestPersonEntityMatcher:
    """Test PersonEntityMatcher functionality."""
    
    @pytest.fixture
    def mock_driver(self):
        """Create a mock Neo4j driver."""
        driver = Mock()
        session = Mock()
        driver.session.return_value.__enter__.return_value = session
        return driver, session
    
    @pytest.fixture
    def matcher(self, mock_driver):
        """Create a PersonEntityMatcher with mocked driver."""
        driver, _ = mock_driver
        return PersonEntityMatcher(driver)
    
    def test_name_similarity_matching(self, matcher):
        """Test name similarity matching logic."""
        entity1 = PersonEntity("1", "John Doe", "john@example.com")
        entity2 = PersonEntity("2", "John D. Doe", "john@example.com")
        
        candidate = matcher._evaluate_match(entity1, entity2)
        
        assert candidate is not None
        assert candidate.confidence_score > 0.8
        assert any("name_similarity" in reason for reason in candidate.match_reasons)
        assert any("email_exact_match" in reason for reason in candidate.match_reasons)
    
    def test_no_match_for_different_entities(self, matcher):
        """Test that different entities don't match."""
        entity1 = PersonEntity("1", "John Doe", "john@example.com")
        entity2 = PersonEntity("2", "Mary Smith", "mary@example.com")
        
        candidate = matcher._evaluate_match(entity1, entity2)
        
        # Should be None or very low confidence
        assert candidate is None or candidate.confidence_score < 0.6
    
    def test_exact_email_match_high_score(self, matcher):
        """Test that exact email matches get high scores."""
        entity1 = PersonEntity("1", "J. Doe", "john.doe@company.com")
        entity2 = PersonEntity("2", "John Doe", "john.doe@company.com")
        
        candidate = matcher._evaluate_match(entity1, entity2)
        
        assert candidate is not None
        assert candidate.confidence_score > 0.8
        assert "email_exact_match" in candidate.match_reasons
    
    def test_relationship_similarity_calculation(self, matcher):
        """Test relationship similarity calculation."""
        entity1 = PersonEntity("1", "John", relationships={"WORKS_FOR", "KNOWS", "FRIEND_OF"})
        entity2 = PersonEntity("2", "John", relationships={"WORKS_FOR", "KNOWS", "FAMILY_OF"})
        
        similarity = matcher._calculate_relationship_similarity(entity1, entity2)
        
        # Should be 2/4 = 0.5 (2 shared, 4 total unique)
        assert abs(similarity - 0.5) < 0.01
    
    @patch('person_entity_deduplication.PersonEntityMatcher._get_all_person_entities')
    def test_find_potential_duplicates(self, mock_get_entities, matcher):
        """Test finding potential duplicates."""
        # Mock entities
        entities = [
            PersonEntity("1", "John Doe", "john@example.com"),
            PersonEntity("2", "John D. Doe", "john@example.com"),
            PersonEntity("3", "Mary Smith", "mary@example.com")
        ]
        mock_get_entities.return_value = entities
        
        candidates = matcher.find_potential_duplicates()
        
        # Should find one high-confidence match between John Doe entities
        assert len(candidates) >= 1
        high_confidence_candidates = [c for c in candidates if c.is_high_confidence]
        assert len(high_confidence_candidates) >= 1


class TestPersonEntityMerger:
    """Test PersonEntityMerger functionality."""
    
    @pytest.fixture
    def mock_driver(self):
        """Create a mock Neo4j driver with transaction support."""
        driver = Mock()
        session = Mock()
        transaction = Mock()
        
        driver.session.return_value.__enter__.return_value = session
        session.begin_transaction.return_value.__enter__.return_value = transaction
        
        return driver, session, transaction
    
    @pytest.fixture
    def merger(self, mock_driver):
        """Create a PersonEntityMerger with mocked driver."""
        driver, _, _ = mock_driver
        return PersonEntityMerger(driver)
    
    def test_canonical_entity_selection(self, merger):
        """Test selection of canonical entity during merge."""
        # Entity with email should be preferred
        entity_with_email = PersonEntity("1", "John Doe", "john@example.com")
        entity_without_email = PersonEntity("2", "John D. Doe")
        
        canonical = merger._select_canonical_entity(entity_with_email, entity_without_email)
        assert canonical == entity_with_email
        
        # Entity with more properties should be preferred
        entity_more_props = PersonEntity("3", "Jane", properties={"age": 30, "city": "NYC", "phone": "123"})
        entity_fewer_props = PersonEntity("4", "Jane", properties={"age": 30})
        
        canonical = merger._select_canonical_entity(entity_more_props, entity_fewer_props)
        assert canonical == entity_more_props
    
    @patch('person_entity_deduplication.uuid.uuid4')
    def test_merge_entities(self, mock_uuid, merger, mock_driver):
        """Test complete entity merge process."""
        driver, session, transaction = mock_driver
        mock_uuid.return_value = uuid.UUID('12345678-1234-5678-1234-567812345678')
        
        # Create merge candidate
        entity1 = PersonEntity("1", "John Doe", "john@example.com")
        entity2 = PersonEntity("2", "John D. Doe", properties={"age": 30})
        candidate = MergeCandidate(entity1, entity2, 0.9, ["name_similarity"])
        
        # Mock transaction methods
        transaction.run = Mock()
        transaction.commit = Mock()
        
        # Perform merge
        result_id = merger.merge_entities(candidate)
        
        # Verify transaction was used
        assert transaction.run.called
        assert transaction.commit.called
        assert result_id == entity1.node_id  # Should return canonical entity ID


class TestDeduplicationConfig:
    """Test configuration management."""
    
    def test_config_validation_success(self):
        """Test successful configuration validation."""
        issues = DeduplicationConfig.validate_config()
        assert len(issues) == 0
    
    def test_config_validation_with_invalid_thresholds(self):
        """Test configuration validation with invalid values."""
        # Temporarily modify config for testing
        original_threshold = DeduplicationConfig.NAME_SIMILARITY_THRESHOLD
        DeduplicationConfig.NAME_SIMILARITY_THRESHOLD = 1.5  # Invalid value
        
        try:
            issues = DeduplicationConfig.validate_config()
            assert len(issues) > 0
            assert any("NAME_SIMILARITY_THRESHOLD" in issue for issue in issues)
        finally:
            # Restore original value
            DeduplicationConfig.NAME_SIMILARITY_THRESHOLD = original_threshold
    
    def test_get_matching_config(self):
        """Test getting matching configuration dictionary."""
        config = DeduplicationConfig.get_matching_config()
        
        assert isinstance(config, dict)
        assert 'name_threshold' in config
        assert 'auto_merge_threshold' in config
        assert 'min_confidence' in config
    
    def test_environment_specific_config(self):
        """Test environment-specific configurations."""
        dev_config = get_config('development')
        prod_config = get_config('production')
        
        # Development should be more verbose
        assert dev_config.LOG_LEVEL == "DEBUG"
        assert dev_config.INTERACTIVE_MODE is True
        
        # Production should be more conservative
        assert prod_config.AUTO_MERGE_THRESHOLD >= 0.95
        assert prod_config.LOG_LEVEL == "INFO"


class TestPersonDeduplicationEngine:
    """Test the main deduplication engine."""
    
    @pytest.fixture
    def mock_driver(self):
        """Create a comprehensive mock driver."""
        driver = Mock()
        session = Mock()
        driver.session.return_value.__enter__.return_value = session
        return driver, session
    
    @pytest.fixture
    def engine(self, mock_driver):
        """Create engine with mocked dependencies."""
        driver, _ = mock_driver
        with patch('person_entity_deduplication.GraphDatabase.driver', return_value=driver):
            engine = PersonDeduplicationEngine("bolt://test", "user", "pass")
            return engine
    
    def test_engine_initialization(self, engine):
        """Test engine initializes correctly."""
        assert engine.matcher is not None
        assert engine.merger is not None
        assert engine.driver is not None
    
    @patch('person_entity_deduplication.PersonEntityMatcher.find_potential_duplicates')
    @patch('person_entity_deduplication.PersonEntityMerger.merge_entities')
    def test_run_deduplication_no_candidates(self, mock_merge, mock_find, engine):
        """Test deduplication with no candidates found."""
        mock_find.return_value = []
        
        result = engine.run_deduplication()
        
        assert result['status'] == 'completed'
        assert result['merges_performed'] == 0
        assert result['candidates_found'] == 0
        assert not mock_merge.called
    
    @patch('person_entity_deduplication.PersonEntityMatcher.find_potential_duplicates')
    @patch('person_entity_deduplication.PersonEntityMerger.merge_entities')
    def test_run_deduplication_with_auto_merge(self, mock_merge, mock_find, engine):
        """Test deduplication with automatic merges."""
        # Create high-confidence candidate
        entity1 = PersonEntity("1", "John Doe")
        entity2 = PersonEntity("2", "John D. Doe")
        candidate = MergeCandidate(entity1, entity2, 0.95, ["high_confidence"])
        
        mock_find.return_value = [candidate]
        mock_merge.return_value = "1"  # Return canonical entity ID
        
        result = engine.run_deduplication(auto_merge_threshold=0.9)
        
        assert result['status'] == 'completed'
        assert result['auto_merges'] == 1
        assert result['candidates_found'] == 1
        assert mock_merge.called
    
    def test_get_mapping_by_original_id(self, engine, mock_driver):
        """Test retrieval of canonical ID by original ID."""
        driver, session = mock_driver
        
        # Mock session.run to return a mapping record
        mock_result = Mock()
        mock_record = Mock()
        mock_record.__getitem__.return_value = "canonical_123"
        mock_result.single.return_value = mock_record
        session.run.return_value = mock_result
        
        canonical_id = engine.get_mapping_by_original_id("original_123")
        
        assert canonical_id == "canonical_123"
        assert session.run.called


class TestIntegrationScenarios:
    """Integration tests for realistic scenarios."""
    
    @pytest.fixture
    def sample_entities(self):
        """Create sample entities for testing."""
        return [
            PersonEntity("1", "John Doe", "john.doe@company.com", 
                        properties={"age": 35, "city": "New York"}),
            PersonEntity("2", "John D. Doe", "john.doe@company.com", 
                        properties={"phone": "555-1234"}),
            PersonEntity("3", "J. Doe", "j.doe@personal.com", 
                        properties={"age": 35, "city": "New York"}),
            PersonEntity("4", "Mary Smith", "mary@example.com", 
                        properties={"age": 28, "city": "Boston"}),
            PersonEntity("5", "Robert Johnson", "bob@company.com", 
                        properties={"nickname": "Bob"})
        ]
    
    def test_scenario_exact_email_different_names(self, sample_entities):
        """Test scenario where entities have same email but different name formats."""
        # Entities 1 and 2 have same email
        entity1, entity2 = sample_entities[0], sample_entities[1]
        
        driver = Mock()
        matcher = PersonEntityMatcher(driver)
        
        candidate = matcher._evaluate_match(entity1, entity2)
        
        assert candidate is not None
        assert candidate.confidence_score > 0.8
        assert "email_exact_match" in candidate.match_reasons
    
    def test_scenario_similar_info_different_emails(self, sample_entities):
        """Test scenario where entities have similar info but different emails."""
        # Entities 1 and 3 have same age/city but different emails
        entity1, entity3 = sample_entities[0], sample_entities[2]
        
        driver = Mock()
        matcher = PersonEntityMatcher(driver)
        
        candidate = matcher._evaluate_match(entity1, entity3)
        
        # Should still match due to name similarity and shared properties
        assert candidate is not None
        # But confidence should be lower than exact email match
        assert candidate.confidence_score > 0.6


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
