#!/usr/bin/env python3
"""
Circuit Breaker Module - Prevent cascading failures
=====================================================

Implements the circuit breaker pattern to prevent cascading failures
and provide graceful degradation when external services fail.

Features:
- Three states: CLOSED, OPEN, HALF_OPEN
- Configurable failure thresholds
- Automatic recovery testing
- Fallback mechanisms
- Detailed metrics and monitoring
"""

import time
import logging
import threading
from typing import Callable, Optional, Any, Dict, List, TypeVar, Generic
from functools import wraps
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

# Import error handler
from .error_handler import AvatarEngineError, NetworkError, APIError, DatabaseError

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for generic return types
T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation, requests pass through
    OPEN = "open"  # Circuit is open, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service has recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior"""
    # Failure detection
    failure_threshold: int = 5  # Number of failures to open circuit
    success_threshold: int = 3  # Number of successes to close circuit from half-open
    timeout: float = 60.0  # Seconds before attempting to half-open
    
    # Time windows
    window_size: int = 60  # Seconds for failure counting window
    half_open_max_calls: int = 3  # Max calls allowed in half-open state
    
    # Error handling
    expected_exceptions: List[type] = field(default_factory=lambda: [
        NetworkError, APIError, DatabaseError,
        ConnectionError, TimeoutError
    ])
    fallback_function: Optional[Callable] = None
    
    # Advanced options
    failure_rate_threshold: Optional[float] = 0.5  # Open if failure rate exceeds this
    slow_call_duration: Optional[float] = None  # Consider call slow if exceeds this
    slow_call_rate_threshold: Optional[float] = 0.5  # Open if slow call rate exceeds


@dataclass
class CallMetrics:
    """Metrics for a single call"""
    timestamp: datetime
    duration: float
    succeeded: bool
    exception: Optional[Exception] = None


class CircuitBreakerError(AvatarEngineError):
    """Exception raised when circuit breaker is open"""
    def __init__(self, message: str, circuit_name: str, **kwargs):
        super().__init__(
            message,
            recovery_suggestions=[
                "Wait for circuit to recover",
                "Check service health",
                "Use fallback mechanism if available"
            ],
            circuit_name=circuit_name,
            **kwargs
        )


