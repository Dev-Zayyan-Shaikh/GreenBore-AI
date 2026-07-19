from typing import Any, Literal

from pydantic import BaseModel, Field


class ModelMetrics(BaseModel):
    """Evaluation metrics for a trained classification model."""

    accuracy: float = Field(..., ge=0.0, le=1.0)
    precision: float = Field(..., ge=0.0, le=1.0)
    recall: float = Field(..., ge=0.0, le=1.0)
    f1: float = Field(..., ge=0.0, le=1.0)


class ModelMetadata(BaseModel):
    """Metadata catalog schema for registered model versions."""

    model_id: str
    model_type: Literal["RandomForest", "XGBoost"]
    version: int = Field(..., gt=0)
    parameters: dict[str, Any]
    metrics: ModelMetrics
    features: list[str]
    created_at: str
    is_production: bool = False


class ExperimentRun(BaseModel):
    """Metadata for tracking hyperparameter optimization runs."""

    run_id: str
    model_type: Literal["RandomForest", "XGBoost"]
    parameters: dict[str, Any]
    metrics: ModelMetrics
    created_at: str
    dataset_name: str


class PredictRequest(BaseModel):
    """Single point telemetry data for water classification inference."""

    density: float = Field(..., ge=1.0, le=4.0)
    porosity: float = Field(..., ge=0.0, le=1.0)
    resistivity: float = Field(..., ge=0.0)
    gamma_ray: float = Field(..., ge=0.0)
    sonic_travel_time: float = Field(..., ge=30.0)

    # MA5 variables
    density_ma5: float = Field(..., ge=1.0, le=4.0)
    porosity_ma5: float = Field(..., ge=0.0, le=1.0)
    resistivity_ma5: float = Field(..., ge=0.0)
    gamma_ray_ma5: float = Field(..., ge=0.0)
    sonic_travel_time_ma5: float = Field(..., ge=30.0)

    # Derived petrophysical variables
    porosity_resistivity_ratio: float = Field(..., ge=0.0)
    density_porosity_ratio: float = Field(..., ge=0.0)
    rock_type_encoded: int = Field(..., ge=0, le=4)


class PredictResponse(BaseModel):
    """Result payload representing water classification inference."""

    model_id: str
    prediction: bool = Field(
        ..., description="True if borehole location contains water"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Inference probability confidence score"
    )
