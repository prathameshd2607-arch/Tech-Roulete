"""Real-time telemetry and citizen report ingestion endpoint."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from fastapi import APIRouter, BackgroundTasks, Body
from pydantic import BaseModel, Field

from src.api.websocket_manager import ws_manager
from src.services.state_manager import get_system_state

router = APIRouter(prefix="/api/v1/telemetry", tags=["Telemetry Ingestion"])


class TelemetryIngestPayload(BaseModel):
    provenance: Optional[str] = Field("SIMULATED", description="Data provenance (LIVE, HISTORICAL, SIMULATED)")
    rainfall: Optional[Dict[str, float]] = Field(default_factory=dict, description="Settlement ID -> rainfall mm/hr")
    river_gauges: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="List of river gauge readings")
    reports: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Citizen incident observations")
    edge_overrides: Optional[Dict[str, float]] = Field(default_factory=dict, description="Direct edge risk overrides")


@router.post("/ingest", summary="Ingest real-time telemetry stream data or hazard reports")
async def ingest_telemetry(
    background_tasks: BackgroundTasks,
    payload: Dict[str, Any] = Body(...),
) -> Dict[str, Any]:
    """
    Ingest streaming weather, hydrometric, or citizen report telemetry.
    Supports either Envelope-wrapped payloads or dictionary structures with rainfall/gauges/reports.
    Dynamically recalculates risk scores, mutates graph edge states, and dispatches emergency alerts.
    """
    state = get_system_state()

    # Unwrap envelope if payload is single Envelope schema
    normalized_batch: Dict[str, Any] = {}

    if "payload" in payload and "provenance" in payload:
        inner_payload = payload["payload"]
        # Check payload type by fields
        if "intensity_mm_hr" in inner_payload and "settlement_id" in inner_payload:
            normalized_batch["rainfall"] = {
                inner_payload["settlement_id"]: float(inner_payload["intensity_mm_hr"])
            }
        elif "level_meters" in inner_payload and "station_id" in inner_payload:
            normalized_batch["river_gauges"] = [inner_payload]
        elif "user_reliability_score" in inner_payload:
            normalized_batch["reports"] = [inner_payload]
        else:
            normalized_batch = inner_payload
    else:
        normalized_batch = payload

    # Handle string-formatted edge overrides (e.g. "S01,S10" -> ("S01", "S10"))
    if "edge_overrides" in normalized_batch and isinstance(normalized_batch["edge_overrides"], dict):
        parsed_overrides = {}
        for k, v in normalized_batch["edge_overrides"].items():
            if isinstance(k, str) and "," in k:
                u, v_node = k.split(",", 1)
                parsed_overrides[(u.strip(), v_node.strip())] = float(v)
            elif isinstance(k, tuple):
                parsed_overrides[k] = float(v)
        normalized_batch["edge_overrides"] = parsed_overrides

    # Mutate state and detect alerts
    new_alerts, summary = state.update_telemetry(normalized_batch)

    # Broadcast event payload via WebSocket to active monitoring dashboards
    broadcast_msg = {
        "event_type": "TELEMETRY_INGESTED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "new_alerts": new_alerts,
    }
    background_tasks.add_task(ws_manager.broadcast, broadcast_msg)

    return {
        "status": "INGESTED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "alerts_triggered": len(new_alerts),
        "alerts": new_alerts,
        "network_summary": summary,
    }
