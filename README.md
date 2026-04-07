# FastAPI ML Skeleton — Modernized

> **Learning & Practice Project** — This repo exists for hands-on learning. Every file was written or rewritten deliberately, with the goal of understanding *why* each pattern exists, not just copying boilerplate. If you're studying FastAPI, Docker, or ML serving, you're in the right place.

A production-ready FastAPI skeleton for serving machine learning models, built in two phases:

- **FastAPI layer** — modernized from [eightBEC/fastapi-ml-skeleton](https://github.com/eightBEC/fastapi-ml-skeleton) through a 34-change, 7-layer audit. Every deprecated pattern, wrong type, and missing error handler was identified and fixed.
- **Docker layer** — implemented from scratch. The `Dockerfile`, `docker-compose.yml`, and `.dockerignore` were written line-by-line with inline comments explaining every decision: multi-stage builds, layer caching, non-root users, health checks, secret injection, and resource limits.

The goal is a repo you can clone, run, and learn from — not just a template to copy-paste.

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

### Option A — Docker (recommended, no Python setup needed)

**Prerequisites:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

```bash
# 1. Clone the repo
git clone https://github.com/Uzbekswe/fastapi-ml-skeleton.git
cd fastapi-ml-skeleton

# 2. Build the image and start the container
docker compose up --build

# 3. Open Swagger UI in your browser
open http://localhost:8000/docs
```

That's it. Docker handles Python, dependencies, and the model — nothing to install locally.

To run in the background:

```bash
docker compose up -d --build

# View logs
docker compose logs -f

# Stop the container
docker compose down
```

**Authenticate in Swagger UI:** click **Authorize** → enter `change-me-in-production` in the `X-API-Key` field (the default from `docker-compose.yml`).

To use your own key, set it before running:

```bash
API_KEY=my-secret-key docker compose up --build
```

---

### Option B — Local (Poetry)

**Prerequisites:** Python 3.11+, [Poetry](https://python-poetry.org/docs/#installation).

```bash
# 1. Clone the repo
git clone https://github.com/Uzbekswe/fastapi-ml-skeleton.git
cd fastapi-ml-skeleton

# 2. Install dependencies
poetry install

# 3. Create .env from example and set your API key
cp .env.example .env
# Edit .env — change API_KEY to any string you want

# 4. Run the server
poetry run uvicorn fastapi_skeleton.main:app --reload

# 5. Open interactive docs
open http://localhost:8000/docs
```

**Authenticate in Swagger UI:** click **Authorize** → enter the `API_KEY` value you set in `.env`.

---

### Making a prediction

Once the server is running (either way), try the prediction endpoint:

```bash
curl -X POST http://localhost:8000/api/model/predict \
  -H "X-API-Key: change-me-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "MedInc": 8.3252,
    "HouseAge": 41.0,
    "AveRooms": 6.984,
    "AveBedrms": 1.024,
    "Population": 322.0,
    "AveOccup": 2.555,
    "Latitude": 37.88,
    "Longitude": -122.23
  }'
```

Expected response:

```json
{"median_house_value": 452600.0}
```

## Run Tests

**Requires Option B (local Poetry setup).**

```bash
poetry run pytest
```

19 tests: auth rejection, health check, prediction correctness, and parametrized edge cases for every `Field()` constraint.

## Docker Files Explained

The Docker setup was written from scratch as a learning exercise. Every line has a comment explaining *why* it exists. Here's the high-level picture:

### `Dockerfile` — multi-stage build

```
Stage 1 (deps):        python:3.11-slim
                       └── pip install poetry
                       └── COPY pyproject.toml poetry.lock
                       └── poetry export → requirements.txt
                           (Poetry is DISCARDED after this)

Stage 2 (production):  python:3.11-slim
                       └── apt install curl       (for health check)
                       └── create non-root user   (security)
                       └── pip install -r requirements.txt
                       └── COPY sample_model/
                       └── COPY fastapi_skeleton/
                       └── HEALTHCHECK + CMD
```

Key concepts exercised:
- **Multi-stage builds** — Poetry (~30MB) never enters the production image
- **Layer caching** — dependencies copied before code, so code edits don't re-run `pip install`
- **Non-root user** — `appuser:1001` reduces blast radius if the app is compromised
- **`HEALTHCHECK`** — Docker polls `/api/health/heartbeat` every 30s to report container health

### `docker-compose.yml`

Handles the three things a `Dockerfile` can't:
1. **Port mapping** — `8000:8000` (host:container)
2. **Secret injection** — `API_KEY` comes from your shell environment, never baked into the image
3. **Restart policy + resource limits** — `unless-stopped`, 512MB memory cap, 1 CPU

**Image tagging** — the compose file tags the image as both `1.0` and `latest`:

```
fastapi-ml-skeleton-app:1.0      ← pinned, never changes
fastapi-ml-skeleton-app:latest   ← always points to newest
```

`latest` alone is a moving target — if a base image update (e.g. Python 3.11 → 3.12) breaks something, you have no pinned version to roll back to. With a version tag you can always run the last known-good image. To upgrade, bump the version in `docker-compose.yml` and rebuild.

### `.dockerignore`

Tells Docker what to exclude from the build context. Without it, Docker would send `.git/`, `docs/`, `tests/`, and `.env` to the build daemon — adding size and potentially leaking secrets into image layers.

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

### v2.1.0 — Docker setup (implemented from scratch)

- `Dockerfile`: two-stage build — Poetry export stage → slim production runtime
- `docker-compose.yml`: port mapping, environment variable injection, health check, restart policy, resource limits
- `.dockerignore`: excludes `.git`, tests, docs, `.env`, scripts from the build context
- Fixed `poetry.lock` to include `pydantic-settings` (was missing, caused startup failure)

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
