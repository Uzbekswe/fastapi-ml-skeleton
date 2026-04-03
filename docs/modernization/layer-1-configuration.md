# Layer 1: Configuration — Modernization Plan

**Files:** `core/config.py`, `tox.ini` (deleted), `setup.cfg` (deleted), `.env.example`
**Depends on:** Nothing — this is the foundation
**Depended on by:** Every other layer

---

## Change 1: Replace `starlette.config.Config` with `pydantic-settings` `BaseSettings`

**Priority:** Critical

**Why:** `starlette.config.Config` is a thin, unvalidated env var loader with no schema, no docs generation, and no nested config support. It's effectively unmaintained and not recommended by the FastAPI docs. `pydantic-settings` `BaseSettings` validates types at startup, generates JSON schema, supports `.env` files natively, and integrates with Pydantic v2.

**Old:**
```python
from starlette.config import Config
from starlette.datastructures import Secret

config = Config(".env")
API_KEY = config("API_KEY", cast=Secret)
IS_DEBUG = config("IS_DEBUG", cast=bool, default=False)
DEFAULT_MODEL_PATH = config("DEFAULT_MODEL_PATH", cast=str)
```

**New:**
```python
from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    API_KEY: SecretStr
    IS_DEBUG: bool = False
    DEFAULT_MODEL_PATH: str

    @field_validator("DEFAULT_MODEL_PATH")
    @classmethod
    def validate_model_path(cls, v: str) -> str:
        if not Path(v).exists():
            raise ValueError(f"Model file not found: {v}")
        return v

settings = Settings()
```

---

## Change 2: Replace `starlette.datastructures.Secret` with `pydantic.SecretStr`

**Priority:** Important

**Why:** `SecretStr` integrates with `BaseSettings`, has `.get_secret_value()` for explicit unwrapping, and is excluded from serialization and logs by default — preventing accidental secret exposure.

Covered by Change 1 — `API_KEY: SecretStr` in the `Settings` class.

---

## Change 3: Add `@field_validator` to check `DEFAULT_MODEL_PATH` exists at startup

**Priority:** Important

**Why:** Without validation, a missing or mistyped model path only surfaces later when the model is loaded — producing a confusing error far from the root cause. The validator fails fast at startup with a clear message.

Covered by Change 1 — the `validate_model_path` field validator.

---

## Change 4: Delete `tox.ini`

**Priority:** Critical

**Why:** Referenced `py36` (Python 3.6, EOL since Dec 2021), contradicted `pyproject.toml`'s `python = "^3.11"` requirement, and duplicated test/lint config already in `pyproject.toml`.

---

## Change 5: Delete `setup.cfg`

**Priority:** Important

**Why:** Had `[coverage:run] source = app` — but the package is `fastapi_skeleton`, not `app`. Coverage was silently measuring nothing. Config is now consolidated in `pyproject.toml`.

---

## Change 6: Update `.env.example` with comments

**Priority:** Nice-to-have

**Old:**
```
API_KEY=sample_api_key
IS_DEBUG=False
DEFAULT_MODEL_PATH=./sample_model/lin_reg_california_housing_model.joblib
```

**New:**
```
# Enable debug mode (detailed error responses, auto-reload)
# Values: True / False
IS_DEBUG=False

# API authentication key. Generate one with: python -c "import uuid; print(uuid.uuid4())"
API_KEY=sample_api_key

# Path to the trained ML model file (joblib format)
# Must exist on disk — validated at startup
DEFAULT_MODEL_PATH=./sample_model/lin_reg_california_housing_model.joblib
```
