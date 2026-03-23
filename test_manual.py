from limiter.sliding_window import is_allowed

for i in range(7):
    result = is_allowed(key="test_user", limit=5, window_seconds=10)
    status = "ALLOWED" if result["allowed"] else "BLOCKED"
    print(f"Request {i+1}: {status} | count={result['count']} | remaining={result['remaining']}")