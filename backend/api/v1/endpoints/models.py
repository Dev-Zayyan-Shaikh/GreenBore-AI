import json
import logging
import os
from typing import Any, Literal

import pandas as pd  # type: ignore[import-untyped]
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.ml.pipeline import MLPipeline
from backend.ml.registry import ModelRegistry
from backend.ml.schema import ModelMetadata

router = APIRouter()
logger = logging.getLogger("api.models")

REGISTRY_DIR = "datasets/model_registry"
SIMULATIONS_DIR = "datasets/simulations"


class TrainRequest(BaseModel):
    model_type: Literal["RandomForest", "XGBoost"]
    hyperparameters: dict[str, Any] = Field(default_factory=dict)
    dataset_name: str
    set_prod: bool = False


@router.get("", response_model=list[dict[str, Any]])
async def list_models() -> list[dict[str, Any]]:
    """
    Lists all models in the model registry catalog, including versions and evaluation metrics.
    """
    logger.info("Listing registered models.")
    try:
        registry = ModelRegistry(REGISTRY_DIR)
        return registry.get_all_metadata()
    except Exception as e:
        logger.error(f"Failed to load model registry catalog: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch models list: {str(e)}"
        ) from e


@router.post("/train", response_model=ModelMetadata, status_code=status.HTTP_201_CREATED)
async def train_model(payload: TrainRequest) -> ModelMetadata:
    """
    Trains a new RandomForest or XGBoost classification model using a simulated dataset
    and registers it in the catalog.
    """
    logger.info(f"Received request to train {payload.model_type} model on dataset {payload.dataset_name}.")

    # Check if dataset exists
    json_path = os.path.join(SIMULATIONS_DIR, f"{payload.dataset_name}.json")
    if not os.path.exists(json_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Simulated dataset '{payload.dataset_name}' does not exist. Run a simulation first."
        )

    try:
        # Load dataset
        with open(json_path) as f:
            records = json.load(f)
        df = pd.DataFrame(records)

        # Run pipeline
        pipeline = MLPipeline(registry_dir=REGISTRY_DIR, dataset_name=payload.dataset_name)
        metadata = pipeline.run_training_pipeline(
            df=df,
            model_type=payload.model_type,
            hyperparameters=payload.hyperparameters,
            set_prod=payload.set_prod
        )
        return metadata
    except Exception as e:
        logger.error(f"Model training pipeline failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Training pipeline execution failed: {str(e)}"
        ) from e


@router.post("/set-production/{model_id}")
async def set_production_model(model_id: str) -> dict[str, Any]:
    """
    Sets the active production model tag for serving real-time predictions.
    """
    logger.info(f"Promoting model '{model_id}' to active production tag.")
    try:
        registry = ModelRegistry(REGISTRY_DIR)
        registry.set_production_model(model_id)
        return {
            "status": "success",
            "message": f"Model '{model_id}' is now set as the active production model.",
            "production_model_id": model_id
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        ) from e
    except Exception as e:
        logger.error(f"Failed to update production model tag: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set production model: {str(e)}"
        ) from e
