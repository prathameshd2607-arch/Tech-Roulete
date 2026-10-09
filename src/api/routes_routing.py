"""Routing and network topology inspection endpoints."""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.router import find_disaster_aware_route
from src.services.state_manager import get_system_state

router = APIRouter(prefix="/api/v1", tags=["Routing & Network"])


class RouteRequest(BaseModel):
    source: str = Field(..., description="Origin settlement ID (e.g. 'S01' or 'SETTLE_001')")
    target: str = Field(..., description="Destination settlement ID (e.g. 'S10' or 'SETTLE_010')")
    max_risk: Optional[float] = Field(0.80, ge=0.0, le=1.0, description="Maximum acceptable edge risk threshold")


def normalize_node_id(graph_nodes: List[str], raw_id: str) -> str:
    """Normalize node IDs like 'SETTLE_001', 'SETTLE_1', 's01', 'S01' to canonical graph node ID."""
    clean_id = raw_id.strip()
    if clean_id in graph_nodes:
        return clean_id

    upper_id = clean_id.upper()
    if upper_id in graph_nodes:
        return upper_id

    # Handle SETTLE_001 or SETTLE_1 -> S01
    if upper_id.startswith("SETTLE_"):
        suffix = upper_id.replace("SETTLE_", "").lstrip("0") or "0"
        try:
            num = int(suffix)
            s_candidate = f"S{num:02d}"
            if s_candidate in graph_nodes:
                return s_candidate
        except ValueError:
            pass

    return clean_id


@router.post("/route", summary="Calculate optimal disaster-aware evacuation or supply route")
def calculate_route(request: RouteRequest) -> Dict[str, Any]:
    state = get_system_state()
    graph = state.get_graph()
    nodes = list(graph.nodes)

    src_norm = normalize_node_id(nodes, request.source)
    tgt_norm = normalize_node_id(nodes, request.target)

    if src_norm not in nodes:
        raise HTTPException(
            status_code=404,
            detail=f"Source settlement '{request.source}' not found in active graph. Available: {nodes}",
        )
    if tgt_norm not in nodes:
        raise HTTPException(
            status_code=404,
            detail=f"Target settlement '{request.target}' not found in active graph. Available: {nodes}",
        )

    route_res = find_disaster_aware_route(
        graph=graph,
        source_id=src_norm,
        target_id=tgt_norm,
        max_acceptable_risk=request.max_risk or 0.80,
    )

    return route_res


@router.get("/network/edges", summary="Inspect live road segments, operational statuses, and risk indices")
def get_network_edges() -> Dict[str, Any]:
    state = get_system_state()
    graph = state.get_graph()

    edges_list = []
    for u, v, data in graph.edges(data=True):
        edges_list.append({
            "source_id": u,
            "target_id": v,
            "road_type": data.get("road_type", "PRIMARY"),
            "length_km": data.get("length_km"),
            "max_speed_kmh": data.get("max_speed_kmh"),
            "risk_score": data.get("risk_score", 0.0),
            "status": data.get("status", "ACCESSIBLE"),
            "effective_cost": str(data.get("effective_cost")),
        })

    return {
        "total_edges": len(edges_list),
        "edges": edges_list,
    }


@router.get("/network/nodes", summary="List all settlements with coordinates and topography")
def get_network_nodes() -> Dict[str, Any]:
    state = get_system_state()
    graph = state.get_graph()

    nodes_list = []
    for node_id, data in graph.nodes(data=True):
        nodes_list.append({
            "id": node_id,
            "name": data.get("name"),
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "population": data.get("population"),
            "elevation_m": data.get("elevation_m"),
            "slope_deg": data.get("slope_deg"),
        })

    return {
        "total_nodes": len(nodes_list),
        "nodes": nodes_list,
    }
