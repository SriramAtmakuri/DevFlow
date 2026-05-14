import os
import json
import hashlib
from typing import Optional, Any
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))

_client: Optional[redis.Redis] = None


def get_redis() -> Optional[redis.Redis]:
    global _client
    if _client is None:
        try:
            _client = redis.from_url(REDIS_URL, decode_responses=True)
            _client.ping()
        except Exception:
            _client = None
    return _client


def make_cache_key(prefix: str, data: Any) -> str:
    payload = json.dumps(data, sort_keys=True)
    hash_val = hashlib.sha256(payload.encode()).hexdigest()[:16]
    return f"devflow:{prefix}:{hash_val}"


def get_cached(key: str) -> Optional[dict]:
    client = get_redis()
    if not client:
        return None
    try:
        value = client.get(key)
        return json.loads(value) if value else None
    except Exception:
        return None


def set_cached(key: str, value: dict, ttl: int = CACHE_TTL) -> bool:
    client = get_redis()
    if not client:
        return False
    try:
        client.setex(key, ttl, json.dumps(value))
        return True
    except Exception:
        return False


def invalidate_pattern(pattern: str) -> int:
    client = get_redis()
    if not client:
        return 0
    try:
        keys = client.keys(f"devflow:{pattern}:*")
        return client.delete(*keys) if keys else 0
    except Exception:
        return 0
