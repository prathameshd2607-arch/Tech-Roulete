"""Unit tests for Phase 2 Risk Assessment Engine and Dynamic Routing Optimization."""
import math
import networkx as nx
import pytest

from src.config import RoadStatus, RoadType
from src.graph_updater import update_graph_weights
from src.risk_engine import (
    aggregate_edge_risk,
    calculate_flood_risk,
    calculate_landslide_risk,
)
from src.router import find_disaster_aware_route
from src.simulation_phase2 import run_phase2_simulation
from src.spatial_builder import build_road_graph, generate_district_data


def test_landslide_risk_bounds_and_dynamics():
    """Test calculate_landslide_risk for strict [0.0, 1.0] bounds and monotonic risk increase."""
    # Flat slope, zero rain
    low_risk = calculate_landslide_risk(slope_deg=5.0, rainfall_mm_hr=0.0)
    assert 0.0 <= low_risk <= 0.25

    # Moderate conditions
    mod_risk = calculate_landslide_risk(slope_deg=20.0, rainfall_mm_hr=25.0)
    assert 0.0 <= mod_risk <= 1.0
    assert mod_risk > low_risk

    # Extreme conditions: steep slope > 25 deg and intense rain > 30 mm/hr
    high_risk = calculate_landslide_risk(slope_deg=38.0, rainfall_mm_hr=75.0)
    assert high_risk >= 0.70
    assert high_risk <= 1.0

    # Ground report confirmation boost
    confirmed_risk = calculate_landslide_risk(slope_deg=38.0, rainfall_mm_hr=75.0, report_confidence=0.95)
    assert confirmed_risk >= high_risk
    assert confirmed_risk <= 1.0


def test_flood_risk_bounds_and_dynamics():
    """Test calculate_flood_risk for [0.0, 1.0] bounds and elevation/threshold sensitivity."""
    # Safe stage level in high elevation hamlet
    safe_risk = calculate_flood_risk(river_level_m=1.0, threshold_m=5.0, elevation_m=2800.0)
    assert 0.0 <= safe_risk <= 0.15

    # Overflowing river in low valley basin (<1000m)
    overflow_risk = calculate_flood_risk(river_level_m=6.5, threshold_m=4.5, elevation_m=650.0)
    assert overflow_risk >= 0.60
    assert overflow_risk <= 1.0


def test_edge_risk_aggregation():
    """Test aggregate_edge_risk with combined telemetry."""
    road_data = {"source_id": "S01", "target_id": "S02", "road_type": "PRIMARY"}
    src_node = {"slope_deg": 35.0, "elevation_m": 800.0}
    tgt_node = {"slope_deg": 32.0, "elevation_m": 850.0}

    rainfall = {"S01": 80.0, "S02": 75.0}
    reports = [{"settlement_id": "S01", "user_reliability_score": 0.90, "hazard_type": "LANDSLIDE"}]

    risk = aggregate_edge_risk(road_data, src_node, tgt_node, rainfall_data=rainfall, reports_data=reports)
    assert 0.0 <= risk <= 1.0
    assert risk >= 0.75  # High risk expected under torrential rain on steep terrain


def test_graph_updater_impassable_transition():
    """Test that edge with risk >= 0.85 transitions to IMPASSABLE with infinite effective_cost."""
    gdf = generate_district_data()
    graph = build_road_graph(gdf)

    u, v = list(graph.edges())[0]

    # Explicit override to risk 0.92
    telemetry = {
        "edge_overrides": {(u, v): 0.92}
    }

    updated_graph = update_graph_weights(graph, telemetry)
    edge_data = updated_graph[u][v]

    assert edge_data["risk_score"] == 0.92
    assert edge_data["status"] == RoadStatus.IMPASSABLE.value
    assert math.isinf(edge_data["effective_cost"])


def test_graph_updater_partially_blocked_transition():
    """Test that edge with 0.50 <= risk < 0.85 transitions to PARTIALLY_BLOCKED with penalty cost."""
    gdf = generate_district_data()
    graph = build_road_graph(gdf)

    u, v = list(graph.edges())[0]

    telemetry = {
        "edge_overrides": {(u, v): 0.60}
    }

    updated_graph = update_graph_weights(graph, telemetry)
    edge_data = updated_graph[u][v]

    assert edge_data["risk_score"] == 0.60
    assert edge_data["status"] == RoadStatus.PARTIALLY_BLOCKED.value
    assert not math.isinf(edge_data["effective_cost"])
    assert edge_data["effective_cost"] > edge_data["base_time_min"]


def test_router_never_uses_impassable_edges():
    """Verify that find_disaster_aware_route never traverses an IMPASSABLE edge or risk > max_acceptable_risk."""
    gdf = generate_district_data()
    graph = build_road_graph(gdf)

    # Initialize graph with safe weights
    graph = update_graph_weights(graph, {"rainfall": {sid: 5.0 for sid in graph.nodes}})

    # Find initial path
    initial = find_disaster_aware_route(graph, "S01", "S10", max_acceptable_risk=0.80)
    assert initial["status"] == "SUCCESS"
    assert len(initial["path"]) >= 2

    # Block the first edge along this path
    u, v = initial["path"][0], initial["path"][1]
    graph = update_graph_weights(graph, {"edge_overrides": {(u, v): 0.95}})

    # Reroute
    rerouted = find_disaster_aware_route(graph, "S01", "S10", max_acceptable_risk=0.80)

    if rerouted["status"] == "SUCCESS":
        rerouted_edges = [
            (rerouted["path"][i], rerouted["path"][i + 1])
            for i in range(len(rerouted["path"]) - 1)
        ]
        assert (u, v) not in rerouted_edges
        assert (v, u) not in rerouted_edges
        assert rerouted["max_risk_encountered"] <= 0.80


def test_dynamic_rerouting_simulation_execution():
    """End-to-end test of Phase 2 simulation scenario."""
    result = run_phase2_simulation(source_id="S01", target_id="S10")

    assert result["simulation_status"] == "COMPLETED"
    assert result["initial_route"]["status"] == "SUCCESS"
    assert result["disaster_event"]["resulting_edge_status"] == RoadStatus.IMPASSABLE.value
    assert result["comparison"]["blocked_edge_avoided"] is True
    if result["rerouted_route"]["status"] == "SUCCESS":
        assert result["comparison"]["path_changed"] is True
