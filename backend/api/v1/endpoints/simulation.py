import logging
import os
import re
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import FileResponse

from backend.synthetic.generator import GeologicalSimulator
from backend.synthetic.pipeline import DataPipeline
from backend.synthetic.schema import SimulationConfig

router = APIRouter()
logger = logging.getLogger("api.simulation")

SIMULATIONS_DIR = os.path.abspath("datasets/simulations")


@router.post("/generate", status_code=status.HTTP_201_CREATED)
async def generate_simulation(config: SimulationConfig) -> dict[str, Any]:
    """
    Triggers the geological simulator to generate, feature engineer, and
    persist a synthetic borehole log dataset.
    """
    logger.info("Starting synthetic geological log simulation.")
    try:
        # 1. Run geological simulator
        simulator = GeologicalSimulator(config)
        logs = simulator.simulate()

        # 2. Process features through data pipeline
        pipeline = DataPipeline(logs)
        processed_df = pipeline.process()

        # 3. Validate processed data
        pipeline.validate()

        # 4. Export files (CSV, JSON, Parquet)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        prefix = f"sim_{timestamp}"

        # Save to datasets/simulations folder
        export_paths = pipeline.export(SIMULATIONS_DIR, prefix)

        # 5. Build summary details to return
        return {
            "status": "success",
            "dataset_name": prefix,
            "total_depth": config.total_depth,
            "interval": config.interval,
            "records_count": len(processed_df),
            "files": {
                "csv": os.path.basename(export_paths["csv"]),
                "json": os.path.basename(export_paths["json"]),
                "parquet": os.path.basename(export_paths["parquet"]),
            },
            "data": processed_df.to_dict(orient="records")
        }
    except Exception as e:
        logger.error(f"Failed to generate synthetic dataset: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation execution failed: {str(e)}"
        ) from e


@router.get("/datasets")
async def list_datasets() -> list[dict[str, Any]]:
    """
    Lists all available generated simulation datasets.
    """
    logger.info("Scanning simulations directory for datasets.")
    if not os.path.exists(SIMULATIONS_DIR):
        return []

    datasets = []
    try:
        for file in os.listdir(SIMULATIONS_DIR):
            if file.endswith(".json"):
                prefix = file[:-5]
                json_path = os.path.join(SIMULATIONS_DIR, file)
                stat = os.stat(json_path)

                # Check for sibling CSV and Parquet files
                has_csv = os.path.exists(os.path.join(SIMULATIONS_DIR, f"{prefix}.csv"))
                has_parquet = os.path.exists(os.path.join(SIMULATIONS_DIR, f"{prefix}.parquet"))

                # Read a brief metadata summary or records count from file name / size
                datasets.append({
                    "dataset_name": prefix,
                    "created_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                    "size_bytes": stat.st_size,
                    "has_csv": has_csv,
                    "has_json": True,
                    "has_parquet": has_parquet,
                })

        # Sort by creation time descending
        datasets.sort(key=lambda x: x["created_at"], reverse=True)
        return datasets
    except Exception as e:
        logger.error(f"Failed to list datasets: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read datasets list: {str(e)}"
        ) from e


@router.get("/datasets/{filename}")
async def get_dataset(filename: str) -> list[dict[str, Any]]:
    """
    Retrieves the raw records for a specific simulation dataset.
    """
    logger.info(f"Retrieving dataset records for: {filename}")

    # Strip extension if provided to prevent directory traversal
    clean_prefix = re.sub(r"\.(json|csv|parquet)$", "", filename)
    json_path = os.path.join(SIMULATIONS_DIR, f"{clean_prefix}.json")

    if not os.path.exists(json_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{clean_prefix}' not found."
        )

    try:
        # Load and parse the JSON file
        import json
        with open(json_path) as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Failed to load dataset records: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse dataset file: {str(e)}"
        ) from e


@router.get("/datasets/{filename}/download")
async def download_dataset(
    filename: str,
    format: str = Query("csv", regex="^(csv|json|parquet)$")
) -> FileResponse:
    """
    Downloads the simulation dataset in the requested format (CSV, JSON, or Parquet).
    """
    logger.info(f"Downloading dataset {filename} in format: {format}")

    clean_prefix = re.sub(r"\.(json|csv|parquet)$", "", filename)
    target_path = os.path.join(SIMULATIONS_DIR, f"{clean_prefix}.{format}")

    if not os.path.exists(target_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset file '{clean_prefix}.{format}' not found."
        )

    media_types = {
        "csv": "text/csv",
        "json": "application/json",
        "parquet": "application/octet-stream"
    }

    return FileResponse(
        path=target_path,
        media_type=media_types[format],
        filename=f"{clean_prefix}.{format}"
    )
