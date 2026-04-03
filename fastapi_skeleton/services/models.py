import joblib
import numpy as np
from loguru import logger

from fastapi_skeleton.core.messages import NO_VALID_PAYLOAD
from fastapi_skeleton.models.payload import HousePredictionPayload
from fastapi_skeleton.models.prediction import HousePredictionResult

# Scalar applied to raw model output to convert to human-readable USD.
# The California Housing dataset target is in units of $100,000;
# multiplying by 100_000 gives the dollar value.
RESULT_UNIT_FACTOR = 100_000


class HousePriceModel:
    def __init__(self, path: str) -> None:
        self.path = path
        self._load_local_model()

    def _load_local_model(self) -> None:
        try:
            self.model = joblib.load(self.path)
        except Exception as e:
            logger.error(f"Failed to load model from {self.path}: {e}")
            raise

    def _pre_process(self, payload: HousePredictionPayload) -> np.ndarray:
        logger.debug("Pre-processing payload.")
        result = np.asarray(payload.to_list()).reshape(1, -1)
        return result

    def _post_process(self, prediction: np.ndarray) -> HousePredictionResult:
        logger.debug("Post-processing prediction.")
        result = prediction.tolist()
        human_readable_unit = result[0] * RESULT_UNIT_FACTOR
        hpp = HousePredictionResult(median_house_value=human_readable_unit)
        return hpp

    def _predict(self, features: np.ndarray) -> np.ndarray:
        logger.debug("Predicting.")
        try:
            prediction_result = self.model.predict(features)
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise
        return prediction_result

    def predict(self, payload: HousePredictionPayload) -> HousePredictionResult:
        pre_processed_payload = self._pre_process(payload)
        prediction = self._predict(pre_processed_payload)
        logger.info(prediction)
        post_processed_result = self._post_process(prediction)

        return post_processed_result
