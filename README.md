# Rate Limiter

A production-style **sliding window rate limiter** built with Python, FastAPI, and Redis.

Implements the same algorithm used by Stripe, GitHub, and Cloudflare — with per-IP and per-API-key limiting, tiered rate limits, and standard HTTP rate limit headers.

## How it works

Instead of counting requests in fixed time buckets (which allows burst abuse at bucket boundaries), the sliding window tracks every request timestamp in a Redis sorted set. At any moment, only requests within the last N seconds are counted — the window travels with time.
```
Redis Sorted Set: "ratelimit:apikey:pro-key-xyz789"

Score (timestamp)   →   Request ID
1711180800.001      →   req_abc
1711180801.200      →   req_def   ← window start (now - 60s)
...
1711180860.000      →   req_xyz   ← now

Count entries between window_start and now.
If count ≥ limit → 429. Else → allow and add entry.
```

## Features

- **Sliding window algorithm** backed by Redis sorted sets
- **Per-IP limiting** for anonymous requests
- **Per-API-key limiting** with tiered limits (free / pro / enterprise)
- **Standard HTTP headers** on every response:
  - `X-RateLimit-Limit` — total requests allowed in window
  - `X-RateLimit-Remaining` — requests left in current window
  - `X-RateLimit-Reset` — seconds until window resets
  - `Retry-After` — seconds to wait before retrying (429 only)
- **401 vs 429** — correctly distinguishes invalid keys from exhausted limits
- **Exempt paths** — `/ping` bypass rate limiting

## API Key Tiers

| Tier       | Limit       |
|------------|-------------|
| Anonymous  | 6 req/min   |
| Free       | 10 req/min  |
| Pro        | 100 req/min |
| Enterprise | 1000 req/min|

## Project Structure
```
rate-limiter/
├── app/
│   └── main.py              # FastAPI app + middleware
├── limiter/
│   └── sliding_window.py    # Core algorithm
├── seed_keys.py             # Populate Redis with API keys
├── load_test.py             # Demo script
├── docker-compose.yml       # Redis via Docker
└── requirements.txt
```

## Quick Start

**1. Start Redis**
```bash
docker compose up -d
```

**2. Install dependencies**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**3. Seed API keys**
```bash
python3 seed_keys.py
```

**4. Run the server**
```bash
uvicorn app.main:app --reload
```

**5. Test it**
```bash
# Anonymous IP (limit: 10/min)
curl -i http://localhost:8000/data

# Pro API key (limit: 100/min)
curl -i http://localhost:8000/data -H "X-API-Key: pro-key-xyz789"

# Invalid key
curl -i http://localhost:8000/data -H "X-API-Key: fake-key-000"
```

**6. Run the load test**
```bash
python3 load_test.py
```

## Load Test Output
```
───────────────────────────────────────────────────────
 Free tier API key (alice) — limit: 10/min
───────────────────────────────────────────────────────
  Req  1 → 200 ✅  remaining: 9   reset: 60s
  ...
  Req 10 → 200 ✅  remaining: 0   reset: 57s
  Req 11 → 429 🚫  remaining: 0   reset: 57s  retry-after: 57s
```

## Tech Stack

- **FastAPI** — middleware intercepts every request before it hits a route
- **Redis** — sorted sets for O(log n) timestamp range queries; hashes for key metadata
- **Python** — `redis-py` pipeline batches 5 Redis commands into a single round trip