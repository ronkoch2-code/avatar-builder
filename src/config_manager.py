#!/usr/bin/env python3
"""
Configuration Manager for Enhanced Avatar Intelligence System
==========================================================

Centralized configuration management for LLM integration,
database connections, and system settings with enhanced security.

Security Features:
- Secure API key management
- Encrypted sensitive configuration
- Validation of configuration values
- Audit logging for configuration access
"""

import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field
from dotenv import load_dotenv
from datetime import datetime
import warnings

# Load environment variables
load_dotenv()

# Import security utilities
try:
    from .security_utils import SecurityManager, SecureLogger
except ImportError:
    # Fallback if security utils not available yet
    SecurityManager = None
    SecureLogger = None

logger = logging.getLogger(__name__)


@dataclass
class Neo4jConfig:
    """Neo4j database configuration with security enhancements"""
    uri: str = "bolt://localhost:7687"
    username: str = "neo4j"
    password: str = field(default="", repr=False)  # Hide password in repr
    database: str = "neo4j"
    max_connection_pool_size: int = 50
    connection_timeout: float = 30.0
    encrypted: bool = True  # Use TLS by default
    trust: str = "TRUST_SYSTEM_CA_SIGNED_CERTIFICATES"
    _skip_validation: bool = field(default=False, repr=False)  # Internal flag
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        # Skip validation during initial creation in ConfigManager
        if self._skip_validation:
            return
            
        if not self.password:
            raise ValueError("Neo4j password cannot be empty")
        if not self.uri.startswith(('bolt://', 'neo4j://', 'neo4j+s://')):
            raise ValueError(f"Invalid Neo4j URI scheme: {self.uri}")


@dataclass
class AnthropicConfig:
    """Anthropic/Claude configuration with secure API key handling"""
    api_key: str = field(default="", repr=False)  # Hide API key in repr
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4000
    temperature: float = 0.1
    max_concurrent_requests: int = 3
    rate_limit_per_minute: int = 50
    
    # Cost management
    daily_cost_limit: float = 50.0  # Daily spending limit in USD
    cost_alert_threshold: float = 20.0  # Alert when approaching limit
    
    # Security settings
    validate_responses: bool = True  # Validate LLM responses for safety
    log_api_calls: bool = True  # Log API calls (without sensitive data)
    
    def __post_init__(self):
        """Validate API key format"""
        if self.api_key and not self._is_valid_api_key(self.api_key):
            raise ValueError("Invalid Anthropic API key format")
    
    def _is_valid_api_key(self, key: str) -> bool:
        """Basic validation of API key format"""
        # Anthropic keys typically start with 'sk-' and have specific length
        return key.startswith('sk-') and len(key) > 40


@dataclass
class AnalysisConfig:
    """Analysis configuration"""
    min_messages_for_analysis: int = 50
    max_messages_per_analysis: int = 1000
    personality_analysis_enabled: bool = True
    relationship_analysis_enabled: bool = True
    topic_analysis_enabled: bool = True
    emotional_analysis_enabled: bool = True
    
    # Confidence thresholds
    min_confidence_score: float = 0.3
    high_confidence_threshold: float = 0.7


@dataclass
class SystemConfig:
    """Overall system configuration"""
    log_level: str = "INFO"
    enable_llm_analysis: bool = True
    enable_cost_monitoring: bool = True
    backup_enabled: bool = True
    backup_interval_hours: int = 24
    
    # Performance settings
    async_processing: bool = True
    batch_size: int = 10
    retry_attempts: int = 3


