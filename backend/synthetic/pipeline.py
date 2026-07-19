import os
from typing import Any

import pandas as pd  # type: ignore[import-untyped]


class DataPipeline:
    """
    Pipeline responsible for feature engineering, schema validation,
    and exporting synthetic logs into multiple storage formats.
    """

    def __init__(self, data: list[dict[str, Any]]) -> None:
        self.df = pd.DataFrame(data)

    def process(self) -> pd.DataFrame:
        """
        Executes feature engineering steps:
        - Calculates rolling mean averages (window=5) for all sensor channels.
        - Calculates Porosity-Resistivity index and Density-Porosity ratio.
        - Encodes categorical rock types numerically.

        Returns:
            The processed pandas DataFrame.
        """
        if self.df.empty:
            return self.df

        # 1. Rolling averages (window=5 lagging, filling boundaries with min_periods=1)
        sensor_columns = [
            "gamma_ray",
            "resistivity",
            "porosity",
            "density",
            "sonic_travel_time",
        ]
        for col in sensor_columns:
            self.df[f"{col}_ma5"] = self.df[col].rolling(window=5, min_periods=1).mean()

        # 2. Advanced petrophysical ratio features
        # Add 1e-5 epsilon to prevent division-by-zero
        self.df["porosity_resistivity_ratio"] = self.df["porosity"] / (
            self.df["resistivity"] + 1e-5
        )
        self.df["density_porosity_ratio"] = self.df["density"] / (
            self.df["porosity"] + 1e-5
        )

        # 3. Categorical Rock Type Encoding
        rock_mapping = {
            "Claystone": 0,
            "Sandstone": 1,
            "Limestone": 2,
            "Shale": 3,
            "Granite": 4,
        }
        self.df["rock_type_encoded"] = self.df["rock_type"].map(rock_mapping)

        # 4. Standardize floating precision for consistency
        precision_dict = {
            "gamma_ray_ma5": 2,
            "resistivity_ma5": 3,
            "porosity_ma5": 4,
            "density_ma5": 3,
            "sonic_travel_time_ma5": 2,
            "porosity_resistivity_ratio": 4,
            "density_porosity_ratio": 3,
        }
        self.df = self.df.round(precision_dict)

        return self.df

    def validate(self) -> bool:
        """
        Runs validations against the dataset checking for structural headers,
        null presence, and physical/geological feasibility ranges.

        Raises:
            ValueError: If validation conditions are violated.

        Returns:
            True if dataset conforms to all specifications.
        """
        if self.df.empty:
            raise ValueError("Dataset is empty. Validation cannot run.")

        # Header presence validation
        required_cols = [
            "depth",
            "rock_type",
            "density",
            "porosity",
            "resistivity",
            "gamma_ray",
            "sonic_travel_time",
            "has_water",
            "is_fractured",
            "gamma_ray_ma5",
            "resistivity_ma5",
            "porosity_ma5",
            "density_ma5",
            "sonic_travel_time_ma5",
            "porosity_resistivity_ratio",
            "density_porosity_ratio",
            "rock_type_encoded",
        ]
        for col in required_cols:
            if col not in self.df.columns:
                raise ValueError(f"Validation failed: missing header '{col}'")

        # Null/Inf values validation
        if self.df.isnull().any().any():
            raise ValueError("Validation failed: dataset contains NaN values.")

        # Physical limit validations
        if (self.df["density"] < 1.0).any() or (self.df["density"] > 4.0).any():
            raise ValueError(
                "Validation failed: rock density outside boundary [1.0, 4.0]"
            )

        if (self.df["porosity"] < 0.0).any() or (self.df["porosity"] > 1.0).any():
            raise ValueError(
                "Validation failed: rock porosity outside boundary [0.0, 1.0]"
            )

        if (self.df["resistivity"] < 0.0).any():
            raise ValueError(
                "Validation failed: negative electrical resistivity value detected."
            )

        if (self.df["gamma_ray"] < 0.0).any():
            raise ValueError(
                "Validation failed: negative gamma ray measurement detected."
            )

        if (self.df["sonic_travel_time"] < 30.0).any():
            raise ValueError(
                "Validation failed: acoustic travel time below physical limit (<30)"
            )

        return True

    def export(self, base_path: str, filename_prefix: str) -> dict[str, str]:
        """
        Exports the validated dataframe into CSV, JSON, and Parquet formats.

        Args:
            base_path: Absolute directory to export output files.
            filename_prefix: Output files prefix.

        Returns:
            Dictionary with file paths of exported formats.
        """
        os.makedirs(base_path, exist_ok=True)

        csv_path = os.path.abspath(os.path.join(base_path, f"{filename_prefix}.csv"))
        json_path = os.path.abspath(os.path.join(base_path, f"{filename_prefix}.json"))
        parquet_path = os.path.abspath(
            os.path.join(base_path, f"{filename_prefix}.parquet")
        )

        # Export CSV
        self.df.to_csv(csv_path, index=False)

        # Export JSON (records format)
        self.df.to_json(json_path, orient="records", indent=2)

        # Export Parquet
        self.df.to_parquet(parquet_path, index=False)

        return {"csv": csv_path, "json": json_path, "parquet": parquet_path}
