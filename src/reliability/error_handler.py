#!/usr/bin/env python3
"""
Error Handler Module - Centralized error handling for Avatar Engine
=====================================================================

Provides comprehensive error handling with:
- Structured exception hierarchy
- Detailed error logging
- Error categorization and severity levels
- Recovery suggestions
- Error metrics tracking
"""

import logging
import traceback
import json
from typing import Optional, Dict, Any, List, Type
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels for prioritization"""
    CRITICAL = "critical"  # System failure, immediate attention needed
    HIGH = "high"  # Major functionality impaired
    MEDIUM = "medium"  # Some functionality affected
    LOW = "low"  # Minor issue, workaround available
    INFO = "info"  # Informational, no action required


class ErrorCategory(Enum):
    """Error categories for classification"""
    DATABASE = "database"  # Database connection/query errors
    API = "api"  # External API errors
    VALIDATION = "validation"  # Input validation errors
    CONFIGURATION = "configuration"  # Configuration errors
    SECURITY = "security"  # Security-related errors
    NETWORK = "network"  # Network connectivity errors
    FILESYSTEM = "filesystem"  # File system errors
    PARSING = "parsing"  # Data parsing errors
    PROCESSING = "processing"  # Data processing errors
    UNKNOWN = "unknown"  # Uncategorized errors


@dataclass
class ErrorContext:
    """Context information for error tracking"""
    timestamp: datetime = field(default_factory=datetime.now)
    module: Optional[str] = None
    function: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorReport:
    """Comprehensive error report"""
    error_id: str
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    exception_type: str
    traceback: str
    context: ErrorContext
    recovery_suggestions: List[str] = field(default_factory=list)
    related_errors: List[str] = field(default_factory=list)


# ============================================================================
# Custom Exception Hierarchy
# ============================================================================

class AvatarEngineError(Exception):
    """Base exception for all Avatar Engine errors"""
    
    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        recovery_suggestions: Optional[List[str]] = None,
        **kwargs
    ):
        super().__init__(message)
        self.severity = severity
        self.category = category
        self.recovery_suggestions = recovery_suggestions or []
        self.additional_data = kwargs
        self.error_id = self._generate_error_id()
    
    def _generate_error_id(self) -> str:
        """Generate unique error ID"""
        from uuid import uuid4
        return f"ERR-{datetime.now().strftime('%Y%m%d')}-{uuid4().hex[:8]}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging"""
        return {
            "error_id": self.error_id,
            "message": str(self),
            "severity": self.severity.value,
            "category": self.category.value,
            "recovery_suggestions": self.recovery_suggestions,
            "additional_data": self.additional_data
        }


class DatabaseError(AvatarEngineError):
    """Database-related errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DATABASE,
            recovery_suggestions=[
                "Check database connection settings",
                "Verify database server is running",
                "Check network connectivity to database",
                "Verify database credentials"
            ],
            **kwargs
        )


class APIError(AvatarEngineError):
    """External API errors"""
    def __init__(self, message: str, api_name: str, status_code: Optional[int] = None, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.API,
            recovery_suggestions=[
                f"Check {api_name} API status",
                "Verify API credentials",
                "Check rate limits",
                "Retry with exponential backoff"
            ],
            api_name=api_name,
            status_code=status_code,
            **kwargs
        )


class ValidationError(AvatarEngineError):
    """Input validation errors"""
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.LOW,
            category=ErrorCategory.VALIDATION,
            recovery_suggestions=[
                "Check input format",
                "Verify required fields are provided",
                "Ensure data types are correct"
            ],
            field=field,
            **kwargs
        )


class ConfigurationError(AvatarEngineError):
    """Configuration errors"""
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.CONFIGURATION,
            recovery_suggestions=[
                "Check configuration file",
                "Verify environment variables",
                "Ensure all required settings are configured",
                "Review configuration documentation"
            ],
            config_key=config_key,
            **kwargs
        )


class SecurityError(AvatarEngineError):
    """Security-related errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.SECURITY,
            recovery_suggestions=[
                "Review security configuration",
                "Check authentication credentials",
                "Verify authorization settings",
                "Contact security team if issue persists"
            ],
            **kwargs
        )


class NetworkError(AvatarEngineError):
    """Network connectivity errors"""
    def __init__(self, message: str, endpoint: Optional[str] = None, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.NETWORK,
            recovery_suggestions=[
                "Check network connectivity",
                "Verify firewall settings",
                "Check DNS resolution",
                "Retry after network recovery"
            ],
            endpoint=endpoint,
            **kwargs
        )


class FileSystemError(AvatarEngineError):
    """File system errors"""
    def __init__(self, message: str, path: Optional[str] = None, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.FILESYSTEM,
            recovery_suggestions=[
                "Check file/directory permissions",
                "Verify path exists",
                "Ensure sufficient disk space",
                "Check file system integrity"
            ],
            path=path,
            **kwargs
        )