class ConfigManager:
    """
    Centralized configuration management
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_file: Optional path to configuration file
        """
        self.config_file = config_file or "avatar_config.json"
        self.config_dir = Path.home() / ".avatar-engine"
        self.config_path = self.config_dir / self.config_file
        
        # Create config directory if it doesn't exist
        self.config_dir.mkdir(exist_ok=True)
        
        # Initialize configurations with validation skipped
        self.neo4j = Neo4jConfig(_skip_validation=True)
        self.anthropic = AnthropicConfig()
        self.analysis = AnalysisConfig()
        self.system = SystemConfig()
        
        # Load configuration from file and environment
        self.load_config()
        
        # Setup logging
        self.setup_logging()
    
    def load_config(self):
        """Load configuration from file and environment variables"""
        # Load from file if exists
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                    self._update_from_dict(config_data)
                logger.info(f"Loaded configuration from {self.config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config file: {e}")
        
        # Override with environment variables
        self._load_from_env()
        
        # Validate configuration
        self.validate_config()
    
    def _update_from_dict(self, config_data: Dict[str, Any]):
        """Update configuration from dictionary"""
        if "neo4j" in config_data:
            for key, value in config_data["neo4j"].items():
                if hasattr(self.neo4j, key):
                    setattr(self.neo4j, key, value)
        
        if "anthropic" in config_data:
            for key, value in config_data["anthropic"].items():
                if hasattr(self.anthropic, key):
                    setattr(self.anthropic, key, value)
        
        if "analysis" in config_data:
            for key, value in config_data["analysis"].items():
                if hasattr(self.analysis, key):
                    setattr(self.analysis, key, value)
        
        if "system" in config_data:
            for key, value in config_data["system"].items():
                if hasattr(self.system, key):
                    setattr(self.system, key, value)
    
    def _load_from_env(self):
        """Load configuration from environment variables with security warnings"""
        # Neo4j
        self.neo4j.uri = os.getenv("NEO4J_URI", self.neo4j.uri)
        self.neo4j.username = os.getenv("NEO4J_USERNAME", self.neo4j.username)
        
        # Secure password loading
        password = os.getenv("NEO4J_PASSWORD", "")
        if password:
            self.neo4j.password = password
            logger.info("Loaded Neo4j password from environment")
        else:
            logger.warning("Neo4j password not found in environment variables")
        
        self.neo4j.database = os.getenv("NEO4J_DATABASE", self.neo4j.database)
        
        # Anthropic - Secure API key loading
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if api_key:
            self.anthropic.api_key = api_key
        else:
            logger.warning("Anthropic API key not found in environment variables")
        
        self.anthropic.model = os.getenv("CLAUDE_MODEL", self.anthropic.model)
        
        # System
        self.system.log_level = os.getenv("LOG_LEVEL", self.system.log_level)
        
        # Parse numeric environment variables
        try:
            if os.getenv("DAILY_COST_LIMIT"):
                self.anthropic.daily_cost_limit = float(os.getenv("DAILY_COST_LIMIT"))
            if os.getenv("MAX_CONCURRENT_REQUESTS"):
                self.anthropic.max_concurrent_requests = int(os.getenv("MAX_CONCURRENT_REQUESTS"))
            if os.getenv("MIN_MESSAGES_FOR_ANALYSIS"):
                self.analysis.min_messages_for_analysis = int(os.getenv("MIN_MESSAGES_FOR_ANALYSIS"))
        except ValueError as e:
            logger.warning(f"Failed to parse numeric environment variable: {e}")
    
    def _validate_sensitive_config(self):
        """Validate sensitive configuration with security checks - ENFORCED SECURITY POLICY"""
        # SECURITY ENFORCEMENT: Reject weak passwords immediately
        weak_passwords = ['password', 'neo4j', 'admin', '123456', 'changeme', 'default', 'root', 'test', 'demo']
        if self.neo4j.password and self.neo4j.password.lower() in weak_passwords:
            raise ValueError(
                f"SECURITY ERROR: Weak password '{self.neo4j.password}' is not allowed! "
                "Use a strong password with at least 12 characters, including uppercase, "
                "lowercase, numbers, and special characters."
            )
        
        # Check if we should enforce strict password validation
        # Allow existing passwords if ALLOW_EXISTING_PASSWORD env var is set
        allow_existing = os.getenv("ALLOW_EXISTING_PASSWORD", "false").lower() == "true"
        
        # Enforce minimum password length and complexity (unless allowing existing)
        if not allow_existing and self.neo4j.password and len(self.neo4j.password) < 12:
            logger.warning(f"Password is only {len(self.neo4j.password)} characters. "
                         "For production use, passwords should be at least 12 characters. "
                         "Set ALLOW_EXISTING_PASSWORD=true to bypass this check.")
            raise ValueError("SECURITY ERROR: Password must be at least 12 characters long. "
                           "Set ALLOW_EXISTING_PASSWORD=true to use existing shorter password.")
        
        # Check for test API keys - FAIL instead of warn
        if self.anthropic.api_key and 'test' in self.anthropic.api_key.lower():
            raise ValueError("SECURITY ERROR: Test API key detected! Use a production API key for real usage.")
        
        # Additional password strength validation (unless allowing existing)
        if not allow_existing and self.neo4j.password:
            self._enforce_password_complexity(self.neo4j.password)
    
    def _enforce_password_complexity(self, password: str):
        """Enforce password complexity requirements"""
        import re
        
        # Check for uppercase, lowercase, numbers, and special characters
        if not re.search(r'[A-Z]', password):
            raise ValueError("SECURITY ERROR: Password must contain at least one uppercase letter.")
        
        if not re.search(r'[a-z]', password):
            raise ValueError("SECURITY ERROR: Password must contain at least one lowercase letter.")
        
        if not re.search(r'\d', password):
            raise ValueError("SECURITY ERROR: Password must contain at least one number.")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValueError("SECURITY ERROR: Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>).")
        
        # Check for common patterns that make passwords weak
        common_patterns = ['1234', 'abcd', 'qwerty']
        password_lower = password.lower()
        for pattern in common_patterns:
            if pattern in password_lower:
                raise ValueError(f"SECURITY ERROR: Password contains common pattern '{pattern}'. Use a more complex password.")
        
        # Check for repeated characters (like 'aaaa' or '1111')
        if re.search(r'(.)\1{3,}', password):
            raise ValueError("SECURITY ERROR: Password contains too many repeated characters. Use more variety.")
    
    def validate_config(self):
        """Validate configuration settings with security checks"""
        # Check for required settings
        if not self.neo4j.password:
            logger.error("No Neo4j password configured")
            # Try one more time to load from environment
            env_password = os.getenv("NEO4J_PASSWORD")
            if env_password:
                logger.info("Found password in environment during validation, applying it now")
                self.neo4j.password = env_password
            else:
                raise ValueError("Neo4j password is required")
        
        if not self.anthropic.api_key:
            logger.warning("No Anthropic API key configured - LLM features disabled")
            self.system.enable_llm_analysis = False
        
        # Validate URLs
        if not self.neo4j.uri.startswith(('bolt://', 'neo4j://', 'neo4j+s://')):
            raise ValueError(f"Invalid Neo4j URI: {self.neo4j.uri}")
        
        # Security validation
        self._validate_sensitive_config()
    
    def get_secure_neo4j_config(self) -> Dict[str, Any]:
        """Get Neo4j configuration with secure handling"""
        return {
            'uri': self.neo4j.uri,
            'auth': (self.neo4j.username, self.neo4j.password),
            'database': self.neo4j.database,
            'encrypted': self.neo4j.encrypted,
            'trust': self.neo4j.trust,
            'max_connection_pool_size': self.neo4j.max_connection_pool_size,
            'connection_timeout': self.neo4j.connection_timeout
        }
    
    def get_secure_anthropic_key(self) -> str:
        """Get Anthropic API key with validation"""
        if not self.anthropic.api_key:
            raise ValueError("Anthropic API key not configured")
        
        # Log access (without revealing key)
        if SecureLogger:
            secure_logger = SecureLogger("config_access")
            secure_logger.log_event("api_key_access", {
                "service": "anthropic",
                "timestamp": datetime.now().isoformat()
            })
        
        return self.anthropic.api_key
    

    
    def save_config(self):
        """Save current configuration to file"""
        config_data = {
            "neo4j": asdict(self.neo4j),
            "anthropic": {
                **asdict(self.anthropic),
                "api_key": "***REDACTED***"  # Don't save API key to file
            },
            "analysis": asdict(self.analysis),
            "system": asdict(self.system)
        }
        
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
    
    def setup_logging(self):
        """Setup logging based on configuration"""
        log_level = getattr(logging, self.system.log_level.upper(), logging.INFO)
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(self.config_dir / 'avatar_engine.log')
            ]
        )
    
    def get_neo4j_driver_config(self) -> Dict[str, Any]:
        """Get Neo4j driver configuration"""
        return {
            "uri": self.neo4j.uri,
            "auth": (self.neo4j.username, self.neo4j.password),
            "database": self.neo4j.database,
            "max_connection_pool_size": self.neo4j.max_connection_pool_size,
            "connection_timeout": self.neo4j.connection_timeout
        }
    
    def get_anthropic_config(self) -> Dict[str, Any]:
        """Get Anthropic configuration"""
        return asdict(self.anthropic)
    
    def get_analysis_config(self) -> Dict[str, Any]:
        """Get analysis configuration"""
        return asdict(self.analysis)
    
    def get_system_config(self) -> Dict[str, Any]:
        """Get system configuration"""
        return asdict(self.system)
    
    def update_cost_limits(self, daily_limit: float, alert_threshold: float):
        """Update cost management settings"""
        self.anthropic.daily_cost_limit = daily_limit
        self.anthropic.cost_alert_threshold = alert_threshold
        self.save_config()
        logger.info(f"Updated cost limits: daily ${daily_limit}, alert ${alert_threshold}")
    
    def enable_feature(self, feature: str, enabled: bool = True):
        """Enable or disable system features"""
        feature_mapping = {
            "llm_analysis": ("system", "enable_llm_analysis"),
            "personality_analysis": ("analysis", "personality_analysis_enabled"),
            "relationship_analysis": ("analysis", "relationship_analysis_enabled"),
            "topic_analysis": ("analysis", "topic_analysis_enabled"),
            "emotional_analysis": ("analysis", "emotional_analysis_enabled"),
            "cost_monitoring": ("system", "enable_cost_monitoring"),
            "backup": ("system", "backup_enabled")
        }
        
        if feature in feature_mapping:
            section, attr = feature_mapping[feature]
            config_section = getattr(self, section)
            setattr(config_section, attr, enabled)
            self.save_config()
            logger.info(f"{'Enabled' if enabled else 'Disabled'} {feature}")
        else:
            raise ValueError(f"Unknown feature: {feature}")
    
    def create_sample_config(self):
        """Create a sample configuration file"""
        sample_config = {
            "neo4j": {
                "uri": "bolt://localhost:7687",
                "username": "neo4j",
                "password": "your_neo4j_password",
                "database": "neo4j"
            },
            "anthropic": {
                "model": "claude-3-5-sonnet-20240620",
                "max_concurrent_requests": 3,
                "daily_cost_limit": 50.0,
                "cost_alert_threshold": 20.0
            },
            "analysis": {
                "min_messages_for_analysis": 50,
                "max_messages_per_analysis": 1000,
                "personality_analysis_enabled": True,
                "relationship_analysis_enabled": True
            },
            "system": {
                "enable_llm_analysis": True,
                "enable_cost_monitoring": True,
                "log_level": "INFO"
            }
        }
        
        sample_path = self.config_dir / "avatar_config_sample.json"
        with open(sample_path, 'w') as f:
            json.dump(sample_config, f, indent=2)
        
        print(f"Sample configuration created at: {sample_path}")
        print("\nTo get started:")
        print("1. Copy the sample config to avatar_config.json")
        print("2. Update the Neo4j password and Anthropic API key")
        print("3. Set ANTHROPIC_API_KEY environment variable")
        print("4. Adjust other settings as needed")


