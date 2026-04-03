import os

import pytest
from starlette.testclient import TestClient

# Set test environment variables before any application imports.
# This is necessary because pydantic-settings reads env vars at import time
# when `settings = Settings()` runs at module level in config.py.
os.environ.setdefault("API_KEY", "a1279d26-63ac-41f1-8266-4ef3702ad7cb")
os.environ.setdefault(
    "DEFAULT_MODEL_PATH",
    "./sample_model/lin_reg_california_housing_model.joblib",
)

from fastapi_skeleton.main import get_app  # noqa: E402


TEST_API_KEY = os.environ["API_KEY"]


@pytest.fixture()
def test_client():
    app = get_app()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def auth_headers() -> dict[str, str]:
    return {"X-API-Key": TEST_API_KEY}
