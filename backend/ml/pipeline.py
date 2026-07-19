from typing import Any, Literal

import pandas as pd  # type: ignore[import-untyped]
from sklearn.ensemble import RandomForestClassifier  # type: ignore[import-untyped]
from sklearn.metrics import (  # type: ignore[import-untyped]
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split  # type: ignore[import-untyped]
from sklearn.preprocessing import StandardScaler  # type: ignore[import-untyped]
from xgboost import XGBClassifier  # type: ignore[import-untyped]

from backend.ml.registry import ModelRegistry
from backend.ml.schema import ModelMetadata, ModelMetrics
from backend.ml.tracker import ExperimentTracker


class MLPipeline:
    """
    End-to-end training and evaluation pipeline for water presence
    classification models using synthetic borehole logs.
    """

    def __init__(
        self,
        registry_dir: str = "datasets/model_registry",
        dataset_name: str = "borehole_data",
    ) -> None:
        self.registry = ModelRegistry(registry_dir)
        self.tracker = ExperimentTracker(registry_dir)
        self.dataset_name = dataset_name
        self.features = [
            "density",
            "porosity",
            "resistivity",
            "gamma_ray",
            "sonic_travel_time",
            "density_ma5",
            "porosity_ma5",
            "resistivity_ma5",
            "gamma_ray_ma5",
            "sonic_travel_time_ma5",
            "porosity_resistivity_ratio",
            "density_porosity_ratio",
            "rock_type_encoded",
        ]
        self.target = "has_water"

    def run_training_pipeline(
        self,
        df: pd.DataFrame,
        model_type: Literal["RandomForest", "XGBoost"],
        hyperparameters: dict[str, Any],
        set_prod: bool = False,
    ) -> ModelMetadata:
        """
        Executes preprocessing, model fitting, metric evaluation,
        and persists results to registry.

        Args:
            df: Raw DataFrame containing borehole datasets.
            model_type: Either 'RandomForest' or 'XGBoost'.
            hyperparameters: Configurations for model constructors.
            set_prod: If True, marks the registered model version as production.

        Returns:
            The registered ModelMetadata configuration.
        """
        # 1. Feature Ingestion & Preprocessing
        X = df[self.features]
        y = df[self.target].astype(int)

        # 2. Train/Test Split (80% train, 20% test)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # 3. Scale Features using StandardScaler
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # 4. Model Training
        if model_type == "RandomForest":
            # Set default random state if absent
            rf_params: dict[str, Any] = {"random_state": 42, **hyperparameters}
            model = RandomForestClassifier(**rf_params)
        elif model_type == "XGBoost":
            xgb_params: dict[str, Any] = {
                "random_state": 42,
                "eval_metric": "logloss",
                **hyperparameters,
            }
            model = XGBClassifier(**xgb_params)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")

        model.fit(X_train_scaled, y_train)

        # 5. Model Evaluation
        y_pred = model.predict(X_test_scaled)
        metrics = ModelMetrics(
            accuracy=float(accuracy_score(y_test, y_pred)),
            precision=float(precision_score(y_test, y_pred, zero_division=0)),
            recall=float(recall_score(y_test, y_pred, zero_division=0)),
            f1=float(f1_score(y_test, y_pred, zero_division=0)),
        )

        # 6. Local Logging & Version Registration
        self.tracker.log_run(
            model_type=model_type,
            parameters=hyperparameters,
            metrics=metrics,
            dataset_name=self.dataset_name,
        )

        metadata = self.registry.register_model(
            model_obj=model,
            preprocessor_obj=scaler,
            model_type=model_type,
            parameters=hyperparameters,
            metrics=metrics,
            features=self.features,
        )

        if set_prod:
            self.registry.set_production_model(metadata.model_id)
            metadata.is_production = True

        return metadata
