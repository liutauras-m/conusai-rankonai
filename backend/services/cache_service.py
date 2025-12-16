"""
Cache Service - Single Responsibility for Redis Caching

Handles all Redis cache operations with proper abstraction.
"""

import hashlib
import json
import logging
import os
from typing import Any, Optional, Protocol
from urllib.parse import urlparse

import redis.asyncio as redis


def normalize_url(url: str) -> str:
    """
    Normalize URL for consistent cache keys.
    
    - Removes www. prefix
    - Removes trailing slash
    - Lowercases the domain
    
    Example:
        https://www.conusai.com/ -> https://conusai.com
        https://CONUSAI.COM/page/ -> https://conusai.com/page
    """
    if not url:
        return url
    
    # Parse the URL
    parsed = urlparse(url)
    
    # Normalize the domain (lowercase, remove www.)
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    
    # Rebuild URL with normalized parts
    # Keep path but remove trailing slash (except for root)
    path = parsed.path.rstrip("/") or ""
    
    # Reconstruct URL
    normalized = f"{parsed.scheme}://{netloc}{path}"
    
    # Add query string if present
    if parsed.query:
        normalized += f"?{parsed.query}"
    
    return normalized

logger = logging.getLogger(__name__)


class ICacheService(Protocol):
    """Interface for cache operations."""
    
    async def get(self, key: str) -> Optional[dict]:
        """Get value from cache."""
        ...
    
    async def set(self, key: str, value: dict, ttl: int | None = None) -> bool:
        """Set value in cache with optional TTL."""
        ...
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        ...
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        ...
    
    def generate_key(self, prefix: str, *args: str) -> str:
        """Generate a cache key from prefix and arguments."""
        ...


class CacheService:
    """
    Redis-backed cache service with connection management.
    
    Follows Single Responsibility - only handles caching.
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        default_ttl: int = 3600,
    ):
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self._client: Optional[redis.Redis] = None
        self._connected = False
    
    async def connect(self) -> bool:
        """Establish Redis connection."""
        if self._connected:
            return True
        
        try:
            self._client = redis.from_url(self.redis_url, decode_responses=True)
            await self._client.ping()
            self._connected = True
            logger.info(f"✓ Connected to Redis at {self.redis_url}")
            return True
        except Exception as e:
            logger.warning(f"⚠ Redis connection failed: {e}. Running without cache.")
            self._client = None
            self._connected = False
            return False
    
    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None
            self._connected = False
            logger.info("Redis connection closed")
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to Redis."""
        return self._connected and self._client is not None
    
    async def get(self, key: str) -> Optional[dict]:
        """Get value from cache, returns None if not found or error."""
        if not self._client:
            return None
        
        try:
            cached = await self._client.get(key)
            if cached:
                return json.loads(cached)
            return None
        except Exception as e:
            logger.error(f"Cache read error for {key}: {e}")
            return None
    
    async def set(self, key: str, value: dict, ttl: int | None = None) -> bool:
        """Set value in cache with TTL."""
        if not self._client:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            await self._client.setex(
                key,
                ttl,
                json.dumps(value, ensure_ascii=False),
            )
            return True
        except Exception as e:
            logger.error(f"Cache write error for {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if not self._client:
            return False
        
        try:
            deleted = await self._client.delete(key)
            return bool(deleted)
        except Exception as e:
            logger.error(f"Cache delete error for {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self._client:
            return False
        
        try:
            return bool(await self._client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error for {key}: {e}")
            return False
    
    async def get_raw(self, key: str) -> Optional[str]:
        """Get raw string value from cache."""
        if not self._client:
            return None
        
        try:
            return await self._client.get(key)
        except Exception as e:
            logger.error(f"Cache read error for {key}: {e}")
            return None
    
    async def set_raw(self, key: str, value: str, ttl: int | None = None) -> bool:
        """Set raw string value in cache."""
        if not self._client:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            await self._client.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.error(f"Cache write error for {key}: {e}")
            return False
    
    @staticmethod
    def generate_key(prefix: str, *args: str) -> str:
        """
        Generate a deterministic cache key from prefix and arguments.
        
        Example: generate_key("workflow", url, "overview") 
                 → "workflow:abc123def456"
        """
        key_data = ":".join(str(arg) for arg in args)
        hash_suffix = hashlib.sha256(key_data.encode()).hexdigest()[:16]
        return f"{prefix}:{hash_suffix}"
    
    @property
    def client(self) -> Optional[redis.Redis]:
        """Get the raw Redis client for advanced operations."""
        return self._client


# Singleton instance
_cache_service: Optional[CacheService] = None


async def get_cache_service() -> CacheService:
    """
    Dependency injection factory for CacheService.
    
    Usage:
        @app.get("/endpoint")
        async def endpoint(cache: CacheService = Depends(get_cache_service)):
            ...
    """
    global _cache_service
    
    if _cache_service is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        default_ttl = int(os.getenv("CACHE_TTL", "3600"))
        _cache_service = CacheService(redis_url=redis_url, default_ttl=default_ttl)
        await _cache_service.connect()
    
    return _cache_service


async def shutdown_cache_service() -> None:
    """Cleanup function for application shutdown."""
    global _cache_service
    if _cache_service:
        await _cache_service.disconnect()
        _cache_service = None
