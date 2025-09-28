#!/usr/bin/env python3
"""
Anthropic Token Balance Monitoring Module
=========================================

Provides comprehensive token usage tracking, balance monitoring, and cost analysis
for Anthropic API calls throughout the Avatar-Engine system.

Features:
- Real-time token usage tracking
- Balance queries and threshold alerts
- Cost calculation and reporting
- Session aggregation and history storage
- Prompt caching effectiveness tracking

Author: Avatar-Engine Team
Date: 2025-09-28
Version: 1.0.0
"""

import json
import logging
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import asyncio
import anthropic
from anthropic import Anthropic

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TokenAlertLevel(Enum):
    """Alert levels for token usage"""
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    EXCEEDED = "exceeded"


@dataclass
class TokenUsage:
    """Represents token usage for a single API call"""
    timestamp: datetime
    session_id: str
    model: str
    operation: str
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    cost_usd: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def total_tokens(self) -> int:
        """Total tokens used"""
        return self.input_tokens + self.output_tokens
    
    @property
    def cache_savings(self) -> float:
        """Estimated savings from cache hits"""
        # Cache reads are typically 90% cheaper
        if self.cache_read_tokens > 0:
            full_cost = (self.cache_read_tokens / 1_000_000) * self._get_input_price()
            cache_cost = full_cost * 0.1  # 10% of regular cost
            return full_cost - cache_cost
        return 0.0
    
    def _get_input_price(self) -> float:
        """Get input token price for the model"""
        prices = {
            "claude-3-5-sonnet-20240620": 3.00,
            "claude-3-opus-20240229": 15.00,
            "claude-3-haiku-20240307": 0.25,
            "claude-sonnet-4-20250514": 3.00  # Adjust as needed
        }
        return prices.get(self.model, 3.00)


@dataclass
class SessionSummary:
    """Summary of token usage for a session"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cache_read_tokens: int = 0
    total_cache_write_tokens: int = 0
    total_cost: float = 0.0
    total_cache_savings: float = 0.0
    num_requests: int = 0
    operations: Dict[str, int] = field(default_factory=dict)
    
    @property
    def total_tokens(self) -> int:
        return self.total_input_tokens + self.total_output_tokens
    
    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate percentage"""
        total_input = self.total_input_tokens + self.total_cache_read_tokens
        if total_input == 0:
            return 0.0
        return (self.total_cache_read_tokens / total_input) * 100


