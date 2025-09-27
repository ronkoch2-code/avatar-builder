#!/usr/bin/env python3
"""
Retry Manager Module - Intelligent retry logic with exponential backoff
========================================================================

Provides sophisticated retry mechanisms with:
- Exponential backoff with jitter
- Circuit breaker integration
- Retry budgets and quotas
- Customizable retry strategies
- Detailed retry metrics
"""

import time
import random
import logging
import asyncio
from typing import Callable, Optional, Any, Dict, List, Union, TypeVar, Type
from functools import wraps
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

# Import error handler for integration
from .error_handler import AvatarEngineError, NetworkError, APIError, DatabaseError

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for generic return types
T = TypeVar('T')


class RetryStrategy(Enum):
    """Retry strategies available"""
    EXPONENTIAL = "exponential"  # Exponential backoff
    LINEAR = "linear"  # Linear backoff
    CONSTANT = "constant"  # Constant delay
    FIBONACCI = "fibonacci"  # Fibonacci sequence backoff
    DECORRELATED = "decorrelated"  # Decorrelated jitter


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    jitter: bool = True
    jitter_range: tuple = (0.8, 1.2)  # 80% to 120% of calculated delay
    
    # Retry conditions
    retry_on_exceptions: List[Type[Exception]] = field(default_factory=lambda: [
        NetworkError, APIError, DatabaseError, ConnectionError, TimeoutError
    ])
    retry_on_status_codes: List[int] = field(default_factory=lambda: [
        429,  # Too Many Requests
        500, 501, 502, 503, 504,  # Server errors
        408,  # Request Timeout
    ])
    
    # Advanced options
    deadline: Optional[timedelta] = None  # Total time limit for all retries
    retry_budget: Optional[int] = None  # Max retries across all operations per time window
    budget_window: timedelta = timedelta(minutes=1)


@dataclass
class RetryAttempt:
    """Information about a single retry attempt"""
    attempt_number: int
    delay: float
    timestamp: datetime
    exception: Optional[Exception] = None
    result: Optional[Any] = None
    succeeded: bool = False


@dataclass
class RetryResult:
    """Result of a retry operation"""
    succeeded: bool
    result: Optional[Any]
    attempts: List[RetryAttempt]
    total_duration: float
    final_exception: Optional[Exception] = None


class RetryBudget:
    """Manages retry budget to prevent retry storms"""
    
    def __init__(self, max_retries: int, window: timedelta):
        self.max_retries = max_retries
        self.window = window
        self.attempts = deque()
    
    def can_retry(self) -> bool:
        """Check if retry is allowed within budget"""
        self._cleanup_old_attempts()
        return len(self.attempts) < self.max_retries
    
    def record_attempt(self) -> None:
        """Record a retry attempt"""
        self.attempts.append(datetime.now())
    
    def _cleanup_old_attempts(self) -> None:
        """Remove attempts outside the time window"""
        cutoff = datetime.now() - self.window
        while self.attempts and self.attempts[0] < cutoff:
            self.attempts.popleft()
    
    def get_usage(self) -> Dict[str, Any]:
        """Get current budget usage"""
        self._cleanup_old_attempts()
        return {
            "used": len(self.attempts),
            "available": max(0, self.max_retries - len(self.attempts)),
            "percentage": (len(self.attempts) / self.max_retries * 100) if self.max_retries else 0
        }


