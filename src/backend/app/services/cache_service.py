import redis
import json
import hashlib
from typing import Optional, Any
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    def __init__(self):
        self.client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        
    def _make_key(self, tenant_id: int, question: str) -> str:
        """Generate cache key from tenant and question"""
        # Normalize question for caching
        normalized = question.lower().strip()
        question_hash = hashlib.md5(normalized.encode()).hexdigest()
        return f"qa:{tenant_id}:{question_hash}"
    
    def get_cached_answer(self, tenant_id: int, question: str) -> Optional[dict]:
        """Get cached answer if exists"""
        key = self._make_key(tenant_id, question)
        try:
            cached = self.client.get(key)
            if cached:
                logger.info(f"Cache hit for tenant {tenant_id}")
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        return None
    
    def cache_answer(
        self,
        tenant_id: int,
        question: str,
        answer: dict,
        ttl: Optional[int] = None
    ):
        """Cache an answer"""
        key = self._make_key(tenant_id, question)
        ttl = ttl or settings.CACHE_TTL
        try:
            self.client.setex(key, ttl, json.dumps(answer))
            logger.info(f"Cached answer for tenant {tenant_id}")
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    def check_rate_limit(self, tenant_id: int) -> bool:
        """Check if tenant is within rate limit"""
        key = f"rate:{tenant_id}"
        try:
            current = self.client.get(key)
            if current is None:
                self.client.setex(key, 60, 1)
                return True
            if int(current) >= settings.RATE_LIMIT_PER_MINUTE:
                return False
            self.client.incr(key)
            return True
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return True  # Fail open
    
    def check_idempotency(self, request_id: str) -> bool:
        """Check if request was already processed (idempotency)"""
        key = f"idem:{request_id}"
        try:
            # SETNX returns True if key was set (new request)
            return self.client.setnx(key, "1")
        except Exception as e:
            logger.error(f"Idempotency check error: {e}")
            return True
    
    def set_idempotency(self, request_id: str, ttl: int = 3600):
        """Mark request as processed"""
        key = f"idem:{request_id}"
        try:
            self.client.setex(key, ttl, "1")
        except Exception as e:
            logger.error(f"Idempotency set error: {e}")
    
    def health_check(self) -> bool:
        """Check if Redis is healthy"""
        try:
            return self.client.ping()
        except Exception:
            return False
