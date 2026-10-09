"""Responder Role Controller: Prioritized settlements, open corridors, and field report ingestion."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel, Field

from src.router import find_disaster_aware_route
from src.services.state_manager import get_system_state

router = APIRouter(prefix="/api/responder", tags=["Responder Controller"])


class FieldReportRequest(BaseModel):
    reporter_id: str = Field(..., description="ID or callsign of the reporting responder unit")
    edge: List[str] = Field(..., description="[source_id, target_id] road segment being reported")
    hazard_type: str = Field("LANDSLIDE", description="Observed hazard (e.g. 'BRIDGE_COLLAPSE', 'LANDSLIDE', 'FLOOD')")
    description: str = Field(..., description="Detailed situation description")
    user_reliability_score: float = Field(0.95, ge=0.0, le=1.0, description="Confidence score of field unit")


@router.get("/settlements/prioritized", summary="Ranked list of affected settlements ordered by risk, vulnerability, and isolation")
def get_prioritized_settlements() -> Dict[str, Any]:
    state = get_system_state()
    graph = state.get_graph()

    prioritized_list = []

    for sid, node in graph.nodes(data=True):
        name = node.get("name", sid)
        pop = node.get("population", 5000)
        elev = node.get("elevation_m", 1000.0)
        slope = node.get("slope_deg", 15.0)

        # Evaluate connecting edges
        connected_edges = list(graph.edges(sid, data=True))
        total_connections = len(connected_edges)
        impassable_count = sum(1 for _, _, d in connected_edges if d.get("status") == "IMPASSABLE")
        partially_count = sum(1 for _, _, d in connected_edges if d.get("status") == "PARTIALLY_BLOCKED")
        accessible_count = total_connections - impassable_count - partially_count

        max_edge_risk = max((float(d.get("risk_score", 0.0)) for _, _, d in connected_edges), default=0.0)
        isolation_ratio = (impassable_count / total_connections) if total_connections > 0 else 1.0

        # Vulnerability score calculation: combination of population weight, slope risk, and isolation
        vulnerability_score = round(
            (pop / 15000.0) * 0.35 + (slope / 45.0) * 0.25 + isolation_ratio * 0.40, 4
        )

        isolation_status = "CRITICALLY_ISOLATED" if isolation_ratio >= 0.70 else (
            "PARTIALLY_ISOLATED" if isolation_ratio > 0.0 else "ACCESSIBLE"
        )

        prioritized_list.append({
            "settlement_id": sid,
            "name": name,
            "population": pop,
            "elevation_m": elev,
            "slope_deg": slope,
            "isolation_status": isolation_status,
            "isolation_ratio": round(isolation_ratio, 2),
            "max_connecting_risk": round(max_edge_risk, 4),
            "vulnerability_score": vulnerability_score,
            "access_corridors": {
                "total": total_connections,
                "open": accessible_count,
                "delayed": partially_count,
                "blocked": impassable_count,
            },
        })

    # Sort descending by vulnerability score and isolation
    prioritized_list.sort(key=lambda x: (x["vulnerability_score"], x["max_connecting_risk"]), reverse=True)

    return {
        "total_settlements": len(prioritized_list),
        "prioritized_settlements": prioritized_list,
    }


@router.get("/routes/open", summary="Fetch all currently verified open and accessible road corridors")
def get_open_routes() -> Dict[str, Any]:
    state = get_system_state()
    graph = state.get_graph()

    open_edges = []
    for u, v, data in graph.edges(data=True):
        if data.get("status") == "ACCESSIBLE":
            open_edges.append({
                "source_id": u,
                "target_id": v,
                "road_type": data.get("road_type", "PRIMARY"),
                "length_km": data.get("length_km"),
                "max_speed_kmh": data.get("max_speed_kmh"),
                "risk_score": data.get("risk_score", 0.0),
                "effective_travel_time_min": data.get("base_time_min", 0.0),
            })

    return {
        "total_open_corridors": len(open_edges),
        "open_corridors": open_edges,
    }


@router.post("/field-report", summary="Ingest ground field report triggering dynamic edge invalidation & rerouting")
def submit_field_report(report: FieldReportRequest) -> Dict[str, Any]:
    state = get_system_state()
    graph = state.get_graph()

    if len(report.edge) != 2:
        raise HTTPException(status_code=400, detail="Field 'edge' must contain [source_id, target_id]")

    u, v = report.edge[0], report.edge[1]
    if not graph.has_edge(u, v):
        raise HTTPException(status_code=404, detail=f"Road corridor between {u} and {v} does not exist.")

    telemetry_payload = {
        "reports": [
            {
                "report_id": f"FIELD-REP-{report.reporter_id}",
                "hazard_type": report.hazard_type,
                "user_reliability_score": report.user_reliability_score,
                "description": report.description,
                "edge": [u, v],
            }
        ]
    }

    new_alerts, summary = state.update_telemetry(telemetry_payload)
    updated_edge = graph[u][v]

    # Calculate alternate route for the blocked endpoints
    alternate_route = find_disaster_aware_route(
        graph=graph,
        source_id=u,
        target_id=v,
        max_acceptable_risk=0.80,
    )

    return {
        "status": "FIELD_REPORT_INGESTED",
        "reporter_id": report.reporter_id,
        "affected_edge": [u, v],
        "resulting_status": updated_edge.get("status"),
        "resulting_risk_score": updated_edge.get("risk_score"),
        "alerts_triggered": len(new_alerts),
        "new_alerts": new_alerts,
        "alternate_evacuation_route": alternate_route,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
