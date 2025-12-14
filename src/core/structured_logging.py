"""
Structured logging system for XAUUSD Gold Trading System.

Provides comprehensive logging with correlation IDs, structured output,
security event tracking, and performance monitoring.
"""

import json
import time
import uuid
import logging
import threading
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from contextlib import contextmanager
import traceback

from .memory_manager import memory_monitor
from .error_recovery import error_recovery_manager


class LogLevel(Enum):
    """Log levels with severity ordering."""
    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    FATAL = "FATAL"


class LogCategory(Enum):
    """Log categories for filtering and analysis."""
    SYSTEM = "SYSTEM"
    SECURITY = "SECURITY"
    TRADING = "TRADING"
    DATABASE = "DATABASE"
    API = "API"
    PERFORMANCE = "PERFORMANCE"
    AUDIT = "AUDIT"
    ERROR = "ERROR"
    MEMORY = "MEMORY"


@dataclass
class LogContext:
    """Log context information."""
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    trade_id: Optional[str] = None
    signal_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    component: Optional[str] = None
    function: Optional[str] = None
    line_number: Optional[int] = None


@dataclass
class LogEvent:
    """Structured log event."""
    timestamp: float = field(default_factory=time.time)
    level: LogLevel = LogLevel.INFO
    category: LogCategory = LogCategory.SYSTEM
    message: str = ""
    context: LogContext = field(default_factory=LogContext)
    data: Dict[str, Any] = field(default_factory=dict)
    exception: Optional[Exception] = None
    stack_trace: Optional[str] = None
    duration_ms: Optional[float] = None
    memory_usage_mb: Optional[float] = None


