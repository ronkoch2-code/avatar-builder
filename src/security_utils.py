#!/usr/bin/env python3
"""
Security Utilities for Avatar-Engine
=====================================

Provides encryption, hashing, and security utilities for the Avatar-Engine system.
Implements data protection, key management, and secure operations.

Author: Avatar-Engine Security Team
Date: 2025-01-30
"""

import os
import re
import hashlib
import secrets
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from functools import wraps
import time
import json
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64

logger = logging.getLogger(__name__)


class SecurityManager:
    """Central security management for Avatar-Engine"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize security manager
        
        Args:
            encryption_key: Optional encryption key, otherwise generated from environment
        """
        self.cipher = self._initialize_cipher(encryption_key)
        self.sensitive_patterns = self._compile_sensitive_patterns()
        
    def _initialize_cipher(self, encryption_key: Optional[str] = None) -> Fernet:
        """Initialize encryption cipher with key from environment or parameter
        
        Uses PBKDF2 key derivation for enhanced security when using environment variables.
        """
        if encryption_key:
            # Use provided key with key derivation
            key = self._derive_key(encryption_key)
        else:
            # Try to get from environment
            env_key = os.getenv("AVATAR_ENCRYPTION_KEY")
            if env_key:
                # Derive key from environment variable using PBKDF2
                key = self._derive_key(env_key)
            else:
                # Require explicit key - no automatic generation for security
                raise ValueError(
                    "CRITICAL: No encryption key provided. "
                    "Set AVATAR_ENCRYPTION_KEY environment variable or provide key directly. "
                    "Generate a secure key using: python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
                )
        
        return Fernet(key)
    
    def _derive_key(self, passphrase: str) -> bytes:
        """Derive encryption key from passphrase using PBKDF2
        
        Args:
            passphrase: Password or passphrase to derive key from
            
        Returns:
            32-byte key suitable for Fernet
        """
        # Use a fixed salt from environment or generate a deterministic one
        salt = os.getenv("AVATAR_KEY_SALT", "avatar-engine-salt-2025").encode()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,  # OWASP recommended minimum
            backend=default_backend()
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))
        return key
    
    def _compile_sensitive_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for detecting sensitive data
        
        Patterns can be extended via configuration file if needed.
        """
        # Load base patterns
        patterns = {
            'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            'credit_card': re.compile(r'\b(?:\d{4}[\s-]?){3}\d{4}\b'),
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'),
            'api_key': re.compile(r'\b(?:api[_-]?key|token|secret)["\']?\s*[:=]\s*["\']?[\w-]+["\']?\b', re.IGNORECASE),
            'aws_key': re.compile(r'\b(AKIA[0-9A-Z]{16})\b'),
            'jwt_token': re.compile(r'\beyJ[A-Za-z0-9+/]+=*\.[A-Za-z0-9+/]+=*\.[A-Za-z0-9+/]+=*\b'),
        }
        
        # Try to load custom patterns from config file if exists
        config_path = Path(os.getenv("AVATAR_PATTERNS_CONFIG", "config/sensitive_patterns.json"))
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    custom_patterns = json.load(f)
                    for name, pattern_str in custom_patterns.items():
                        patterns[name] = re.compile(pattern_str)
            except Exception as e:
                logger.error(f"Failed to load custom patterns: {e}")
        
        return patterns
    
    def encrypt_data(self, data: Union[str, bytes]) -> str:
        """
        Encrypt sensitive data
        
        Args:
            data: Data to encrypt (string or bytes)
            
        Returns:
            Base64-encoded encrypted data
        """
        if isinstance(data, str):
            data = data.encode()
        
        encrypted = self.cipher.encrypt(data)
        return base64.b64encode(encrypted).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrypt encrypted data
        
        Args:
            encrypted_data: Base64-encoded encrypted data
            
        Returns:
            Decrypted string
        """
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Failed to decrypt data") from e
    
    def hash_pii(self, data: str, salt: Optional[str] = None) -> str:
        """
        Create a secure hash of PII data for anonymization
        
        Args:
            data: Data to hash
            salt: Optional salt for hashing
            
        Returns:
            Hexadecimal hash string
        """
        if salt is None:
            salt = os.getenv("AVATAR_HASH_SALT", "default-salt-change-me")
        
        salted_data = f"{salt}{data}"
        return hashlib.sha256(salted_data.encode()).hexdigest()
    
    def anonymize_phone(self, phone: str) -> str:
        """
        Anonymize phone number while preserving some structure
        
        Args:
            phone: Phone number to anonymize
            
        Returns:
            Anonymized phone identifier
        """
        # Remove non-digits
        digits_only = re.sub(r'\D', '', phone)
        
        # Keep country code and area code, hash the rest
        if len(digits_only) >= 10:
            prefix = digits_only[:6]  # Country + area code
            suffix_hash = self.hash_pii(digits_only[6:])[:4]
            return f"{prefix}****{suffix_hash}"
        else:
            return self.hash_pii(phone)[:12]
    
    def sanitize_log_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize sensitive data from logs
        
        Args:
            data: Dictionary containing log data
            
        Returns:
            Sanitized dictionary safe for logging
        """
        sensitive_keys = [
            'password', 'api_key', 'token', 'secret', 'auth',
            'authorization', 'credit_card', 'ssn', 'private_key'
        ]
        
        sanitized = {}
        for key, value in data.items():
            # Check if key contains sensitive terms
            if any(term in key.lower() for term in sensitive_keys):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, str):
                # Check if value contains sensitive patterns
                if self._contains_sensitive_data(value):
                    sanitized[key] = "***CONTAINS_PII***"
                else:
                    sanitized[key] = value
            elif isinstance(value, dict):
                # Recursively sanitize nested dictionaries
                sanitized[key] = self.sanitize_log_data(value)
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _contains_sensitive_data(self, text: str) -> bool:
        """Check if text contains sensitive data patterns"""
        for pattern_name, pattern in self.sensitive_patterns.items():
            if pattern.search(text):
                return True
        return False
    
    def validate_input(self, input_data: str, input_type: str = "general") -> str:
        """
        Validate and sanitize user input
        
        Args:
            input_data: User input to validate
            input_type: Type of input (general, sql, prompt, etc.)
            
        Returns:
            Sanitized input
            
        Raises:
            ValueError: If input contains malicious content
        """
        # Check for common injection patterns
        injection_patterns = {
            'sql': [
                r"(\b(DROP|DELETE|INSERT|UPDATE|ALTER|CREATE)\b.*\b(TABLE|DATABASE)\b)",
                r"(;.*--)|(--.*)",
                r"(\bOR\b.*=.*)",
            ],
            'prompt': [
                r"(ignore previous instructions)",
                r"(system:|admin:|root:)",
                r"(<script|javascript:|onerror=)",
                r"(\[INST\]|\[/INST\]|<s>|</s>)",
            ],
            'general': [
                r"(<script|javascript:|onerror=|onclick=)",
                r"(file:///|..\/|\.\.\\)",
            ]
        }
        
        patterns_to_check = injection_patterns.get(input_type, []) + injection_patterns['general']
        
        for pattern in patterns_to_check:
            if re.search(pattern, input_data, re.IGNORECASE):
                logger.warning(f"Potential injection attempt detected: {pattern}")
                raise ValueError(f"Input validation failed: potentially malicious content detected")
        
        # Remove control characters
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', input_data)
        
        return sanitized


class RateLimiter:
    """Rate limiting for API and database operations"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = {}
    
    def check_limit(self, identifier: str) -> bool:
        """
        Check if request is within rate limit
        
        Args:
            identifier: Unique identifier for the requester
            
        Returns:
            True if request is allowed, False otherwise
        """
        now = time.time()
        
        # Initialize if new identifier
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Clean old requests outside window
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if now - req_time < self.window_seconds
        ]
        
        # Check if limit exceeded
        if len(self.requests[identifier]) >= self.max_requests:
            return False
        
        # Add current request
        self.requests[identifier].append(now)
        return True
    
    def get_retry_after(self, identifier: str) -> int:
        """
        Get seconds until next request is allowed
        
        Args:
            identifier: Unique identifier for the requester
            
        Returns:
            Seconds to wait before retry
        """
        if identifier not in self.requests or not self.requests[identifier]:
            return 0
        
        oldest_request = min(self.requests[identifier])
        retry_after = self.window_seconds - (time.time() - oldest_request)
        
        return max(0, int(retry_after))


