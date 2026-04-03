# Phase 1: Anatomy of `fastapi-ml-skeleton`

## Project Architecture (the "Skeleton Map")

```
fastapi_skeleton/
  main.py                    # App factory - creates & wires everything
  core/
    config.py                # Env-based settings (API key, model path, debug)
    event_handlers.py        # Startup/shutdown: load & unload the ML model
    security.py              # API key auth via dependency injection
    messages.py              # Reusable error message constants
  api/
    routes/
      router.py              # Central router - glues sub-routers together
      prediction.py          # POST /predict endpoint
      heartbeat.py           # GET /heartbeat health check
  models/                    # Pydantic schemas (NOT ML models!)
    payload.py               # Request body schema + conversion helper
    prediction.py            # Response schema
    heartbeat.py             # Health check response schema
  services/
    models.py                # ML model wrapper class (load, preprocess, predict, postprocess)
```

---

## Concept-by-Concept Mapping

### 1. Path Operations - IMPLEMENTED
**File:** `api/routes/prediction.py` line 12

```python
@router.post("/predict", response_model=HousePredictionResult, name="predict")
def post_predict(request: Request, block_data: HousePredictionPayload, ...):
```

**What they did right:** Used `POST` for inference (not GET). Tagged routes for Swagger grouping.
**What's missing:** No versioning (e.g., `/v1/predict`). Single endpoint only.


### 2. Pydantic Models - IMPLEMENTED (basic)
**File:** `models/payload.py` lines 6-15

```python
class HousePredictionPayload(BaseModel):
    median_income_in_block: float
    median_house_age_in_block: int
    average_rooms: int
    ...
```

**What they did right:** Clean separation of request/response schemas.
**What's MISSING (your golden rule!):** No `Field()` validators! No `ge=0`, `le=1`, no ranges.
A user could send `average_rooms: -999` and it would hit the model. This is the "bodyguard" gap.

**How to fix it:**
```python
from pydantic import BaseModel, Field

class HousePredictionPayload(BaseModel):
    median_income_in_block: float = Field(..., ge=0, description="Median income in $10k")
    median_house_age_in_block: int = Field(..., ge=1, le=100)
    average_rooms: int = Field(..., ge=1, le=50)
    average_bedrooms: int = Field(..., ge=1, le=30)
    population_per_block: int = Field(..., ge=1)
    average_house_occupancy: int = Field(..., ge=1)
    block_latitude: float = Field(..., ge=32.0, le=42.0)   # California bounds
    block_longitude: float = Field(..., ge=-125.0, le=-114.0)
```


### 3. Response Models - IMPLEMENTED
**File:** `models/prediction.py`

```python
class HousePredictionResult(BaseModel):
    median_house_value: int
    currency: str = "USD"
```

**What they did right:** Typed response with a default for currency.
**What's MISSING (your golden rule!):** No metadata! No latency, version, model_name, timestamp.

**How to fix it:**
```python
class HousePredictionResult(BaseModel):
    median_house_value: int
    currency: str = "USD"
    model_version: str = "1.0.0"
    latency_ms: float          # time taken for inference
    timestamp: datetime        # when prediction was made
```


### 4. Async / Await - NOT IMPLEMENTED
**File:** `api/routes/prediction.py` line 13

```python
def post_predict(...)   # <-- sync def, not async def
```

**This is actually CORRECT for ML!** Your golden rule says: use `def` (not `async def`) for ML inference because heavy CPU math (numpy, sklearn, PyTorch) blocks the event loop and freezes the server.

FastAPI automatically runs sync `def` routes in a threadpool, so this IS the right pattern for CPU-bound model inference.

**Key insight:** `async def` is for I/O-bound work (database queries, external API calls). For ML prediction with numpy/sklearn/PyTorch, sync `def` lets FastAPI offload it to a thread.


### 5. File Uploads - NOT IMPLEMENTED
No `UploadFile` anywhere. This project only handles JSON payloads.

**What we'll add in Phase 2:** Image upload endpoint for a CV model using `UploadFile` to stream binary data without loading it all into RAM.


### 6. Background Tasks - NOT IMPLEMENTED
No `BackgroundTasks` usage anywhere.

**What we'll add in Phase 2:** Log predictions to a file/database AFTER returning the response, keeping the API fast. Also metrics collection.


### 7. Dependency Injection - IMPLEMENTED (for auth only)
**File:** `core/security.py` + `api/routes/prediction.py` line 16

```python
# security.py - the dependency
def validate_request(header: Optional[str] = Security(api_key)) -> bool:
    if header is None:
        raise HTTPException(status_code=400, detail=NO_API_KEY)
    if not secrets.compare_digest(header, str(config.API_KEY)):
        raise HTTPException(status_code=401, detail=AUTH_REQ)
    return True

# prediction.py - injecting it
def post_predict(..., _: bool = Depends(security.validate_request)):
```

