from fastapi import APIRouter, Depends, HTTPException, Request
from loguru import logger
from starlette.status import HTTP_503_SERVICE_UNAVAILABLE

from fastapi_skeleton.core import security
from fastapi_skeleton.models.payload import HousePredictionPayload
from fastapi_skeleton.models.prediction import HousePredictionResult
from fastapi_skeleton.services.models import HousePriceModel

router = APIRouter()


def get_model(request: Request) -> HousePriceModel:
    model = request.app.state.model
    if model is None:
        raise HTTPException(
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not available",
        )
    return model


@router.post(
    "/predict",
    response_model=HousePredictionResult,
    name="predict",
    responses={
        200: {
            "description": "Successful prediction",
            "content": {
                "application/json": {
                    "example": {"median_house_value": 452600.0, "currency": "USD"}
                }
            },
        },
        503: {"description": "Model not available"},
    },
)
def post_predict(
    block_data: HousePredictionPayload,
    _: None = Depends(security.validate_request),
    model: HousePriceModel = Depends(get_model),
) -> HousePredictionResult:
    try:
        prediction: HousePredictionResult = model.predict(block_data)
    except Exception as e:
        logger.error(f"Prediction endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Prediction failed")
    return prediction
