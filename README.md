# FastAPI ML Skeleton — Modernized

A production-ready FastAPI skeleton for serving machine learning models, modernized from [eightBEC/fastapi-ml-skeleton](https://github.com/eightBEC/fastapi-ml-skeleton) to follow current FastAPI best practices.

The original repo provides a clean starting point for serving ML models behind a REST API. This fork takes it through a **34-change, 7-layer modernization** — updating deprecated patterns, fixing bugs, and aligning every file with the FastAPI and Pydantic v2 documentation.

## Target Versions

| Dependency | Version |
|---|---|
| Python | 3.11+ |
| FastAPI | 0.109+ |
| Pydantic | 2.x |
| pydantic-settings | 2.x |
| scikit-learn | 1.8+ |

## What Changed — Summary Table

### Layer 1: Configuration

| Old Approach | New Approach | Why |
|---|---|---|
| `starlette.config.Config` for env vars | `pydantic-settings` `BaseSettings` with `SettingsConfigDict` | Type validation, `.env` support, JSON schema generation, maintained by Pydantic team |
| `starlette.datastructures.Secret` for API key | `pydantic.SecretStr` | Excluded from serialization/logs by default, `.get_secret_value()` makes unwrapping explicit |
| No validation on model path | `@field_validator` checks file exists at startup | Fail-fast instead of a cryptic error later when prediction is called |
| `tox.ini` referencing Python 3.6 | Deleted | EOL since 2021, contradicted `pyproject.toml`'s `python = "^3.11"` |
| `setup.cfg` with `source = app` | Deleted | Wrong package name, duplicated `pyproject.toml` config |

### Layer 2: Models / Schemas

| Old Approach | New Approach | Why |
|---|---|---|
| `HearbeatResult` (typo) | `HeartbeatResult` | Typo propagated to OpenAPI schema and generated clients |
| `average_rooms`, `average_bedrooms` typed as `int` | `float` | Averages are fractional — `int` silently truncates, corrupting ML input |
| `median_house_value: int` | `float` | ML model outputs floats; `int()` cast lost precision |
| `payload_to_list()` standalone function with manual field ordering | `to_list()` method using `model_dump().values()` | Fragile manual ordering breaks silently when fields change |
| Bare `List` return type | `list[float]` | Modern Python 3.11+ syntax, tells type checkers what's inside |
| No field constraints | `Field(gt=0, description="...")`, lat/lon with `ge`/`le` bounds | Catches nonsensical input at the API boundary, auto-generates OpenAPI docs |
| No schema examples | `model_config = ConfigDict(json_schema_extra={"examples": [...]})` | Populates Swagger UI "Try it out" with realistic values |

### Layer 3: Services

| Old Approach | New Approach | Why |
|---|---|---|
| `joblib.load()` with no error handling | `try/except` with `logger.error`, then re-raise | Corrupt model file now produces a clear error instead of an opaque traceback |
| `model.predict()` with no error handling | `try/except` with `logger.error`, then re-raise | Logs the actual sklearn error for debugging |
| `RESULT_UNIT_FACTOR = 100` (unexplained, wrong) | `RESULT_UNIT_FACTOR = 100_000` with documenting comment | California Housing target is in $100k units; `100` produced values 1000x too low |

### Layer 4: App Lifecycle & Middleware

| Old Approach | New Approach | Why |
|---|---|---|
| `add_event_handler("startup"/"shutdown")` | `@asynccontextmanager` lifespan function | `add_event_handler` is deprecated since Starlette 0.20+ / FastAPI 0.93+ |
| `event_handlers.py` with 4 wrapper functions | Deleted — 6 lines in lifespan | Entire file was boilerplate around two operations |
| No CORS middleware | `CORSMiddleware` added | Required for any browser-based client or cross-origin Swagger UI |
| No global exception handler | `@app.exception_handler(Exception)` returns structured JSON | Prevents traceback leaks, ensures consistent error format |

### Layer 5: Routes / Endpoints

| Old Approach | New Approach | Why |
|---|---|---|
| `get_hearbeat` (typo) | `get_heartbeat` | Typo in function name |
| `request.app.state.model` (untyped, no null check) | `Depends(get_model)` with type check and 503 response | Centralized retrieval, type safety, clear error when model isn't loaded |
| No error handling in prediction route | `try/except` returning 500 with structured error | Prevents raw tracebacks leaking to clients |
| Heartbeat always returns `is_alive: True` | Checks `app.state.model is not None`, returns 503 if not loaded | Load balancers can distinguish "app is up" from "app is ready" |
| No response examples on routes | `responses={200: {...}, 503: {...}}` in decorators | Self-documenting API in Swagger UI |

### Layer 6: Security

| Old Approach | New Approach | Why |
|---|---|---|
| `headers={}` in HTTPException | Removed | Empty dict was a no-op |
| Header name `"token"` | `"X-API-Key"` | Standard convention; `"token"` is ambiguous |
| `Optional[str]` parameter type | `str \| None` | Modern Python 3.11+ union syntax |
| Returns `bool` (never used) | Returns `None` | Guard dependency — it either raises or passes, return value was meaningless |

### Layer 7: Tests

| Old Approach | New Approach | Why |
|---|---|---|
| `starlette.config.environ` for test env vars | `os.environ.setdefault()` | No dependency on Starlette internals; `setdefault` won't override shell env |
| Header `"token"` in test requests | `"X-API-Key"` via shared `auth_headers` fixture | Matches Layer 6 rename; single place to update |
| Assertions check field existence only | Check types, values, and ranges | `"median_house_value" in response` doesn't catch wrong types or garbage values |
| No edge case tests | 12 parametrized tests: negative values, out-of-range lat/lon, missing fields | Validates that `Field()` constraints work end-to-end |
| Sample model from scikit-learn 0.22.1 | Retrained with scikit-learn 1.8.0 | Old pickle format incompatible with current sklearn |

## Project Structure

```
fastapi_skeleton/
    api/
        routes/
            heartbeat.py      # GET /api/health/heartbeat
            prediction.py      # POST /api/model/predict
            router.py          # Aggregates all routers
    core/
        config.py              # BaseSettings, env var loading
        messages.py            # Error message constants
        security.py            # API key auth via X-API-Key header
    models/
        heartbeat.py           # HeartbeatResult schema
        payload.py             # HousePredictionPayload schema
        prediction.py          # HousePredictionResult schema
    services/
        models.py              # ML model loading, pre/post-processing, prediction
    main.py                    # App factory, lifespan, middleware, exception handler
tests/
    conftest.py                # Fixtures: test client, auth headers
    test_api/
        test_api_auth.py       # Auth rejection tests
        test_heartbeat.py      # Health check tests
        test_prediction.py     # Prediction endpoint + edge cases
    test_service/
        test_models.py         # Direct model service tests
```

## Quick Start

```bash
# Install dependencies
poetry install

# Create .env from example
cp .env.example .env
# Edit .env — set API_KEY to any secret string

# Run the server
uvicorn fastapi_skeleton.main:app

# Open interactive docs
open http://localhost:8000/docs
```

Authenticate in Swagger UI by clicking **Authorize** and entering your `API_KEY` in the `X-API-Key` header field.

## Run Tests

```bash
pytest
```

19 tests, including parametrized edge cases for input validation.

## What You Can Learn From This Repo

This repo is a **before/after study** in modernizing a FastAPI application. Each layer was updated independently, bottom-up, so you can trace the reasoning behind every change. Specifically:

- **pydantic-settings for configuration** — how `BaseSettings` replaces manual env var loading with type validation, `.env` file support, and `SecretStr` for secrets
- **Pydantic v2 model patterns** — `Field()` constraints, `model_config` with `ConfigDict`, `json_schema_extra` for OpenAPI examples, `model_dump()` for serialization
- **Lifespan context manager** — the modern replacement for deprecated `add_event_handler("startup"/"shutdown")`
- **Dependency injection with `Depends()`** — typed model retrieval instead of untyped `request.app.state` access
- **CORSMiddleware and global exception handling** — production essentials that skeleton apps often skip
- **API key security** — `APIKeyHeader` with timing-safe comparison via `secrets.compare_digest`
- **Layered architecture** — clean separation between config, schemas, services, routes, and security
- **Testing FastAPI apps** — `TestClient`, fixtures, parametrized edge cases, and testing validation constraints end-to-end

The full audit documents with old-vs-new comparisons are in [`docs/modernization/`](./docs/modernization/).

## Original Project

Based on [eightBEC/fastapi-ml-skeleton](https://github.com/eightBEC/fastapi-ml-skeleton) by [eightBEC](https://github.com/eightBEC). Licensed under Apache License 2.0.

## Changelog

### v2.0.0 — Modernization (34 changes across 7 layers)

- Migrated configuration from `starlette.config.Config` to `pydantic-settings` `BaseSettings`
- Fixed all Pydantic schemas: correct types, field constraints, OpenAPI examples
- Added error handling in model loading and prediction pipeline
- Replaced deprecated `add_event_handler` with lifespan context manager
- Added CORSMiddleware and global exception handler
- Replaced untyped `app.state` access with typed `Depends()` dependencies
- Modernized security: `X-API-Key` header, removed redundant code
- Rewrote tests with stronger assertions and edge case coverage
- Retrained sample model for scikit-learn 1.8+ compatibility
- Deleted `tox.ini`, `setup.cfg`, `event_handlers.py`

### v1.1.0 — Update to Python 3.11, FastAPI 0.108.0

- Updated to Python 3.11
- Added linting script
- Updated to Pydantic 2.x
- Added Poetry as package manager

### v1.0.0 — Initial release

- Base functionality for using FastAPI to serve ML models
- Full test coverage