**What they did right:** Clean auth as a reusable dependency.
**What's MISSING:** Model is accessed via `request.app.state.model` (line 18 of prediction.py) instead of being injected with `Depends()`. This works but isn't the proper DI pattern.

**How to fix it (proper DI for model):**
```python
def get_model(request: Request) -> HousePriceModel:
    return request.app.state.model

@router.post("/predict")
def post_predict(
    block_data: HousePredictionPayload,
    model: HousePriceModel = Depends(get_model),
    _: bool = Depends(security.validate_request),
) -> HousePredictionResult:
    return model.predict(block_data)
```


### 8. Lifespan Events - IMPLEMENTED (old style)
**File:** `core/event_handlers.py`

```python
def _startup_model(app: FastAPI) -> None:
    model_instance = HousePriceModel(model_path)
    app.state.model = model_instance

def _shutdown_model(app: FastAPI) -> None:
    app.state.model = None
```

**File:** `main.py` lines 12-13

```python
fast_app.add_event_handler("startup", start_app_handler(fast_app))
fast_app.add_event_handler("shutdown", stop_app_handler(fast_app))
```

**What they did right:** Model loads once at startup, not per request. Cleanup on shutdown.
**What's OUTDATED:** This uses the old `add_event_handler` API. Modern FastAPI uses `@asynccontextmanager` lifespan.

**Modern approach:**
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP: load model
    app.state.model = HousePriceModel(model_path)
    yield
    # SHUTDOWN: cleanup GPU memory, close connections
    app.state.model = None

app = FastAPI(lifespan=lifespan)
```


### 9. Error Handling - PARTIAL
**File:** `core/security.py` - HTTPException for auth errors.
**File:** `core/messages.py` - Constants for error messages.

**What's MISSING:**
- No global exception handler for unexpected errors
- No 503 "model not ready" response
- No custom error format (just bare HTTPException)
- No validation error customization

**What we'll add in Phase 2:**
```python
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(status_code=500, content={"error": "Internal server error", "detail": str(exc)})

# Model readiness check
if app.state.model is None:
    raise HTTPException(status_code=503, detail="Model not loaded yet")
```


### 10. Health Checks - PARTIAL
**File:** `api/routes/heartbeat.py`

```python
@router.get("/heartbeat", response_model=HearbeatResult)
def get_hearbeat() -> HearbeatResult:
    return HearbeatResult(is_alive=True)
```

**What's MISSING (your golden rule!):** No distinction between `/health` (alive) and `/ready` (model loaded). This endpoint always returns `True` even if the model failed to load!

**How to fix it:**
```python
@router.get("/health")     # Is the server running?
def health(): return {"status": "alive"}

@router.get("/ready")      # Is the model loaded and ready for inference?
def ready(request: Request):
    model = request.app.state.model
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {"status": "ready", "model": model.path}
```

---

## Concept Coverage Scorecard

| # | Concept              | Covered? | Quality |
|---|----------------------|----------|---------|
| 1 | Path Operations      | Yes      | Good (POST for inference)       |
| 2 | Pydantic Models      | Yes      | Weak (no Field validators)      |
| 3 | Response Models      | Yes      | Weak (no metadata)              |
| 4 | Async/Await          | Yes*     | Correct (sync for CPU-bound)    |
| 5 | File Uploads         | No       | -                               |
| 6 | Background Tasks     | No       | -                               |
| 7 | Dependency Injection | Partial  | Auth only, model via app.state  |
| 8 | Lifespan Events      | Yes      | Outdated API                    |
| 9 | Error Handling       | Partial  | Auth only, no global handler    |
| 10| Health Checks        | Partial  | No /health vs /ready split      |

**Score: 5.5 / 10 concepts fully covered**

---

## Key Architectural Patterns Worth Keeping

1. **App Factory (`get_app()`)** - Testable. Tests can create fresh app instances.
2. **Service Layer** (`services/models.py`) - ML logic is separated from API routes. The route doesn't know about numpy.
3. **Schema Layer** (`models/`) - Request/response schemas live separately from business logic.
4. **Config from Environment** - No hardcoded secrets. `.env` file + environment variables.
5. **Router Composition** - Sub-routers composed into a main router with prefixes and tags.

---

## What We'll Fix & Add in Phase 2

We will build our own multi-model API that:
- Fixes all the gaps above (Field validators, metadata, modern lifespan, etc.)
- Adds 3 model types: sklearn regression, text sentiment, image classification
- Implements ALL 12 concepts at production quality
- Includes proper tests
