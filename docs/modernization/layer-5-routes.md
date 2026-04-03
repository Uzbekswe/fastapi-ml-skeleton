# Layer 5: Routes / Endpoints — Modernization Plan

**Files:** `api/routes/prediction.py`, `api/routes/heartbeat.py`
**Depends on:** Layer 3 (Services), Layer 4 (Lifecycle)

---

## Change 1: Fix typo `get_hearbeat` -> `get_heartbeat`

Already completed in Layer 2.

---

## Change 2: Replace `request.app.state.model` with typed `Depends()`

**Priority:** Important

**Why:** `request.app.state.model` is untyped and has no null check. If the model failed to load, calling `.predict()` on `None` gives an opaque `AttributeError`. A `Depends()` function centralizes the retrieval, type-checks the result, and returns 503 if the model isn't loaded.

**Old:**
```python
def post_predict(request: Request, block_data: ...) -> ...:
    model: HousePriceModel = request.app.state.model
```

**New:**
```python
def get_model(request: Request) -> HousePriceModel:
    model = request.app.state.model
    if model is None:
        raise HTTPException(status_code=503, detail="Model is not available")
    return model

def post_predict(
    block_data: ...,
    model: HousePriceModel = Depends(get_model),
) -> ...:
```

---

## Change 3: Add error handling in prediction route

**Priority:** Important

**Why:** If `model.predict()` throws, the raw exception leaks to the client. Wrapping in try/except returns a clean 500 and logs the actual error.

---

## Change 4: Add model readiness check to heartbeat

**Priority:** Important

**Why:** The old heartbeat always returned `is_alive: True` even if the model failed to load. Now it checks `app.state.model is not None` and returns 503 with `is_alive: False` if the model isn't loaded — useful for load balancer health checks.

---

## Change 5: Add `responses` parameter with examples to route decorators

**Priority:** Nice-to-have

**Why:** Populates Swagger UI with response examples for each status code, making the API self-documenting.
