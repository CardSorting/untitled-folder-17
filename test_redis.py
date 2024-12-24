import redis
import sys

def test_redis_connection():
    redis_url = 'redis://matrix-redis.oo6rj9.0001.usw2.cache.amazonaws.com:6379'
    print(f"Connecting to Redis at: {redis_url}")
    
    try:
        r = redis.from_url(redis_url, socket_timeout=5)
        result = r.ping()
        print(f"Connection successful! Ping result: {result}")
        return True
    except redis.ConnectionError as e:
        print(f"Connection error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

if __name__ == '__main__':
    success = test_redis_connection()
    sys.exit(0 if success else 1)
