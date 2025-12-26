"""
Memory management module for XAUUSD Gold Trading System.

Provides bounded data structures, memory monitoring, and cleanup
to prevent memory leaks and ensure system stability.
"""

# Copyright (c) 2024 Simon Callaghan. All rights reserved.

import asyncio
import gc
import psutil
import threading
import time
from typing import Any, Optional, Dict, List, Set, Callable, Union
from dataclasses import dataclass, field
from collections import OrderedDict
import logging
import weakref

from .synchronization import ThreadSafeDict, AsyncLockManager


@dataclass
class MemoryStats:
    """Memory statistics."""

    total_memory_mb: float = 0.0
    used_memory_mb: float = 0.0
    available_memory_mb: float = 0.0
    process_memory_mb: float = 0.0
    gc_count: int = 0
    timestamp: float = field(default_factory=time.time)


class BoundedCache:
    """
    Thread-safe bounded cache with LRU eviction.
    Prevents memory exhaustion by limiting cache size.
    """

    def __init__(self, maxsize: int = 1000, ttl_seconds: int = 3600):
        """
        Initialize bounded cache.

        Args:
            maxsize: Maximum number of items
            ttl_seconds: Time to live for items in seconds
        """
        self.maxsize = maxsize
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict = OrderedDict()
        self._timestamps: Dict[str, float] = {}
        self._lock = threading.RLock()
        self.logger = logging.getLogger(__name__)

    def get(self, key: str) -> Optional[Any]:
        """
        Get item from cache.

        Args:
            key: Cache key

        Returns:
            Cached item or None if expired/not found
        """
        with self._lock:
            if key not in self._cache:
                return None

            # Check TTL
            if time.time() - self._timestamps[key] > self.ttl_seconds:
                self._remove_item(key)
                return None

            # Move to end (LRU)
            value = self._cache.pop(key)
            self._cache[key] = value
            return value

    def put(self, key: str, value: Any) -> bool:
        """
        Put item in cache.

        Args:
            key: Cache key
            value: Value to cache

        Returns:
            True if item was cached
        """
        with self._lock:
            current_time = time.time()

            # Remove expired items
            self._cleanup_expired(current_time)

            # Evict if necessary
            while len(self._cache) >= self.maxsize:
                oldest_key = next(iter(self._cache))
                self._remove_item(oldest_key)

            # Add new item
            self._cache[key] = value
            self._timestamps[key] = current_time
            return True

    def remove(self, key: str) -> bool:
        """
        Remove item from cache.

        Args:
            key: Cache key

        Returns:
            True if item was removed
        """
        with self._lock:
            return self._remove_item(key)

    def _remove_item(self, key: str) -> bool:
        """Remove item without lock."""
        if key in self._cache:
            del self._cache[key]
            del self._timestamps[key]
            return True
        return False

    def _cleanup_expired(self, current_time: float):
        """Remove expired items."""
        expired_keys = [
            key
            for key, timestamp in self._timestamps.items()
            if current_time - timestamp > self.ttl_seconds
        ]

        for key in expired_keys:
            self._remove_item(key)

    def size(self) -> int:
        """Get current cache size."""
        with self._lock:
            return len(self._cache)

    def clear(self):
        """Clear all items."""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()


class MemoryPool:
    """
    Memory pool for reusing objects to reduce GC pressure.
    """

    def __init__(self, factory: Callable, max_size: int = 100):
        """
        Initialize memory pool.

        Args:
            factory: Function to create new objects
            max_size: Maximum pool size
        """
        self.factory = factory
        self.max_size = max_size
        self._pool: List[Any] = []
        self._lock = threading.Lock()
        self.logger = logging.getLogger(__name__)

    def acquire(self) -> Any:
        """
        Acquire object from pool.

        Returns:
            Object from pool or new object
        """
        with self._lock:
            if self._pool:
                return self._pool.pop()
            else:
                return self.factory()

    def release(self, obj: Any):
        """
        Release object back to pool.

        Args:
            obj: Object to release
        """
        with self._lock:
            if len(self._pool) < self.max_size:
                # Reset object state if possible
                if hasattr(obj, "reset"):
                    obj.reset()
                self._pool.append(obj)
            else:
                self.logger.warning("Memory pool full, object not returned")

    def size(self) -> int:
        """Get current pool size."""
        with self._lock:
            return len(self._pool)


