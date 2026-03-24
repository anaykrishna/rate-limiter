from limiter.sliding_window import get_key_metadata, is_allowed

# Test 1: valid key lookup
meta = get_key_metadata("pro-key-xyz789")
print("Metadata:", meta)

# Test 2: invalid key
bad = get_key_metadata("fake-key-000")
print("Invalid key:", bad)

# Test 3: rate limit using pro key's config
if meta:
    result = is_allowed(
        identifier=f"ratelimit:apikey:pro-key-xyz789",
        limit=meta["limit"],
        window_seconds=meta["window"]
    )
    print("Rate limit result:", result)