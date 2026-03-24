import redis
import time

r = redis.Redis("localhost", port=6379, decode_responses=True)

SLIDING_WINDOW_SCRIPT = """
local key          = KEYS[1]
local now          = tonumber(ARGV[1])
local window_start = tonumber(ARGV[2])
local window_secs  = tonumber(ARGV[3])

redis.call('ZREMRANGEBYSCORE', key, '-inf', window_start)

local count = redis.call('ZCARD', key)

redis.call('ZADD', key, now, tostring(now))

redis.call('EXPIRE', key, window_secs)

local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')

return {count, oldest}
"""

sliding_window = r.register_script(SLIDING_WINDOW_SCRIPT)

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
  window_start = now - window_seconds 

  results = sliding_window(
    keys=[identifier],
    args=[now, window_start, window_seconds]
  )

  current_count = results[0]
  oldest = results[1]

  allowed = current_count < limit

  if oldest:
    oldest_timestap = float(oldest[1])
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

  
