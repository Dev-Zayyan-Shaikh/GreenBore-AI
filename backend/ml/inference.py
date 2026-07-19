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

    def predict(self, request: PredictRequest, model_id: str | None = None) -> PredictResponse:
        """Loads the production model and evaluates the classification probability.

        Args:
            request: The telemetry predict payload request.
            model_id: Optional specific model ID to use instead of the production model.

        Returns:
            The PredictResponse containing classification result and confidence.
        """
        if model_id:
            model_obj, preprocessor_obj, features = self.registry.load_model(model_id)
            active_model_id = model_id
        else:
            self._ensure_model_loaded()
            model_obj = self._model
            preprocessor_obj = self._preprocessor
            features = self._metadata.features
            active_model_id = self._metadata.model_id

        # Build DataFrame to align with the model's feature names and avoid warnings
        features_dict = request.model_dump()
        input_row = {feat: [features_dict[feat]] for feat in features}
        df_input = pd.DataFrame(input_row)

        # Scale features
        scaled_input = preprocessor_obj.transform(df_input)

        # Run classification
        prediction = model_obj.predict(scaled_input)[0]
        probabilities = model_obj.predict_proba(scaled_input)[0]

        # Confidence corresponds to the probability of the predicted outcome class
        confidence = probabilities[int(prediction)]

        return PredictResponse(
            model_id=active_model_id,
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
