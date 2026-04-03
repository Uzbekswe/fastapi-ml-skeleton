# FastAPI-ML-Skeleton Audit — Grouped by Architecture Layer

Implementation order: bottom-up (dependencies first). Layers that other layers depend on get fixed first.

---

## Layer 1: Configuration (`core/config.py`, `tox.ini`, `setup.cfg`, `.env.example`)

**Responsibility:** Load, validate, and expose application settings (env vars, secrets, paths). Every other layer imports from here — it's the foundation.

**Changes needed: 5**

**Fix order:**
1. Replace `starlette.config.Config` + `starlette.datastructures.Secret` with **`pydantic-settings` `BaseSettings`** + `SecretStr` — **Critical**
2. Delete `tox.ini` (references dead py36 target, conflicts with pyproject.toml) — **Critical**
3. Delete `setup.cfg` (coverage source points to `app` instead of `fastapi_skeleton`, duplicates pyproject.toml) — **Important**
4. Add `@field_validator` to check `DEFAULT_MODEL_PATH` exists at startup — **Important**
5. Update `.env.example` with comments documenting each variable — **Nice-to-have**

**FastAPI tutorial/docs reference:**
- [Settings and Environment Variables](https://fastapi.tiangolo.com/advanced/settings/)

---

## Layer 2: Models / Schemas (`models/payload.py`, `models/prediction.py`, `models/heartbeat.py`)

**Responsibility:** Define Pydantic request/response models.

**Changes needed: 7**

**Fix order:**
1. Fix typo: `HearbeatResult` → `HeartbeatResult`
2. Change `average_rooms` and `average_bedrooms` from `int` to `float`
3. Change `median_house_value` from `int` to `float`
4. Replace `payload_to_list()` standalone function with a method using `model_dump()`
5. Type the return as `list[float]` instead of bare `List`
6. Add `Field(gt=0, description="...")` constraints to payload fields
7. Add `json_schema_extra` / `model_config` examples to models

**FastAPI tutorial/docs reference:**
- [Request Body](https://fastapi.tiangolo.com/tutorial/body/)
- [Schema Extra / Examples](https://fastapi.tiangolo.com/tutorial/schema-extra-example/)
- [Body - Fields](https://fastapi.tiangolo.com/tutorial/body-fields/)
- [Response Model](https://fastapi.tiangolo.com/tutorial/response-model/)

---

## Layer 3: Services (`services/models.py`)

**Responsibility:** Business logic layer. Loads the ML model, runs pre/post-processing, prediction pipeline.

**Changes needed: 4**

**Fix order:**
1. Add try/except around `joblib.load()` in `_load_local_model()`
2. Add try/except around `model.predict()` in `_predict()`
3. Fix `_pre_process` to use `model_dump().values()` instead of `payload_to_list()`
4. Document or make `RESULT_UNIT_FACTOR = 100` configurable

**FastAPI tutorial/docs reference:**
- [Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/)

---

## Layer 4: App Lifecycle & Middleware (`core/event_handlers.py`, `main.py`)

**Responsibility:** Application startup/shutdown, middleware stack, and the app factory.

**Changes needed: 5**

**Fix order:**
1. Replace `add_event_handler("startup"/"shutdown")` with the **lifespan context manager**
2. Delete `event_handlers.py` (logic moves into lifespan in `main.py`)
3. Add `CORSMiddleware`
4. Add a global exception handler
5. Make `get_app()` compatible with `gunicorn --factory`

**FastAPI tutorial/docs reference:**
- [Lifespan Events](https://fastapi.tiangolo.com/advanced/events/)
- [CORS](https://fastapi.tiangolo.com/tutorial/cors/)
- [Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/)
- [Middleware](https://fastapi.tiangolo.com/tutorial/middleware/)

---

## Layer 5: Routes / Endpoints (`api/routes/prediction.py`, `api/routes/heartbeat.py`)

**Responsibility:** HTTP interface.

**Changes needed: 5**

**Fix order:**
1. Fix typo: `get_hearbeat` → `get_heartbeat`
2. Replace `request.app.state.model` with a typed `Depends()` function
3. Add error handling in prediction route
4. Add model readiness check to heartbeat endpoint
5. Add `responses` parameter with examples to route decorators

**FastAPI tutorial/docs reference:**
- [Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [Additional Responses](https://fastapi.tiangolo.com/advanced/additional-responses/)
- [Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/)

---

## Layer 6: Security (`core/security.py`, `core/messages.py`)

**Responsibility:** Authentication and authorization.

**Changes needed: 4** (all nice-to-have)

**Fix order:**
1. Remove redundant `headers={}` from HTTPException calls
2. Use `SecretStr.get_secret_value()` instead of `str(config.API_KEY)`
3. Change header name from `"token"` to `"X-API-Key"`
4. Change `validate_request` return type from `bool` to `None`

**FastAPI tutorial/docs reference:**
- [Security - First Steps](https://fastapi.tiangolo.com/tutorial/security/)

---

## Layer 7: Tests (`tests/conftest.py`, `tests/test_api/*`, `tests/test_service/*`)

**Responsibility:** Verify all the above works correctly. Fix last.

**Changes needed: 4**

**Fix order:**
1. Replace `os.environ[...]` mutations with `monkeypatch.setenv()` inside fixtures
2. Update all references to renamed classes
3. Strengthen assertions: check response values, not just field existence
4. Add edge case tests

**FastAPI tutorial/docs reference:**
- [Testing](https://fastapi.tiangolo.com/tutorial/testing/)

---

## Recommended Implementation Order

```
Layer 1: Configuration          ← everything depends on this
   ↓
Layer 2: Models/Schemas         ← services and routes depend on these
   ↓
Layer 3: Services               ← routes depend on this
   ↓
Layer 4: Lifecycle & Middleware  ← wires everything together
   ↓
Layer 5: Routes                 ← consumes all above
   ↓
Layer 6: Security               ← mostly cosmetic changes
   ↓
Layer 7: Tests                  ← fix last, after code stabilizes
```

**Total changes: 34 across 7 layers**
- Critical: 5
- Important: 17
- Nice-to-have: 12
