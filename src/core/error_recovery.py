"""
Error recovery mechanisms for XAUUSD Gold Trading System.

Provides comprehensive error handling, retry logic, circuit breakers,
and recovery strategies to ensure system resilience.
"""

# Copyright (c) 2024 Simon Callaghan. All rights reserved.

import asyncio
import time
import logging
from typing import Any, Callable, Optional, Dict, List, Union, Type
from dataclasses import dataclass, field
from enum import Enum
import traceback
from functools import wraps

from .memory_manager import memory_monitor
from .synchronization import AsyncLockManager


class ErrorSeverity(Enum):
    """Error severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecoveryAction(Enum):
    """Recovery action types."""

    RETRY = "retry"
    CIRCUIT_BREAK = "circuit_break"
    FALLBACK = "fallback"
    ESCALATE = "escalate"
    IGNORE = "ignore"


@dataclass
class ErrorInfo:
    """Error information container."""

    error_type: str
    severity: ErrorSeverity
    message: str
    exception: Exception
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    retry_count: int = 0
    recovery_actions: List[RecoveryAction] = field(default_factory=list)


@dataclass
class CircuitBreakerState:
    """Circuit breaker state."""

    failure_count: int = 0
    last_failure_time: float = 0.0
    state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    success_count: int = 0


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.
    Prevents cascading failures by temporarily disabling failing operations.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Type[Exception] = Exception,
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening
            recovery_timeout: Seconds to wait before trying again
            expected_exception: Exception type to catch
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.state = CircuitBreakerState()
        self.logger = logging.getLogger(__name__)

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state.state == "OPEN":
            if time.time() - self.state.last_failure_time > self.recovery_timeout:
                self.state.state = "HALF_OPEN"
                self.logger.info("Circuit breaker transitioning to HALF_OPEN")
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result

        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _on_success(self):
        """Handle successful operation."""
        self.state.success_count += 1

        if self.state.state == "HALF_OPEN":
            self.state.state = "CLOSED"
            self.state.failure_count = 0
            self.logger.info("Circuit breaker transitioning to CLOSED")

    def _on_failure(self):
        """Handle failed operation."""
        self.state.failure_count += 1
        self.state.last_failure_time = time.time()

        if self.state.failure_count >= self.failure_threshold:
            self.state.state = "OPEN"
            self.logger.warning(
                f"Circuit breaker OPEN after {self.state.failure_count} failures"
            )

    def get_state(self) -> Dict[str, Any]:
        """Get circuit breaker state."""
        return {
            "state": self.state.state,
            "failure_count": self.state.failure_count,
            "success_count": self.state.success_count,
            "last_failure_time": self.state.last_failure_time,
        }


class RetryHandler:
    """
    Exponential backoff retry handler with jitter.
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
    ):
        """
        Initialize retry handler.

        Args:
            max_retries: Maximum retry attempts
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            backoff_factor: Multiplier for delay
            jitter: Add random jitter to delay
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        self.logger = logging.getLogger(__name__)

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with retry logic.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If all retries fail
        """
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)

            except Exception as e:
                last_exception = e

                if attempt == self.max_retries:
                    self.logger.error(f"All {self.max_retries} retries failed: {e}")
                    raise e

                delay = self._calculate_delay(attempt)
                self.logger.warning(
                    f"Retry {attempt + 1}/{self.max_retries} failed: {e}, retrying in {delay:.2f}s"
                )
                await asyncio.sleep(delay)

        raise last_exception

    def _calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay with exponential backoff and jitter.

        Args:
            attempt: Current attempt number

        Returns:
            Delay in seconds
        """
        delay = min(self.base_delay * (self.backoff_factor**attempt), self.max_delay)

        if self.jitter:
            # Add ±25% jitter
            jitter_range = delay * 0.25
            delay += (time.time() % 1) * jitter_range * 2 - jitter_range

        return max(0, delay)


class ErrorRecoveryManager:
    """
    Comprehensive error recovery manager.
    """

    def __init__(self):
        """Initialize error recovery manager."""
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_handlers: Dict[str, RetryHandler] = {}
        self.error_handlers: Dict[str, Callable] = {}
        self.error_history: List[ErrorInfo] = []
        self._lock = AsyncLockManager("error_recovery")
        self.logger = logging.getLogger(__name__)

        # Register default error handlers
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Register default error handlers."""
        self.register_error_handler("memory_error", self._handle_memory_error)
        self.register_error_handler("database_error", self._handle_database_error)
        self.register_error_handler("network_error", self._handle_network_error)
        self.register_error_handler("trading_error", self._handle_trading_error)
        self.register_error_handler(
            "authentication_error", self._handle_authentication_error
        )

    def register_circuit_breaker(
        self, name: str, failure_threshold: int = 5, recovery_timeout: int = 60
    ) -> CircuitBreaker:
        """
        Register circuit breaker for operation.

        Args:
            name: Circuit breaker name
            failure_threshold: Failure threshold
            recovery_timeout: Recovery timeout

        Returns:
            Circuit breaker instance
        """
        breaker = CircuitBreaker(failure_threshold, recovery_timeout)
        self.circuit_breakers[name] = breaker
        return breaker

    def register_retry_handler(
        self, name: str, max_retries: int = 3, base_delay: float = 1.0
    ) -> RetryHandler:
        """
        Register retry handler for operation.

        Args:
            name: Handler name
            max_retries: Maximum retries
            base_delay: Base delay

        Returns:
            Retry handler instance
        """
        handler = RetryHandler(max_retries, base_delay)
        self.retry_handlers[name] = handler
        return handler

    def register_error_handler(self, error_type: str, handler: Callable):
        """
        Register error handler.

        Args:
            error_type: Error type
            handler: Handler function
        """
        self.error_handlers[error_type] = handler

    async def handle_error(self, error_info: ErrorInfo) -> bool:
        """
        Handle error with registered handlers.

        Args:
            error_info: Error information

        Returns:
            True if error was handled
        """
        async with self._lock.acquire():
            self.error_history.append(error_info)

            # Keep history bounded
            if len(self.error_history) > 1000:
                self.error_history = self.error_history[-500:]

            # Get appropriate handler
            handler = self.error_handlers.get(error_info.error_type)
            if handler:
                try:
                    return await handler(error_info)
                except Exception as e:
                    self.logger.error(f"Error handler failed: {e}")

            return False

    async def _handle_memory_error(self, error_info: ErrorInfo) -> bool:
        """Handle memory-related errors."""
        self.logger.critical(f"Memory error: {error_info.message}")

        # Trigger memory cleanup
        await memory_monitor._emergency_cleanup()

        # Suggest recovery actions
        error_info.recovery_actions.extend(
            [RecoveryAction.RETRY, RecoveryAction.FALLBACK]
        )

        return True

    async def _handle_database_error(self, error_info: ErrorInfo) -> bool:
        """Handle database-related errors."""
        self.logger.error(f"Database error: {error_info.message}")

        # Check if it's a connection error
        if "connection" in error_info.message.lower():
            error_info.recovery_actions.extend(
                [RecoveryAction.RETRY, RecoveryAction.CIRCUIT_BREAK]
            )
        else:
            # For other database errors, use circuit breaker
            error_info.recovery_actions.extend(
                [RecoveryAction.CIRCUIT_BREAK, RecoveryAction.ESCALATE]
            )

        return True

    async def _handle_network_error(self, error_info: ErrorInfo) -> bool:
        """Handle network-related errors."""
        self.logger.error(f"Network error: {error_info.message}")

        # Network errors are usually retryable
        error_info.recovery_actions.extend(
            [RecoveryAction.RETRY, RecoveryAction.FALLBACK]
        )

        return True

    async def _handle_trading_error(self, error_info: ErrorInfo) -> bool:
        """Handle trading-related errors."""
        self.logger.error(f"Trading error: {error_info.message}")

        # Trading errors might need immediate attention
        if "margin" in error_info.message.lower():
            error_info.recovery_actions.extend(
                [RecoveryAction.ESCALATE, RecoveryAction.CIRCUIT_BREAK]
            )
        else:
            error_info.recovery_actions.extend(
                [RecoveryAction.RETRY, RecoveryAction.FALLBACK]
            )

        return True

    async def _handle_authentication_error(self, error_info: ErrorInfo) -> bool:
        """Handle authentication-related errors."""
        self.logger.warning(f"Authentication error: {error_info.message}")

        # Auth errors should not be retried immediately
        error_info.recovery_actions.extend(
            [RecoveryAction.CIRCUIT_BREAK, RecoveryAction.ESCALATE]
        )

        return True

    def get_error_stats(self) -> Dict[str, Any]:
        """
        Get error statistics.

        Returns:
            Error statistics dictionary
        """
        if not self.error_history:
            return {}

        # Count errors by type and severity
        error_counts = {}
        severity_counts = {}

        for error in self.error_history[-100:]:  # Last 100 errors
            error_counts[error.error_type] = error_counts.get(error.error_type, 0) + 1
            severity_counts[error.severity.value] = (
                severity_counts.get(error.severity.value, 0) + 1
            )

        return {
            "total_errors": len(self.error_history),
            "error_counts": error_counts,
            "severity_counts": severity_counts,
            "recent_errors": len(
                [e for e in self.error_history if time.time() - e.timestamp < 3600]
            ),  # Last hour
            "circuit_breakers": {
                name: breaker.get_state()
                for name, breaker in self.circuit_breakers.items()
            },
        }


