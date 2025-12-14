"""
Thread-safe synchronization primitives for XAUUSD Gold Trading System.

Provides locks, semaphores, and bounded data structures
to prevent race conditions and ensure thread safety.
"""

import asyncio
import threading
from typing import Any, Optional, Dict, List, Set, Generic, TypeVar
from collections import deque
from dataclasses import dataclass
from contextlib import asynccontextmanager, contextmanager
import time
import logging

T = TypeVar('T')


class BoundedQueue:
    """
    Thread-safe bounded queue with maximum capacity.
    Prevents memory exhaustion by limiting queue size.
    """
    
    def __init__(self, maxsize: int = 1000):
        """
        Initialize bounded queue.
        
        Args:
            maxsize: Maximum queue size
        """
        self.maxsize = maxsize
        self._queue = deque(maxlen=maxsize)
        self._lock = threading.RLock()
        self._not_empty = threading.Condition(self._lock)
        self._not_full = threading.Condition(self._lock)
        self.logger = logging.getLogger(__name__)
    
    def put(self, item: T, block: bool = True, timeout: Optional[float] = None) -> bool:
        """
        Add item to queue.
        
        Args:
            item: Item to add
            block: Whether to block if queue is full
            timeout: Timeout in seconds
            
        Returns:
            True if item was added
        """
        with self._not_full:
            if not block:
                if len(self._queue) >= self.maxsize:
                    self.logger.warning(f"Queue full, dropping item: {type(item)}")
                    return False
                self._queue.append(item)
                self._not_empty.notify()
                return True
            
            start_time = time.time()
            while len(self._queue) >= self.maxsize:
                remaining = timeout - (time.time() - start_time) if timeout else None
                if remaining is not None and remaining <= 0:
                    self.logger.warning(f"Queue full timeout, dropping item: {type(item)}")
                    return False
                
                if not self._not_full.wait(timeout=remaining):
                    return False
            
            self._queue.append(item)
            self._not_empty.notify()
            return True
    
    def get(self, block: bool = True, timeout: Optional[float] = None) -> Optional[T]:
        """
        Get item from queue.
        
        Args:
            block: Whether to block if queue is empty
            timeout: Timeout in seconds
            
        Returns:
            Item or None if timeout
        """
        with self._not_empty:
            if not block:
                if not self._queue:
                    return None
                item = self._queue.popleft()
                self._not_full.notify()
                return item
            
            start_time = time.time()
            while not self._queue:
                remaining = timeout - (time.time() - start_time) if timeout else None
                if remaining is not None and remaining <= 0:
                    return None
                
                if not self._not_empty.wait(timeout=remaining):
                    return None
            
            item = self._queue.popleft()
            self._not_full.notify()
            return item
    
    def size(self) -> int:
        """Get current queue size."""
        with self._lock:
            return len(self._queue)
    
    def is_empty(self) -> bool:
        """Check if queue is empty."""
        with self._lock:
            return len(self._queue) == 0
    
    def is_full(self) -> bool:
        """Check if queue is full."""
        with self._lock:
            return len(self._queue) >= self.maxsize


