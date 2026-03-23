import redis
import time

r = redis.Redis("localhost", port=6379, decode_responses=True)

def is_allowed(key:str, limit:int, window_seconds:int) -> dict:
  # Key : the identifier(IP)
  now = time.time()
  window_start = now - window_seconds

  pipe = r.pipeline()               # Mutiple redis commands to be executed as one

  # Deleting all requests outside the current range
  pipe.zremrangebyscore(key, 0, window_start)

  # Count of number of requests from the key
  pipe.zcard(key)

  # Add the current key and timestamp
  pipe.zadd(key, {str(now) : now})

  # Set the key to expire after the current window
  pipe.expire(key, window_seconds)

  results = pipe.execute()
  current_count = results[1]
  allowed = current_count < limit

  return{
    "allowed" : allowed,
    "count" : current_count,
    "remaining" : max(0, limit - current_count - 1) if allowed else 0,
    "limit" : limit,
    "retry_after" : window_seconds if not allowed else None
  }

  
