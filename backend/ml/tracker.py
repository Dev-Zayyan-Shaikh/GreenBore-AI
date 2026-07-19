import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from backend.ml.schema import ExperimentRun, ModelMetrics


class ExperimentTracker:
    """Logs and manages hyperparameter training runs and metadata locally."""

    def __init__(self, registry_dir: str = "datasets/model_registry") -> None:
        self.registry_dir = os.path.abspath(registry_dir)
        self.experiments_file = os.path.join(self.registry_dir, "experiments.json")
        os.makedirs(self.registry_dir, exist_ok=True)

    def log_run(
        self,
        model_type: Literal["RandomForest", "XGBoost"],
        parameters: dict[str, Any],
        metrics: ModelMetrics,
        dataset_name: str,
    ) -> ExperimentRun:
        """
        Saves a single experiment run entry to the tracker database.

        Args:
            model_type: Classifier model class name.
            parameters: Configured hyperparameters dict.
            metrics: Accuracy, precision, recall, and F1 score schema.
            dataset_name: Identifier for the training dataset.

        Returns:
            The tracked ExperimentRun record.
        """
        run = ExperimentRun(
            run_id=str(uuid.uuid4()),
            model_type=model_type,
            parameters=parameters,
            metrics=metrics,
            created_at=datetime.now(timezone.utc).isoformat(),
            dataset_name=dataset_name,
        )

        runs = self.get_runs()
        runs.append(run.model_dump())

        with open(self.experiments_file, "w") as f:
            json.dump(runs, f, indent=2)

        return run

    def get_runs(self) -> list[dict[str, Any]]:
        """Retrieves all logged runs from the tracking file."""
        if not os.path.exists(self.experiments_file):
            return []
        try:
            with open(self.experiments_file) as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                return []
        except Exception:
            return []
