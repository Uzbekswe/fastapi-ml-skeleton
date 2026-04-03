import pytest

from fastapi_skeleton.core.config import settings
from fastapi_skeleton.models.payload import HousePredictionPayload
from fastapi_skeleton.models.prediction import HousePredictionResult
from fastapi_skeleton.services.models import HousePriceModel


def test_prediction() -> None:
    model_path = settings.DEFAULT_MODEL_PATH
    hpp = HousePredictionPayload.model_validate(
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
    )

    hpm = HousePriceModel(model_path)
    result = hpm.predict(hpp)
    assert isinstance(result, HousePredictionResult)
    assert isinstance(result.median_house_value, float)
    assert result.median_house_value > 0
    assert result.currency == "USD"


def test_model_load_invalid_path() -> None:
    with pytest.raises(Exception):
        HousePriceModel("/nonexistent/model.joblib")


def test_payload_to_list() -> None:
    hpp = HousePredictionPayload.model_validate(
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
    )
    result = hpp.to_list()
    assert len(result) == 8
    assert result[0] == 8.3252
    assert result[6] == 37.88