def rate_limit(max_requests: int = 100, window: int = 60):
    """
    Decorator for rate limiting functions
    
    Args:
        max_requests: Maximum requests in window
        window: Time window in seconds
    """
    limiter = RateLimiter(max_requests, window)
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Try to extract identifier from args
            identifier = kwargs.get('user_id', kwargs.get('identifier', 'default'))
            
            if not limiter.check_limit(identifier):
                retry_after = limiter.get_retry_after(identifier)
                raise Exception(f"Rate limit exceeded. Retry after {retry_after} seconds")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


class SecureLogger:
    """Enhanced secure logging with comprehensive PII protection and secret sanitization"""
    
    def __init__(self, name: str, log_file: str = "security.log"):
        """
        Initialize secure logger with enhanced protection
        
        Args:
            name: Logger name
            log_file: Path to log file
        """
        self.logger = logging.getLogger(name)
        self.security_manager = SecurityManager()
        
        # Enhanced sensitive data patterns
        self.sensitive_patterns = {
            'api_key': re.compile(r'\b(?:api[_-]?key|token|secret|password)["\']?\s*[:=]\s*["\']?[\w\-+/=]{8,}["\']?\b', re.IGNORECASE),
            'credit_card': re.compile(r'\b(?:\d{4}[\s\-]?){3}\d{4}\b'),
            'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'\b(?:\+?1[-\.\s]?)?\(?\d{3}\)?[-\.\s]?\d{3}[-\.\s]?\d{4}\b'),
            'base64_secrets': re.compile(r'\b[A-Za-z0-9+/]{20,}={0,2}\b'),  # Potential base64 encoded secrets
            'jwt_token': re.compile(r'\beyJ[A-Za-z0-9+/]+=*\.[A-Za-z0-9+/]+=*\.[A-Za-z0-9+/]+=*\b'),  # JWT tokens
            'private_key': re.compile(r'-----BEGIN [A-Z ]+PRIVATE KEY-----[\s\S]*?-----END [A-Z ]+PRIVATE KEY-----'),
        }
        
        # Create handler with rotation and secure permissions
        from logging.handlers import RotatingFileHandler
        import os
        
        # Create logs directory with secure permissions
        log_dir = os.path.dirname(log_file) or './logs'
        os.makedirs(log_dir, mode=0o750, exist_ok=True)
        
        handler = RotatingFileHandler(
            log_file,
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        
        # Set secure file permissions
        try:
            os.chmod(log_file, 0o640)  # Read/write for owner, read for group, no access for others
        except OSError:
            pass  # File might not exist yet
        
        # Enhanced formatter with sanitization
        formatter = SecureFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            self
        )
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def sanitize_message(self, message: str) -> str:
        """Comprehensively sanitize log message to prevent secret leakage"""
        if not isinstance(message, str):
            message = str(message)
        
        # Apply all sensitive data patterns
        for pattern_name, pattern in self.sensitive_patterns.items():
            message = pattern.sub(f'***{pattern_name.upper()}_REDACTED***', message)
        
        # Additional sanitization for common secret formats
        # Replace potential passwords in URLs
        message = re.sub(r'(://[^:]+:)[^@]+(@)', r'\1***PASSWORD***\2', message)
        
        # Replace Bearer tokens
        message = re.sub(r'Bearer\s+[A-Za-z0-9\-._~+/]+=*', 'Bearer ***TOKEN***', message, flags=re.IGNORECASE)
        
        # Replace Authorization headers
        message = re.sub(r'Authorization:\s*[^\s]+', 'Authorization: ***REDACTED***', message, flags=re.IGNORECASE)
        
        return message
    
    def log_event(self, event_type: str, details: Dict[str, Any], level: str = "info"):
        """
        Log event with comprehensive PII and secret sanitization
        
        Args:
            event_type: Type of event
            details: Event details
            level: Log level (info, warning, error, critical)
        """
        # Double sanitization: first through security manager, then message-level
        safe_details = self.security_manager.sanitize_log_data(details)
        
        # Create log entry
        log_entry = {
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "details": safe_details,
            "session_id": hash(f"{datetime.now().date()}{os.getpid()}")  # Safe session tracking
        }
        
        # Convert to JSON and apply message-level sanitization
        log_message = json.dumps(log_entry)
        safe_message = self.sanitize_message(log_message)
        
        # Log at appropriate level
        getattr(self.logger, level)(safe_message)
    
    def log_security_event(self, event: str, user_id: Optional[str] = None, 
                          ip_address: Optional[str] = None, details: Optional[Dict] = None):
        """
        Log security-specific event
        
        Args:
            event: Security event description
            user_id: User identifier (will be hashed)
            ip_address: IP address
            details: Additional details
        """
        entry = {
            "security_event": event,
            "user_id_hash": self.security_manager.hash_pii(user_id) if user_id else None,
            "ip_address": ip_address,
            "details": self.security_manager.sanitize_log_data(details or {})
        }
        
        self.log_event("security", entry, "warning")


