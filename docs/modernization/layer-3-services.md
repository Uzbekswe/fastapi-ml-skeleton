# Layer 3: Services — Modernization Plan

**File:** `services/models.py`
**Depends on:** Layer 2 (Models/Schemas)
**Depended on by:** Layer 4 (Lifecycle), Layer 5 (Routes)

---

## Change 1: Add try/except around `joblib.load()` in `_load_local_model()`

**Priority:** Critical

**Why:** If the model file is corrupt or incompatible, `joblib.load()` throws an opaque exception. Wrapping it logs the path and error clearly, then re-raises so the app fails fast with a useful message instead of a traceback.

**Old:**
```python
def _load_local_model(self) -> None:
    self.model = joblib.load(self.path)
```

**New:**
```python
def _load_local_model(self) -> None:
    try:
        self.model = joblib.load(self.path)
    except Exception as e:
        logger.error(f"Failed to load model from {self.path}: {e}")
        raise
```

---

## Change 2: Add try/except around `model.predict()` in `_predict()`

**Priority:** Important

**Why:** sklearn's `predict()` can fail on malformed features. Without handling, the error bubbles up as an unstructured 500. Logging the failure makes debugging easier.

**Old:**
```python
def _predict(self, features: np.ndarray) -> np.ndarray:
    logger.debug("Predicting.")
    prediction_result = self.model.predict(features)
    return prediction_result
```

**New:**
```python
def _predict(self, features: np.ndarray) -> np.ndarray:
    logger.debug("Predicting.")
    try:
        prediction_result = self.model.predict(features)
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise
    return prediction_result
```

---

## Change 3: Fix `_pre_process` to use `payload.to_list()`

**Priority:** Important

Already completed in Layer 2 — `payload_to_list(payload)` was replaced with `payload.to_list()`.

---

## Change 4: Document `RESULT_UNIT_FACTOR`

**Priority:** Nice-to-have

**Why:** `RESULT_UNIT_FACTOR = 100` was an unexplained magic number. The California Housing dataset target is in units of $100,000, so the correct factor is actually `100_000` to convert to dollars.

**Old:**
```python
class HousePriceModel:
    RESULT_UNIT_FACTOR = 100
```

**New:**
```python
# Scalar applied to raw model output to convert to human-readable USD.
# The California Housing dataset target is in units of $100,000;
# multiplying by 100_000 gives the dollar value.
RESULT_UNIT_FACTOR = 100_000
```

Moved to module-level constant since it's not instance-specific.
