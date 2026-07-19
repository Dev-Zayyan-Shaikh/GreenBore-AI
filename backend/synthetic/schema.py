from typing import Literal

from pydantic import BaseModel, Field


class LayerConfig(BaseModel):
    """Configuration for a specific geological stratum layer."""

    rock_type: Literal["Claystone", "Sandstone", "Limestone", "Shale", "Granite"]
    depth_start: float = Field(
        ..., ge=0.0, description="Start depth of the layer in meters"
    )
    depth_end: float = Field(
        ..., ge=0.0, description="End depth of the layer in meters"
    )
    density: float = Field(
        ..., gt=0.0, description="Mean density of the rock type in g/cm3"
    )
    porosity: float = Field(
        ..., ge=0.0, le=1.0, description="Mean porosity of the rock type"
    )
    base_resistivity: float = Field(
        ..., gt=0.0, description="Base resistivity in ohm-m"
    )
    base_gamma: float = Field(
        ..., ge=0.0, description="Base gamma radiation in API units"
    )
    base_sonic: float = Field(
        ..., gt=0.0, description="Base sonic travel time in us/ft"
    )


class FractureConfig(BaseModel):
    """Configuration for a fracture zone intersecting the borehole."""

    depth: float = Field(
        ..., ge=0.0, description="Depth of the fracture center in meters"
    )
    width: float = Field(..., gt=0.0, description="Width of the fracture in meters")
    dip_angle: float = Field(
        ..., ge=0.0, le=90.0, description="Dip angle in degrees relative to horizontal"
    )


class WaterZoneConfig(BaseModel):
    """Configuration for a water-bearing formation zone."""

    depth_start: float = Field(
        ..., ge=0.0, description="Start depth of the water zone in meters"
    )
    depth_end: float = Field(
        ..., ge=0.0, description="End depth of the water zone in meters"
    )
    flow_rate: float = Field(..., ge=0.0, description="Water flow rate index in m3/hr")
    salinity: float = Field(..., ge=0.0, description="Salinity in ppm")


class SensorNoiseConfig(BaseModel):
    """Standard deviations config for Gaussian sensor noise."""

    gamma_std: float = Field(default=0.5, ge=0.0)
    resistivity_std: float = Field(default=0.1, ge=0.0)
    porosity_std: float = Field(default=0.005, ge=0.0)
    density_std: float = Field(default=0.01, ge=0.0)
    sonic_std: float = Field(default=0.2, ge=0.0)


class SimulationConfig(BaseModel):
    """Full execution config for the synthetic borehole simulation."""

    total_depth: float = Field(
        100.0, gt=0.0, description="Total depth of the simulated borehole in meters"
    )
    interval: float = Field(
        0.5, gt=0.0, description="Distance step between sensor samples in meters"
    )
    layers: list[LayerConfig] = Field(default_factory=list)
    fractures: list[FractureConfig] = Field(default_factory=list)
    water_zones: list[WaterZoneConfig] = Field(default_factory=list)
    noise: SensorNoiseConfig = Field(default_factory=lambda: SensorNoiseConfig())
