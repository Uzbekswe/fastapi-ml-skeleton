# Layer 6: Security — Modernization Plan

**Files:** `core/security.py`, `core/messages.py`
**Depends on:** Layer 1 (Configuration)

---

## Change 1: Remove redundant `headers={}` from HTTPException calls

**Priority:** Nice-to-have

**Why:** The empty dict does nothing — `HTTPException` defaults to `None` for headers. Removing it reduces noise.

---

## Change 2: Use `SecretStr.get_secret_value()` instead of `str(config.API_KEY)`

**Priority:** Nice-to-have

Already done in Layer 1 — `settings.API_KEY` is a `SecretStr` and the code already used `.get_secret_value()`.

---

## Change 3: Change header name from `"token"` to `"X-API-Key"`

**Priority:** Nice-to-have

**Why:** `"token"` is non-standard and confusing — could be mistaken for a Bearer token. `"X-API-Key"` is the conventional header name for API key auth and matches what developers expect.

---

## Change 4: Change `validate_request` return type from `bool` to `None`

**Priority:** Nice-to-have

**Why:** The return value `True` was never used — callers assigned it to `_`. Changing to `None` makes the intent clear: this dependency is a guard, not a data source. Also switched `Optional[str]` to `str | None` (modern Python 3.11+ syntax).