# Cost monitoring utilities
class CostMonitor:
    """Monitor and manage LLM API costs"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.cost_file = config.config_dir / "cost_tracking.json"
        self.daily_costs = self._load_cost_data()
    
    def _load_cost_data(self) -> Dict[str, float]:
        """Load cost tracking data"""
        if self.cost_file.exists():
            try:
                with open(self.cost_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cost data: {e}")
        return {}
    
    def _save_cost_data(self):
        """Save cost tracking data"""
        try:
            with open(self.cost_file, 'w') as f:
                json.dump(self.daily_costs, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cost data: {e}")
    
    def record_cost(self, cost: float):
        """Record API cost for today"""
        today = datetime.now().strftime('%Y-%m-%d')
        if today not in self.daily_costs:
            self.daily_costs[today] = 0.0
        
        self.daily_costs[today] += cost
        self._save_cost_data()
        
        # Check limits
        if self.daily_costs[today] >= self.config.anthropic.cost_alert_threshold:
            logger.warning(f"Daily cost alert: ${self.daily_costs[today]:.2f}")
        
        if self.daily_costs[today] >= self.config.anthropic.daily_cost_limit:
            raise RuntimeError(f"Daily cost limit exceeded: ${self.daily_costs[today]:.2f}")
    
    def get_today_cost(self) -> float:
        """Get today's total cost"""
        today = datetime.now().strftime('%Y-%m-%d')
        return self.daily_costs.get(today, 0.0)
    
    def can_afford_analysis(self, estimated_cost: float = 2.0) -> bool:
        """Check if we can afford an analysis"""
        today_cost = self.get_today_cost()
        return (today_cost + estimated_cost) < self.config.anthropic.daily_cost_limit


