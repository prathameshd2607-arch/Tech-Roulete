"""Dynamic NetworkX edge weight & status mutation engine based on real-time hazards."""
import math
from typing import Any, Dict, List, Optional
import networkx as nx

from src.config import RoadStatus
from src.risk_engine import aggregate_edge_risk


def parse_telemetry_batch(telemetry_batch: Dict[str, Any]) -> Tuple_Telemetry:
    """Parse rainfall, river gauge, reports, and overrides from various telemetry payload representations."""
    rainfall_map: Dict[str, float] = {}
    river_gauges: List[Dict[str, Any]] = []
    reports: List[Dict[str, Any]] = []
    edge_overrides: Dict[tuple, float] = {}

    # 1. Parse rainfall
    raw_rain = telemetry_batch.get("rainfall", {})
    if isinstance(raw_rain, dict):
        rainfall_map = {k: float(v) for k, v in raw_rain.items()}
    elif isinstance(raw_rain, list):
        for item in raw_rain:
            # Envelope or dict or Pydantic model
            payload = getattr(item, "payload", item)
            sid = getattr(payload, "settlement_id", None) or (payload.get("settlement_id") if isinstance(payload, dict) else None)
            intensity = getattr(payload, "intensity_mm_hr", None) or (payload.get("intensity_mm_hr") if isinstance(payload, dict) else 0.0)
            if sid:
                rainfall_map[sid] = float(intensity)

    # 2. Parse river gauges
    raw_gauges = telemetry_batch.get("river_gauges", [])
    if isinstance(raw_gauges, list):
        for item in raw_gauges:
            payload = getattr(item, "payload", item)
            if isinstance(payload, dict):
                river_gauges.append(payload)
            else:
                river_gauges.append({
                    "station_id": getattr(payload, "station_id", ""),
                    "river_name": getattr(payload, "river_name", ""),
                    "level_meters": float(getattr(payload, "level_meters", 0.0)),
                    "flood_threshold_meters": float(getattr(payload, "flood_threshold_meters", 5.0)),
                })

    # 3. Parse crowdsourced reports
    raw_reports = telemetry_batch.get("reports", [])
    if isinstance(raw_reports, list):
        for item in raw_reports:
            payload = getattr(item, "payload", item)
            if isinstance(payload, dict):
                reports.append(payload)
            else:
                reports.append({
                    "report_id": getattr(payload, "report_id", ""),
                    "hazard_type": getattr(payload, "hazard_type", ""),
                    "user_reliability_score": float(getattr(payload, "user_reliability_score", 0.8)),
                    "description": getattr(payload, "description", ""),
                    "edge": getattr(payload, "edge", None),
                    "settlement_id": getattr(payload, "settlement_id", None),
                })

    # 4. Parse edge overrides
    raw_overrides = telemetry_batch.get("edge_overrides", {})
    if isinstance(raw_overrides, dict):
        for edge_k, r_val in raw_overrides.items():
            if isinstance(edge_k, (list, tuple)) and len(edge_k) == 2:
                edge_overrides[(edge_k[0], edge_k[1])] = float(r_val)
                edge_overrides[(edge_k[1], edge_k[0])] = float(r_val)

    return rainfall_map, river_gauges, reports, edge_overrides


# Simple helper type annotation for unpack
Tuple_Telemetry = Any


def update_graph_weights(
    graph: nx.Graph,
    telemetry_batch: Optional[Dict[str, Any]] = None,
) -> nx.Graph:
    """
    Update edge attributes across the road network graph based on real-time multi-hazard telemetry.
    Computes:
      - risk_score: float [0.0, 1.0]
      - status: IMPASSABLE (if risk >= 0.85), PARTIALLY_BLOCKED (if risk >= 0.50), else ACCESSIBLE
      - effective_cost: Travel time in minutes penalty-adjusted by risk score:
                        (length_km / speed_kmh) * 60 * (1.0 + 3.0 * risk_score).
                        Set to inf if IMPASSABLE or risk >= 0.85.
    """
    telemetry_batch = telemetry_batch or {}
    rainfall_map, river_gauges, reports, edge_overrides = parse_telemetry_batch(telemetry_batch)

    for u, v, data in graph.edges(data=True):
        u_node = graph.nodes[u]
        v_node = graph.nodes[v]

        # Check explicit edge override first
        if (u, v) in edge_overrides or (v, u) in edge_overrides:
            risk_score = edge_overrides.get((u, v), edge_overrides.get((v, u)))
        else:
            risk_score = aggregate_edge_risk(
                road_segment_data=data,
                source_node_data=u_node,
                target_node_data=v_node,
                rainfall_data=rainfall_map,
                river_gauge_data=river_gauges,
                reports_data=reports,
            )

        # Determine Road Status
        if risk_score >= 0.85:
            status = RoadStatus.IMPASSABLE.value
        elif risk_score >= 0.50:
            status = RoadStatus.PARTIALLY_BLOCKED.value
        else:
            status = RoadStatus.ACCESSIBLE.value

        # Calculate Travel Time & Effective Routing Cost
        length_km = float(data.get("length_km", 10.0))
        max_speed = float(data.get("max_speed_kmh", 40.0))
        if max_speed <= 0.0:
            max_speed = 30.0

        base_time_min = (length_km / max_speed) * 60.0

        if status == RoadStatus.IMPASSABLE.value or risk_score >= 0.85:
            effective_cost = float("inf")
        else:
            effective_cost = round(base_time_min * (1.0 + 3.0 * risk_score), 3)

        # Update edge attributes
        graph[u][v]["risk_score"] = float(risk_score)
        graph[u][v]["status"] = status
        graph[u][v]["base_time_min"] = round(base_time_min, 2)
        graph[u][v]["effective_cost"] = effective_cost

    return graph