class RetryManager:
    """Manages retry logic with various strategies"""
    
    def __init__(self, default_config: Optional[RetryConfig] = None):
        self.default_config = default_config or RetryConfig()
        self.budgets: Dict[str, RetryBudget] = {}
        self.metrics = {
            "total_retries": 0,
            "successful_retries": 0,
            "failed_retries": 0,
            "total_delay_time": 0.0,
            "retry_storms_prevented": 0
        }
        self._fibonacci_cache = [0, 1]  # Cache for Fibonacci sequence
    
    def retry(
        self,
        func: Callable[..., T],
        *args,
        config: Optional[RetryConfig] = None,
        budget_key: Optional[str] = None,
        **kwargs
    ) -> RetryResult:
        """
        Execute function with retry logic
        
        Args:
            func: Function to execute
            config: Retry configuration (uses default if None)
            budget_key: Key for retry budget tracking
            *args, **kwargs: Arguments for the function
        
        Returns:
            RetryResult with execution details
        """
        config = config or self.default_config
        attempts = []
        start_time = time.time()
        deadline = time.time() + config.deadline.total_seconds() if config.deadline else None
        
        # Check budget if configured
        if budget_key and config.retry_budget:
            if budget_key not in self.budgets:
                self.budgets[budget_key] = RetryBudget(
                    config.retry_budget,
                    config.budget_window
                )
        
        for attempt_num in range(config.max_attempts):
            # Check deadline
            if deadline and time.time() > deadline:
                logger.warning(f"Retry deadline exceeded after {attempt_num} attempts")
                break
            
            # Check budget
            if budget_key and budget_key in self.budgets:
                if not self.budgets[budget_key].can_retry():
                    logger.warning(f"Retry budget exhausted for {budget_key}")
                    self.metrics["retry_storms_prevented"] += 1
                    break
                self.budgets[budget_key].record_attempt()
            
            # Calculate delay
            delay = self._calculate_delay(attempt_num, config) if attempt_num > 0 else 0
            
            if delay > 0:
                logger.info(f"Retry attempt {attempt_num + 1}/{config.max_attempts} after {delay:.2f}s delay")
                time.sleep(delay)
                self.metrics["total_delay_time"] += delay
            
            # Create attempt record
            attempt = RetryAttempt(
                attempt_number=attempt_num + 1,
                delay=delay,
                timestamp=datetime.now()
            )
            
            try:
                # Execute function
                result = func(*args, **kwargs)
                attempt.result = result
                attempt.succeeded = True
                attempts.append(attempt)
                
                # Update metrics
                if attempt_num > 0:
                    self.metrics["successful_retries"] += 1
                
                return RetryResult(
                    succeeded=True,
                    result=result,
                    attempts=attempts,
                    total_duration=time.time() - start_time
                )
                
            except Exception as e:
                attempt.exception = e
                attempts.append(attempt)
                
                # Check if we should retry this exception
                if not self._should_retry(e, config):
                    logger.error(f"Exception not retryable: {e}")
                    break
                
                # Log the retry
                logger.warning(
                    f"Attempt {attempt_num + 1} failed with {type(e).__name__}: {e}"
                )
                
                # Update metrics
                self.metrics["total_retries"] += 1
                
                # If this was the last attempt, record failure
                if attempt_num == config.max_attempts - 1:
                    self.metrics["failed_retries"] += 1
        
        # All attempts failed
        return RetryResult(
            succeeded=False,
            result=None,
            attempts=attempts,
            total_duration=time.time() - start_time,
            final_exception=attempts[-1].exception if attempts else None
        )
    
    async def retry_async(
        self,
        func: Callable[..., T],
        *args,
        config: Optional[RetryConfig] = None,
        budget_key: Optional[str] = None,
        **kwargs
    ) -> RetryResult:
        """
        Async version of retry
        
        Args:
            func: Async function to execute
            config: Retry configuration
            budget_key: Key for retry budget tracking
            *args, **kwargs: Arguments for the function
        
        Returns:
            RetryResult with execution details
        """
        config = config or self.default_config
        attempts = []
        start_time = time.time()
        deadline = time.time() + config.deadline.total_seconds() if config.deadline else None
        
        # Check budget if configured
        if budget_key and config.retry_budget:
            if budget_key not in self.budgets:
                self.budgets[budget_key] = RetryBudget(
                    config.retry_budget,
                    config.budget_window
                )
        
        for attempt_num in range(config.max_attempts):
            # Check deadline
            if deadline and time.time() > deadline:
                logger.warning(f"Retry deadline exceeded after {attempt_num} attempts")
                break
            
            # Check budget
            if budget_key and budget_key in self.budgets:
                if not self.budgets[budget_key].can_retry():
                    logger.warning(f"Retry budget exhausted for {budget_key}")
                    self.metrics["retry_storms_prevented"] += 1
                    break
                self.budgets[budget_key].record_attempt()
            
            # Calculate delay
            delay = self._calculate_delay(attempt_num, config) if attempt_num > 0 else 0
            
            if delay > 0:
                logger.info(f"Retry attempt {attempt_num + 1}/{config.max_attempts} after {delay:.2f}s delay")
                await asyncio.sleep(delay)
                self.metrics["total_delay_time"] += delay
            
            # Create attempt record
            attempt = RetryAttempt(
                attempt_number=attempt_num + 1,
                delay=delay,
                timestamp=datetime.now()
            )
            
            try:
                # Execute async function
                result = await func(*args, **kwargs)
                attempt.result = result
                attempt.succeeded = True
                attempts.append(attempt)
                
                # Update metrics
                if attempt_num > 0:
                    self.metrics["successful_retries"] += 1
                
                return RetryResult(
                    succeeded=True,
                    result=result,
                    attempts=attempts,
                    total_duration=time.time() - start_time
                )
                
            except Exception as e:
                attempt.exception = e
                attempts.append(attempt)
                
                # Check if we should retry this exception
                if not self._should_retry(e, config):
                    logger.error(f"Exception not retryable: {e}")
                    break
                
                # Log the retry
                logger.warning(
                    f"Attempt {attempt_num + 1} failed with {type(e).__name__}: {e}"
                )
                
                # Update metrics
                self.metrics["total_retries"] += 1
                
                # If this was the last attempt, record failure
                if attempt_num == config.max_attempts - 1:
                    self.metrics["failed_retries"] += 1
        
        # All attempts failed
        return RetryResult(
            succeeded=False,
            result=None,
            attempts=attempts,
            total_duration=time.time() - start_time,
            final_exception=attempts[-1].exception if attempts else None
        )
    
    def _calculate_delay(self, attempt_num: int, config: RetryConfig) -> float:
        """Calculate delay based on strategy"""
        if config.strategy == RetryStrategy.EXPONENTIAL:
            delay = min(
                config.initial_delay * (config.exponential_base ** attempt_num),
                config.max_delay
            )
        
        elif config.strategy == RetryStrategy.LINEAR:
            delay = min(
                config.initial_delay * (attempt_num + 1),
                config.max_delay
            )
        
        elif config.strategy == RetryStrategy.CONSTANT:
            delay = config.initial_delay
        
        elif config.strategy == RetryStrategy.FIBONACCI:
            delay = min(
                config.initial_delay * self._get_fibonacci(attempt_num + 1),
                config.max_delay
            )
        
        elif config.strategy == RetryStrategy.DECORRELATED:
            # Decorrelated jitter - AWS recommended
            prev_delay = config.initial_delay if attempt_num == 0 else self._last_delay
            delay = min(
                random.uniform(config.initial_delay, prev_delay * 3),
                config.max_delay
            )
            self._last_delay = delay
        
        else:
            delay = config.initial_delay
        
        # Apply jitter if configured
        if config.jitter and config.strategy != RetryStrategy.DECORRELATED:
            jitter_min, jitter_max = config.jitter_range
            delay *= random.uniform(jitter_min, jitter_max)
        
        return delay
    
    def _get_fibonacci(self, n: int) -> int:
        """Get nth Fibonacci number (cached)"""
        while len(self._fibonacci_cache) <= n:
            self._fibonacci_cache.append(
                self._fibonacci_cache[-1] + self._fibonacci_cache[-2]
            )
        return self._fibonacci_cache[n]
    
    def _should_retry(self, exception: Exception, config: RetryConfig) -> bool:
        """Check if exception should trigger retry"""
        # Check exception type
        for exc_type in config.retry_on_exceptions:
            if isinstance(exception, exc_type):
                return True
        
        # Check status code for API errors
        if isinstance(exception, APIError):
            status_code = exception.additional_data.get('status_code')
            if status_code and status_code in config.retry_on_status_codes:
                return True
        
        return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get retry metrics"""
        success_rate = (
            self.metrics["successful_retries"] / self.metrics["total_retries"] * 100
            if self.metrics["total_retries"] > 0 else 0
        )
        
        return {
            **self.metrics,
            "success_rate": success_rate,
            "average_delay": (
                self.metrics["total_delay_time"] / self.metrics["total_retries"]
                if self.metrics["total_retries"] > 0 else 0
            ),
            "budgets": {
                key: budget.get_usage()
                for key, budget in self.budgets.items()
            }
        }
    
    def reset_metrics(self) -> None:
        """Reset metrics counters"""
        self.metrics = {
            "total_retries": 0,
            "successful_retries": 0,
            "failed_retries": 0,
            "total_delay_time": 0.0,
            "retry_storms_prevented": 0
        }


# ============================================================================
# Decorator for Retry Logic
# ============================================================================

def with_retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    **kwargs
):
    """
    Decorator for adding retry logic to functions
    
    Usage:
        @with_retry(max_attempts=5, initial_delay=2.0)
        def api_call():
            # Your code here
            pass
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        initial_delay=initial_delay,
        strategy=strategy,
        **kwargs
    )
    
    def decorator(func):
        # Check if function is async
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                manager = RetryManager()
                result = await manager.retry_async(func, *args, config=config, **kwargs)
                if not result.succeeded:
                    raise result.final_exception
                return result.result
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                manager = RetryManager()
                result = manager.retry(func, *args, config=config, **kwargs)
                if not result.succeeded:
                    raise result.final_exception
                return result.result
            return sync_wrapper
    
    return decorator


