"""Phase 2 Dynamic Rerouting Simulation Scenario Execution."""
from typing import Any, Dict, List
import networkx as nx

from src.graph_updater import update_graph_weights
from src.router import find_disaster_aware_route
from src.spatial_builder import build_road_graph, generate_district_data


def run_phase2_simulation(
    source_id: str = "S01",
    target_id: str = "S10",
) -> Dict[str, Any]:
    """
    Executes an end-to-end disaster rerouting simulation:
      1. Generates 10-node Himalayan district settlement graph.
      2. Initializes baseline graph edge weights under clear weather (low rainfall).
      3. Finds baseline optimal path between source_id and target_id.
      4. Injects a localized extreme torrential rain event (80mm/hr) and citizen landslide report
         blocking a critical edge on the baseline path.
      5. Triggers dynamic graph mutation (risk score escalation -> IMPASSABLE, effective cost -> inf).
      6. Recalculates disaster-aware alternative route in real time.
    """
    # 1. Instantiate Phase 1 Spatial Graph
    settlements_gdf = generate_district_data()
    graph = build_road_graph(settlements_gdf)

    # 2. Baseline initialization (normal clear weather telemetry)
    baseline_telemetry = {
        "rainfall": {sid: 5.0 for sid in graph.nodes},
        "river_gauges": [
            {"station_id": "RG-TRISHULI-01", "level_meters": 1.5, "flood_threshold_meters": 5.5},
            {"station_id": "RG-MELAMCHI-02", "level_meters": 1.2, "flood_threshold_meters": 4.0},
            {"station_id": "RG-BHOTEKOSHI-03", "level_meters": 2.0, "flood_threshold_meters": 6.8},
        ],
        "reports": [],
    }
    graph = update_graph_weights(graph, baseline_telemetry)

    # 3. Calculate initial optimal route
    initial_route = find_disaster_aware_route(
        graph,
        source_id=source_id,
        target_id=target_id,
        max_acceptable_risk=0.80,
    )

    if initial_route["status"] != "SUCCESS" or len(initial_route["path"]) < 2:
        raise RuntimeError(f"Failed to find baseline path between {source_id} and {target_id}")

    # Pick a critical edge along the initial path to simulate the disaster on
    initial_path = initial_route["path"]
    blocked_edge = (initial_path[0], initial_path[1])
    if len(initial_path) > 2:
        # Pick intermediate segment for a dramatic detour demonstration
        blocked_edge = (initial_path[1], initial_path[2])

    u_blocked, v_blocked = blocked_edge

    # 4. Inject severe hazard event (80 mm/hr torrential storm + high confidence landslide report)
    disaster_telemetry = {
        "rainfall": {
            sid: (82.5 if sid in [u_blocked, v_blocked] else 8.0)
            for sid in graph.nodes
        },
        "river_gauges": [
            {"station_id": "RG-TRISHULI-01", "level_meters": 3.8, "flood_threshold_meters": 5.5},
            {"station_id": "RG-MELAMCHI-02", "level_meters": 2.1, "flood_threshold_meters": 4.0},
            {"station_id": "RG-BHOTEKOSHI-03", "level_meters": 3.2, "flood_threshold_meters": 6.8},
        ],
        "reports": [
            {
                "report_id": "CITIZEN-REP-DISASTER-01",
                "hazard_type": "LANDSLIDE",
                "user_reliability_score": 0.96,
                "description": f"Major rockslide and debris flow completely blocking road between {u_blocked} and {v_blocked}.",
                "edge": (u_blocked, v_blocked),
            }
        ],
    }

    # 5. Mutate Graph Weights Dynamically
    graph = update_graph_weights(graph, disaster_telemetry)

    # Verify blocked edge attributes
    blocked_edge_data = graph[u_blocked][v_blocked]

    # 6. Recalculate Disaster-Aware Dynamic Route
    rerouted_route = find_disaster_aware_route(
        graph,
        source_id=source_id,
        target_id=target_id,
        max_acceptable_risk=0.80,
    )

    # 7. Package structured simulation telemetry
    return {
        "simulation_status": "COMPLETED",
        "endpoints": {
            "source": {
                "id": source_id,
                "name": graph.nodes[source_id]["name"],
                "elevation_m": graph.nodes[source_id]["elevation_m"],
            },
            "target": {
                "id": target_id,
                "name": graph.nodes[target_id]["name"],
                "elevation_m": graph.nodes[target_id]["elevation_m"],
            },
        },
        "initial_route": initial_route,
        "disaster_event": {
            "affected_edge": [u_blocked, v_blocked],
            "hazard_type": "LANDSLIDE",
            "local_rainfall_mm_hr": disaster_telemetry["rainfall"][u_blocked],
            "resulting_edge_risk_score": blocked_edge_data.get("risk_score"),
            "resulting_edge_status": blocked_edge_data.get("status"),
            "resulting_effective_cost": str(blocked_edge_data.get("effective_cost")),
        },
        "rerouted_route": rerouted_route,
        "comparison": {
            "path_changed": initial_route["path"] != rerouted_route["path"],
            "initial_path": " -> ".join(initial_route["path"]),
            "rerouted_path": " -> ".join(rerouted_route["path"]) if rerouted_route["status"] == "SUCCESS" else "NONE",
            "distance_delta_km": round(
                rerouted_route["total_distance_km"] - initial_route["total_distance_km"], 2
            ) if rerouted_route["status"] == "SUCCESS" else 0.0,
            "time_delta_minutes": round(
                rerouted_route["total_time_minutes"] - initial_route["total_time_minutes"], 2
            ) if rerouted_route["status"] == "SUCCESS" else 0.0,
            "blocked_edge_avoided": (
                (u_blocked, v_blocked) not in [
                    (rerouted_route["path"][i], rerouted_route["path"][i+1])
                    for i in range(len(rerouted_route["path"]) - 1)
                ]
                and (v_blocked, u_blocked) not in [
                    (rerouted_route["path"][i], rerouted_route["path"][i+1])
                    for i in range(len(rerouted_route["path"]) - 1)
                ]
            ) if rerouted_route["status"] == "SUCCESS" else True,
        },
    }
