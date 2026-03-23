from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from limiter.sliding_window import is_allowed

app = FastAPI()

@app.middleware("http")

async def rate_linit_middleware(request : Request, call_net):
  client_ip = request.client.host
  key = f"ratelimit:{client_ip}"

  result = is_allowed(key, limit = 10, window_seconds = 60)

  if not result["allowed"]:
    return JSONResponse(
      status_code=429,
      content={"error": "Rate limit exceeded", "retry after": result["retry_after"]},
      headers={
        "Retry-After": str(result["retry_after"]),
        "X-RateLimit-Limit": str(result["limit"]),
        "X-RateLimit-Remaining": str(result["remaining"]),
      }
    )
  
  response = await call_net(request)
  response.headers["X-RateLimit-Limit"] = str(result["limit"])
  response.headers["X-RateLimit-Remaining"] = str(result["remaining"])

  return response


@app.get("/ping")
async def ping():
    return {"message": "pong"}