# ============================================================================
# Global Retry Manager Instance
# ============================================================================

# Create a global retry manager for the application
global_retry_manager = RetryManager(
    default_config=RetryConfig(
        max_attempts=3,
        initial_delay=1.0,
        max_delay=30.0,
        strategy=RetryStrategy.EXPONENTIAL,
        jitter=True
    )
)


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    import random
    
    # Example 1: Simple retry with decorator
    @with_retry(max_attempts=3, initial_delay=1.0)
    def unreliable_api_call():
        if random.random() < 0.7:  # 70% failure rate
            raise APIError("API temporarily unavailable", api_name="TestAPI", status_code=503)
        return {"status": "success"}
    
    try:
        result = unreliable_api_call()
        print(f"API call succeeded: {result}")
    except APIError as e:
        print(f"API call failed after retries: {e}")
    
    # Example 2: Manual retry with custom config
    def database_operation():
        if random.random() < 0.5:
            raise DatabaseError("Connection timeout")
        return "Data retrieved"
    
    config = RetryConfig(
        max_attempts=5,
        initial_delay=2.0,
        strategy=RetryStrategy.FIBONACCI,
        deadline=timedelta(seconds=30)
    )
    
    result = global_retry_manager.retry(
        database_operation,
        config=config,
        budget_key="database"
    )
    
    if result.succeeded:
        print(f"Database operation succeeded: {result.result}")
        print(f"Attempts made: {len(result.attempts)}")
        print(f"Total duration: {result.total_duration:.2f}s")
    else:
        print(f"Database operation failed: {result.final_exception}")
    
    # Example 3: Get metrics
    metrics = global_retry_manager.get_metrics()
    print(f"Retry metrics: {metrics}")
    
    # Example 4: Async retry
    async def async_example():
        @with_retry(max_attempts=3, strategy=RetryStrategy.DECORRELATED)
        async def async_api_call():
            await asyncio.sleep(0.1)
            if random.random() < 0.5:
                raise NetworkError("Network timeout", endpoint="api.example.com")
            return {"async": "result"}
        
        try:
            result = await async_api_call()
            print(f"Async call succeeded: {result}")
        except NetworkError as e:
            print(f"Async call failed: {e}")
    
    # Run async example
    asyncio.run(async_example())
