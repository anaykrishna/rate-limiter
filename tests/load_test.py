import httpx
import time

BASE_URL = "http://localhost:8000"

def print_result(req_num: int, response: httpx.Response):
  status = response.status_code
  headers = response.headers
  icon = "✅" if status == 200 else "🚫"

  remaining = headers.get("x-ratelimit-remaining", "?")
  reset     = headers.get("x-ratelimit-reset", "?")
  retry     = headers.get("retry-after", None)

  line = f"  Req {req_num:>2} → {status} {icon}  remaining: {remaining}  reset: {reset}s"
  if retry:
      line += f"  retry-after: {retry}s"

  print(line)

def run_scenario(label:str, n:int, headers: dict = {}):
  print(f"\n{'─'*55}")
  print(f" {label}")
  print(f"{'─'*55}")

  with httpx.Client() as client:
    for i in range(1, n+1):
      response = client.get(f"{BASE_URL}/data", headers = headers)
      print_result(i, response)
      time.sleep(0.3)   #slight change in the new header timestamps
    
if __name__ == "__main__":
  # Scenario 1: Anonymous IP hits the free limit (10 req/60s)
  run_scenario("Anonymous IP — limit: 10/min", n=13)

  # Small pause so the next scenario feels distinct
  time.sleep(1)

  # Scenario 2: Free tier API key
  run_scenario(
      "Free tier API key (alice) — limit: 10/min",
      n=13,
      headers={"X-API-Key": "free-key-abc123"}
  )

  time.sleep(1)

  # Scenario 3: Pro tier API key — should never 429
  run_scenario(
      "Pro tier API key (bob) — limit: 100/min",
      n=15,
      headers={"X-API-Key": "pro-key-xyz789"}
  )

  time.sleep(1)

  # Scenario 4: Invalid API key
  run_scenario(
      "Invalid API key — should get 401",
      n=3,
      headers={"X-API-Key": "fake-key-000"}
  )