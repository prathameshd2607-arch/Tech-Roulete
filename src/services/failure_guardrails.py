"""Failure Guardrails Engine for physical boundary validation and spatial neighbor anomaly suppression."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
import networkx as nx
from pydantic import BaseModel, Field


class SensorValidationResult(BaseModel):
    sensor_id: str = Field(..., description="Unique sensor identifier")
    settlement_id: Optional[str] = Field(None, description="Associated settlement node identifier")
    original_value: float = Field(..., description="Raw received sensor measurement")
    sanitized_value: float = Field(..., description="Validated and bounded measurement")
    status: str = Field(..., description="'VALID', 'PHYSICAL_LIMIT_EXCEEDED', or 'SPATIAL_ANOMALY_SUPPRESSED'")
    is_valid: bool = Field(..., description="Whether the raw measurement passed validation unchanged")
    message: str = Field(..., description="Validation audit explanation")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FailureGuardrailEngine:
    """
    Real-time safety guardrail protecting the AI routing engine against:
      1. Physical sensor glitches (e.g., impossible 500 mm/hr hardware short circuits).
      2. Isolated sensor spikes diverging wildly from surrounding topological neighbors.
    """

    def __init__(
        self,
        max_physical_rainfall_mm_hr: float = 300.0,
        spatial_divergence_threshold_mm_hr: float = 60.0,
        spatial_divergence_ratio: float = 4.0,
    ) -> None:
        self.max_physical_rainfall = max_physical_rainfall_mm_hr
        self.spatial_divergence_threshold = spatial_divergence_threshold_mm_hr
        self.spatial_divergence_ratio = spatial_divergence_ratio

    def validate_rainfall_reading(
        self,
        sensor_id: str,
        settlement_id: Optional[str],
        value: float,
        neighbor_readings: Optional[List[float]] = None,
    ) -> SensorValidationResult:
        """
        Validate a single precipitation sensor measurement:
          1. Check absolute physical ceiling (<= 300 mm/hr).
          2. Check spatial consistency against surrounding neighbors.
        """
        neighbor_readings = [float(v) for v in (neighbor_readings or []) if v is not None and v >= 0.0]
        neighbor_mean = (sum(neighbor_readings) / len(neighbor_readings)) if neighbor_readings else None

        # 1. Physical Limit Guardrail
        if value > self.max_physical_rainfall or value < 0.0:
            if neighbor_mean is not None:
                sanitized = round(min(self.max_physical_rainfall, neighbor_mean), 2)
            else:
                sanitized = round(min(self.max_physical_rainfall, max(0.0, value)), 2)

            return SensorValidationResult(
                sensor_id=sensor_id,
                settlement_id=settlement_id,
                original_value=value,
                sanitized_value=sanitized,
                status="PHYSICAL_LIMIT_EXCEEDED",
                is_valid=False,
                message=(
                    f"Physical limit violation: Reading {value:.1f} mm/hr exceeds meteorological ceiling "
                    f"({self.max_physical_rainfall:.1f} mm/hr). Sanitized to {sanitized:.1f} mm/hr."
                ),
            )

        # 2. Spatial Neighbor Divergence Guardrail
        if neighbor_readings and len(neighbor_readings) >= 1 and neighbor_mean is not None:
            diff = value - neighbor_mean
            ratio = (value / max(1.0, neighbor_mean)) if neighbor_mean > 0 else 10.0

            # If isolated sensor reports extreme storm while all neighbors report calm/low rain
            if (
                value > 80.0
                and neighbor_mean < 30.0
                and diff >= self.spatial_divergence_threshold
                and ratio >= self.spatial_divergence_ratio
            ):
                sanitized = round(neighbor_mean, 2)
                return SensorValidationResult(
                    sensor_id=sensor_id,
                    settlement_id=settlement_id,
                    original_value=value,
                    sanitized_value=sanitized,
                    status="SPATIAL_ANOMALY_SUPPRESSED",
                    is_valid=False,
                    message=(
                        f"Spatial anomaly suppressed: Isolated spike of {value:.1f} mm/hr diverges from "
                        f"neighbor mean ({neighbor_mean:.1f} mm/hr, diff: {diff:.1f} mm/hr). Sanitized to {sanitized:.1f} mm/hr."
                    ),
                )

        # 3. Valid Reading
        return SensorValidationResult(
            sensor_id=sensor_id,
            settlement_id=settlement_id,
            original_value=value,
            sanitized_value=round(value, 2),
            status="VALID",
            is_valid=True,
            message=f"Sensor reading {value:.1f} mm/hr validated within physical and spatial thresholds.",
        )

    def validate_telemetry_batch(
        self,
        telemetry_batch: Dict[str, Any],
        graph: Optional[nx.Graph] = None,
    ) -> Tuple[Dict[str, Any], List[SensorValidationResult]]:
        """
        Validate and sanitize an entire incoming telemetry batch before passing to the risk engine.
        Cross-references graph topology neighbors if available.
        """
        sanitized_batch = dict(telemetry_batch)
        validation_results: List[SensorValidationResult] = []

        rainfall_data = telemetry_batch.get("rainfall", {})
        if isinstance(rainfall_data, dict):
            sanitized_rain = {}
            for sid, val in rainfall_data.items():
                sensor_id = f"RAIN-{sid}"
                # Find neighbor values from graph or overall batch
                neighbor_vals = []
                if graph and sid in graph:
                    neighbors = list(graph.neighbors(sid))
                    neighbor_vals = [
                        float(rainfall_data[n_id])
                        for n_id in neighbors
                        if n_id in rainfall_data and n_id != sid
                    ]
                else:
                    neighbor_vals = [float(v) for k, v in rainfall_data.items() if k != sid]

                result = self.validate_rainfall_reading(
                    sensor_id=sensor_id,
                    settlement_id=sid,
                    value=float(val),
                    neighbor_readings=neighbor_vals,
                )
                validation_results.append(result)
                sanitized_rain[sid] = result.sanitized_value

            sanitized_batch["rainfall"] = sanitized_rain

        return sanitized_batch, validation_results
