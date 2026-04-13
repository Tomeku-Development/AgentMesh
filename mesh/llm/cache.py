"""Simple in-memory TTL cache for LLM responses."""

from __future__ import annotations

import hashlib
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """A single cache entry with TTL."""

    value: dict[str, Any]
    expires_at: float
    created_at: float = field(default_factory=time.time)


class LLMCache:
    """Simple in-memory TTL cache for LLM responses.

    Thread-safe for single-threaded async operations.
    Uses LRU eviction when max_size is reached.
    """

    def __init__(self, default_ttl: float = 30.0, max_size: int = 100):
        """Initialize the cache.

        Args:
            default_ttl: Default time-to-live in seconds
            max_size: Maximum number of entries (LRU eviction)
        """
        self._default_ttl = default_ttl
        self._max_size = max_size
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()

        # Stats
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> dict[str, Any] | None:
        """Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if miss/expired
        """
        entry = self._cache.get(key)

        if entry is None:
            self._misses += 1
            return None

        # Check expiration
        if time.time() > entry.expires_at:
            logger.debug(f"Cache key expired: {key[:16]}...")
            del self._cache[key]
            self._misses += 1
            return None

        # Move to end (most recently used)
        self._cache.move_to_end(key)
        self._hits += 1
        logger.debug(f"Cache hit: {key[:16]}...")
        return entry.value

    def put(
        self, key: str, value: dict[str, Any], ttl: float | None = None
    ) -> None:
        """Put a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        if ttl is None:
            ttl = self._default_ttl

        now = time.time()
        entry = CacheEntry(
            value=value,
            expires_at=now + ttl,
            created_at=now,
        )

        # Remove if exists (to update position)
        if key in self._cache:
            del self._cache[key]

        # Evict oldest if at capacity
        while len(self._cache) >= self._max_size:
            oldest_key = next(iter(self._cache))
            logger.debug(f"Evicting cache entry: {oldest_key[:16]}...")
            del self._cache[oldest_key]

        self._cache[key] = entry
        logger.debug(f"Cached key: {key[:16]}... (TTL: {ttl}s)")

    def make_key(self, *args: Any) -> str:
        """Create a cache key from arguments.

        Args:
            *args: Arguments to hash into a key

        Returns:
            Hashed cache key
        """
        # Convert args to string representation
        key_parts = []
        for arg in args:
            if isinstance(arg, str):
                key_parts.append(arg)
            elif isinstance(arg, (dict, list)):
                import json

                key_parts.append(json.dumps(arg, sort_keys=True))
            else:
                key_parts.append(str(arg))

        key_str = "|".join(key_parts)

        # Hash to fixed-length key
        return hashlib.sha256(key_str.encode()).hexdigest()[:32]

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        logger.debug("Cache cleared")

    def stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with hits, misses, size, hit_rate
        """
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0

        return {
            "hits": self._hits,
            "misses": self._misses,
            "size": len(self._cache),
            "max_size": self._max_size,
            "hit_rate": hit_rate,
            "default_ttl": self._default_ttl,
        }

    def cleanup_expired(self) -> int:
        """Remove expired entries.

        Returns:
            Number of entries removed
        """
        now = time.time()
        expired_keys = [
            key for key, entry in self._cache.items() if entry.expires_at <= now
        ]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired entries")

        return len(expired_keys)
