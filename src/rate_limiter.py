#!/usr/bin/env python3
"""
Rate Limiter for API Calls
==========================

Implements a token bucket algorithm for rate limiting API calls
to avoid 429 errors from external services like Anthropic.

Author: Avatar-Engine Team
Date: 2025-09-28
"""

import asyncio
import time
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter for API calls.
    
    This implementation uses a token bucket algorithm where:
    - Tokens are added at a fixed rate
    - Each API call consumes one token
    - Calls wait if no tokens are available
    """
    
    def __init__(self, 
                 calls_per_minute: int = 10,
                 burst_size: Optional[int] = None,
                 backoff_on_error: bool = True):
        """
        Initialize rate limiter.
        
        Args:
            calls_per_minute: Maximum calls per minute
            burst_size: Maximum burst size (defaults to calls_per_minute)
            backoff_on_error: Whether to implement exponential backoff on 429 errors
        """
        self.calls_per_minute = calls_per_minute
        self.interval = 60.0 / calls_per_minute  # Seconds between calls
        self.burst_size = burst_size or calls_per_minute
        self.backoff_on_error = backoff_on_error
        
        # Token bucket state
        self.tokens = float(self.burst_size)
        self.last_update = time.time()
        self.lock = asyncio.Lock()
        
        # Backoff state
        self.consecutive_errors = 0
        self.backoff_until = 0
        
        logger.info(f"RateLimiter initialized: {calls_per_minute} calls/min, burst size: {self.burst_size}")
    
    async def acquire(self, tokens: int = 1) -> None:
        """
        Acquire tokens before making an API call.
        Blocks until tokens are available.
        
        Args:
            tokens: Number of tokens to acquire (default: 1)
        """
        async with self.lock:
            while True:
                now = time.time()
                
                # Check if we're in backoff period
                if self.backoff_until > now:
                    wait_time = self.backoff_until - now
                    logger.info(f"Rate limiter in backoff, waiting {wait_time:.1f} seconds")
                    await asyncio.sleep(wait_time)
                    continue
                
                # Refill tokens based on time elapsed
                elapsed = now - self.last_update
                self.tokens = min(
                    self.burst_size,
                    self.tokens + elapsed / self.interval
                )
                self.last_update = now
                
                # Check if we have enough tokens
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    logger.debug(f"Acquired {tokens} token(s), {self.tokens:.1f} remaining")
                    return
                
                # Calculate wait time
                tokens_needed = tokens - self.tokens
                wait_time = tokens_needed * self.interval
                
                logger.debug(f"Rate limit: waiting {wait_time:.1f} seconds for {tokens} token(s)")
                await asyncio.sleep(wait_time)
    
    async def report_error(self, error_code: int) -> None:
        """
        Report an API error to adjust rate limiting.
        
        Args:
            error_code: HTTP error code (e.g., 429)
        """
        if error_code == 429 and self.backoff_on_error:
            async with self.lock:
                self.consecutive_errors += 1
                
                # Exponential backoff: 2^n seconds, max 5 minutes
                backoff_seconds = min(300, 2 ** self.consecutive_errors)
                self.backoff_until = time.time() + backoff_seconds
                
                logger.warning(f"Rate limit error #{self.consecutive_errors}, "
                             f"backing off for {backoff_seconds} seconds")
    
    async def report_success(self) -> None:
        """Report successful API call to reset error counter."""
        if self.consecutive_errors > 0:
            async with self.lock:
                self.consecutive_errors = 0
                self.backoff_until = 0
                logger.info("Rate limit backoff reset after successful call")
    
    def get_status(self) -> dict:
        """
        Get current rate limiter status.
        
        Returns:
            Dictionary with current status information
        """
        now = time.time()
        in_backoff = self.backoff_until > now
        
        return {
            "calls_per_minute": self.calls_per_minute,
            "tokens_available": self.tokens,
            "burst_size": self.burst_size,
            "in_backoff": in_backoff,
            "backoff_seconds_remaining": max(0, self.backoff_until - now) if in_backoff else 0,
            "consecutive_errors": self.consecutive_errors
        }


class AdaptiveRateLimiter(RateLimiter):
    """
    Adaptive rate limiter that adjusts rate based on API responses.
    
    This extends the basic rate limiter with adaptive behavior:
    - Reduces rate on errors
    - Increases rate on sustained success
    - Tracks performance metrics
    """
    
    def __init__(self, 
                 initial_calls_per_minute: int = 10,
                 min_calls_per_minute: int = 1,
                 max_calls_per_minute: int = 60,
                 **kwargs):
        """
        Initialize adaptive rate limiter.
        
        Args:
            initial_calls_per_minute: Starting rate
            min_calls_per_minute: Minimum rate (during errors)
            max_calls_per_minute: Maximum rate (when stable)
            **kwargs: Additional arguments for RateLimiter
        """
        super().__init__(calls_per_minute=initial_calls_per_minute, **kwargs)
        
        self.min_rate = min_calls_per_minute
        self.max_rate = max_calls_per_minute
        self.initial_rate = initial_calls_per_minute
        
        # Adaptive state
        self.successful_calls = 0
        self.total_calls = 0
        self.last_adjustment = time.time()
        self.adjustment_interval = 60  # Adjust every minute
        
        logger.info(f"AdaptiveRateLimiter: {min_calls_per_minute}-{max_calls_per_minute} calls/min")
    
    async def report_success(self) -> None:
        """Report successful API call and potentially increase rate."""
        await super().report_success()
        
        async with self.lock:
            self.successful_calls += 1
            self.total_calls += 1
            
            # Check if we should adjust rate
            now = time.time()
            if now - self.last_adjustment > self.adjustment_interval:
                self._adjust_rate()
                self.last_adjustment = now
    
    async def report_error(self, error_code: int) -> None:
        """Report API error and potentially decrease rate."""
        await super().report_error(error_code)
        
        async with self.lock:
            self.total_calls += 1
            
            if error_code == 429:
                # Immediately reduce rate on 429
                old_rate = self.calls_per_minute
                self.calls_per_minute = max(
                    self.min_rate,
                    self.calls_per_minute * 0.5  # Reduce by 50%
                )
                self.interval = 60.0 / self.calls_per_minute
                
                logger.warning(f"Reduced rate from {old_rate} to {self.calls_per_minute} calls/min")
    
    def _adjust_rate(self) -> None:
        """Adjust rate based on success ratio."""
        if self.total_calls == 0:
            return
        
        success_ratio = self.successful_calls / self.total_calls
        old_rate = self.calls_per_minute
        
        if success_ratio >= 0.95 and self.consecutive_errors == 0:
            # Increase rate by 20% on high success
            self.calls_per_minute = min(
                self.max_rate,
                self.calls_per_minute * 1.2
            )
        elif success_ratio < 0.8:
            # Decrease rate by 30% on low success
            self.calls_per_minute = max(
                self.min_rate,
                self.calls_per_minute * 0.7
            )
        
        self.interval = 60.0 / self.calls_per_minute
        
        if old_rate != self.calls_per_minute:
            logger.info(f"Adjusted rate from {old_rate:.1f} to {self.calls_per_minute:.1f} calls/min "
                       f"(success ratio: {success_ratio:.2%})")
        
        # Reset counters
        self.successful_calls = 0
        self.total_calls = 0


# Example usage
async def example_usage():
    """Example of using the rate limiter."""
    
    # Create an adaptive rate limiter
    rate_limiter = AdaptiveRateLimiter(
        initial_calls_per_minute=15,
        min_calls_per_minute=5,
        max_calls_per_minute=30
    )
    
    # Simulate API calls
    for i in range(10):
        # Acquire permission to make call
        await rate_limiter.acquire()
        
        # Simulate API call
        print(f"Making API call {i+1}")
        
        # Simulate success/error
        if i % 5 == 4:
            # Simulate rate limit error
            await rate_limiter.report_error(429)
        else:
            await rate_limiter.report_success()
        
        # Check status
        if i % 3 == 0:
            status = rate_limiter.get_status()
            print(f"Status: {status}")


if __name__ == "__main__":
    asyncio.run(example_usage())
