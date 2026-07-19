import random
from typing import Any

from backend.synthetic.schema import SimulationConfig


class GeologicalSimulator:
    """
    Simulation engine for generating synthetic borehole logs based on strata,
    fractures, water-bearing zones, and configurable sensor noise.
    """

    def __init__(self, config: SimulationConfig) -> None:
        self.config = config

    def simulate(self) -> list[dict[str, Any]]:
        """
        Executes the geological simulation, running from depth 0 to config.total_depth
        using config.interval steps.

        Returns:
            A list of dictionaries representing the telemetry logs at each step.
        """
        logs: list[dict[str, Any]] = []
        depths = self._generate_depth_steps()

        for depth in depths:
            # 1. Base Stratum Parameters
            layer = self._get_active_layer(depth)
            if layer:
                rock_type = layer.rock_type
                density = layer.density
                porosity = layer.porosity
                resistivity = layer.base_resistivity
                gamma = layer.base_gamma
                sonic = layer.base_sonic
            else:
                # Default fallback stratum (Claystone properties)
                rock_type = "Claystone"
                density = 2.2
                porosity = 0.25
                resistivity = 10.0
                gamma = 80.0
                sonic = 120.0

            # 2. Fracture Effects (Secondary porosity, lower resistivity,
            # slower sonic travel time)
            is_fractured = False
            for fracture in self.config.fractures:
                half_width = fracture.width / 2.0
                if abs(depth - fracture.depth) <= half_width:
                    is_fractured = True
                    # Intensity index decreases towards the edges of the fracture zone
                    proximity = 1.0 - (abs(depth - fracture.depth) / half_width)

                    # Adjust parameters
                    porosity += 0.08 * proximity
                    resistivity *= 1.0 - 0.7 * proximity
                    sonic *= 1.0 + 0.3 * proximity
                    density -= 0.15 * proximity

            # 3. Water-bearing Zone Effects
            has_water = False
            for zone in self.config.water_zones:
                if zone.depth_start <= depth <= zone.depth_end:
                    has_water = True
                    # Scale effects based on salinity and flow rate
                    salinity_factor = max(0.1, 1.0 - (zone.salinity / 50000.0))
                    flow_factor = min(2.0, zone.flow_rate / 5.0)

                    # Adjust physical variables
                    porosity += 0.12 * flow_factor
                    resistivity *= 0.15 * salinity_factor
                    sonic *= 1.15
                    density -= 0.08 * flow_factor

            # 4. Apply Physical Constraints (Clamping values to realistic intervals)
            porosity = max(0.01, min(0.60, porosity))
            density = max(1.2, min(3.5, density))
            resistivity = max(0.01, min(10000.0, resistivity))
            gamma = max(0.0, gamma)
            sonic = max(40.0, sonic)

            # 5. Apply Configurable Gaussian Sensor Noise
            gamma += random.gauss(0.0, self.config.noise.gamma_std)
            resistivity += random.gauss(0.0, self.config.noise.resistivity_std)
            porosity += random.gauss(0.0, self.config.noise.porosity_std)
            density += random.gauss(0.0, self.config.noise.density_std)
            sonic += random.gauss(0.0, self.config.noise.sonic_std)

            # Re-clamp after adding noise
            porosity = max(0.001, min(0.70, porosity))
            density = max(1.0, min(4.0, density))
            resistivity = max(0.001, min(20000.0, resistivity))
            gamma = max(0.0, gamma)
            sonic = max(30.0, sonic)

            logs.append(
                {
                    "depth": round(depth, 2),
                    "rock_type": rock_type,
                    "density": round(density, 3),
                    "porosity": round(porosity, 4),
                    "resistivity": round(resistivity, 3),
                    "gamma_ray": round(gamma, 2),
                    "sonic_travel_time": round(sonic, 2),
                    "has_water": has_water,
                    "is_fractured": is_fractured,
                }
            )

        return logs

    def _generate_depth_steps(self) -> list[float]:
        """Generates continuous depth intervals from 0.0 to total_depth."""
        steps = []
        current = 0.0
        while current <= self.config.total_depth:
            steps.append(current)
            current += self.config.interval
        return steps

    def _get_active_layer(self, depth: float) -> Any:
        """Finds the LayerConfig encompassing the active depth step."""
        for layer in self.config.layers:
            if layer.depth_start <= depth < layer.depth_end:
                return layer
        # Check edge boundary for the exact end depth
        if len(self.config.layers) > 0 and depth == self.config.total_depth:
            return self.config.layers[-1]
        return None
