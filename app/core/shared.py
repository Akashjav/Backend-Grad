"""Shared atomic rate limits across workers and replicas."""
from app.core.config import settings

redis_client = None
if settings.REDIS_URL:
    from redis.asyncio import Redis, BlockingConnectionPool
    redis_client = Redis(connection_pool=BlockingConnectionPool.from_url(
        settings.REDIS_URL, socket_connect_timeout=2, socket_timeout=3,
        timeout=2, max_connections=100, decode_responses=True))

RATE_SCRIPT = """
local n = redis.call('INCR', KEYS[1])
if n == 1 then redis.call('EXPIRE', KEYS[1], 60) end
return n
"""


async def increment(key):
    return await redis_client.eval(RATE_SCRIPT, 1, "gradalumni:rate:" + key)
