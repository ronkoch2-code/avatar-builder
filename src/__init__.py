"""
Avatar Intelligence System
=========================

A comprehensive system for analyzing conversation data and generating personalized AI avatars.

Core Components:
- Avatar System Deployment: Schema setup and system management
- Avatar Intelligence Pipeline: Complete analysis and avatar generation
- Message Processing: iMessage data cleaning and processing
- Relationship Analysis: Detecting and analyzing communication patterns

Usage:
    from src.avatar_system_deployment import AvatarSystemDeployment
    from src.avatar_intelligence_pipeline import AvatarSystemManager
    
    # Deploy system
    deployment = AvatarSystemDeployment(uri, username, password)
    deployment.deploy_system()
    
    # Create avatar manager
    manager = AvatarSystemManager(driver)
    stats = manager.initialize_all_people(min_messages=50)

Version: 1.0.0
Author: Ron Koch
"""

__version__ = "1.0.0"
__author__ = "Ron Koch"

# Import main classes for easy access
try:
    from .avatar_system_deployment import AvatarSystemDeployment
except ImportError:
    # Handle case where deployment module might not be available
    AvatarSystemDeployment = None

try:
    from .avatar_intelligence_pipeline import AvatarSystemManager
except ImportError:
    # Handle case where main pipeline might not be available yet
    AvatarSystemManager = None

# Package metadata
__all__ = [
    "AvatarSystemDeployment",
    "AvatarSystemManager",
    "__version__",
    "__author__",
]
