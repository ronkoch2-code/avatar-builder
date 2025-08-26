#!/usr/bin/env python3
"""
Test Avatar System Deployment - FIXED
=====================================

Fixed tests for avatar system deployment and functionality.
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from avatar_system_deployment import AvatarSystemDeployment
    from avatar_intelligence_pipeline import AvatarSystemManager, NicknameDetector, LinguisticAnalyzer
except ImportError as e:
    pytest.skip(f"Could not import modules: {e}", allow_module_level=True)


class TestAvatarSystemDeployment:
    """Test avatar system deployment"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_driver = MagicMock()
        self.mock_session = MagicMock()
        
        # Mock the session context manager properly
        self.mock_driver.session.return_value = self.mock_session
        self.mock_session.__enter__.return_value = self.mock_session
        self.mock_session.__exit__.return_value = None
        
        # Create deployment with mocked driver
        with patch('neo4j.GraphDatabase.driver') as mock_graph_db:
            mock_graph_db.return_value = self.mock_driver
            self.deployment = AvatarSystemDeployment("bolt://localhost:7687", "neo4j", "password")
    
    def test_initialization(self):
        """Test deployment initialization"""
        assert self.deployment.system_version == "1.0"
        assert isinstance(self.deployment.deployment_date, datetime)
    
    def test_verify_deployment_success(self):
        """Test successful deployment verification"""
        # Mock successful system check
        self.mock_session.run.return_value.single.return_value = {'status': 'active'}
        
        result = self.deployment._verify_deployment()
        assert result is True
    
    def test_verify_deployment_failure(self):
        """Test failed deployment verification"""
        # Mock failed system check
        self.mock_session.run.return_value.single.return_value = None
        
        result = self.deployment._verify_deployment()
        assert result is False
    
    def test_system_status(self):
        """Test system status reporting"""
        # Mock the two queries that get_system_status makes
        profile_result = Mock()
        profile_result.__getitem__ = Mock(side_effect=lambda key: {
            'total': 5, 'active': 4
        }.get(key))
        
        artifact_result = Mock()
        artifact_result.__getitem__ = Mock(side_effect=lambda key: {
            'totalArtifacts': 15
        }.get(key))
        
        # Mock the session.run calls in sequence
        self.mock_session.run.side_effect = [
            Mock(single=Mock(return_value=profile_result)),
            Mock(single=Mock(return_value=artifact_result))
        ]
        
        status = self.deployment.get_system_status()
        
        assert 'total_profiles' in status
        assert 'active_profiles' in status  
        assert 'system_version' in status
        assert status['system_version'] == "1.0"


class TestNicknameDetector:
    """Test nickname detection functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.detector = NicknameDetector()
    
    def test_nickname_extraction(self):
        """Test basic nickname extraction"""
        messages = [
            {'body': 'Hey honey, how are you doing?'},
            {'body': 'Thanks babe for the help'},
            {'body': 'Good morning beautiful'},
            {'body': 'Hey beautiful, ready for dinner?'}
        ]
        
        nicknames = self.detector.extract_nicknames(messages, "John")
        
        # Should detect repeated nicknames
        assert 'beautiful' in nicknames
        assert nicknames['beautiful'] >= 2
    
    def test_nickname_filtering(self):
        """Test nickname filtering rules"""
        messages = [
            {'body': 'Hey you, how are things?'},  # Should be filtered out
            {'body': 'Thanks a for help'},  # Single character, should be filtered
            {'body': 'Hello supercalifragilisticexpialidocious person'}  # Too long
        ]
        
        nicknames = self.detector.extract_nicknames(messages, "John")
        
        # Should not contain filtered nicknames
        assert 'you' not in nicknames
        assert 'a' not in nicknames
        assert 'supercalifragilisticexpialidocious' not in nicknames
    
    def test_empty_messages(self):
        """Test handling of empty messages"""
        messages = []
        nicknames = self.detector.extract_nicknames(messages, "John")
        assert nicknames == {}
        
        messages = [{'body': None}, {'body': ''}]
        nicknames = self.detector.extract_nicknames(messages, "John")
        assert nicknames == {}


class TestLinguisticAnalyzer:
    """Test linguistic analysis functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.analyzer = LinguisticAnalyzer()
    
    def test_message_patterns_analysis(self):
        """Test message pattern analysis"""
        messages = [
            {'body': 'Short msg'},
            {'body': 'This is a much longer message with more content to analyze'},
            {'body': 'Medium length message here'}
        ]
        
        analysis = self.analyzer.analyze_communication_style(messages)
        
        assert 'message_patterns' in analysis
        patterns = analysis['message_patterns']
        assert patterns['total_messages'] == 3
        assert patterns['avg_message_length'] > 0
        assert 'response_style' in patterns
    
    def test_linguistic_features_analysis(self):
        """Test linguistic feature detection"""
        messages = [
            {'body': 'This is amazing! I love it!'},
            {'body': 'Are you sure about that?'},
            {'body': 'thanks so much for your help'}
        ]
        
        analysis = self.analyzer.analyze_communication_style(messages)
        
        assert 'linguistic_features' in analysis
        features = analysis['linguistic_features']
        assert features['exclamation_usage'] > 0  # Should detect exclamations
        assert features['question_usage'] > 0     # Should detect questions
    
    def test_emotional_expressions(self):
        """Test emotional expression detection"""
        messages = [
            {'body': 'I love this amazing food!'},
            {'body': 'Thanks for your help, appreciate it'},
            {'body': 'Haha that was funny lol'}
        ]
        
        analysis = self.analyzer.analyze_communication_style(messages)
        
        emotions = analysis['emotional_expressions']
        assert 'affection' in emotions or 'gratitude' in emotions or 'humor' in emotions
    
    def test_empty_messages_handling(self):
        """Test handling of empty message list"""
        messages = []
        analysis = self.analyzer.analyze_communication_style(messages)
        
        assert analysis['message_patterns']['total_messages'] == 0
        assert analysis['message_patterns']['avg_message_length'] == 0
        assert analysis['emotional_expressions'] == {}