class AsyncBoundedQueue:
    """
    Async bounded queue with maximum capacity.
    """
    
    def __init__(self, maxsize: int = 1000):
        """
        Initialize async bounded queue.
        
        Args:
            maxsize: Maximum queue size
        """
        self.maxsize = maxsize
        self._queue = asyncio.Queue(maxsize=maxsize)
        self.logger = logging.getLogger(__name__)
    
    async def put(self, item: T) -> bool:
        """
        Add item to queue.
        
        Args:
            item: Item to add
            
        Returns:
            True if item was added
        """
        try:
            await asyncio.wait_for(self._queue.put(item), timeout=1.0)
            return True
        except asyncio.TimeoutError:
            self.logger.warning(f"Async queue full, dropping item: {type(item)}")
            return False
    
    async def get(self) -> Optional[T]:
        """
        Get item from queue.
        
        Returns:
            Item or None if timeout
        """
        try:
            return await asyncio.wait_for(self._queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            return None
    
    def size(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()
    
    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return self._queue.empty()
    
    def is_full(self) -> bool:
        """Check if queue is full."""
        return self._queue.full()


class ThreadSafeDict(Generic[T]):
    """
    Thread-safe dictionary with read-write locks.
    """
    
    def __init__(self):
        """Initialize thread-safe dictionary."""
        self._dict: Dict[str, T] = {}
        self._lock = threading.RLock()
    
    def get(self, key: str, default: Optional[T] = None) -> Optional[T]:
        """
        Get value by key.
        
        Args:
            key: Dictionary key
            default: Default value if key not found
            
        Returns:
            Value or default
        """
        with self._lock:
            return self._dict.get(key, default)
    
    def set(self, key: str, value: T) -> None:
        """
        Set value by key.
        
        Args:
            key: Dictionary key
            value: Value to set
        """
        with self._lock:
            self._dict[key] = value
    
    def delete(self, key: str) -> bool:
        """
        Delete key from dictionary.
        
        Args:
            key: Key to delete
            
        Returns:
            True if key was deleted
        """
        with self._lock:
            if key in self._dict:
                del self._dict[key]
                return True
            return False
    
    def keys(self) -> List[str]:
        """Get all keys."""
        with self._lock:
            return list(self._dict.keys())
    
    def values(self) -> List[T]:
        """Get all values."""
        with self._lock:
            return list(self._dict.values())
    
    def items(self) -> List[tuple]:
        """Get all items."""
        with self._lock:
            return list(self._dict.items())
    
    def size(self) -> int:
        """Get dictionary size."""
        with self._lock:
            return len(self._dict)
    
    def clear(self) -> None:
        """Clear dictionary."""
        with self._lock:
            self._dict.clear()
    
    def contains(self, key: str) -> bool:
        """Check if key exists."""
        with self._lock:
            return key in self._dict


class AsyncLockManager:
    """
    Async lock manager with timeout and deadlock prevention.
    """
    
    def __init__(self, name: str = "lock"):
        """
        Initialize async lock manager.
        
        Args:
            name: Lock name for debugging
        """
        self.name = name
        self._lock = asyncio.Lock()
        self._owner = None
        self.logger = logging.getLogger(__name__)
    
    @asynccontextmanager
    async def acquire(self, timeout: float = 30.0):
        """
        Acquire lock with timeout.
        
        Args:
            timeout: Lock timeout in seconds
        """
        try:
            await asyncio.wait_for(self._lock.acquire(), timeout=timeout)
            self._owner = asyncio.current_task()
            yield self
        except asyncio.TimeoutError:
            self.logger.error(f"Lock timeout for {self.name}")
            raise TimeoutError(f"Failed to acquire lock {self.name} within {timeout}s")
        finally:
            if self._lock.locked():
                self._lock.release()
                self._owner = None
    
    def is_locked(self) -> bool:
        """Check if lock is held."""
        return self._lock.locked()


class SemaphoreManager:
    """
    Semaphore manager for resource limiting.
    """
    
    def __init__(self, max_concurrent: int = 10, name: str = "semaphore"):
        """
        Initialize semaphore manager.
        
        Args:
            max_concurrent: Maximum concurrent operations
            name: Semaphore name for debugging
        """
        self.name = name
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._current_count = 0
        self._lock = asyncio.Lock()
        self.logger = logging.getLogger(__name__)
    
    @asynccontextmanager
    async def acquire(self, timeout: float = 30.0):
        """
        Acquire semaphore with timeout.
        
        Args:
            timeout: Acquisition timeout in seconds
        """
        try:
            await asyncio.wait_for(self._semaphore.acquire(), timeout=timeout)
            
            async with self._lock:
                self._current_count += 1
            
            yield self
            
        except asyncio.TimeoutError:
            self.logger.error(f"Semaphore timeout for {self.name}")
            raise TimeoutError(f"Failed to acquire semaphore {self.name} within {timeout}s")
        finally:
            if self._current_count > 0:
                self._semaphore.release()
                async with self._lock:
                    self._current_count -= 1
    
    def current_count(self) -> int:
        """Get current usage count."""
        return self._current_count
    
    def available_count(self) -> int:
        """Get available permits."""
        return self.max_concurrent - self._current_count


@dataclass
class ResourceLock:
    """
    Resource lock for exclusive access to specific resources.
    """
    resource_id: str
    lock_type: str  # "read", "write", "exclusive"
    acquired_at: float
    owner: str


class ResourceManager:
    """
    Manager for coordinating access to shared resources.
    """
    
    def __init__(self):
        """Initialize resource manager."""
        self._locks: Dict[str, List[ResourceLock]] = {}
        self._lock = asyncio.Lock()
        self.logger = logging.getLogger(__name__)
    
    async def acquire_resource(self, resource_id: str, lock_type: str = "write", 
                          owner: str = "unknown", timeout: float = 30.0) -> bool:
        """
        Acquire lock on specific resource.
        
        Args:
            resource_id: Resource identifier
            lock_type: Type of lock (read/write/exclusive)
            owner: Requesting owner
            timeout: Acquisition timeout
            
        Returns:
            True if lock acquired
        """
        async with self._lock:
            current_time = time.time()
            
            # Check if resource is already locked
            existing_locks = self._locks.get(resource_id, [])
            
            # Check for lock conflicts
            for existing_lock in existing_locks:
                if self._locks_conflict(existing_lock.lock_type, lock_type):
                    # Check if lock has expired (timeout protection)
                    if current_time - existing_lock.acquired_at > timeout:
                        existing_locks.remove(existing_lock)
                        self.logger.warning(f"Expired lock removed for {resource_id}")
                    else:
                        return False
            
            # Create new lock
            new_lock = ResourceLock(
                resource_id=resource_id,
                lock_type=lock_type,
                acquired_at=current_time,
                owner=owner
            )
            
            existing_locks.append(new_lock)
            self._locks[resource_id] = existing_locks
            
            self.logger.debug(f"Lock acquired for {resource_id} by {owner} ({lock_type})")
            return True
    
    async def release_resource(self, resource_id: str, owner: str) -> bool:
        """
        Release lock on specific resource.
        
        Args:
            resource_id: Resource identifier
            owner: Lock owner
            
        Returns:
            True if lock released
        """
        async with self._lock:
            existing_locks = self._locks.get(resource_id, [])
            
            for lock in existing_locks:
                if lock.owner == owner:
                    existing_locks.remove(lock)
                    self.logger.debug(f"Lock released for {resource_id} by {owner}")
                    
                    if not existing_locks:
                        del self._locks[resource_id]
                    
                    return True
            
            return False
    
    def _locks_conflict(self, existing_type: str, new_type: str) -> bool:
        """
        Check if two lock types conflict.
        
        Args:
            existing_type: Existing lock type
            new_type: New lock type
            
        Returns:
            True if locks conflict
        """
        if existing_type == "exclusive" or new_type == "exclusive":
            return True
        if existing_type == "write" and new_type == "write":
            return True
        return False
    
    def get_locked_resources(self) -> Dict[str, List[ResourceLock]]:
        """Get all locked resources."""
        return self._locks.copy()


# Global synchronization primitives
trade_locks = ResourceManager()
signal_queue = AsyncBoundedQueue(maxsize=1000)
market_data_queue = AsyncBoundedQueue(maxsize=5000)
notification_queue = AsyncBoundedQueue(maxsize=2000)
database_semaphore = SemaphoreManager(max_concurrent=20, name="database")
trade_semaphore = SemaphoreManager(max_concurrent=5, name="trading")