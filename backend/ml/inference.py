from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from backend.ml.registry import ModelRegistry
from backend.ml.schema import PredictRequest, PredictResponse


class InferenceService:
    """Manages active production model loading and executes predictions."""

    def __init__(self, registry_dir: str = "datasets/model_registry") -> None:
        self.registry = ModelRegistry(registry_dir)
        self._model: Any = None
        self._preprocessor: Any = None
        self._metadata: Any = None

    def predict(self, request: PredictRequest) -> PredictResponse:
        """Loads the production model and evaluates the classification probability.

        Args:
            request: The telemetry predict payload request.

        Returns:
            The PredictResponse containing classification result and confidence.
        """
        self._ensure_model_loaded()

        # Build DataFrame to align with the model's feature names and avoid warnings
        features_dict = request.model_dump()
        input_row = {feat: [features_dict[feat]] for feat in self._metadata.features}
        df_input = pd.DataFrame(input_row)

        # Scale features
        scaled_input = self._preprocessor.transform(df_input)

        # Run classification
        prediction = self._model.predict(scaled_input)[0]
        probabilities = self._model.predict_proba(scaled_input)[0]

        # Confidence corresponds to the probability of the predicted outcome class
        confidence = probabilities[int(prediction)]

        return PredictResponse(
            model_id=self._metadata.model_id,
            prediction=bool(prediction == 1),
            confidence=float(confidence),
        )

    def _ensure_model_loaded(self) -> None:
        if self._model is None:
            model_obj, preprocessor_obj, metadata = (
                self.registry.load_production_model()
            )
            self._model = model_obj
            self._preprocessor = preprocessor_obj
            self._metadata = metadata