class StructuredLogger:
    """
    Structured logger with correlation and context tracking.
    """
    
    def __init__(self, name: str, category: LogCategory = LogCategory.SYSTEM):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name
            category: Log category
        """
        self.name = name
        self.category = category
        self.logger = logging.getLogger(name)
        self._context = LogContext()
        self._lock = threading.Lock()
    
    def set_context(self, **kwargs):
        """
        Set context values.
        
        Args:
            **kwargs: Context key-value pairs
        """
        with self._lock:
            for key, value in kwargs.items():
                if hasattr(self._context, key):
                    setattr(self._context, key, value)
    
    def clear_context(self):
        """Clear all context."""
        with self._lock:
            self._context = LogContext()
    
    @contextmanager
    def context(self, **kwargs):
        """
        Context manager for temporary context.
        
        Args:
            **kwargs: Context key-value pairs
        """
        old_context = self._context
        try:
            self.set_context(**kwargs)
            yield self
        finally:
            with self._lock:
                self._context = old_context
    
    def trace(self, message: str, **data):
        """Log trace message."""
        self._log(LogLevel.TRACE, message, **data)
    
    def debug(self, message: str, **data):
        """Log debug message."""
        self._log(LogLevel.DEBUG, message, **data)
    
    def info(self, message: str, **data):
        """Log info message."""
        self._log(LogLevel.INFO, message, **data)
    
    def warning(self, message: str, **data):
        """Log warning message."""
        self._log(LogLevel.WARN, message, **data)
    
    def error(self, message: str, exception: Optional[Exception] = None, **data):
        """Log error message."""
        self._log(LogLevel.ERROR, message, exception=exception, **data)
    
    def fatal(self, message: str, exception: Optional[Exception] = None, **data):
        """Log fatal message."""
        self._log(LogLevel.FATAL, message, exception=exception, **data)
    
    def audit(self, message: str, **data):
        """Log audit message."""
        self._log(LogLevel.INFO, message, category=LogCategory.AUDIT, **data)
    
    def security(self, message: str, **data):
        """Log security event."""
        self._log(LogLevel.WARN, message, category=LogCategory.SECURITY, **data)
    
    def trading(self, message: str, **data):
        """Log trading event."""
        self._log(LogLevel.INFO, message, category=LogCategory.TRADING, **data)
    
    def performance(self, message: str, duration_ms: Optional[float] = None, **data):
        """Log performance event."""
        self._log(LogLevel.INFO, message, category=LogCategory.PERFORMANCE, 
                 duration_ms=duration_ms, **data)
    
    def database(self, message: str, **data):
        """Log database event."""
        self._log(LogLevel.DEBUG, message, category=LogCategory.DATABASE, **data)
    
    def api(self, message: str, **data):
        """Log API event."""
        self._log(LogLevel.INFO, message, category=LogCategory.API, **data)
    
    def memory(self, message: str, **data):
        """Log memory event."""
        self._log(LogLevel.INFO, message, category=LogCategory.MEMORY, **data)
    
    def _log(self, level: LogLevel, message: str, category: Optional[LogCategory] = None,
              exception: Optional[Exception] = None, **data):
        """
        Internal log method.
        
        Args:
            level: Log level
            message: Log message
            category: Log category override
            exception: Exception if any
            **data: Additional data
        """
        with self._lock:
            # Create log event
            event = LogEvent(
                level=level,
                category=category or self.category,
                message=message,
                context=self._context,
                data=data,
                exception=exception,
                stack_trace=traceback.format_exc() if exception else None
            )
            
            # Add memory usage
            try:
                stats = memory_monitor.get_memory_stats()
                event.memory_usage_mb = stats.process_memory_mb
            except:
                pass
            
            # Convert to structured format
            log_data = asdict(event)
            
            # Add standard logging
            self.logger.log(
                getattr(logging, level.value),
                json.dumps(log_data, default=str, separators=(',', ':')),
                extra={"structured_log": True}
            )
    
    @contextmanager
    def measure_performance(self, operation: str):
        """
        Context manager for measuring performance.
        
        Args:
            operation: Operation name
        """
        start_time = time.time()
        try:
            yield self
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.performance(f"Operation completed", operation=operation, 
                         duration_ms=duration_ms)


class SecurityLogger:
    """
    Specialized logger for security events.
    """
    
    def __init__(self):
        """Initialize security logger."""
        self.logger = StructuredLogger("security", LogCategory.SECURITY)
    
    def login_attempt(self, username: str, ip_address: str, success: bool, 
                    user_agent: str = None):
        """
        Log login attempt.
        
        Args:
            username: Username
            ip_address: Client IP
            success: Login success status
            user_agent: Client user agent
        """
        self.logger.set_context(
            user_id=username,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        message = f"Login {'successful' if success else 'failed'} for user: {username}"
        self.logger.security(
            message,
            event_type="login_attempt",
            username=username,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.logger.clear_context()
    
    def authentication_failure(self, reason: str, token: str = None, ip_address: str = None):
        """
        Log authentication failure.
        
        Args:
            reason: Failure reason
            token: Failed token
            ip_address: Client IP
        """
        self.logger.set_context(ip_address=ip_address)
        
        self.logger.security(
            f"Authentication failure: {reason}",
            event_type="auth_failure",
            reason=reason,
            token=token[:10] + "..." if token else None
        )
        
        self.logger.clear_context()
    
    def privilege_escalation(self, user_id: str, attempted_role: str, success: bool):
        """
        Log privilege escalation attempt.
        
        Args:
            user_id: User ID
            attempted_role: Role being attempted
            success: Escalation success
        """
        self.logger.set_context(user_id=user_id)
        
        self.logger.security(
            f"Privilege escalation {'successful' if success else 'failed'}",
            event_type="privilege_escalation",
            attempted_role=attempted_role,
            success=success
        )
        
        self.logger.clear_context()
    
    def data_access(self, user_id: str, resource: str, action: str, success: bool):
        """
        Log data access event.
        
        Args:
            user_id: User ID
            resource: Resource accessed
            action: Action performed
            success: Access success
        """
        self.logger.set_context(user_id=user_id)
        
        self.logger.security(
            f"Data access: {action} on {resource}",
            event_type="data_access",
            resource=resource,
            action=action,
            success=success
        )
        
        self.logger.clear_context()


class AuditLogger:
    """
    Specialized logger for audit events.
    """
    
    def __init__(self):
        """Initialize audit logger."""
        self.logger = StructuredLogger("audit", LogCategory.AUDIT)
    
    def trade_created(self, trade_id: str, user_id: str, symbol: str, 
                   direction: str, volume: float):
        """
        Log trade creation.
        
        Args:
            trade_id: Trade ID
            user_id: User ID
            symbol: Trading symbol
            direction: Trade direction
            volume: Trade volume
        """
        self.logger.set_context(
            user_id=user_id,
            trade_id=trade_id
        )
        
        self.logger.audit(
            "Trade created",
            event_type="trade_created",
            trade_id=trade_id,
            symbol=symbol,
            direction=direction,
            volume=volume
        )
        
        self.logger.clear_context()
    
    def trade_closed(self, trade_id: str, user_id: str, reason: str, 
                  profit_loss: float):
        """
        Log trade closure.
        
        Args:
            trade_id: Trade ID
            user_id: User ID
            reason: Close reason
            profit_loss: Profit/loss amount
        """
        self.logger.set_context(
            user_id=user_id,
            trade_id=trade_id
        )
        
        self.logger.audit(
            f"Trade closed: {reason}",
            event_type="trade_closed",
            trade_id=trade_id,
            reason=reason,
            profit_loss=profit_loss
        )
        
        self.logger.clear_context()
    
    def signal_generated(self, signal_id: str, user_id: str, symbol: str, 
                     direction: str, confidence: float):
        """
        Log signal generation.
        
        Args:
            signal_id: Signal ID
            user_id: User ID
            symbol: Trading symbol
            direction: Signal direction
            confidence: Confidence score
        """
        self.logger.set_context(
            user_id=user_id,
            signal_id=signal_id
        )
        
        self.logger.audit(
            "Signal generated",
            event_type="signal_generated",
            signal_id=signal_id,
            symbol=symbol,
            direction=direction,
            confidence=confidence
        )
        
        self.logger.clear_context()
    
    def configuration_change(self, user_id: str, key: str, old_value: str, 
                        new_value: str):
        """
        Log configuration change.
        
        Args:
            user_id: User ID
            key: Configuration key
            old_value: Previous value
            new_value: New value
        """
        self.logger.set_context(user_id=user_id)
        
        self.logger.audit(
            f"Configuration changed: {key}",
            event_type="config_change",
            config_key=key,
            old_value=old_value,
            new_value=new_value
        )
        
        self.logger.clear_context()


class PerformanceLogger:
    """
    Specialized logger for performance monitoring.
    """
    
    def __init__(self):
        """Initialize performance logger."""
        self.logger = StructuredLogger("performance", LogCategory.PERFORMANCE)
    
    def database_query(self, query_type: str, duration_ms: float, 
                     table: str = None, rows_affected: int = None):
        """
        Log database query performance.
        
        Args:
            query_type: Type of query
            duration_ms: Query duration
            table: Table accessed
            rows_affected: Number of rows affected
        """
        self.logger.performance(
            f"Database query: {query_type}",
            operation="database_query",
            query_type=query_type,
            duration_ms=duration_ms,
            table=table,
            rows_affected=rows_affected
        )
    
    def api_request(self, endpoint: str, method: str, status_code: int, 
                  duration_ms: float, user_id: str = None):
        """
        Log API request performance.
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            status_code: Response status
            duration_ms: Request duration
            user_id: User ID
        """
        self.logger.set_context(user_id=user_id)
        
        self.logger.performance(
            f"API request: {method} {endpoint}",
            operation="api_request",
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            duration_ms=duration_ms
        )
        
        self.logger.clear_context()
    
    def trading_operation(self, operation: str, duration_ms: float, success: bool,
                       symbol: str = None, volume: float = None):
        """
        Log trading operation performance.
        
        Args:
            operation: Trading operation
            duration_ms: Operation duration
            success: Operation success
            symbol: Trading symbol
            volume: Trade volume
        """
        self.logger.performance(
            f"Trading operation: {operation}",
            operation="trading_operation",
            trading_operation=operation,
            duration_ms=duration_ms,
            success=success,
            symbol=symbol,
            volume=volume
        )


# Global logger instances
security_logger = SecurityLogger()
audit_logger = AuditLogger()
performance_logger = PerformanceLogger()

# Convenience functions
def get_logger(name: str, category: LogCategory = LogCategory.SYSTEM) -> StructuredLogger:
    """
    Get structured logger instance.
    
    Args:
        name: Logger name
        category: Log category
        
    Returns:
        Structured logger instance
    """
    return StructuredLogger(name, category)


def setup_structured_logging():
    """Setup structured logging configuration."""
    # Configure JSON formatter for structured logs
    formatter = logging.Formatter(
        '%(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S'
    )
    
    # Create handler for structured logs
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[handler]
    )