class CircuitBreaker(Generic[T]):
    """
    Circuit breaker implementation
    
    The circuit breaker pattern prevents cascading failures by:
    1. Monitoring failures and opening circuit when threshold is reached
    2. Failing fast when circuit is open (without calling the service)
    3. Periodically testing if service has recovered (half-open state)
    4. Closing circuit when service is healthy again
    """
    
    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.last_failure_time: Optional[float] = None
        self.last_success_time: Optional[float] = None
        
        # Metrics tracking
        self.call_metrics: deque = deque(maxlen=1000)
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Statistics
        self.total_calls = 0
        self.total_failures = 0
        self.total_successes = 0
        self.circuit_opens = 0
        self.fallback_calls = 0
    
    def call(
        self,
        func: Callable[..., T],
        *args,
        fallback: Optional[Callable[..., T]] = None,
        **kwargs
    ) -> T:
        """
        Execute function through circuit breaker
        
        Args:
            func: Function to execute
            fallback: Optional fallback function if circuit is open
            *args, **kwargs: Arguments for the function
        
        Returns:
            Result from function or fallback
        
        Raises:
            CircuitBreakerError if circuit is open and no fallback
        """
        with self._lock:
            # Check circuit state
            self._check_state()
            
            if self.state == CircuitState.OPEN:
                # Circuit is open, fail fast
                logger.warning(f"Circuit {self.name} is OPEN, failing fast")
                self.fallback_calls += 1
                
                if fallback or self.config.fallback_function:
                    fallback_func = fallback or self.config.fallback_function
                    return fallback_func(*args, **kwargs)
                
                raise CircuitBreakerError(
                    f"Circuit breaker {self.name} is open",
                    circuit_name=self.name,
                    state=self.state.value,
                    last_failure=self.last_failure_time
                )
            
            if self.state == CircuitState.HALF_OPEN:
                # Limit calls in half-open state
                if self.half_open_calls >= self.config.half_open_max_calls:
                    logger.warning(
                        f"Circuit {self.name} is HALF_OPEN, max calls reached"
                    )
                    if fallback or self.config.fallback_function:
                        fallback_func = fallback or self.config.fallback_function
                        return fallback_func(*args, **kwargs)
                    
                    raise CircuitBreakerError(
                        f"Circuit breaker {self.name} is half-open, max calls reached",
                        circuit_name=self.name,
                        state=self.state.value
                    )
                
                self.half_open_calls += 1
        
        # Execute the function
        start_time = time.time()
        self.total_calls += 1
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Record success
            self._record_success(duration)
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Check if exception should trigger circuit breaker
            if self._is_expected_exception(e):
                self._record_failure(duration, e)
            else:
                # Unexpected exception, don't trigger circuit breaker
                logger.error(f"Unexpected exception in circuit {self.name}: {e}")
            
            raise
    
    async def call_async(
        self,
        func: Callable[..., T],
        *args,
        fallback: Optional[Callable[..., T]] = None,
        **kwargs
    ) -> T:
        """
        Async version of call
        
        Args:
            func: Async function to execute
            fallback: Optional async fallback function
            *args, **kwargs: Arguments for the function
        
        Returns:
            Result from function or fallback
        """
        import asyncio
        
        with self._lock:
            # Check circuit state
            self._check_state()
            
            if self.state == CircuitState.OPEN:
                # Circuit is open, fail fast
                logger.warning(f"Circuit {self.name} is OPEN, failing fast")
                self.fallback_calls += 1
                
                if fallback or self.config.fallback_function:
                    fallback_func = fallback or self.config.fallback_function
                    return await fallback_func(*args, **kwargs)
                
                raise CircuitBreakerError(
                    f"Circuit breaker {self.name} is open",
                    circuit_name=self.name,
                    state=self.state.value,
                    last_failure=self.last_failure_time
                )
            
            if self.state == CircuitState.HALF_OPEN:
                # Limit calls in half-open state
                if self.half_open_calls >= self.config.half_open_max_calls:
                    logger.warning(
                        f"Circuit {self.name} is HALF_OPEN, max calls reached"
                    )
                    if fallback or self.config.fallback_function:
                        fallback_func = fallback or self.config.fallback_function
                        return await fallback_func(*args, **kwargs)
                    
                    raise CircuitBreakerError(
                        f"Circuit breaker {self.name} is half-open, max calls reached",
                        circuit_name=self.name,
                        state=self.state.value
                    )
                
                self.half_open_calls += 1
        
        # Execute the async function
        start_time = time.time()
        self.total_calls += 1
        
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Record success
            self._record_success(duration)
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Check if exception should trigger circuit breaker
            if self._is_expected_exception(e):
                self._record_failure(duration, e)
            else:
                # Unexpected exception, don't trigger circuit breaker
                logger.error(f"Unexpected exception in circuit {self.name}: {e}")
            
            raise
    
    def _check_state(self) -> None:
        """Check and update circuit state"""
        current_time = time.time()
        
        if self.state == CircuitState.OPEN:
            # Check if timeout has passed to try half-open
            if self.last_failure_time and \
               current_time - self.last_failure_time >= self.config.timeout:
                logger.info(f"Circuit {self.name} transitioning to HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                self.success_count = 0
                self.failure_count = 0
        
        elif self.state == CircuitState.CLOSED:
            # Check if we should open the circuit
            self._cleanup_old_metrics()
            
            # Check failure threshold
            if self.failure_count >= self.config.failure_threshold:
                self._open_circuit()
            
            # Check failure rate if configured
            elif self.config.failure_rate_threshold:
                failure_rate = self._calculate_failure_rate()
                if failure_rate >= self.config.failure_rate_threshold:
                    self._open_circuit()
            
            # Check slow call rate if configured
            elif self.config.slow_call_duration and self.config.slow_call_rate_threshold:
                slow_rate = self._calculate_slow_call_rate()
                if slow_rate >= self.config.slow_call_rate_threshold:
                    self._open_circuit()
    
    def _open_circuit(self) -> None:
        """Open the circuit"""
        logger.warning(f"Circuit {self.name} is now OPEN")
        self.state = CircuitState.OPEN
        self.circuit_opens += 1
        self.last_failure_time = time.time()
    
    def _record_success(self, duration: float) -> None:
        """Record a successful call"""
        with self._lock:
            self.total_successes += 1
            self.last_success_time = time.time()
            
            # Add to metrics
            self.call_metrics.append(CallMetrics(
                timestamp=datetime.now(),
                duration=duration,
                succeeded=True
            ))
            
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                
                # Check if we can close the circuit
                if self.success_count >= self.config.success_threshold:
                    logger.info(f"Circuit {self.name} is now CLOSED")
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
                    self.half_open_calls = 0
            
            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success in closed state
                if self.failure_count > 0:
                    self.failure_count = max(0, self.failure_count - 1)
    
    def _record_failure(self, duration: float, exception: Exception) -> None:
        """Record a failed call"""
        with self._lock:
            self.total_failures += 1
            self.last_failure_time = time.time()
            self.failure_count += 1
            
            # Add to metrics
            self.call_metrics.append(CallMetrics(
                timestamp=datetime.now(),
                duration=duration,
                succeeded=False,
                exception=exception
            ))
            
            if self.state == CircuitState.HALF_OPEN:
                # Failure in half-open state, reopen circuit
                logger.warning(
                    f"Circuit {self.name} failed in HALF_OPEN, reopening"
                )
                self._open_circuit()
    
    def _is_expected_exception(self, exception: Exception) -> bool:
        """Check if exception should trigger circuit breaker"""
        return any(
            isinstance(exception, exc_type)
            for exc_type in self.config.expected_exceptions
        )
    
    def _cleanup_old_metrics(self) -> None:
        """Remove metrics outside the time window"""
        cutoff = datetime.now() - timedelta(seconds=self.config.window_size)
        
        # Remove old metrics
        while self.call_metrics and self.call_metrics[0].timestamp < cutoff:
            self.call_metrics.popleft()
    
    def _calculate_failure_rate(self) -> float:
        """Calculate current failure rate"""
        self._cleanup_old_metrics()
        
        if not self.call_metrics:
            return 0.0
        
        failures = sum(1 for m in self.call_metrics if not m.succeeded)
        return failures / len(self.call_metrics)
    
    def _calculate_slow_call_rate(self) -> float:
        """Calculate rate of slow calls"""
        if not self.config.slow_call_duration:
            return 0.0
        
        self._cleanup_old_metrics()
        
        if not self.call_metrics:
            return 0.0
        
        slow_calls = sum(
            1 for m in self.call_metrics
            if m.duration >= self.config.slow_call_duration
        )
        return slow_calls / len(self.call_metrics)
    
    def reset(self) -> None:
        """Reset circuit breaker to closed state"""
        with self._lock:
            logger.info(f"Resetting circuit {self.name}")
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.half_open_calls = 0
            self.last_failure_time = None
            self.last_success_time = None
    
    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status"""
        with self._lock:
            self._cleanup_old_metrics()
            
            return {
                "name": self.name,
                "state": self.state.value,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "total_calls": self.total_calls,
                "total_failures": self.total_failures,
                "total_successes": self.total_successes,
                "circuit_opens": self.circuit_opens,
                "fallback_calls": self.fallback_calls,
                "failure_rate": self._calculate_failure_rate(),
                "slow_call_rate": self._calculate_slow_call_rate(),
                "last_failure_time": self.last_failure_time,
                "last_success_time": self.last_success_time,
                "metrics_window_size": len(self.call_metrics)
            }


class CircuitBreakerManager:
    """Manages multiple circuit breakers"""
    
    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.RLock()
    
    def get_or_create(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """Get existing or create new circuit breaker"""
        with self._lock:
            if name not in self.breakers:
                self.breakers[name] = CircuitBreaker(name, config)
            return self.breakers[name]
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all circuit breakers"""
        with self._lock:
            return {
                name: breaker.get_status()
                for name, breaker in self.breakers.items()
            }
    
    def reset_all(self) -> None:
        """Reset all circuit breakers"""
        with self._lock:
            for breaker in self.breakers.values():
                breaker.reset()
    
    def reset(self, name: str) -> None:
        """Reset specific circuit breaker"""
        with self._lock:
            if name in self.breakers:
                self.breakers[name].reset()


# ============================================================================
# Global Circuit Breaker Manager
# ============================================================================

global_circuit_manager = CircuitBreakerManager()


# ============================================================================
# Decorator for Circuit Breaker
# ============================================================================

def with_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    timeout: float = 60.0,
    fallback: Optional[Callable] = None,
    **kwargs
):
    """
    Decorator for adding circuit breaker to functions
    
    Usage:
        @with_circuit_breaker("api_service", failure_threshold=3)
        def api_call():
            # Your code here
            pass
    """
    config = CircuitBreakerConfig(
        failure_threshold=failure_threshold,
        timeout=timeout,
        fallback_function=fallback,
        **kwargs
    )
    
    def decorator(func):
        import asyncio
        
        # Get or create circuit breaker
        breaker = global_circuit_manager.get_or_create(name, config)
        
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await breaker.call_async(func, *args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return breaker.call(func, *args, **kwargs)
            return sync_wrapper
    
    return decorator


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    import random
    import asyncio
    
    # Example 1: Simple circuit breaker with decorator
    @with_circuit_breaker("example_service", failure_threshold=2, timeout=5.0)
    def unreliable_service():
        if random.random() < 0.7:  # 70% failure rate
            raise NetworkError("Service unavailable", endpoint="example.com")
        return "Success"
    
    # Test the circuit breaker
    for i in range(10):
        try:
            result = unreliable_service()
            print(f"Call {i+1}: {result}")
        except (NetworkError, CircuitBreakerError) as e:
            print(f"Call {i+1} failed: {e}")
        time.sleep(1)
    
    # Example 2: Manual circuit breaker with fallback
    def fallback_function():
        return "Fallback response"
    
    config = CircuitBreakerConfig(
        failure_threshold=3,
        timeout=10.0,
        fallback_function=fallback_function
    )
    
    breaker = CircuitBreaker("database", config)
    
    def database_query():
        if random.random() < 0.5:
            raise DatabaseError("Connection lost")
        return "Query result"
    
    for i in range(5):
        try:
            result = breaker.call(database_query)
            print(f"Query {i+1}: {result}")
        except Exception as e:
            print(f"Query {i+1} failed: {e}")
    
    # Example 3: Get circuit breaker status
    status = breaker.get_status()
    print(f"Circuit breaker status: {status}")
    
    # Example 4: Global manager status
    all_status = global_circuit_manager.get_all_status()
    print(f"All circuit breakers: {all_status}")
