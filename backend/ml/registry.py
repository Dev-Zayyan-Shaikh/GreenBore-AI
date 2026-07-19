import json
import os
from datetime import datetime, timezone
from typing import Any, Literal

import joblib  # type: ignore[import-untyped]

from backend.ml.schema import ModelMetadata, ModelMetrics


class ModelRegistry:
    """Manages serialization, versions, and deployment tags for models."""

    def __init__(self, registry_dir: str = "datasets/model_registry") -> None:
        self.registry_dir = os.path.abspath(registry_dir)
        self.registry_file = os.path.join(self.registry_dir, "registry.json")
        os.makedirs(self.registry_dir, exist_ok=True)

    def register_model(
        self,
        model_obj: Any,
        preprocessor_obj: Any,
        model_type: Literal["RandomForest", "XGBoost"],
        parameters: dict[str, Any],
        metrics: ModelMetrics,
        features: list[str],
    ) -> ModelMetadata:
        """
        Serializes and catalogs a trained model and scaler preprocessor.

        Args:
            model_obj: Classifier instance (Scikit-Learn or XGBoost).
            preprocessor_obj: Standard scaler fitted transformer instance.
            model_type: Model type tag.
            parameters: Training hyperparameters.
            metrics: Performance metrics.
            features: List of string feature names.

        Returns:
            The registered ModelMetadata.
        """
        # Determine next version increment
        models = self.get_all_metadata()
        type_models = [m for m in models if m["model_type"] == model_type]
        version = max([m["version"] for m in type_models]) + 1 if type_models else 1

        model_id = f"model_{model_type.lower()}_v{version}"
        model_subfolder = os.path.join(self.registry_dir, model_id)
        os.makedirs(model_subfolder, exist_ok=True)

        # Save artifacts
        model_path = os.path.join(model_subfolder, "model.joblib")
        artifacts = {
            "model": model_obj,
            "preprocessor": preprocessor_obj,
            "features": features,
        }
        joblib.dump(artifacts, model_path)

        # Catalog metadata
        metadata = ModelMetadata(
            model_id=model_id,
            model_type=model_type,
            version=version,
            parameters=parameters,
            metrics=metrics,
            features=features,
            created_at=datetime.now(timezone.utc).isoformat(),
            is_production=False,
        )

        models.append(metadata.model_dump())
        self._write_catalog(models)

        return metadata

    def set_production_model(self, model_id: str) -> None:
        """Sets the production tag to the specified model_id, clearing all others."""
        models = self.get_all_metadata()
        found = False
        for m in models:
            if m["model_id"] == model_id:
                m["is_production"] = True
                found = True
            else:
                m["is_production"] = False

        if not found:
            raise ValueError(f"Model ID '{model_id}' not found in registry catalog.")

        self._write_catalog(models)

    def load_model(self, model_id: str) -> tuple[Any, Any, list[str]]:
        """Loads and returns model class, scaler, and features tuple for prediction."""
        model_subfolder = os.path.join(self.registry_dir, model_id)
        model_path = os.path.join(model_subfolder, "model.joblib")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model weights not found at path: {model_path}")

        artifacts = joblib.load(model_path)
        return artifacts["model"], artifacts["preprocessor"], artifacts["features"]

    def load_production_model(self) -> tuple[Any, Any, ModelMetadata]:
        """Retrieves active production weights and metadata record catalog."""
        models = self.get_all_metadata()
        prod_meta_dict = next((m for m in models if m["is_production"]), None)
        if not prod_meta_dict:
            raise FileNotFoundError(
                "No model tagged as 'production' exists in the registry."
            )

        prod_meta = ModelMetadata(**prod_meta_dict)
        model_obj, preprocessor_obj, _ = self.load_model(prod_meta.model_id)
        return model_obj, preprocessor_obj, prod_meta

    def get_all_metadata(self) -> list[dict[str, Any]]:
        """Reads registry.json containing metadata logs of all models."""
        if not os.path.exists(self.registry_file):
            return []
        try:
            with open(self.registry_file) as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                return []
        except Exception:
            return []

    def _write_catalog(self, models: list[dict[str, Any]]) -> None:
        with open(self.registry_file, "w") as f:
            json.dump(models, f, indent=2)
