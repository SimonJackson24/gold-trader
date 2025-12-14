"""
Core utilities and synchronization primitives for XAUUSD Gold Trading System.

Provides thread-safe data structures, locks, and resource management
to prevent race conditions and ensure system stability.
"""

from .synchronization import (
    BoundedQueue,
    AsyncBoundedQueue,
    ThreadSafeDict,
    AsyncLockManager,
    SemaphoreManager,
    ResourceManager,
    ResourceLock,
    
    # Global synchronization primitives
    trade_locks,
    signal_queue,
    market_data_queue,
    notification_queue,
    database_semaphore,
    trade_semaphore
)

from .memory_manager import (
    MemoryStats,
    BoundedCache,
    MemoryPool,
    MemoryMonitor,
    ResourceManager as MemoryResourceManager,
    
    # Global memory management
    memory_monitor,
    signal_cache,
    trade_cache,
    market_data_cache,
    resource_manager,
    tick_pool,
    candle_pool,
    signal_pool
)

from .error_recovery import (
    ErrorSeverity,
    RecoveryAction,
    ErrorInfo,
    CircuitBreakerState,
    CircuitBreaker,
    RetryHandler,
    ErrorRecoveryManager,
    
    # Global error recovery
    error_recovery_manager,
    
    # Decorators
    with_circuit_breaker,
    with_retry,
    with_error_recovery
)

from .structured_logging import (
    LogLevel,
    LogCategory,
    LogContext,
    LogEvent,
    StructuredLogger,
    SecurityLogger,
    AuditLogger,
    PerformanceLogger,
    
    # Global loggers
    security_logger,
    audit_logger,
    performance_logger,
    get_logger,
    setup_structured_logging
)

__all__ = [
    'BoundedQueue',
    'AsyncBoundedQueue',
    'ThreadSafeDict',
    'AsyncLockManager',
    'SemaphoreManager',
    'ResourceManager',
    'ResourceLock',
    'trade_locks',
    'signal_queue',
    'market_data_queue',
    'notification_queue',
    'database_semaphore',
    'trade_semaphore',
    'MemoryStats',
    'BoundedCache',
    'MemoryPool',
    'MemoryMonitor',
    'MemoryResourceManager',
    'memory_monitor',
    'signal_cache',
    'trade_cache',
    'market_data_cache',
    'resource_manager',
    'tick_pool',
    'candle_pool',
    'signal_pool',
    'ErrorSeverity',
    'RecoveryAction',
    'ErrorInfo',
    'CircuitBreakerState',
    'CircuitBreaker',
    'RetryHandler',
    'RetryHandler',
    'ErrorRecoveryManager',
    'error_recovery_manager',
    'with_circuit_breaker',
    'with_retry',
    'with_error_recovery',
    'LogLevel',
    'LogCategory',
    'LogContext',
    'LogEvent',
    'StructuredLogger',
    'SecurityLogger',
    'AuditLogger',
    'PerformanceLogger',
    'security_logger',
    'audit_logger',
    'performance_logger',
    'get_logger',
    'setup_structured_logging'
]