from pydantic import BaseModel, ConfigDict


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

    median_house_value: float
    currency: str = "USD"