def with_circuit_breaker(
    breaker_name: str, failure_threshold: int = 5, recovery_timeout: int = 60
):
    """
    Decorator to add circuit breaker to function.

    Args:
        breaker_name: Circuit breaker name
        failure_threshold: Failure threshold
        recovery_timeout: Recovery timeout

    Returns:
        Decorated function
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get or create circuit breaker
            if not hasattr(error_recovery_manager, "circuit_breakers"):
                error_recovery_manager.circuit_breakers = {}

            breaker = error_recovery_manager.circuit_breakers.get(breaker_name)
            if not breaker:
                breaker = error_recovery_manager.register_circuit_breaker(
                    breaker_name, failure_threshold, recovery_timeout
                )

            return await breaker.call(func, *args, **kwargs)

        return wrapper

    return decorator


def with_retry(max_retries: int = 3, base_delay: float = 1.0):
    """
    Decorator to add retry logic to function.

    Args:
        max_retries: Maximum retry attempts
        base_delay: Base delay in seconds

    Returns:
        Decorated function
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get or create retry handler
            handler_name = f"retry_{func.__name__}"
            handler = error_recovery_manager.retry_handlers.get(handler_name)
            if not handler:
                handler = error_recovery_manager.register_retry_handler(
                    handler_name, max_retries, base_delay
                )

            return await handler.execute(func, *args, **kwargs)

        return wrapper

    return decorator


def with_error_recovery(error_type: str = "general"):
    """
    Decorator to add error recovery to function.

    Args:
        error_type: Error type for handling

    Returns:
        Decorated function
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_info = ErrorInfo(
                    error_type=error_type,
                    severity=ErrorSeverity.MEDIUM,
                    message=str(e),
                    exception=e,
                    context={"function": func.__name__, "args": str(args)[:200]},
                )

                handled = await error_recovery_manager.handle_error(error_info)
                if not handled:
                    raise e

                return None

        return wrapper

    return decorator


# Global error recovery manager
error_recovery_manager = ErrorRecoveryManager()
