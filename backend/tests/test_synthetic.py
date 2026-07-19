import os
import tempfile

import pandas as pd  # type: ignore[import-untyped]
import pytest
from backend.synthetic import (
    DataPipeline,
    FractureConfig,
    GeologicalSimulator,
    LayerConfig,
    SensorNoiseConfig,
    SimulationConfig,
    WaterZoneConfig,
)


@pytest.fixture
def sample_config() -> SimulationConfig:
    """Fixture containing a validated SimulationConfig."""
    return SimulationConfig(
        total_depth=10.0,
        interval=1.0,
        layers=[
            LayerConfig(
                rock_type="Sandstone",
                depth_start=0.0,
                depth_end=5.0,
                density=2.3,
                porosity=0.2,
                base_resistivity=100.0,
                base_gamma=40.0,
                base_sonic=85.0,
            ),
            LayerConfig(
                rock_type="Limestone",
                depth_start=5.0,
                depth_end=10.0,
                density=2.7,
                porosity=0.1,
                base_resistivity=500.0,
                base_gamma=20.0,
                base_sonic=55.0,
            ),
        ],
        fractures=[
            FractureConfig(depth=3.0, width=0.4, dip_angle=45.0),
        ],
        water_zones=[
            WaterZoneConfig(
                depth_start=6.0, depth_end=8.0, flow_rate=3.0, salinity=2000.0
            ),
        ],
        noise=SensorNoiseConfig(
            gamma_std=0.1,
            resistivity_std=0.01,
            porosity_std=0.001,
            density_std=0.001,
            sonic_std=0.05,
        ),
    )


def test_simulation_execution(sample_config: SimulationConfig) -> None:
    """Tests that the simulator runs and outputs expected attributes."""
    simulator = GeologicalSimulator(sample_config)
    logs = simulator.simulate()

    # 10m depth with 1m interval should yield 11 steps (0 to 10 inclusive)
    assert len(logs) == 11

    # Assert check schemas on first item
    first_step = logs[0]
    expected_keys = {
        "depth",
        "rock_type",
        "density",
        "porosity",
        "resistivity",
        "gamma_ray",
        "sonic_travel_time",
        "has_water",
        "is_fractured",
    }
    assert expected_keys.issubset(first_step.keys())
    assert first_step["rock_type"] == "Sandstone"
    assert first_step["depth"] == 0.0


def test_simulation_fracture_effects(sample_config: SimulationConfig) -> None:
    """Verifies that fractures introduce structural physical modifications."""
    simulator = GeologicalSimulator(sample_config)
    logs = simulator.simulate()

    # Depth 3.0 has a fracture center
    fracture_log = next(log for log in logs if log["depth"] == 3.0)
    assert fracture_log["is_fractured"] is True

    # Depth 0.0 is unfractured sandstone
    base_log = next(log for log in logs if log["depth"] == 0.0)
    assert base_log["is_fractured"] is False

    # Porosity should increase and resistivity should decrease relative to
    # base layer config
    assert fracture_log["porosity"] > sample_config.layers[0].porosity


def test_simulation_water_effects(sample_config: SimulationConfig) -> None:
    """Verifies water presence is correctly labeled and affects properties."""
    simulator = GeologicalSimulator(sample_config)
    logs = simulator.simulate()

    # Depth 7.0 is inside the water zone (6.0 to 8.0)
    water_log = next(log for log in logs if log["depth"] == 7.0)
    assert water_log["has_water"] is True

    # Depth 0.0 is outside the water zone
    dry_log = next(log for log in logs if log["depth"] == 0.0)
    assert dry_log["has_water"] is False


def test_pipeline_feature_engineering(sample_config: SimulationConfig) -> None:
    """Verifies that the data pipeline processes rolling means and ratios."""
    simulator = GeologicalSimulator(sample_config)
    logs = simulator.simulate()

    pipeline = DataPipeline(logs)
    df = pipeline.process()

    # Verify column presence
    assert "gamma_ray_ma5" in df.columns
    assert "porosity_resistivity_ratio" in df.columns
    assert "density_porosity_ratio" in df.columns
    assert "rock_type_encoded" in df.columns

    # Verify categorical mapping (Sandstone -> 1)
    assert df.loc[df["depth"] == 0.0, "rock_type_encoded"].values[0] == 1


def test_pipeline_validation_success(sample_config: SimulationConfig) -> None:
    """Tests that a standard valid simulation log passes the validation check."""
    simulator = GeologicalSimulator(sample_config)
    logs = simulator.simulate()

    pipeline = DataPipeline(logs)
    pipeline.process()
    assert pipeline.validate() is True


def test_pipeline_validation_failures() -> None:
    """Tests validation constraints trigger ValueError on invalid data."""
    # 1. Empty dataset validation
    pipeline_empty = DataPipeline([])
    with pytest.raises(ValueError, match="Dataset is empty"):
        pipeline_empty.validate()

    # 2. Missing columns
    invalid_data = [{"depth": 1.0, "rock_type": "Claystone"}]
    pipeline_invalid = DataPipeline(invalid_data)
    with pytest.raises(ValueError, match="Validation failed: missing header"):
        pipeline_invalid.validate()

    # 3. Out-of-bounds density
    out_of_bounds_density = [
        {
            "depth": 1.0,
            "rock_type": "Sandstone",
            "density": 5.0,  # exceeds upper physical bound (4.0)
            "porosity": 0.2,
            "resistivity": 50.0,
            "gamma_ray": 30.0,
            "sonic_travel_time": 80.0,
            "has_water": False,
            "is_fractured": False,
            "gamma_ray_ma5": 30.0,
            "resistivity_ma5": 50.0,
            "porosity_ma5": 0.2,
            "density_ma5": 5.0,
            "sonic_travel_time_ma5": 80.0,
            "porosity_resistivity_ratio": 0.004,
            "density_porosity_ratio": 25.0,
            "rock_type_encoded": 1,
        }
    ]
    pipeline_density_fail = DataPipeline(out_of_bounds_density)
    with pytest.raises(ValueError, match="density outside boundary"):
        pipeline_density_fail.validate()


def test_pipeline_export(sample_config: SimulationConfig) -> None:
    """Verifies that the export routine writes valid CSV, JSON, and Parquet."""
    simulator = GeologicalSimulator(sample_config)
    logs = simulator.simulate()

    pipeline = DataPipeline(logs)
    pipeline.process()
    pipeline.validate()

    with tempfile.TemporaryDirectory() as tmpdir:
        prefix = "borehole_test"
        paths = pipeline.export(tmpdir, prefix)

        # Check files exist
        assert os.path.exists(paths["csv"])
        assert os.path.exists(paths["json"])
        assert os.path.exists(paths["parquet"])

        # Check readability of exported formats
        df_csv = pd.read_csv(paths["csv"])
        df_parquet = pd.read_parquet(paths["parquet"])
        assert len(df_csv) == len(df_parquet) == 11
        assert list(df_csv.columns) == list(df_parquet.columns)
