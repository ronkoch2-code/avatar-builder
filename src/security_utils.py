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
        """Initialize encryption cipher with key from environment or parameter"""
        if encryption_key:
            key = encryption_key.encode()
        else:
            # Try to get from environment
            env_key = os.getenv("AVATAR_ENCRYPTION_KEY")
            if env_key:
                key = env_key.encode()
            else:
                # Generate a new key if none exists
                key = Fernet.generate_key()
                logger.warning("No encryption key found. Generated new key. Save this to AVATAR_ENCRYPTION_KEY environment variable.")
                logger.warning(f"Key: {key.decode()}")
        
        return Fernet(key)
    
    def _compile_sensitive_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for detecting sensitive data"""
        return {
            'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            'credit_card': re.compile(r'\b(?:\d{4}[\s-]?){3}\d{4}\b'),
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'),
            'api_key': re.compile(r'\b(?:api[_-]?key|token|secret)["\']?\s*[:=]\s*["\']?[\w-]+["\']?\b', re.IGNORECASE),
        }
    
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
    """Secure logging with PII protection"""
    
    def __init__(self, name: str, log_file: str = "security.log"):
        """
        Initialize secure logger
        
        Args:
            name: Logger name
            log_file: Path to log file
        """
        self.logger = logging.getLogger(name)
        self.security_manager = SecurityManager()
        
        # Create handler with rotation
        from logging.handlers import RotatingFileHandler
        handler = RotatingFileHandler(
            log_file,
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        
        # Set formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_event(self, event_type: str, details: Dict[str, Any], level: str = "info"):
        """
        Log event with automatic PII sanitization
        
        Args:
            event_type: Type of event
            details: Event details
            level: Log level (info, warning, error, critical)
        """
        # Sanitize details
        safe_details = self.security_manager.sanitize_log_data(details)
        
        # Create log entry
        log_entry = {
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "details": safe_details
        }
        
        # Log at appropriate level
        log_message = json.dumps(log_entry)
        getattr(self.logger, level)(log_message)
    
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


# Export main components
__all__ = [
    'SecurityManager',
    'RateLimiter',
    'SecureLogger',
    'rate_limit'
]
