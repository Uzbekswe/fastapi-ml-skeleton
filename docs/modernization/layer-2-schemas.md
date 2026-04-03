# Layer 2: Models / Schemas — Modernization Plan

**Files:** `models/payload.py`, `models/prediction.py`, `models/heartbeat.py`
**Depends on:** Layer 1 (Configuration) — completed
**Depended on by:** Layer 3 (Services), Layer 5 (Routes)

---

## Change 1: Fix typo `HearbeatResult` -> `HeartbeatResult`

**Priority:** Important
**Files:** `models/heartbeat.py`, `api/routes/heartbeat.py`

**Why:** The typo propagates to OpenAPI docs and any client code generated from the schema. Fixing it now (before more code depends on it) minimizes churn.

**Old (`models/heartbeat.py`):**
```python
class HearbeatResult(BaseModel):
    is_alive: bool
```

**New:**
```python
class HeartbeatResult(BaseModel):
    is_alive: bool
```

Also update all imports and references in `api/routes/heartbeat.py`:
- `from fastapi_skeleton.models.heartbeat import HearbeatResult` -> `HeartbeatResult`
- `get_hearbeat` -> `get_heartbeat` (function name fix handled in Layer 5, but import rename needed now)

---

## Change 2: Change `average_rooms` and `average_bedrooms` from `int` to `float`

**Priority:** Important
**File:** `models/payload.py`

**Why:** These are averages (total rooms / total households). Averages are almost never whole numbers. Using `int` silently truncates `3.7` to `3`, corrupting the ML model input and degrading prediction accuracy.

**Old:**
```python
class HousePredictionPayload(BaseModel):
    median_income_in_block: float
    median_house_age_in_block: int
    average_rooms: int
    average_bedrooms: int
    population_per_block: int
    average_house_occupancy: int
    block_latitude: float
    block_longitude: float
```

**New:**
```python
class HousePredictionPayload(BaseModel):
    median_income_in_block: float
    median_house_age_in_block: int
    average_rooms: float          # was int — averages are fractional
    average_bedrooms: float       # was int — averages are fractional
    population_per_block: int
    average_house_occupancy: float # was int — average is fractional
    block_latitude: float
    block_longitude: float
```

Note: `average_house_occupancy` is also an average and should be `float` too.

---

## Change 3: Change `median_house_value` from `int` to `float`

**Priority:** Important
**File:** `models/prediction.py`

**Why:** The ML model outputs a float. Casting to `int` loses precision (e.g., `206855.43` becomes `206855`). Keeping it as `float` preserves the model's actual output.

**Old:**
```python
class HousePredictionResult(BaseModel):
    median_house_value: int
    currency: str = "USD"
```

**New:**
```python
class HousePredictionResult(BaseModel):
    median_house_value: float
    currency: str = "USD"
```

Also requires updating `services/models.py` `_post_process` to stop casting with `int()`.

---

## Change 4: Replace `payload_to_list()` standalone function with a model method using `model_dump()`

**Priority:** Important
**File:** `models/payload.py`

**Why:** The standalone function manually lists every field in order — fragile and error-prone. If a field is added or reordered, the function silently produces wrong input for the ML model. `model_dump()` uses Pydantic's field registry, so it stays in sync automatically.

**Old:**
```python
def payload_to_list(hpp: HousePredictionPayload) -> List:
    return [
        hpp.median_income_in_block,
        hpp.median_house_age_in_block,
        hpp.average_rooms,
        hpp.average_bedrooms,
        hpp.population_per_block,
        hpp.average_house_occupancy,
        hpp.block_latitude,
        hpp.block_longitude,
    ]
```

**New:**
```python
# Method on HousePredictionPayload class:
def to_list(self) -> list[float]:
    return list(self.model_dump().values())
```

The standalone function is deleted. Callers change from `payload_to_list(payload)` to `payload.to_list()`.

---

## Change 5: Type the return as `list[float]` instead of bare `List`

**Priority:** Nice-to-have
**File:** `models/payload.py`

**Why:** Bare `List` gives no type information — callers don't know what's inside. `list[float]` is the modern Python 3.11+ syntax (no import needed) and tells type checkers / readers exactly what the list contains.

Covered by Change 4 — the new `to_list()` method already uses `list[float]`.

---

## Change 6: Add `Field(gt=0, description="...")` constraints to payload fields

**Priority:** Nice-to-have
**File:** `models/payload.py`

**Why:** Without constraints, the API accepts nonsensical values (negative rooms, zero population) and passes them to the model, which returns garbage predictions silently. `Field()` constraints catch bad input at the API boundary and auto-generate OpenAPI documentation.

**Old:**
```python
class HousePredictionPayload(BaseModel):
    median_income_in_block: float
    ...
```

**New:**
```python
from pydantic import BaseModel, Field

class HousePredictionPayload(BaseModel):
    median_income_in_block: float = Field(gt=0, description="Median income for households in the block (tens of thousands USD)")
    median_house_age_in_block: int = Field(gt=0, description="Median age of houses in the block (years)")
    average_rooms: float = Field(gt=0, description="Average number of rooms per household")
    average_bedrooms: float = Field(gt=0, description="Average number of bedrooms per household")
    population_per_block: int = Field(gt=0, description="Total population in the block")
    average_house_occupancy: float = Field(gt=0, description="Average number of occupants per household")
    block_latitude: float = Field(ge=-90, le=90, description="Latitude of the block centroid")
    block_longitude: float = Field(ge=-180, le=180, description="Longitude of the block centroid")
```

---

## Change 7: Add `model_config` with `json_schema_extra` examples to models

**Priority:** Nice-to-have
**Files:** `models/payload.py`, `models/prediction.py`, `models/heartbeat.py`

**Why:** FastAPI auto-generates interactive docs at `/docs`. Without examples, users see empty fields and have to guess valid inputs. `json_schema_extra` provides a realistic example that appears in Swagger UI's "Try it out" and in generated client SDKs.

**Old:** No examples configured.

**New (`models/payload.py`):**
```python
class HousePredictionPayload(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "median_income_in_block": 8.3252,
                    "median_house_age_in_block": 41,
                    "average_rooms": 6.98,
                    "average_bedrooms": 1.02,
                    "population_per_block": 322,
                    "average_house_occupancy": 2.56,
                    "block_latitude": 37.88,
                    "block_longitude": -122.23,
                }
            ]
        }
    )
    ...
```

**New (`models/prediction.py`):**
```python
class HousePredictionResult(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "median_house_value": 452600.0,
                    "currency": "USD",
                }
            ]
        }
    )
    ...
```

**New (`models/heartbeat.py`):**
```python
class HeartbeatResult(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "is_alive": True,
                }
            ]
        }
    )
    ...
```

---

## Implementation Order

Changes are ordered to minimize breakage:

1. **Typo fix** — rename only, no logic change
2. **int -> float (payload)** — type correction, no logic change
3. **int -> float (prediction)** — type correction, small logic change in services
4. **payload_to_list -> to_list method** — structural refactor, update callers
5. **Type annotation** — covered by change 4
6. **Field constraints** — additive, no breaking change
7. **Schema examples** — additive, no breaking change