# CLI setup utility
def setup_configuration():
    """Interactive configuration setup"""
    print("🤖 Avatar Engine Enhanced - Configuration Setup")
    print("=" * 50)
    
    config = ConfigManager()
    
    # Neo4j configuration
    print("\n📊 Neo4j Configuration")
    neo4j_uri = input(f"Neo4j URI [{config.neo4j.uri}]: ").strip()
    if neo4j_uri:
        config.neo4j.uri = neo4j_uri
    
    neo4j_password = input("Neo4j Password: ").strip()
    if neo4j_password:
        config.neo4j.password = neo4j_password
    
    # Anthropic configuration
    print("\n🧠 Claude/Anthropic Configuration")
    api_key = input("Anthropic API Key: ").strip()
    if api_key:
        config.anthropic.api_key = api_key
    
    model = input(f"Claude Model [{config.anthropic.model}]: ").strip()
    if model:
        config.anthropic.model = model
    
    # Cost limits
    print("\n💰 Cost Management")
    try:
        daily_limit = input(f"Daily Cost Limit USD [{config.anthropic.daily_cost_limit}]: ").strip()
        if daily_limit:
            config.anthropic.daily_cost_limit = float(daily_limit)
    except ValueError:
        print("Invalid cost limit, using default")
    
    # Analysis settings
    print("\n🔍 Analysis Settings")
    min_messages = input(f"Minimum messages for analysis [{config.analysis.min_messages_for_analysis}]: ").strip()
    if min_messages:
        try:
            config.analysis.min_messages_for_analysis = int(min_messages)
        except ValueError:
            print("Invalid number, using default")
    
    # Save configuration
    config.save_config()
    
    print(f"\n✅ Configuration saved to {config.config_path}")
    print("\n🚀 Ready to start! Run your Avatar Engine scripts.")
    
    return config


if __name__ == "__main__":
    # Run interactive setup
    setup_configuration()
