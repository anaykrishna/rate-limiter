import redis
import time

r = redis.Redis("localhost", port=6379, decode_responses=True)

#Find out weather the api_key exisitsin the redis, if so return the meta data
def get_key_metadata(api_key: str) -> dict | None:
  redis_key = f"apikey:{api_key}"
  metadata = r.hgetall(redis_key)

  if not metadata:
    return None

  return{
    "tier" : metadata["tier"],
    "limit": int(metadata["limit"]),
    "window": int(metadata["window"]),
    "owner": metadata["owner"]
  }
  

def is_allowed(identifier:str, limit:int, window_seconds:int) -> dict:
  # identifier : the identifier(IP)
  now = time.time()
  window_start = now - window_seconds - 0.001

  pipe = r.pipeline()               # Mutiple redis commands to be executed as one

  # Deleting all requests outside the current range
  pipe.zremrangebyscore(identifier, "-inf", window_start)

  # Count of number of requests from the identifier
  pipe.zcard(identifier)

  # Add the current identifier and timestamp
  pipe.zadd(identifier, {str(now) : now})

  # Set the identifier to expire after the current window
  pipe.expire(identifier, window_seconds)

  # The oldest request in the curretn window
  pipe.zrange(identifier, 0, 0, withscores=True)

  results = pipe.execute()

  current_count = results[1]
  oldest = results[4]

  allowed = current_count < limit

  if oldest:
    oldest_timestap = oldest[0][1]
    reset_after = (oldest_timestap + window_seconds) - now
  else:
    reset_after = window_seconds
  
  return {
    "allowed":     allowed,
    "count":       current_count,
    "limit":       limit,
    "remaining":   max(0, limit - current_count - 1) if allowed else 0,
    "retry_after": round(reset_after) if not allowed else None,
    "reset_after": round(reset_after),
  }

  