class TokenMonitor:
    """Central token monitoring system for Anthropic API usage"""
    
    # Model pricing per 1M tokens
    PRICING = {
        "claude-3-5-sonnet-20240620": {"input": 3.00, "output": 15.00},
        "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
        "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00}  # Update with actual pricing
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize token monitor
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or self._get_default_config()
        self.current_session_id = self._generate_session_id()
        self.current_session = SessionSummary(
            session_id=self.current_session_id,
            start_time=datetime.now()
        )
        
        # Initialize database
        self.db_path = Path(self.config['storage']['db_path']).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True, mode=0o750)
        self._init_database()
        
        # Initialize Anthropic client for balance queries
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            self.anthropic_client = Anthropic(api_key=api_key)
        else:
            self.anthropic_client = None
            logger.warning("No Anthropic API key found. Balance queries disabled.")
        
        # Track usage history in memory for quick access
        self.usage_history: List[TokenUsage] = []
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "enabled": True,
            "thresholds": {
                "daily_limit": 1_000_000,
                "warning_percent": 80,
                "critical_percent": 95
            },
            "display": {
                "show_per_request": False,
                "show_session_summary": True,
                "show_daily_summary": True,
                "format": "detailed"  # "detailed" or "compact"
            },
            "storage": {
                "db_path": "~/.avatar-engine/token_usage.db",
                "retention_days": 30,
                "backup_enabled": True
            },
            "alerts": {
                "enabled": True,
                "log_alerts": True,
                "email_alerts": False
            }
        }
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def _init_database(self):
        """Initialize SQLite database for token usage history"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Token usage table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS token_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    session_id TEXT NOT NULL,
                    model TEXT NOT NULL,
                    operation TEXT,
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    cache_read_tokens INTEGER DEFAULT 0,
                    cache_write_tokens INTEGER DEFAULT 0,
                    cost_usd REAL DEFAULT 0.0,
                    metadata TEXT
                )
            """)
            
            # Daily summary table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_token_summary (
                    date DATE PRIMARY KEY,
                    total_input_tokens INTEGER DEFAULT 0,
                    total_output_tokens INTEGER DEFAULT 0,
                    total_cache_hits INTEGER DEFAULT 0,
                    total_cost_usd REAL DEFAULT 0.0,
                    num_requests INTEGER DEFAULT 0,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Session summary table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS session_summary (
                    session_id TEXT PRIMARY KEY,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME,
                    total_input_tokens INTEGER DEFAULT 0,
                    total_output_tokens INTEGER DEFAULT 0,
                    total_cache_read_tokens INTEGER DEFAULT 0,
                    total_cache_write_tokens INTEGER DEFAULT 0,
                    total_cost REAL DEFAULT 0.0,
                    total_cache_savings REAL DEFAULT 0.0,
                    num_requests INTEGER DEFAULT 0,
                    operations TEXT
                )
            """)
            
            # Create indices
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON token_usage(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_session ON token_usage(session_id)")
            
            conn.commit()
    
    def track_request(self, 
                     model: str,
                     operation: str,
                     response: Optional[Any] = None,
                     response_headers: Optional[Dict[str, str]] = None,
                     input_tokens: Optional[int] = None,
                     output_tokens: Optional[int] = None) -> TokenUsage:
        """
        Track token usage for an API request
        
        Args:
            model: Model name used
            operation: Type of operation (e.g., "personality_analysis")
            response: Anthropic API response object
            response_headers: Response headers containing token counts
            input_tokens: Manual input token count
            output_tokens: Manual output token count
            
        Returns:
            TokenUsage object with tracked data
        """
        # Extract token counts
        if response and hasattr(response, 'usage'):
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            # Check for cache tokens if available
            cache_read = getattr(response.usage, 'cache_read_tokens', 0)
            cache_write = getattr(response.usage, 'cache_write_tokens', 0)
        elif response_headers:
            input_tokens = int(response_headers.get("anthropic-input-tokens", 0))
            output_tokens = int(response_headers.get("anthropic-output-tokens", 0))
            cache_read = int(response_headers.get("anthropic-cache-read-tokens", 0))
            cache_write = int(response_headers.get("anthropic-cache-write-tokens", 0))
        else:
            input_tokens = input_tokens or 0
            output_tokens = output_tokens or 0
            cache_read = 0
            cache_write = 0
        
        # Calculate cost
        cost = self._calculate_cost(model, input_tokens, output_tokens)
        
        # Create usage record
        usage = TokenUsage(
            timestamp=datetime.now(),
            session_id=self.current_session_id,
            model=model,
            operation=operation,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read,
            cache_write_tokens=cache_write,
            cost_usd=cost,
            metadata={"operation": operation}
        )
        
        # Update current session
        self._update_session(usage)
        
        # Store in history
        self.usage_history.append(usage)
        
        # Save to database
        self._save_usage_to_db(usage)
        
        # Check thresholds
        self._check_thresholds(usage)
        
        # Display if configured
        if self.config['display']['show_per_request']:
            self._display_usage(usage)
        
        return usage
    
    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for token usage"""
        pricing = self.PRICING.get(model, {"input": 3.00, "output": 15.00})
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return round(input_cost + output_cost, 6)
    
    def _update_session(self, usage: TokenUsage):
        """Update current session summary"""
        self.current_session.total_input_tokens += usage.input_tokens
        self.current_session.total_output_tokens += usage.output_tokens
        self.current_session.total_cache_read_tokens += usage.cache_read_tokens
        self.current_session.total_cache_write_tokens += usage.cache_write_tokens
        self.current_session.total_cost += usage.cost_usd
        self.current_session.total_cache_savings += usage.cache_savings
        self.current_session.num_requests += 1
        
        # Track operations
        if usage.operation not in self.current_session.operations:
            self.current_session.operations[usage.operation] = 0
        self.current_session.operations[usage.operation] += 1
    
    def _save_usage_to_db(self, usage: TokenUsage):
        """Save usage record to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO token_usage (
                        timestamp, session_id, model, operation,
                        input_tokens, output_tokens, cache_read_tokens, cache_write_tokens,
                        cost_usd, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    usage.timestamp, usage.session_id, usage.model, usage.operation,
                    usage.input_tokens, usage.output_tokens, 
                    usage.cache_read_tokens, usage.cache_write_tokens,
                    usage.cost_usd, json.dumps(usage.metadata)
                ))
                
                # Update daily summary
                self._update_daily_summary(cursor, usage)
                
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save token usage to database: {e}")
    
    def _update_daily_summary(self, cursor: sqlite3.Cursor, usage: TokenUsage):
        """Update daily summary in database"""
        today = datetime.now().date()
        
        cursor.execute("""
            INSERT OR REPLACE INTO daily_token_summary (
                date, total_input_tokens, total_output_tokens, 
                total_cache_hits, total_cost_usd, num_requests, last_updated
            ) VALUES (
                ?,
                COALESCE((SELECT total_input_tokens FROM daily_token_summary WHERE date = ?), 0) + ?,
                COALESCE((SELECT total_output_tokens FROM daily_token_summary WHERE date = ?), 0) + ?,
                COALESCE((SELECT total_cache_hits FROM daily_token_summary WHERE date = ?), 0) + ?,
                COALESCE((SELECT total_cost_usd FROM daily_token_summary WHERE date = ?), 0) + ?,
                COALESCE((SELECT num_requests FROM daily_token_summary WHERE date = ?), 0) + 1,
                CURRENT_TIMESTAMP
            )
        """, (
            today,
            today, usage.input_tokens,
            today, usage.output_tokens,
            today, usage.cache_read_tokens,
            today, usage.cost_usd,
            today
        ))
    
    def _check_thresholds(self, usage: TokenUsage) -> TokenAlertLevel:
        """Check usage against configured thresholds"""
        daily_usage = self.get_daily_usage()
        daily_limit = self.config['thresholds']['daily_limit']
        
        usage_percent = (daily_usage['total_tokens'] / daily_limit) * 100
        
        if usage_percent >= 100:
            level = TokenAlertLevel.EXCEEDED
            logger.error(f"Daily token limit EXCEEDED: {daily_usage['total_tokens']:,}/{daily_limit:,}")
        elif usage_percent >= self.config['thresholds']['critical_percent']:
            level = TokenAlertLevel.CRITICAL
            logger.warning(f"CRITICAL token usage: {usage_percent:.1f}% of daily limit")
        elif usage_percent >= self.config['thresholds']['warning_percent']:
            level = TokenAlertLevel.WARNING
            logger.warning(f"High token usage: {usage_percent:.1f}% of daily limit")
        else:
            level = TokenAlertLevel.NORMAL
        
        return level
    
    def _display_usage(self, usage: TokenUsage):
        """Display token usage information"""
        if self.config['display']['format'] == 'detailed':
            print(f"\n--- Token Usage ---")
            print(f"Operation: {usage.operation}")
            print(f"Input: {usage.input_tokens:,} tokens")
            print(f"Output: {usage.output_tokens:,} tokens")
            if usage.cache_read_tokens > 0:
                print(f"Cache Hits: {usage.cache_read_tokens:,} tokens")
            print(f"Cost: ${usage.cost_usd:.4f}")
        else:
            print(f"Tokens: {usage.total_tokens:,} (${usage.cost_usd:.4f})")
    
    def get_balance(self) -> Optional[Dict[str, Any]]:
        """
        Query Anthropic for remaining balance and usage
        
        Note: This is a placeholder as Anthropic doesn't currently provide
        a direct balance API. This would need to be implemented based on
        your account setup or billing API if available.
        
        Returns:
            Balance information or None if unavailable
        """
        # This is a simulated response - replace with actual API call when available
        daily_usage = self.get_daily_usage()
        daily_limit = self.config['thresholds']['daily_limit']
        
        return {
            "daily_limit": daily_limit,
            "daily_used": daily_usage['total_tokens'],
            "daily_remaining": daily_limit - daily_usage['total_tokens'],
            "percent_used": (daily_usage['total_tokens'] / daily_limit) * 100,
            "cost_today": daily_usage['total_cost'],
            "status": "active"
        }
    
    def get_daily_usage(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get token usage for a specific day"""
        target_date = (date or datetime.now()).date()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT total_input_tokens, total_output_tokens, 
                           total_cache_hits, total_cost_usd, num_requests
                    FROM daily_token_summary
                    WHERE date = ?
                """, (target_date,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        "date": target_date.isoformat(),
                        "input_tokens": row[0],
                        "output_tokens": row[1],
                        "cache_hits": row[2],
                        "total_tokens": row[0] + row[1],
                        "total_cost": row[3],
                        "num_requests": row[4]
                    }
        except Exception as e:
            logger.error(f"Failed to get daily usage: {e}")
        
        return {
            "date": target_date.isoformat(),
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_hits": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "num_requests": 0
        }
    
    def get_session_summary(self, format: str = "detailed") -> str:
        """Get formatted summary of current session"""
        summary = self.current_session
        
        if format == "detailed":
            lines = [
                "\n" + "=" * 50,
                f"Token Usage Summary - {summary.session_id}",
                "=" * 50,
                f"\nTokens Used:",
                f"  Input:        {summary.total_input_tokens:>10,} tokens",
                f"  Output:       {summary.total_output_tokens:>10,} tokens",
                f"  Total:        {summary.total_tokens:>10,} tokens",
                f"\nCache Performance:",
                f"  Cache Reads:  {summary.total_cache_read_tokens:>10,} tokens",
                f"  Cache Writes: {summary.total_cache_write_tokens:>10,} tokens",
                f"  Hit Rate:     {summary.cache_hit_rate:>10.1f}%",
                f"  Savings:      ${summary.total_cache_savings:>9.4f}",
                f"\nCost Analysis:",
                f"  Total Cost:   ${summary.total_cost:>9.4f}",
                f"  Requests:     {summary.num_requests:>10,}",
                f"  Avg Cost:     ${(summary.total_cost / max(1, summary.num_requests)):>9.4f}",
            ]
            
            # Add balance information
            balance = self.get_balance()
            if balance:
                lines.extend([
                    f"\nDaily Usage:",
                    f"  Limit:        {balance['daily_limit']:>10,} tokens",
                    f"  Used:         {balance['daily_used']:>10,} tokens",
                    f"  Remaining:    {balance['daily_remaining']:>10,} tokens",
                    f"  Percent:      {balance['percent_used']:>10.1f}%"
                ])
            
            # Add operation breakdown
            if summary.operations:
                lines.extend(["\nOperations:"])
                for op, count in summary.operations.items():
                    lines.append(f"  {op:20s}: {count:>5,} calls")
            
            lines.append("=" * 50)
            return "\n".join(lines)
        else:
            # Compact format
            return (f"Tokens: {summary.total_tokens:,} | "
                   f"Cost: ${summary.total_cost:.4f} | "
                   f"Requests: {summary.num_requests}")
    
    def end_session(self) -> SessionSummary:
        """End current session and save summary"""
        self.current_session.end_time = datetime.now()
        
        # Save session summary to database
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO session_summary (
                        session_id, start_time, end_time,
                        total_input_tokens, total_output_tokens,
                        total_cache_read_tokens, total_cache_write_tokens,
                        total_cost, total_cache_savings, num_requests, operations
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.current_session.session_id,
                    self.current_session.start_time,
                    self.current_session.end_time,
                    self.current_session.total_input_tokens,
                    self.current_session.total_output_tokens,
                    self.current_session.total_cache_read_tokens,
                    self.current_session.total_cache_write_tokens,
                    self.current_session.total_cost,
                    self.current_session.total_cache_savings,
                    self.current_session.num_requests,
                    json.dumps(self.current_session.operations)
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save session summary: {e}")
        
        # Display final summary if configured
        if self.config['display']['show_session_summary']:
            print(self.get_session_summary())
        
        # Return the completed session
        completed_session = self.current_session
        
        # Start new session
        self.current_session_id = self._generate_session_id()
        self.current_session = SessionSummary(
            session_id=self.current_session_id,
            start_time=datetime.now()
        )
        
        return completed_session
    
    def generate_report(self, days: int = 7, format: str = "text") -> str:
        """
        Generate usage report for specified number of days
        
        Args:
            days: Number of days to include in report
            format: Report format ("text", "json", "csv")
            
        Returns:
            Formatted report string
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days-1)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT date, total_input_tokens, total_output_tokens,
                           total_cache_hits, total_cost_usd, num_requests
                    FROM daily_token_summary
                    WHERE date >= ? AND date <= ?
                    ORDER BY date DESC
                """, (start_date, end_date))
                
                rows = cursor.fetchall()
                
                if format == "json":
                    report_data = []
                    for row in rows:
                        report_data.append({
                            "date": row[0],
                            "input_tokens": row[1],
                            "output_tokens": row[2],
                            "cache_hits": row[3],
                            "total_cost": row[4],
                            "requests": row[5]
                        })
                    return json.dumps(report_data, indent=2, default=str)
                
                elif format == "csv":
                    lines = ["Date,Input Tokens,Output Tokens,Cache Hits,Total Cost,Requests"]
                    for row in rows:
                        lines.append(f"{row[0]},{row[1]},{row[2]},{row[3]},{row[4]:.4f},{row[5]}")
                    return "\n".join(lines)
                
                else:  # text format
                    lines = [
                        "\n" + "=" * 70,
                        f"Token Usage Report ({days} days)",
                        "=" * 70,
                        f"Period: {start_date} to {end_date}",
                        "-" * 70
                    ]
                    
                    total_input = 0
                    total_output = 0
                    total_cache = 0
                    total_cost = 0.0
                    total_requests = 0
                    
                    for row in rows:
                        date_str = row[0]
                        input_tok = row[1]
                        output_tok = row[2]
                        cache_hits = row[3]
                        cost = row[4]
                        requests = row[5]
                        
                        total_input += input_tok
                        total_output += output_tok
                        total_cache += cache_hits
                        total_cost += cost
                        total_requests += requests
                        
                        lines.append(
                            f"{date_str}: {input_tok + output_tok:>10,} tokens | "
                            f"${cost:>8.4f} | {requests:>5} requests"
                        )
                    
                    lines.extend([
                        "-" * 70,
                        f"Total Input:    {total_input:>15,} tokens",
                        f"Total Output:   {total_output:>15,} tokens",
                        f"Total Cache:    {total_cache:>15,} tokens",
                        f"Total Tokens:   {total_input + total_output:>15,} tokens",
                        f"Total Cost:     ${total_cost:>14.4f}",
                        f"Total Requests: {total_requests:>15,}",
                        f"Avg Daily Cost: ${(total_cost / days):>14.4f}",
                        "=" * 70
                    ])
                    
                    return "\n".join(lines)
                    
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return f"Error generating report: {e}"
    
    def cleanup_old_data(self, retention_days: Optional[int] = None):
        """Remove old data from database"""
        retention_days = retention_days or self.config['storage']['retention_days']
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete old token usage records
                cursor.execute("DELETE FROM token_usage WHERE timestamp < ?", (cutoff_date,))
                deleted_usage = cursor.rowcount
                
                # Delete old daily summaries
                cursor.execute("DELETE FROM daily_token_summary WHERE date < ?", 
                             (cutoff_date.date(),))
                deleted_summaries = cursor.rowcount
                
                conn.commit()
                
                logger.info(f"Cleaned up {deleted_usage} usage records and "
                          f"{deleted_summaries} daily summaries older than {retention_days} days")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")


# CLI interface
def main():
    """Command-line interface for token monitoring"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Anthropic Token Monitor")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate usage report')
    report_parser.add_argument('--days', type=int, default=7, help='Number of days')
    report_parser.add_argument('--format', choices=['text', 'json', 'csv'], 
                              default='text', help='Output format')
    
    # Balance command
    balance_parser = subparsers.add_parser('balance', help='Check token balance')
    
    # Summary command
    summary_parser = subparsers.add_parser('summary', help='Show session summary')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean old data')
    cleanup_parser.add_argument('--days', type=int, help='Retention days')
    
    args = parser.parse_args()
    
    # Initialize monitor
    monitor = TokenMonitor()
    
    if args.command == 'report':
        print(monitor.generate_report(args.days, args.format))
    elif args.command == 'balance':
        balance = monitor.get_balance()
        if balance:
            print(f"Daily Limit: {balance['daily_limit']:,} tokens")
            print(f"Used Today:  {balance['daily_used']:,} tokens")
            print(f"Remaining:   {balance['daily_remaining']:,} tokens")
            print(f"Percent:     {balance['percent_used']:.1f}%")
            print(f"Cost Today:  ${balance['cost_today']:.4f}")
    elif args.command == 'summary':
        print(monitor.get_session_summary())
    elif args.command == 'cleanup':
        monitor.cleanup_old_data(args.days)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
