#!/usr/bin/env python3
"""
Reliability Module - Comprehensive error handling and resilience patterns
==========================================================================

This module provides enterprise-grade reliability features for the Avatar Engine:
- Structured error handling with detailed reporting
- Intelligent retry logic with exponential backoff
- Circuit breaker pattern for fault tolerance
- Connection pooling for efficient resource management

Example Usage:
    from src.reliability import (
        with_retry, 
        with_circuit_breaker,
        DatabaseError,
        global_pool_manager
    )
    
    @with_retry(max_attempts=3)
    @with_circuit_breaker("api_service")
    def api_call():
        # Your code here
        pass
"""

# Import error handling components
from .error_handler import (
    # Error severity levels
    ErrorSeverity,
    ErrorCategory,
    
    # Context and reporting
    ErrorContext,
    ErrorReport,
    
    # Base exception hierarchy
    AvatarEngineError,
    DatabaseError,
    APIError,
    ValidationError,
    ConfigurationError,
    SecurityError,
    NetworkError,
    FileSystemError,
    ParsingError,
    ProcessingError,
    
    # Error handler
    ErrorHandler,
    global_error_handler,
    
    # Decorator
    handle_errors
)

# Import retry manager components
from .retry_manager import (
    # Retry strategies
    RetryStrategy,
    
    # Configuration
    RetryConfig,
    RetryAttempt,
    RetryResult,
    RetryBudget,
    
    # Manager
    RetryManager,
    global_retry_manager,
    
    # Decorator
    with_retry
)

# Import circuit breaker components
from .circuit_breaker import (
    # Circuit states
    CircuitState,
    
    # Configuration
    CircuitBreakerConfig,
    CallMetrics,
    
    # Exceptions
    CircuitBreakerError,
    
    # Circuit breaker
    CircuitBreaker,
    CircuitBreakerManager,
    global_circuit_manager,
    
    # Decorator
    with_circuit_breaker
)

# Import connection pool components
from .connection_pool import (
    # Configuration
    PoolConfig,
    ConnectionInfo,
    
    # Factories
    ConnectionFactory,
    Neo4jConnectionFactory,
    HTTPConnectionFactory,
    
    # Pool management
    ConnectionPool,
    PoolManager,
    global_pool_manager
)

# Version info
__version__ = "1.0.0"
__author__ = "Avatar Engine Team"

# Module exports
__all__ = [
    # Error handling
    "ErrorSeverity",
    "ErrorCategory",
    "ErrorContext",
    "ErrorReport",
    "AvatarEngineError",
    "DatabaseError",
    "APIError",
    "ValidationError",
    "ConfigurationError",
    "SecurityError",
    "NetworkError",
    "FileSystemError",
    "ParsingError",
    "ProcessingError",
    "ErrorHandler",
    "global_error_handler",
    "handle_errors",
    
    # Retry manager
    "RetryStrategy",
    "RetryConfig",
    "RetryAttempt",
    "RetryResult",
    "RetryBudget",
    "RetryManager",
    "global_retry_manager",
    "with_retry",
    
    # Circuit breaker
    "CircuitState",
    "CircuitBreakerConfig",
    "CallMetrics",
    "CircuitBreakerError",
    "CircuitBreaker",
    "CircuitBreakerManager",
    "global_circuit_manager",
    "with_circuit_breaker",
    
    # Connection pool
    "PoolConfig",
    "ConnectionInfo",
    "ConnectionFactory",
    "Neo4jConnectionFactory",
    "HTTPConnectionFactory",
    "ConnectionPool",
    "PoolManager",
    "global_pool_manager"
]