class ParsingError(AvatarEngineError):
    """Data parsing errors"""
    def __init__(self, message: str, data_format: Optional[str] = None, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.PARSING,
            recovery_suggestions=[
                "Verify data format",
                "Check for encoding issues",
                "Validate data structure",
                "Review parsing rules"
            ],
            data_format=data_format,
            **kwargs
        )


class ProcessingError(AvatarEngineError):
    """Data processing errors"""
    def __init__(self, message: str, stage: Optional[str] = None, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.PROCESSING,
            recovery_suggestions=[
                "Check input data quality",
                "Verify processing pipeline configuration",
                "Review processing logs",
                "Retry with smaller batch size"
            ],
            stage=stage,
            **kwargs
        )


# ============================================================================
# Error Handler Class
# ============================================================================

class ErrorHandler:
    """Centralized error handling and recovery"""
    
    def __init__(
        self,
        log_file: Optional[Path] = None,
        metrics_enabled: bool = True,
        max_error_history: int = 1000
    ):
        self.log_file = log_file
        self.metrics_enabled = metrics_enabled
        self.max_error_history = max_error_history
        self.error_history: List[ErrorReport] = []
        self.error_metrics: Dict[str, int] = {
            "total_errors": 0,
            "critical_errors": 0,
            "recovered_errors": 0,
            "unhandled_errors": 0
        }
    
    def handle_error(
        self,
        error: Exception,
        context: Optional[ErrorContext] = None,
        reraise: bool = False,
        attempt_recovery: bool = True
    ) -> Optional[ErrorReport]:
        """
        Handle an error with logging and optional recovery
        
        Args:
            error: The exception to handle
            context: Additional context information
            reraise: Whether to re-raise the exception after handling
            attempt_recovery: Whether to attempt automatic recovery
        
        Returns:
            ErrorReport if error was handled, None if recovery succeeded
        """
        # Create error report
        report = self._create_error_report(error, context)
        
        # Log the error
        self._log_error(report)
        
        # Update metrics
        if self.metrics_enabled:
            self._update_metrics(report)
        
        # Attempt recovery if requested
        if attempt_recovery and self._can_recover(error):
            if self._attempt_recovery(error, report):
                self.error_metrics["recovered_errors"] += 1
                logger.info(f"Successfully recovered from error: {report.error_id}")
                return None
        
        # Store in history
        self._add_to_history(report)
        
        # Re-raise if requested
        if reraise:
            raise error
        
        return report
    
    def _create_error_report(
        self,
        error: Exception,
        context: Optional[ErrorContext] = None
    ) -> ErrorReport:
        """Create a comprehensive error report"""
        if isinstance(error, AvatarEngineError):
            severity = error.severity
            category = error.category
            recovery_suggestions = error.recovery_suggestions
            error_id = error.error_id
        else:
            severity = ErrorSeverity.MEDIUM
            category = ErrorCategory.UNKNOWN
            recovery_suggestions = ["Check application logs", "Contact support"]
            error_id = f"ERR-{datetime.now().strftime('%Y%m%d')}-{id(error):08x}"
        
        return ErrorReport(
            error_id=error_id,
            severity=severity,
            category=category,
            message=str(error),
            exception_type=type(error).__name__,
            traceback=traceback.format_exc(),
            context=context or ErrorContext(),
            recovery_suggestions=recovery_suggestions
        )
    
    def _log_error(self, report: ErrorReport) -> None:
        """Log error with appropriate level"""
        log_data = {
            "error_id": report.error_id,
            "severity": report.severity.value,
            "category": report.category.value,
            "message": report.message,
            "exception_type": report.exception_type,
            "module": report.context.module,
            "function": report.context.function,
            "timestamp": report.context.timestamp.isoformat()
        }
        
        log_message = json.dumps(log_data, indent=2)
        
        if report.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif report.severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif report.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        # Also write to file if configured
        if self.log_file:
            self._write_to_log_file(log_data)
    
    def _write_to_log_file(self, log_data: Dict[str, Any]) -> None:
        """Write error to log file"""
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_data) + '\n')
        except Exception as e:
            logger.error(f"Failed to write to log file: {e}")
    
    def _update_metrics(self, report: ErrorReport) -> None:
        """Update error metrics"""
        self.error_metrics["total_errors"] += 1
        
        if report.severity == ErrorSeverity.CRITICAL:
            self.error_metrics["critical_errors"] += 1
        
        # Update category-specific metrics
        category_key = f"{report.category.value}_errors"
        if category_key not in self.error_metrics:
            self.error_metrics[category_key] = 0
        self.error_metrics[category_key] += 1
    
    def _can_recover(self, error: Exception) -> bool:
        """Check if automatic recovery is possible"""
        # Define recoverable error types
        recoverable_types = [
            NetworkError,
            APIError,
            DatabaseError  # With retry logic
        ]
        
        return any(isinstance(error, err_type) for err_type in recoverable_types)
    
    def _attempt_recovery(self, error: Exception, report: ErrorReport) -> bool:
        """Attempt automatic recovery from error"""
        # This is a placeholder for recovery logic
        # Actual implementation would depend on error type
        
        if isinstance(error, NetworkError):
            # Could implement network reconnection logic
            logger.info(f"Attempting network recovery for {report.error_id}")
            return False  # Placeholder
        
        elif isinstance(error, APIError):
            # Could implement API retry logic
            logger.info(f"Attempting API recovery for {report.error_id}")
            return False  # Placeholder
        
        elif isinstance(error, DatabaseError):
            # Could implement database reconnection logic
            logger.info(f"Attempting database recovery for {report.error_id}")
            return False  # Placeholder
        
        return False
    
    def _add_to_history(self, report: ErrorReport) -> None:
        """Add error to history with size limit"""
        self.error_history.append(report)
        
        # Maintain size limit
        if len(self.error_history) > self.max_error_history:
            self.error_history = self.error_history[-self.max_error_history:]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current error metrics"""
        return {
            **self.error_metrics,
            "error_rate": self._calculate_error_rate(),
            "critical_rate": self._calculate_critical_rate(),
            "recovery_rate": self._calculate_recovery_rate()
        }
    
    def _calculate_error_rate(self) -> float:
        """Calculate error rate per minute"""
        if not self.error_history:
            return 0.0
        
        time_span = (datetime.now() - self.error_history[0].context.timestamp).total_seconds() / 60
        if time_span == 0:
            return 0.0
        
        return len(self.error_history) / time_span
    
    def _calculate_critical_rate(self) -> float:
        """Calculate critical error rate"""
        if self.error_metrics["total_errors"] == 0:
            return 0.0
        
        return self.error_metrics["critical_errors"] / self.error_metrics["total_errors"]
    
    def _calculate_recovery_rate(self) -> float:
        """Calculate recovery success rate"""
        total_recoverable = (
            self.error_metrics.get("network_errors", 0) +
            self.error_metrics.get("api_errors", 0) +
            self.error_metrics.get("database_errors", 0)
        )
        
        if total_recoverable == 0:
            return 0.0
        
        return self.error_metrics["recovered_errors"] / total_recoverable
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of recent errors"""
        if not self.error_history:
            return {"message": "No errors recorded"}
        
        recent_errors = self.error_history[-10:]  # Last 10 errors
        
        return {
            "total_errors": len(self.error_history),
            "recent_errors": [
                {
                    "error_id": err.error_id,
                    "severity": err.severity.value,
                    "category": err.category.value,
                    "message": err.message,
                    "timestamp": err.context.timestamp.isoformat()
                }
                for err in recent_errors
            ],
            "metrics": self.get_metrics()
        }
    
    def clear_history(self) -> None:
        """Clear error history and reset metrics"""
        self.error_history.clear()
        self.error_metrics = {
            "total_errors": 0,
            "critical_errors": 0,
            "recovered_errors": 0,
            "unhandled_errors": 0
        }
        logger.info("Error history and metrics cleared")


