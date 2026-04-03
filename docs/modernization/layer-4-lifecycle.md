# Layer 4: App Lifecycle & Middleware — Modernization Plan

**Files:** `core/event_handlers.py` (deleted), `main.py`
**Depends on:** Layer 3 (Services)
**Depended on by:** Layer 5 (Routes)

---

## Change 1: Replace `add_event_handler()` with lifespan context manager

**Priority:** Critical

**Why:** `add_event_handler("startup"/"shutdown")` is deprecated since Starlette 0.20+ / FastAPI 0.93+. The lifespan context manager is the official replacement — it's clearer (startup before `yield`, shutdown after) and supports shared state between startup and shutdown.

**Old (`main.py`):**
```python
fast_app.add_event_handler("startup", start_app_handler(fast_app))
fast_app.add_event_handler("shutdown", stop_app_handler(fast_app))
```

**New:**
```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Running app start handler.")
    model_instance = HousePriceModel(settings.DEFAULT_MODEL_PATH)
    app.state.model = model_instance
    yield
    logger.info("Running app shutdown handler.")
    app.state.model = None

def get_app() -> FastAPI:
    fast_app = FastAPI(..., lifespan=lifespan)
```

---

## Change 2: Delete `event_handlers.py`

**Priority:** Critical

**Why:** All its logic (startup_model, shutdown_model, handler factories) now lives in the `lifespan` function in `main.py`. The file is dead code.

---

## Change 3: Add `CORSMiddleware`

**Priority:** Important

**Why:** Without CORS headers, any browser-based client (React dashboard, Swagger UI on a different origin) gets blocked by the browser. This is required for any frontend integration.

**New:**
```python
fast_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Change 4: Add global exception handler

**Priority:** Important

**Why:** Without a catch-all handler, unhandled exceptions return raw tracebacks to the client (information leak) and produce inconsistent error formats. The global handler returns a structured JSON `{"detail": "Internal server error"}` and logs the actual exception.

**New:**
```python
@fast_app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
```

---

## Change 5: Make `get_app()` compatible with `gunicorn --factory`

**Priority:** Nice-to-have

**Why:** `app = get_app()` at module level still works. Gunicorn's `--factory` flag calls the factory function directly. Both patterns are supported — the module-level `app` lets `uvicorn fastapi_skeleton.main:app` work, and the factory lets `gunicorn -k uvicorn.workers.UvicornWorker fastapi_skeleton.main:get_app --factory` work.

No code change needed — already compatible by having both `get_app()` and `app = get_app()`.
