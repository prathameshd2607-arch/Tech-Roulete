"""Hazard-aware dynamic pathfinding module with risk penalties and safety thresholds."""
import math
from typing import Any, Dict, List, Optional
import networkx as nx

from src.config import RoadStatus


def find_disaster_aware_route(
    graph: nx.Graph,
    source_id: str,
    target_id: str,
    max_acceptable_risk: float = 0.80,
) -> Dict[str, Any]:
    """
    Compute optimal disaster-aware path between source and target settlements.
    Eliminates IMPASSABLE / high-hazard edges (risk > max_acceptable_risk) and solves
    minimum risk-weighted effective travel time using Dijkstra's algorithm.

    Returns:
      Dict with path, total_distance_km, total_time_minutes, max_risk_encountered, status.
    """
    empty_result = {
        "path": [],
        "total_distance_km": 0.0,
        "total_time_minutes": 0.0,
        "max_risk_encountered": 0.0,
        "status": "NO_PATH_FOUND",
        "segment_breakdown": [],
    }

    if source_id not in graph or target_id not in graph:
        return empty_result

    if source_id == target_id:
        return {
            "path": [source_id],
            "total_distance_km": 0.0,
            "total_time_minutes": 0.0,
            "max_risk_encountered": 0.0,
            "status": "SUCCESS",
            "segment_breakdown": [],
        }

    # Construct safe navigable subgraph
    safe_graph = nx.Graph()

    # Copy nodes
    for node, data in graph.nodes(data=True):
        safe_graph.add_node(node, **data)

    # Filter edges based on status, risk thresholds, and finite effective cost
    for u, v, data in graph.edges(data=True):
        status = data.get("status", RoadStatus.ACCESSIBLE.value)
        risk_score = float(data.get("risk_score", 0.0))
        effective_cost = float(data.get("effective_cost", data.get("length_km", 1.0)))

        # Edge must not be IMPASSABLE, must not exceed acceptable risk, and must have finite cost
        if (
            status != RoadStatus.IMPASSABLE.value
            and risk_score <= max_acceptable_risk
            and not math.isinf(effective_cost)
            and effective_cost > 0.0
        ):
            safe_graph.add_edge(u, v, **data)

    # Check connectivity between endpoints in safe subgraph
    if not nx.has_path(safe_graph, source_id, target_id):
        return empty_result

    try:
        path = nx.dijkstra_path(safe_graph, source_id, target_id, weight="effective_cost")
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return empty_result

    # Compute path statistics
    total_distance_km = 0.0
    total_effective_time_min = 0.0
    max_risk_encountered = 0.0
    segment_breakdown = []

    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        edge_data = safe_graph[u][v]

        dist = float(edge_data.get("length_km", 0.0))
        eff_time = float(edge_data.get("effective_cost", 0.0))
        risk = float(edge_data.get("risk_score", 0.0))
        status = edge_data.get("status", RoadStatus.ACCESSIBLE.value)
        road_type = edge_data.get("road_type", "PRIMARY")

        total_distance_km += dist
        total_effective_time_min += eff_time
        max_risk_encountered = max(max_risk_encountered, risk)

        segment_breakdown.append({
            "segment": f"{u} -> {v}",
            "road_type": road_type,
            "length_km": dist,
            "effective_time_minutes": eff_time,
            "risk_score": risk,
            "status": status,
        })

    return {
        "path": path,
        "total_distance_km": round(total_distance_km, 2),
        "total_time_minutes": round(total_effective_time_min, 2),
        "max_risk_encountered": round(max_risk_encountered, 4),
        "status": "SUCCESS",
        "segment_breakdown": segment_breakdown,
    }