# ============================================================================
# Global Error Handler Instance
# ============================================================================

# Create a global error handler instance for the application
global_error_handler = ErrorHandler(
    log_file=Path("logs/errors.jsonl"),
    metrics_enabled=True
)


# ============================================================================
# Decorator for Error Handling
# ============================================================================

def handle_errors(
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    reraise: bool = True,
    log_args: bool = False
):
    """
    Decorator for automatic error handling
    
    Usage:
        @handle_errors(severity=ErrorSeverity.HIGH, category=ErrorCategory.DATABASE)
        def database_operation():
            # Your code here
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            context = ErrorContext(
                module=func.__module__,
                function=func.__name__
            )
            
            if log_args:
                context.additional_data = {
                    "args": str(args)[:1000],  # Limit size
                    "kwargs": str(kwargs)[:1000]
                }
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Convert to AvatarEngineError if needed
                if not isinstance(e, AvatarEngineError):
                    e = AvatarEngineError(
                        str(e),
                        severity=severity,
                        category=category
                    )
                
                # Handle the error
                global_error_handler.handle_error(
                    e,
                    context=context,
                    reraise=reraise
                )
        
        return wrapper
    return decorator


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Example 1: Raising custom errors
    try:
        raise DatabaseError("Failed to connect to Neo4j", host="localhost", port=7687)
    except DatabaseError as e:
        report = global_error_handler.handle_error(e, reraise=False)
        print(f"Handled error: {report.error_id}")
    
    # Example 2: Using decorator
    @handle_errors(severity=ErrorSeverity.HIGH, category=ErrorCategory.API)
    def fetch_api_data():
        raise APIError("Rate limit exceeded", api_name="OpenAI", status_code=429)
    
    try:
        fetch_api_data()
    except APIError:
        print("API error was re-raised as expected")
    
    # Example 3: Get error summary
    summary = global_error_handler.get_error_summary()
    print(f"Error summary: {json.dumps(summary, indent=2)}")
