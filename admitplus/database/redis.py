import logging
from typing import Optional

import redis.asyncio as redis

from admitplus.config import settings


class RedisConnector:
    _instances = {}

    def __init__(self):
        logging.info("[Redis Service] [Init] Initializing Redis connection...")
        self.host = settings.REDIS_HOST or "localhost"
        self.port = settings.REDIS_PORT
        self.username = settings.REDIS_USERNAME
        self.password = settings.REDIS_PASSWORD
        self.client: Optional[redis.Redis] = None
        self._initialized = False

    @classmethod
    async def get_instance(cls) -> "RedisConnector":
        if "default" not in cls._instances:
            logging.info("[Redis Service] [Init] Creating new Redis instance")
            cls._instances["default"] = RedisConnector()

        instance = cls._instances["default"]
        if not instance._initialized:
            await instance._connect()
            instance._initialized = True

        logging.info("[Redis Service] [Init] Returning Redis instance")
        return instance

    async def _connect(self):
        """Initialize Redis connection"""
        if self.client is not None:
            logging.info(
                "[Redis Service] [Connection] Redis client already initialized."
            )
            return

        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                decode_responses=True,
                retry_on_timeout=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            logging.info(
                f"[Redis Service] [Connection] Redis client initialized for {self.host}:{self.port}"
            )

        except Exception as e:
            logging.error(f"[Redis Service] [Connection] Redis connection failed: {e}")
            self.client = None
            raise

    async def get_client(self) -> redis.Redis:
        """Get Redis client instance"""
        if self.client is None:
            logging.error(
                "[Redis Service] [Client] get_client failed: No Redis connection."
            )
            raise ConnectionError("[RedisConnector] Redis is not connected.")
        return self.client

    async def ping(self) -> bool:
        """Test Redis connection"""
        try:
            client = await self.get_client()
            await client.ping()
            return True
        except Exception as e:
            logging.error(f"[Redis Service] [Ping] Redis ping failed: {e}")
            return False

    def close(self):
        """Close Redis connection"""
        if self.client:
            self.client.close()
            self.client = None
            self._initialized = False
            logging.info("[Redis Service] [Connection] Redis connection closed.")

    @classmethod
    def close_all(cls):
        """Close all Redis connections"""
        for name, instance in cls._instances.items():
            instance.close()
        cls._instances.clear()
        logging.info("[Redis Service] [Connection] All Redis connections closed.")


# Create singleton instance (legacy support)
async def get_redis_client() -> RedisConnector:
    """Get Redis client instance"""
    return await RedisConnector.get_instance()


# For backward compatibility
redis_client = None


