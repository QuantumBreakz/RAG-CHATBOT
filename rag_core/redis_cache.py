import redis
import os

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))

_redis_client = None

def get_redis_client():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    return _redis_client

def redis_set(key, value, ex=None):
    client = get_redis_client()
    return client.set(key, value, ex=ex)

def redis_get(key):
    client = get_redis_client()
    return client.get(key) 