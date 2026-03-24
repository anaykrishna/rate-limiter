import redis

r = redis.Redis("localhost", port=6379, decode_responses=True)

TIERS = {
  "free": {"limit": 10, "window" : 60},
  "pro" : {"limit": 100, "window" : 60},
  "enterprise" : {"limit": 1000, "window" : 60}
}

API_KEYS = [
  {"key": "free-key-abc123",  "tier": "free",       "owner": "alice"},
  {"key": "pro-key-xyz789",   "tier": "pro",         "owner": "bob"},
  {"key": "ent-key-god999",   "tier": "enterprise",  "owner": "corp"}
]

for entry in API_KEYS:
  tier_config = TIERS[entry["tier"]]
  redis_key = f"apikey:{entry['key']}"

  r.hset(redis_key, mapping = {
    "tier" : entry["tier"],
    "limit" : tier_config["limit"],
    "window" : tier_config["window"],
    "owner" : entry["owner"]
  })

  print(f"Seeded {redis_key} → tier={entry['tier']}, limit={tier_config['limit']}")

print("\nDone. Verify with: redis-cli hgetall apikey:free-key-abc123")