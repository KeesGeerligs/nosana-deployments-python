"""TTL Cache implementation following Theoriq Agent SDK patterns.

Provides time-to-live caching for improved performance in API operations.
"""

from __future__ import annotations

import time
from typing import Dict, Generic, Optional, TypeVar

T = TypeVar("T")


class TTLCache(Generic[T]):
    """Time-to-live cache implementation.
    
    Similar to Theoriq's TTLCache, provides automatic expiration
    and size-limited caching for performance optimization.
    """
    
    def __init__(self, *, ttl: Optional[int] = None, max_size: int = 100) -> None:
        """Initialize TTL cache.
        
        Args:
            ttl: Time-to-live in seconds. If None, items never expire
            max_size: Maximum number of items to cache
        """
        self.ttl = ttl
        self.max_size = max_size
        self._cache: Dict[str, T] = {}
        self._timestamps: Dict[str, float] = {}
        self._access_order: list[str] = []
    
    def get(self, key: str) -> Optional[T]:
        """Get item from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if present and not expired, None otherwise
        """
        if key not in self._cache:
            return None
        
        # Check expiration
        if self.ttl is not None:
            current_time = time.time()
            if current_time - self._timestamps[key] > self.ttl:
                self._remove(key)
                return None
        
        # Update access order for LRU eviction
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
        
        return self._cache[key]
    
    def put(self, key: str, value: T) -> None:
        """Put item in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        current_time = time.time()
        
        # Remove existing entry if present
        if key in self._cache:
            self._remove(key)
        
        # Evict oldest entries if cache is full
        while len(self._cache) >= self.max_size:
            if self._access_order:
                oldest_key = self._access_order[0]
                self._remove(oldest_key)
            else:
                break
        
        # Add new entry
        self._cache[key] = value
        self._timestamps[key] = current_time
        self._access_order.append(key)
    
    def clear(self) -> None:
        """Clear all cached items."""
        self._cache.clear()
        self._timestamps.clear()
        self._access_order.clear()
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)
    
    def _remove(self, key: str) -> None:
        """Remove item from cache."""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
        if key in self._access_order:
            self._access_order.remove(key)
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        return self.get(key) is not None
    
    def __len__(self) -> int:
        """Get current cache size."""
        return len(self._cache)