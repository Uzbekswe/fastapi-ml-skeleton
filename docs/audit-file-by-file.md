# FastAPI-ML-Skeleton — File-by-File Audit

## Context
Audit of the `fastapi-ml-skeleton` repo for outdated patterns, deprecated functions, and suboptimal approaches across all files. No code changes — findings only.

---

## File-by-File Audit

---

### 1. `fastapi_skeleton/core/config.py`

**Role:** Loads environment variables (API_KEY, IS_DEBUG, DEFAULT_MODEL_PATH) using Starlette's Config class.

| # | Issue | Modern Alternative | Priority |
|---|-------|--------------------|----------|
| 1 | Uses `starlette.config.Config` — this is a thin, unvalidated loader with no schema, no docs generation, and no nested config support | Use **`pydantic-settings` BaseSettings** (v2). It validates types, generates JSON schema, supports `.env`, env prefixes, nested models, and `SecretStr` natively | **Critical** — Starlette Config is effectively unmaintained and not recommended by FastAPI docs |
| 2 | Uses `starlette.datastructures.Secret` for API_KEY | Use **`pydantic.SecretStr`** — integrates with BaseSettings, has `.get_secret_value()`, and is excluded from serialization/logs by default | **Important** |
| 3 | No validation that `DEFAULT_MODEL_PATH` exists or is readable | BaseSettings + `@field_validator` can validate path existence at startup | **Important** |

---

### 2. `fastapi_skeleton/core/event_handlers.py`

**Role:** Provides startup/shutdown lifecycle hooks. Loads the ML model into `app.state` on startup, clears it on shutdown.

| # | Issue | Modern Alternative | Priority |
|---|-------|--------------------|----------|
| 1 | Uses `app.add_event_handler("startup", ...)` / `"shutdown"` — string-based, deprecated since FastAPI 0.93+ | Use the **lifespan context manager** (`async def lifespan(app)` with `async with` / `yield`) introduced in FastAPI 0.93 | **Critical** — `add_event_handler` is deprecated in Starlette and will be removed |
| 2 | Stores model on `app.state` (untyped dynamic attribute) | Use a **typed dependency** via lifespan + `Depends()`, or a typed state class | **Important** |
| 3 | No error handling — if `joblib.load()` fails, app starts in a broken state | Wrap in try/except, log the error, and either fail-fast or set a health flag | **Important** |
| 4 | Shutdown sets `app.state.model = None` but doesn't release resources | In the lifespan pattern, cleanup happens naturally after `yield` | **Nice-to-have** |

---

### 3. `fastapi_skeleton/core/security.py`

**Role:** API key authentication via `APIKeyHeader` dependency. Uses timing-safe comparison (good).

| # | Issue | Modern Alternative | Priority |
|---|-------|--------------------|----------|
| 1 | Header name is `"token"` — non-standard | Use `"X-API-Key"` or `"Authorization"` with Bearer scheme | **Nice-to-have** |
| 2 | `headers={}` passed to HTTPException — redundant, does nothing | Remove the `headers` kwarg | **Nice-to-have** |
| 3 | `str(config.API_KEY)` converts Secret back to plain string, undermining the Secret type | With Pydantic `SecretStr`, use `.get_secret_value()` — makes the intentional unwrapping explicit | **Nice-to-have** |
| 4 | Returns `bool` but the return value is never used by any route (assigned to `_`) | Change return type to `None` or use it as a proper dependency that returns user/scope info | **Nice-to-have** |

---

### 4. `fastapi_skeleton/main.py`

**Role:** App factory. Creates FastAPI instance, includes routers, registers event handlers.

| # | Issue | Modern Alternative | Priority |
|---|-------|--------------------|----------|
| 1 | Uses `add_event_handler("startup"/shutdown")` — see event_handlers above | Use **lifespan context manager** | **Critical** |
| 2 | No CORS middleware configured | Add `CORSMiddleware` — required for any browser-facing usage | **Important** |
| 3 | No global exception handler | Add `@app.exception_handler(Exception)` or custom middleware for structured error responses | **Important** |
| 4 | `app = get_app()` at module level — prevents using Gunicorn's `--factory` flag | Expose the factory and let the ASGI server call it | **Nice-to-have** |

---

### 5. `fastapi_skeleton/api/routes/heartbeat.py`

**Role:** Health check endpoint at `/api/health/heartbeat`.

| # | Issue | Modern Alternative | Priority |
|---|-------|--------------------|----------|
| 1 | **Typo**: class `HearbeatResult` and function `get_hearbeat` — missing the "t" in "Heart" | Rename to `HeartbeatResult` / `get_heartbeat` | **Important** |
| 2 | No model readiness check — returns healthy even if model failed to load | Add a readiness probe that checks `app.state.model is not None` | **Important** |

---

### 6. `fastapi_skeleton/api/routes/prediction.py`

**Role:** POST endpoint for house price prediction. Secured with API key dependency.

