from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from limiter.sliding_window import is_allowed, get_key_metadata

app = FastAPI()

# Puclic IP based connection limit and window
PUBLIC_LIMIT = 6
PUBLIC_WINDOW = 60

EXEMPT_PATHS = {'/ping'}

@app.middleware("http")

async def rate_limit_middleware(request : Request, call_next):
  #Rate limit exception paths
  if request.url.path in EXEMPT_PATHS:
    return await call_next(request)
  
  #Normal Working for rate limited Endpoints
  api_key = request.headers.get("X-API-Key")

  if api_key:
    metadata = get_key_metadata(api_key)

    if not metadata:
       return JSONResponse(
          status_code=401,
          content={"error":"Invalid API Key"}
       )
    
    identifier = f"ratelimit:apikey:{api_key}"
    limit = metadata["limit"]
    window = metadata["window"]

  else:
    # IP BASED REQUESTS  
    client_ip = request.client.host
    identifier = f"ratelimit:ip:{client_ip}"
    limit = PUBLIC_LIMIT
    window = PUBLIC_WINDOW

  result = is_allowed(identifier, limit = limit, window_seconds = window)

  # Headers are added in both success and failure
  rl_headers = {
      "X-RateLimit-Limit":     str(result["limit"]),
      "X-RateLimit-Remaining": str(result["remaining"]),
      "X-RateLimit-Reset":     str(result["reset_after"]),
  }

  if not result["allowed"]:
      return JSONResponse(
          status_code=429,
          content={
              "error":       "Rate limit exceeded",
              "retry_after": result["retry_after"],
          },
          headers={
              **rl_headers,
              "Retry-After": str(result["retry_after"]),
          },
      )
  
  response = await call_next(request)

  for key, value in rl_headers.items():
    response.headers[key] = value
  
  return response


@app.get("/ping")
async def ping():
  # This route is not protected  
    return {"message": "pong"}

@app.get("/data")
async def data():
    # This route is protected — middleware handles auth/limiting
    return {"message": "here is your data"}