class BaseRedisCRUD:
    def __init__(self):
        self.redis_connector: Optional[RedisConnector] = None
        self._initialized = False

    async def _ensure_initialized(self):
        """Ensure Redis connector is initialized"""
        if not self._initialized or self.redis_connector is None:
            self.redis_connector = await RedisConnector.get_instance()
            self._initialized = True

    async def ping(self) -> bool:
        """Test Redis connection"""
        await self._ensure_initialized()
        return await self.redis_connector.ping()

    async def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        # await self._ensure_initialized()
        try:
            # client = await self.redis_connector.get_client()
            value = await redismanager.pool.get(key)
            logging.debug(f"[Redis Repository] [Get] Retrieved value for key '{key}'")
            return value
        except Exception as e:
            logging.error(
                f"[Redis Repository] [Get] Error getting value for key '{key}': {e}"
            )
            raise

    async def set(self, key: str, value: str, expire: Optional[int] = None) -> bool:
        """Set key-value pair with optional expiration"""
        # await self._ensure_initialized()
        try:
            # client = await self.redis_connector.get_client()
            result = await redismanager.pool.set(key, value, ex=expire)
            logging.debug(f"[Redis Repository] [Set] Set value for key '{key}'")
            return result
        except Exception as e:
            logging.error(
                f"[Redis Repository] [Set] Error setting value for key '{key}': {e}"
            )
            raise

    async def delete(self, key: str) -> bool:
        """Delete key"""
        # await self._ensure_initialized()
        try:
            # client = await self.redis_connector.get_client()
            result = await redismanager.pool.delete(key)
            logging.debug(f"[Redis Repository] [Delete] Deleted key '{key}'")
            return bool(result)
        except Exception as e:
            logging.error(
                f"[Redis Repository] [Delete] Error deleting key '{key}': {e}"
            )
            raise

    async def increment(self, key: str) -> int:
        """Increment value by key"""
        # await self._ensure_initialized()
        try:
            # client = await self.redis_connector.get_client()
            result = await redismanager.pool.incr(key)
            logging.debug(
                f"[Redis Repository] [Increment] Incremented value for key '{key}'"
            )
            return result
        except Exception as e:
            logging.error(
                f"[Redis Repository] [Increment] Error incrementing value for key '{key}': {e}"
            )
            raise

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        # await self._ensure_initialized()
        try:
            # client = await self.redis_connector.get_client()
            result = await redismanager.pool.exists(key)
            return bool(result)
        except Exception as e:
            logging.error(
                f"[Redis Repository] [Exists] Error checking key '{key}': {e}"
            )
            raise

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for key"""
        # await self._ensure_initialized()
        try:
            # client = await self.redis_connector.get_client()
            result = await redismanager.pool.expire(key, seconds)
            return bool(result)
        except Exception as e:
            logging.error(
                f"[Redis Repository] [Expire] Error setting expiration for key '{key}': {e}"
            )
            raise

    async def ttl(self, key: str) -> int:
        """Get time to live for key"""
        # await self._ensure_initialized()
        try:
            # client = await self.redis_connector.get_client()
            result = await redismanager.pool.ttl(key)
            return result
        except Exception as e:
            logging.error(
                f"[Redis Repository] [TTL] Error getting TTL for key '{key}': {e}"
            )
            raise

    # Hash operations
    async def hset(self, name: str, key: str, value: str) -> int:
        """Set hash field"""
        # await self._ensure_initialized()
        try:
            # client = await self.redis_connector.get_client()
            result = await redismanager.pool.hset(name, key, value)
            logging.debug(
                f"[Redis Repository] [HSet] Set hash field '{key}' in '{name}'"
            )
            return result
        except Exception as e:
            logging.error(
                f"[Redis Repository] [HSet] Error setting hash field '{key}' in '{name}': {e}"
            )
            raise

    async def hset_with_expire(
        self, name: str, key: str, value: str, expire_seconds: int
    ) -> int:
        """
        Set a hash field and ensure the hash has an expiration time.
        If the hash doesn't exist, set the expiration. If it exists, only extend if current TTL is less.
        """
        # await self._ensure_initialized()
        try:
            # client = await self.redis_connector.get_client()
            result = await redismanager.pool.hset(name, key, value)
            current_ttl = await redismanager.pool.ttl(name)
            if current_ttl <= 0 or current_ttl < expire_seconds:
                await redismanager.pool.expire(name, expire_seconds)
                logging.debug(
                    f"[Redis Repository] [HSetWithExpire] Set/updated expiration for hash '{name}' to {expire_seconds} seconds"
                )
            logging.debug(
                f"[Redis Repository] [HSetWithExpire] Set hash field '{key}' in '{name}' with expiration"
            )
            return result
        except Exception as e:
            logging.error(
                f"[Redis Repository] [HSetWithExpire] Error setting hash field '{key}' in '{name}' with expiration: {e}"
            )
            raise

    async def hget(self, name: str, key: str) -> Optional[str]:
        """Get hash field"""
        # await self._ensure_initialized()
        try:
            # client = await self.redis_connector.get_client()
            value = await redismanager.pool.hget(name, key)
            logging.debug(
                f"[Redis Repository] [HGet] Retrieved hash field '{key}' from '{name}'"
            )
            return value
        except Exception as e:
            logging.error(
                f"[Redis Repository] [HGet] Error getting hash field '{key}' from '{name}': {e}"
            )
            raise

    async def hgetall(self, name: str) -> dict:
        """Get all hash fields"""
        # await self._ensure_initialized()
        try:
            # client = await self.redis_connector.get_client()
            result = await redismanager.pool.hgetall(name)
            logging.debug(
                f"[Redis Repository] [HGetAll] Retrieved all fields from hash '{name}'"
            )
            return result
        except Exception as e:
            logging.error(
                f"[Redis Repository] [HGetAll] Error getting all fields from hash '{name}': {e}"
            )
            raise

    async def hdel(self, name: str, *keys: str) -> int:
        """Delete hash fields"""
        # await self._ensure_initialized()
        try:
            # client = await self.redis_connector.get_client()
            result = await redismanager.pool.hdel(name, *keys)
            logging.debug(
                f"[Redis Repository] [HDel] Deleted fields {keys} from hash '{name}'"
            )
            return result
        except Exception as e:
            logging.error(
                f"[Redis Repository] [HDel] Error deleting fields {keys} from hash '{name}': {e}"
            )
            raise

    async def sadd(self, key: str, *values: str) -> int:
        """Add members to a set"""
        # await self._ensure_initialized()
        try:
            # client = await self.redis_connector.get_client()
            result = await redismanager.pool.sadd(key, *values)
            logging.debug(
                f"[Redis Repository] [SAdd] Added {len(values)} members to set '{key}'"
            )
            return result
        except Exception as e:
            logging.error(
                f"[Redis Repository] [SAdd] Error adding members to set '{key}': {e}"
            )
            raise

    async def smembers(self, key: str) -> set:
        """Get all members of a set"""
        # await self._ensure_initialized()
        try:
            # client = await self.redis_connector.get_client()
            result = await redismanager.pool.smembers(key)
            logging.debug(
                f"[Redis Repository] [SMembers] Retrieved {len(result)} members from set '{key}'"
            )
            return result
        except Exception as e:
            logging.error(
                f"[Redis Repository] [SMembers] Error getting members from set '{key}': {e}"
            )
            raise

    async def srem(self, key: str, *values: str) -> int:
        """Remove members from a set"""
        # await self._ensure_initialized()
        try:
            # client = await self.redis_connector.get_client()
            result = await redismanager.pool.srem(key, *values)
            logging.debug(
                f"[Redis Repository] [SRem] Removed {len(values)} members from set '{key}'"
            )
            return result
        except Exception as e:
            logging.error(
                f"[Redis Repository] [SRem] Error removing members from set '{key}': {e}"
            )
            raise

    async def keys(self, pattern: str) -> list:
        """Get keys matching pattern"""
        # await self._ensure_initialized()
        try:
            # client = await self.redis_connector.get_client()
            result = await redismanager.pool.keys(pattern)
            logging.debug(
                f"[Redis Repository] [Keys] Found {len(result)} keys matching pattern '{pattern}'"
            )
            return result
        except Exception as e:
            logging.error(
                f"[Redis Repository] [Keys] Error getting keys with pattern '{pattern}': {e}"
            )
            raise

    async def close(self):
        """Close Redis connections"""
        if self.redis_connector:
            self.redis_connector.close()
            self._initialized = False

    # Create singleton instance for convenience
    # This mirrors previous usage pattern
    redis_repository = None


class RedisConnectionManager:
    def __init__(self):
        self.pool = None
        self.dsn = (
            f"redis://{settings.REDIS_USERNAME}:"
            f"{settings.REDIS_PASSWORD}@"
            f"{settings.REDIS_HOST}:"
            f"{settings.REDIS_PORT}/"
            f"{settings.REDIS_DB_NUM}"
        )

    def init(self):
        self.pool = redis.from_url(self.dsn, encoding="utf-8", decode_responses=True)

    async def close(self):
        if self.pool is None:
            # pylint: disable=broad-exception-raised
            raise Exception("RedisConnectionManager is not initialized")
        await self.pool.close()
        self.pool = None


redismanager = RedisConnectionManager()
