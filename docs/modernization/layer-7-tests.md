# Layer 7: Tests — Modernization Plan

**Files:** `tests/conftest.py`, `tests/test_api/*`, `tests/test_service/*`
**Depends on:** All previous layers

---

## Change 1: Replace `starlette.config.environ` with `os.environ.setdefault()`

**Priority:** Important

**Why:** The old code used `starlette.config.environ` to set env vars at module level — a Starlette-specific side channel. Since we migrated to pydantic-settings in Layer 1, we use `os.environ.setdefault()` to set test env vars before the app import. `setdefault` avoids overriding any env vars already set in the shell.

**Old:**
```python
from starlette.config import environ
environ["API_KEY"] = "a1279d26-63ac-41f1-8266-4ef3702ad7cb"
environ["DEFAULT_MODEL_PATH"] = "..."
```

**New:**
```python
import os
os.environ.setdefault("API_KEY", "a1279d26-63ac-41f1-8266-4ef3702ad7cb")
os.environ.setdefault("DEFAULT_MODEL_PATH", "...")
```

Also added a shared `auth_headers` fixture that returns `{"X-API-Key": <key>}` so tests don't hardcode the header name.

---

## Change 2: Update all references to renamed classes/headers

**Priority:** Important

- Header name `"token"` -> `"X-API-Key"` in all test requests
- Removed unused `app = get_app()` at module level in `test_heartbeat.py`
- Changed `config.DEFAULT_MODEL_PATH` -> `settings.DEFAULT_MODEL_PATH` in service test
- Updated test payloads to use `float` values for average fields (matching Layer 2 type changes)

---

## Change 3: Strengthen assertions

**Priority:** Important

- **test_prediction**: now asserts `median_house_value` is a `float`, is positive, and `currency == "USD"` — not just field existence
- **test_service/test_models**: same stronger assertions, plus `isinstance` and value checks
- **test_api_auth**: already had strong assertions (exact JSON match)

---

## Change 4: Add edge case tests

**Priority:** Nice-to-have

Added 12 new parametrized test cases:

- **`test_prediction_invalid_field_values`** — 9 cases: negative income, zero rooms/bedrooms/population/occupancy, out-of-range latitude (100, -100), out-of-range longitude (200, -200). All return 422 thanks to Layer 2's `Field()` constraints.
- **`test_prediction_missing_field`** — verifies a missing required field returns 422.
- **`test_model_load_invalid_path`** — verifies `HousePriceModel` raises on a nonexistent path.
- **`test_payload_to_list`** — verifies the new `to_list()` method returns 8 values in the correct order.

---

## Additional fix: Retrained sample model

The bundled `.joblib` model was saved with scikit-learn 0.22.1. The current scikit-learn 1.8.0 can't unpickle it (`'LinearRegression' object has no attribute 'positive'`). Retrained with the current version using the same California Housing dataset and LinearRegression.
