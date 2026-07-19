
import pandas as pd  # type: ignore[import-untyped]
import pytest
from backend.ml import InferenceService, MLPipeline, ModelRegistry, PredictRequest


def test_ml_pipeline_training(
    synthetic_dataframe: pd.DataFrame, temp_registry_dir: str
) -> None:
    """Verifies that MLPipeline successfully trains, evaluates, and registers models."""
    pipeline = MLPipeline(registry_dir=temp_registry_dir, dataset_name="test_well")

    # 1. Train RandomForest Classifier
    rf_meta = pipeline.run_training_pipeline(
        df=synthetic_dataframe,
        model_type="RandomForest",
        hyperparameters={"n_estimators": 10},
        set_prod=True,
    )
    assert rf_meta.model_id == "model_randomforest_v1"
    assert rf_meta.version == 1
    assert rf_meta.is_production is True
    assert rf_meta.metrics.accuracy >= 0.0

    # 2. Train XGBoost Classifier
    xgb_meta = pipeline.run_training_pipeline(
        df=synthetic_dataframe,
        model_type="XGBoost",
        hyperparameters={"n_estimators": 5, "max_depth": 3},
        set_prod=False,
    )
    assert xgb_meta.model_id == "model_xgboost_v1"
    assert xgb_meta.is_production is False


def test_model_registry_operations(
    synthetic_dataframe: pd.DataFrame, temp_registry_dir: str
) -> None:
    """Tests metadata updates, retrieval, and version increments in the registry."""
    pipeline = MLPipeline(registry_dir=temp_registry_dir, dataset_name="test_well")
    registry = ModelRegistry(temp_registry_dir)

    # Register first version
    meta_v1 = pipeline.run_training_pipeline(
        df=synthetic_dataframe,
        model_type="RandomForest",
        hyperparameters={"n_estimators": 5},
    )
    assert meta_v1.version == 1

    # Register second version (should auto-increment)
    meta_v2 = pipeline.run_training_pipeline(
        df=synthetic_dataframe,
        model_type="RandomForest",
        hyperparameters={"n_estimators": 10},
    )
    assert meta_v2.version == 2

    # Set version 2 to production
    registry.set_production_model(meta_v2.model_id)

    # Load production model
    _, _, prod_meta = registry.load_production_model()
    assert prod_meta.model_id == meta_v2.model_id
    assert prod_meta.is_production is True


def test_inference_service(
    synthetic_dataframe: pd.DataFrame, temp_registry_dir: str
) -> None:
    """Verifies that InferenceService loads active models and scores inputs."""
    # Ensure FileNotFoundError is raised when no production model is registered
    inference = InferenceService(registry_dir=temp_registry_dir)
    with pytest.raises(FileNotFoundError, match="No model tagged as 'production'"):
        request = PredictRequest(
            density=2.3,
            porosity=0.2,
            resistivity=120.0,
            gamma_ray=40.0,
            sonic_travel_time=80.0,
            density_ma5=2.3,
            porosity_ma5=0.2,
            resistivity_ma5=120.0,
            gamma_ray_ma5=40.0,
            sonic_travel_time_ma5=80.0,
            porosity_resistivity_ratio=0.0016,
            density_porosity_ratio=11.5,
            rock_type_encoded=1,
        )
        inference.predict(request)

    # Train and set a model to production
    pipeline = MLPipeline(registry_dir=temp_registry_dir, dataset_name="test_well")
    pipeline.run_training_pipeline(
        df=synthetic_dataframe,
        model_type="RandomForest",
        hyperparameters={"n_estimators": 10},
        set_prod=True,
    )

    # Score prediction
    prediction_response = inference.predict(request)
    assert prediction_response.model_id == "model_randomforest_v1"
    assert isinstance(prediction_response.prediction, bool)
    assert 0.0 <= prediction_response.confidence <= 1.0
