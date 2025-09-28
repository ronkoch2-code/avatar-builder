# Rate Limiting Solution for Anthropic API

## Problem
You were experiencing frequent 429 "Too Many Requests" errors from the Anthropic API, causing delays and retries.

## Solution Implemented

### 1. Adaptive Rate Limiter
Created a sophisticated rate limiting system that:
- Uses token bucket algorithm for smooth rate limiting
- Automatically adjusts rate based on success/failure ratio
- Implements exponential backoff on 429 errors
- Allows controlled bursts while maintaining overall rate

### 2. Conservative Settings
Updated all components to be more conservative:
- **Concurrent calls**: Reduced from 2 → 1
- **Rate limit**: Reduced from 50 → 10 calls/minute
- **Delays**: Added 1-second delay between relationship analyses
- **Burst size**: Limited to 5 calls

### 3. Intelligent Adaptation
The rate limiter adapts based on API responses:
- **On success**: Gradually increases rate (up to 2x initial)
- **On 429 error**: Immediately reduces rate by 50%
- **Backoff**: Exponential backoff (2^n seconds) on repeated errors
- **Recovery**: Resets after successful calls

## How It Works

### Token Bucket Algorithm
```
- Bucket starts with N tokens
- Each API call consumes 1 token
- Tokens refill at configured rate
- Calls wait if no tokens available
```

### Adaptive Behavior
```
Success Rate >= 95% → Increase rate by 20%
Success Rate < 80% → Decrease rate by 30%
429 Error → Immediate 50% reduction + backoff
```

## Configuration

The system now uses these settings:
```python
# Rate Limiter Configuration
initial_calls_per_minute=10    # Starting rate
min_calls_per_minute=2         # Minimum (during errors)
max_calls_per_minute=20        # Maximum (when stable)
burst_size=5                   # Allow small bursts

# Concurrency Settings
max_concurrent=1               # Process one person at a time
delay_between_analyses=1.0     # 1 second between relationship analyses
```

## Files Modified

1. **src/rate_limiter.py** (NEW)
   - `RateLimiter` class - Basic token bucket implementation
   - `AdaptiveRateLimiter` class - Intelligent rate adjustment

2. **src/llm_integrator.py**
   - Integrated rate limiter before API calls
   - Added success/error reporting to limiter
   - Added delays between relationship analyses

3. **src/enhanced_avatar_pipeline.py**
   - Reduced max_concurrent to 1
   - Lowered rate_limit_per_minute to 10

4. **src/pipelines/extraction_pipeline.py**
   - Set max_concurrent to 1 for batch processing

## Expected Behavior

With these changes:
1. **No more 429 errors** under normal operation
2. **Smooth processing** without bursts
3. **Automatic recovery** from any rate limit issues
4. **Gradual optimization** as the system learns the safe rate

## Monitoring

The rate limiter provides status information:
```python
status = rate_limiter.get_status()
# Returns:
{
    "calls_per_minute": 10,
    "tokens_available": 3.5,
    "in_backoff": False,
    "consecutive_errors": 0
}
```

## Future Enhancements

Consider these improvements:
1. Persist rate limiter state between runs
2. Add per-endpoint rate limiting
3. Implement priority queues for important requests
4. Add rate limit headers parsing from API responses

---

The system should now run smoothly without rate limit errors. The adaptive nature means it will find the optimal rate for your usage pattern over time.