| # | Issue | Modern Alternative | Priority |
|---|-------|--------------------|----------|
| 1 | Accesses `request.app.state.model` — untyped, no null check | Use a proper **`Depends()` function** that retrieves and type-checks the model, raising 503 if unavailable | **Important** |
| 2 | No error handling around `model.predict()` | Wrap in try/except, return 500 with structured error | **Important** |
| 3 | No response examples in route decorator | Add `responses={200: {"example": {...}}}` or use Pydantic `model_config` with `json_schema_extra` for auto-docs | **Nice-to-have** |

---

### 7. `fastapi_skeleton/models/payload.py`

**Role:** Pydantic model for prediction request body. Includes `payload_to_list()` helper.

| # | Issue | Modern Alternative | Priority |
|---|-------|--------------------|----------|
| 1 | `average_rooms` and `average_bedrooms` typed as `int` — averages should be `float` | Change to `float` | **Important** |
| 2 | `payload_to_list()` is a standalone function with manual field ordering — fragile and error-prone | Use `model.model_dump().values()` or define field order via method on the model | **Important** |
| 3 | Return type is bare `List` instead of `List[float]` | Use `list[float]` (Python 3.11+) | **Nice-to-have** |
| 4 | No `Field()` constraints (min/max/description) on any field | Add `Field(gt=0, description="...")` for validation and OpenAPI docs | **Nice-to-have** |

---

### 8. `fastapi_skeleton/models/prediction.py`

**Role:** Pydantic model for prediction response.

| # | Issue | Modern Alternative | Priority |
|---|-------|--------------------|----------|
| 1 | `median_house_value: int` — predictions are floats, casting to int loses precision | Use `float` | **Important** |
| 2 | No field descriptions or examples | Add `Field(description="...", examples=[...])` | **Nice-to-have** |

---

### 9. `fastapi_skeleton/models/heartbeat.py`

**Role:** Response model for health check.

| # | Issue | Modern Alternative | Priority |
|---|-------|--------------------|----------|
| 1 | **Typo**: `HearbeatResult` — missing "t" | Rename to `HeartbeatResult` | **Important** |

---

### 10. `fastapi_skeleton/services/models.py`

**Role:** ML model service — loads joblib model, runs pre/post-processing, prediction pipeline.

| # | Issue | Modern Alternative | Priority |
|---|-------|--------------------|----------|
| 1 | `joblib.load()` in `__init__` with no error handling | Wrap in try/except; fail with clear error message | **Critical** |
| 2 | `model.predict()` with no error handling | Catch sklearn exceptions, return structured error | **Important** |
| 3 | `RESULT_UNIT_FACTOR = 100` is an unexplained magic number | Document it or make it configurable | **Nice-to-have** |
| 4 | `_pre_process` uses `payload_to_list()` + `np.asarray().reshape(1, -1)` — fragile pipeline | Use `model_dump().values()` or pandas DataFrame | **Important** |

---

### 11. `tests/conftest.py`

**Role:** Pytest fixtures. Sets env vars and creates test client.

| # | Issue | Modern Alternative | Priority |
|---|-------|--------------------|----------|
| 1 | Directly mutates `os.environ` at module level — pollutes process env, breaks test isolation | Use `monkeypatch.setenv()` or `@pytest.fixture(autouse=True)` with env cleanup | **Important** |
| 2 | Hardcoded UUID as test API key at module level | Use `monkeypatch` inside fixture scope | **Nice-to-have** |

---

### 12. `tests/test_api/test_prediction.py`

**Role:** Tests prediction endpoint.

| # | Issue | Modern Alternative | Priority |
|---|-------|--------------------|----------|
| 1 | Only asserts field existence, not value correctness | Assert value ranges or expected output for known input | **Important** |
| 2 | No edge case tests (negative values, NaN, missing fields) | Add parametrized tests | **Nice-to-have** |

---

### 13. `pyproject.toml` / `tox.ini` / `setup.cfg`

**Role:** Build config, dependencies, linting, testing config.

| # | Issue | Modern Alternative | Priority |
|---|-------|--------------------|----------|
| 1 | `tox.ini` references `py36` — Python 3.6 has been EOL since Dec 2021 | Remove tox.ini or update to `py311` | **Critical** |
| 2 | `setup.cfg` has `[coverage:run] source = app` — package is `fastapi_skeleton` | Fix or remove setup.cfg | **Important** |
| 3 | Three config files with overlapping/conflicting settings | Consolidate everything into `pyproject.toml` | **Important** |
| 4 | Dependency versions are ~1.5 years old | Update to latest stable versions | **Nice-to-have** |

---

## Priority Summary

### Critical (5 issues)
1. `add_event_handler("startup"/"shutdown")` — deprecated, use lifespan context manager
2. `starlette.config.Config` — use pydantic-settings BaseSettings
3. `tox.ini` references py36 — contradicts pyproject.toml's Python 3.11+ requirement
4. No error handling in model loading — app starts broken if model file is missing

### Important (17 issues)
5-21. See individual file sections above.

### Nice-to-have (12 issues)
22-34. See individual file sections above.
