"""Admin Role Controller: Scenario triggers, real-time threshold sliders, and bulk data uploads."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel, Field

from src.services.state_manager import get_system_state

router = APIRouter(prefix="/api/admin", tags=["Admin Controller"])


class ScenarioTriggerRequest(BaseModel):
    scenario_name: str = Field("Monsoon Flash Flood & Landslide", description="Name of the emergency simulation scenario")
    rainfall_mm_hr: float = Field(85.0, ge=0.0, le=500.0, description="Precipitation intensity to simulate")
    river_surge_meters: Optional[float] = Field(5.2, description="River gauge level stage height")
    target_settlements: Optional[List[str]] = Field(default=None, description="Specific settlements to target, or None for all")


class RainfallSliderConfig(BaseModel):
    rainfall_rate_mm_hr: Optional[float] = Field(None, ge=0.0, le=300.0, description="Global uniform rainfall rate")
    regional_zones: Optional[Dict[str, float]] = Field(default_factory=dict, description="Settlement ID -> rainfall rate")
    global_multiplier: Optional[float] = Field(1.0, ge=0.1, le=5.0, description="Multiplier applied across all zones")


class BulkDataUploadRequest(BaseModel):
    dataset_type: str = Field(..., description="Dataset classification: 'TELEMETRY_STREAM', 'HISTORICAL_LOGS', 'HAZARD_POINTS'")
    records: List[Dict[str, Any]] = Field(..., description="List of raw data dictionaries")


@router.post("/scenario/trigger", summary="Initiate system-wide disaster simulation scenario")
def trigger_scenario(request: ScenarioTriggerRequest) -> Dict[str, Any]:
    state = get_system_state()
    graph = state.get_graph()
    target_sids = request.target_settlements or list(graph.nodes)

    rainfall_map = {sid: request.rainfall_mm_hr for sid in target_sids}

    gauges = []
    if request.river_surge_meters:
        gauges = [
            {"station_id": "RG-TRISHULI-01", "river_name": "Trishuli River", "level_meters": request.river_surge_meters, "flood_threshold_meters": 5.5},
            {"station_id": "RG-MELAMCHI-02", "river_name": "Melamchi River", "level_meters": request.river_surge_meters * 0.9, "flood_threshold_meters": 4.0},
        ]

    telemetry_payload = {
        "provenance": "SIMULATED",
        "rainfall": rainfall_map,
        "river_gauges": gauges,
    }

    new_alerts, summary = state.update_telemetry(telemetry_payload)

    return {
        "status": "SCENARIO_TRIGGERED",
        "scenario_name": request.scenario_name,
        "targeted_settlements": len(target_sids),
        "alerts_generated": len(new_alerts),
        "alerts": new_alerts,
        "network_summary": summary,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/config/rainfall", summary="Adjust dynamic rainfall thresholds and zone sliders in real-time")
def adjust_rainfall_sliders(config: RainfallSliderConfig) -> Dict[str, Any]:
    state = get_system_state()
    graph = state.get_graph()

    rain_map = {}
    if config.rainfall_rate_mm_hr is not None:
        rain_map = {sid: config.rainfall_rate_mm_hr * (config.global_multiplier or 1.0) for sid in graph.nodes}

    if config.regional_zones:
        for sid, rate in config.regional_zones.items():
            rain_map[sid] = rate * (config.global_multiplier or 1.0)

    if not rain_map:
        rain_map = {sid: 10.0 * (config.global_multiplier or 1.0) for sid in graph.nodes}

    new_alerts, summary = state.update_telemetry({"rainfall": rain_map})

    return {
        "status": "CONFIG_UPDATED",
        "applied_rainfall": rain_map,
        "global_multiplier": config.global_multiplier,
        "alerts_triggered": len(new_alerts),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/ground-data/upload", summary="Bulk upload ground telemetry and geospatial hazard datasets")
def upload_ground_data(upload: BulkDataUploadRequest) -> Dict[str, Any]:
    state = get_system_state()
    records_count = len(upload.records)

    # Process batch telemetry records
    if upload.dataset_type.upper() in ["TELEMETRY_STREAM", "HAZARD_POINTS"]:
        rainfall_batch = {}
        reports_batch = []
        for rec in upload.records:
            if "settlement_id" in rec and "intensity_mm_hr" in rec:
                rainfall_batch[rec["settlement_id"]] = float(rec["intensity_mm_hr"])
            elif "hazard_type" in rec:
                reports_batch.append(rec)

        new_alerts, summary = state.update_telemetry({
            "rainfall": rainfall_batch,
            "reports": reports_batch,
        })
        return {
            "status": "UPLOAD_SUCCESS",
            "dataset_type": upload.dataset_type,
            "records_processed": records_count,
            "alerts_generated": len(new_alerts),
        }

    return {
        "status": "UPLOAD_SUCCESS",
        "dataset_type": upload.dataset_type,
        "records_processed": records_count,
        "message": f"Successfully ingested {records_count} records for {upload.dataset_type}.",
    }