class MemoryMonitor:
    """
    Memory monitoring and management system.
    """

    def __init__(
        self,
        warning_threshold_mb: float = 1000.0,
        critical_threshold_mb: float = 1500.0,
    ):
        """
        Initialize memory monitor.

        Args:
            warning_threshold_mb: Memory warning threshold in MB
            critical_threshold_mb: Memory critical threshold in MB
        """
        self.warning_threshold_mb = warning_threshold_mb
        self.critical_threshold_mb = critical_threshold_mb
        self._lock = AsyncLockManager("memory_monitor")
        self.logger = logging.getLogger(__name__)
        self._cleanup_callbacks: List[Callable] = []
        self._monitoring = False

    async def start_monitoring(self, interval_seconds: int = 30):
        """
        Start memory monitoring.

        Args:
            interval_seconds: Monitoring interval
        """
        self._monitoring = True
        self.logger.info("Memory monitoring started")

        while self._monitoring:
            try:
                stats = await self.get_memory_stats()
                await self._check_thresholds(stats)
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                self.logger.error(f"Memory monitoring error: {e}")
                await asyncio.sleep(interval_seconds)

    def stop_monitoring(self):
        """Stop memory monitoring."""
        self._monitoring = False
        self.logger.info("Memory monitoring stopped")

    async def get_memory_stats(self) -> MemoryStats:
        """
        Get current memory statistics.

        Returns:
            Memory statistics
        """
        try:
            # System memory
            memory = psutil.virtual_memory()

            # Process memory
            process = psutil.Process()
            process_memory = process.memory_info()

            return MemoryStats(
                total_memory_mb=memory.total / (1024 * 1024),
                used_memory_mb=memory.used / (1024 * 1024),
                available_memory_mb=memory.available / (1024 * 1024),
                process_memory_mb=process_memory.rss / (1024 * 1024),
                gc_count=gc.get_count()[0],
                timestamp=time.time(),
            )
        except Exception as e:
            self.logger.error(f"Error getting memory stats: {e}")
            return MemoryStats()

    async def _check_thresholds(self, stats: MemoryStats):
        """
        Check memory thresholds and trigger cleanup.

        Args:
            stats: Current memory statistics
        """
        if stats.process_memory_mb > self.critical_threshold_mb:
            self.logger.critical(f"Memory critical: {stats.process_memory_mb:.1f} MB")
            await self._emergency_cleanup()
        elif stats.process_memory_mb > self.warning_threshold_mb:
            self.logger.warning(f"Memory warning: {stats.process_memory_mb:.1f} MB")
            await self._trigger_cleanup()

    async def _trigger_cleanup(self):
        """Trigger cleanup callbacks."""
        for callback in self._cleanup_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                self.logger.error(f"Cleanup callback error: {e}")

        # Force garbage collection
        gc.collect()

    async def _emergency_cleanup(self):
        """Emergency cleanup for critical memory situations."""
        self.logger.critical("Emergency memory cleanup triggered")

        # Aggressive garbage collection
        for _ in range(3):
            gc.collect()
            await asyncio.sleep(0.1)

        # Trigger all cleanup callbacks
        await self._trigger_cleanup()

        # Clear caches if available
        if hasattr(self, "_caches"):
            for cache in self._caches:
                cache.clear()

    def add_cleanup_callback(self, callback: Callable):
        """
        Add cleanup callback.

        Args:
            callback: Function to call during cleanup
        """
        self._cleanup_callbacks.append(callback)

    def register_cache(self, cache: BoundedCache):
        """
        Register cache for cleanup.

        Args:
            cache: Cache to register
        """
        if not hasattr(self, "_caches"):
            self._caches = []
        self._caches.append(cache)


class ResourceManager:
    """
    Resource manager with automatic cleanup.
    """

    def __init__(self):
        """Initialize resource manager."""
        self._resources: Dict[str, weakref.ref] = {}
        self._lock = threading.Lock()
        self.logger = logging.getLogger(__name__)

    def register_resource(self, name: str, resource: Any):
        """
        Register resource for cleanup.

        Args:
            name: Resource name
            resource: Resource object
        """
        with self._lock:
            # Use weak reference to prevent memory leaks
            self._resources[name] = weakref.ref(resource, self._cleanup_callback)

    def unregister_resource(self, name: str):
        """
        Unregister resource.

        Args:
            name: Resource name
        """
        with self._lock:
            self._resources.pop(name, None)

    def _cleanup_callback(self, weak_ref):
        """Callback when resource is garbage collected."""
        self.logger.debug(f"Resource automatically cleaned up: {weak_ref}")

    async def cleanup_all(self):
        """Cleanup all registered resources."""
        with self._lock:
            for name, weak_ref in list(self._resources.items()):
                resource = weak_ref()
                if resource:
                    try:
                        if hasattr(resource, "close"):
                            if asyncio.iscoroutinefunction(resource.close):
                                await resource.close()
                            else:
                                resource.close()
                        elif hasattr(resource, "cleanup"):
                            if asyncio.iscoroutinefunction(resource.cleanup):
                                await resource.cleanup()
                            else:
                                resource.cleanup()
                    except Exception as e:
                        self.logger.error(f"Error cleaning up resource {name}: {e}")

                self._resources.pop(name, None)


# Global memory management instances
memory_monitor = MemoryMonitor()
signal_cache = BoundedCache(maxsize=500, ttl_seconds=1800)  # 30 minutes
trade_cache = BoundedCache(maxsize=1000, ttl_seconds=3600)  # 1 hour
market_data_cache = BoundedCache(maxsize=2000, ttl_seconds=300)  # 5 minutes
resource_manager = ResourceManager()

# Memory pools for common objects
tick_pool = MemoryPool(
    lambda: {"symbol": "", "price": 0, "timestamp": 0}, max_size=1000
)
candle_pool = MemoryPool(
    lambda: {"open": 0, "high": 0, "low": 0, "close": 0, "volume": 0}, max_size=500
)
signal_pool = MemoryPool(
    lambda: {"signal_id": "", "direction": "", "entry_price": 0}, max_size=200
)