class TestAvatarSystemManager:
    """Test main avatar system manager"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_driver = MagicMock()
        self.mock_session = MagicMock()
        
        # Mock the session context manager properly
        self.mock_driver.session.return_value = self.mock_session
        self.mock_session.__enter__.return_value = self.mock_session
        self.mock_session.__exit__.return_value = None
        
        self.manager = AvatarSystemManager(self.mock_driver)
    
    def test_initialization(self):
        """Test manager initialization"""
        assert self.manager.driver == self.mock_driver
        assert hasattr(self.manager, 'nickname_detector')
        assert hasattr(self.manager, 'relationship_inferrer')
        assert hasattr(self.manager, 'linguistic_analyzer')
    
    def test_generate_response_no_profile(self):
        """Test response generation when no profile exists"""
        # Mock no profile found
        self.mock_session.run.return_value.single.return_value = None
        
        response = self.manager.generate_response("NonexistentPerson")
        
        assert "Error" in response
        assert "not found" in response.lower()
    
    def test_format_formality(self):
        """Test formality score formatting"""
        assert self.manager._format_formality(0.8) == "formal"
        assert self.manager._format_formality(0.5) == "moderate"
        assert self.manager._format_formality(0.2) == "casual/informal"
    
    def test_get_system_stats(self):
        """Test system statistics retrieval"""
        # Mock database response
        mock_result = {
            'profiles': 10,
            'relationships': 25, 
            'phrases': 50,
            'avgMessages': 75.5
        }
        
        self.mock_session.run.return_value.single.return_value = mock_result
        
        stats = self.manager.get_system_stats()
        
        assert 'total_profiles' in stats
        assert 'system_status' in stats
        assert stats['total_profiles'] == 10


# Simple unit tests that don't require Neo4j
class TestUtilityFunctions:
    """Test utility functions independently"""
    
    def test_nickname_detector_common_nicknames(self):
        """Test that common nicknames are properly defined"""
        detector = NicknameDetector()
        assert 'mom' in detector.common_nicknames
        assert 'dad' in detector.common_nicknames
        assert 'babe' in detector.common_nicknames
    
    def test_linguistic_analyzer_empty_style_analysis(self):
        """Test empty style analysis structure"""
        analyzer = LinguisticAnalyzer()
        empty_analysis = analyzer._empty_style_analysis()
        
        assert 'message_patterns' in empty_analysis
        assert 'linguistic_features' in empty_analysis
        assert 'emotional_expressions' in empty_analysis
        assert empty_analysis['message_patterns']['total_messages'] == 0


@pytest.mark.integration
class TestSystemIntegration:
    """Integration tests requiring actual Neo4j connection"""
    
    @pytest.mark.skip(reason="Requires Neo4j connection")
    def test_full_system_deployment(self):
        """Test complete system deployment (requires Neo4j)"""
        # This would test actual deployment against Neo4j
        # Skipped by default as it requires external dependencies
        pass
    
    @pytest.mark.skip(reason="Requires Neo4j connection and data")
    def test_profile_initialization(self):
        """Test avatar profile initialization (requires Neo4j and data)"""
        # This would test actual profile creation
        # Skipped by default as it requires external dependencies  
        pass


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v"])