class SecureFormatter(logging.Formatter):
    """Custom formatter that sanitizes log messages before output"""
    
    def __init__(self, fmt=None, secure_logger=None):
        super().__init__(fmt)
        self.secure_logger = secure_logger
    
    def format(self, record):
        """Format log record with sanitization"""
        # First apply standard formatting
        formatted = super().format(record)
        
        # Then sanitize if we have a secure logger
        if self.secure_logger and hasattr(self.secure_logger, 'sanitize_message'):
            formatted = self.secure_logger.sanitize_message(formatted)
        
        return formatted


class InputValidator:
    """Enhanced input validation for all user inputs"""
    
    def __init__(self):
        self.security_manager = SecurityManager()
    
    def validate_database_input(self, input_data: str, field_name: str = "input") -> str:
        """Validate input specifically for database operations"""
        if not input_data:
            return input_data
        
        # Check for SQL/Cypher injection patterns
        dangerous_patterns = [
            r'\b(DROP|DELETE|REMOVE|DETACH)\s+(DATABASE|TABLE|NODE|RELATIONSHIP)\b',
            r';\s*(DROP|DELETE|REMOVE)',
            r'//.*--',  # Comment-based injection
            r'/\*.*\*/',  # Block comments
            r'\bUNION\s+SELECT\b',
            r'\bOR\s+1\s*=\s*1\b',
            r'\bAND\s+1\s*=\s*1\b',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                raise ValueError(f"SECURITY ERROR: Potentially malicious input detected in {field_name}: {pattern}")
        
        # Validate length
        if len(input_data) > 10000:  # Reasonable max length
            raise ValueError(f"SECURITY ERROR: Input too long for {field_name} (max 10000 characters)")
        
        return self.security_manager.validate_input(input_data, "sql")
    
    def validate_llm_prompt(self, prompt: str) -> str:
        """Validate input for LLM prompts"""
        if not prompt:
            return prompt
        
        # Check for prompt injection patterns
        injection_patterns = [
            r'ignore\s+previous\s+instructions',
            r'system\s*:',
            r'admin\s*:',
            r'root\s*:',
            r'\[INST\]',
            r'\[/INST\]',
            r'<\|endoftext\|>',
            r'<\|startoftext\|>',
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                logger.warning(f"Potential prompt injection detected: {pattern}")
                # Log but don't fail - may be legitimate use
        
        # Validate length
        if len(prompt) > 50000:  # Large but reasonable for LLM
            raise ValueError("SECURITY ERROR: Prompt too long (max 50000 characters)")
        
        return self.security_manager.validate_input(prompt, "prompt")
    
    def validate_file_path(self, file_path: str) -> str:
        """Validate file paths to prevent directory traversal"""
        if not file_path:
            return file_path
        
        # Check for directory traversal
        if '..' in file_path or file_path.startswith('/'):
            raise ValueError("SECURITY ERROR: Invalid file path - directory traversal detected")
        
        # Check for suspicious patterns
        if re.search(r'[<>:"|?*]', file_path):
            raise ValueError("SECURITY ERROR: Invalid characters in file path")
        
        return file_path


# Export main components
__all__ = [
    'SecurityManager',
    'RateLimiter',
    'SecureLogger',
    'SecureFormatter',
    'InputValidator',
    'rate_limit'
]
