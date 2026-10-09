"""Unit tests for Phase 1 Data Architecture and Simulation Pipeline."""
import networkx as nx
import pytest

from src.config import DataProvenance, HazardType, RoadStatus, RoadType
from src.schemas import (
    CrowdsourcedReport,
    Envelope,
    HistoricalHazardLog,
    RainfallMeasurement,
    RiverGaugeMeasurement,
    RoadSegment,
    Settlement,
)
from src.spatial_builder import (
    build_road_graph,
    generate_district_data,
    roads_to_geodataframe,
)
from src.stream_generators import (
    crowdsourced_report_stream_generator,
    load_historical_hazard_logs,
    rainfall_stream_generator,
    river_gauge_stream_generator,
)


def test_settlements_count_and_attributes():
    """Verify that district data generates exactly 10 settlements with valid spatial attributes."""
    gdf = generate_district_data()
    assert len(gdf) == 10, f"Expected 10 settlements, got {len(gdf)}"

    # Check required columns
    expected_cols = {"id", "name", "latitude", "longitude", "population", "elevation_m", "slope_deg", "geometry"}
    assert expected_cols.issubset(set(gdf.columns))

    # Verify coordinate boundaries (Central Himalayas cluster)
    assert (gdf["latitude"] >= 27.5).all() and (gdf["latitude"] <= 28.5).all()
    assert (gdf["longitude"] >= 85.0).all() and (gdf["longitude"] <= 86.0).all()

    # Elevation & slope ranges
    assert (gdf["elevation_m"] >= 500).all() and (gdf["elevation_m"] <= 3500).all()
    assert (gdf["slope_deg"] >= 5).all() and (gdf["slope_deg"] <= 45).all()


def test_road_network_graph_connectivity():
    """Verify that the generated road network is fully connected (single component) across all 10 nodes."""
    gdf = generate_district_data()
    graph = build_road_graph(gdf)

    assert graph.number_of_nodes() == 10
    assert nx.is_connected(graph), "Road network graph is disconnected! All settlements must be reachable."

    # Validate road segment schema on each edge
    for u, v, data in graph.edges(data=True):
        segment = RoadSegment(
            source_id=data["source_id"],
            target_id=data["target_id"],
            road_type=RoadType(data["road_type"]),
            length_km=data["length_km"],
            status=RoadStatus(data["status"]),
            max_speed_kmh=data["max_speed_kmh"],
        )
        assert segment.length_km > 0.0
        assert segment.max_speed_kmh > 0.0


def test_road_network_status_distribution():
    """Verify that road network statuses contain ACCESSIBLE as well as disrupted segments."""
    gdf = generate_district_data()
    graph = build_road_graph(gdf)
    statuses = [data["status"] for _, _, data in graph.edges(data=True)]

    accessible_count = statuses.count(RoadStatus.ACCESSIBLE.value)
    disrupted_count = (
        statuses.count(RoadStatus.PARTIALLY_BLOCKED.value)
        + statuses.count(RoadStatus.IMPASSABLE.value)
    )

    total = len(statuses)
    assert accessible_count > 0
    assert disrupted_count > 0
    assert accessible_count / total >= 0.70  # Approximately 80% accessible


def test_streaming_rainfall_generator_provenance():
    """Verify rainfall telemetry stream generates 10 readings per tick with SIMULATED provenance."""
    gdf = generate_district_data()
    settlement_ids = list(gdf["id"])
    gen = rainfall_stream_generator(settlement_ids)

    batch = next(gen)
    assert len(batch) == 10

    for envelope in batch:
        assert isinstance(envelope, Envelope)
        assert envelope.provenance == DataProvenance.SIMULATED
        assert envelope.provenance.value == "SIMULATED"
        assert isinstance(envelope.payload, RainfallMeasurement)
        assert envelope.payload.intensity_mm_hr >= 0.0


def test_streaming_river_gauge_provenance():
    """Verify river gauge generator emits 3 stations with SIMULATED provenance."""
    gen = river_gauge_stream_generator()
    batch = next(gen)
    assert len(batch) == 3

    for envelope in batch:
        assert isinstance(envelope, Envelope)
        assert envelope.provenance == DataProvenance.SIMULATED
        assert envelope.provenance.value == "SIMULATED"
        assert isinstance(envelope.payload, RiverGaugeMeasurement)
        assert envelope.payload.level_meters > 0.0
        assert envelope.payload.flood_threshold_meters > 0.0


def test_historical_hazard_logs_provenance_and_count():
    """Verify 25 historical logs are created with valid dates, severities and SIMULATED provenance."""
    logs = load_historical_hazard_logs(25)
    assert len(logs) == 25

    for envelope in logs:
        assert isinstance(envelope, Envelope)
        assert envelope.provenance == DataProvenance.SIMULATED
        assert envelope.provenance.value == "SIMULATED"
        assert isinstance(envelope.payload, HistoricalHazardLog)
        assert 1 <= envelope.payload.severity_index <= 5
        assert envelope.payload.hazard_type in list(HazardType)


def test_crowdsourced_report_stream_provenance():
    """Verify citizen crowdsourced reports generator emits reports with SIMULATED provenance."""
    gen = crowdsourced_report_stream_generator()
    for _ in range(5):
        envelope = next(gen)
        assert isinstance(envelope, Envelope)
        assert envelope.provenance == DataProvenance.SIMULATED
        assert envelope.provenance.value == "SIMULATED"
        assert isinstance(envelope.payload, CrowdsourcedReport)
        assert 0.0 <= envelope.payload.user_reliability_score <= 1.0
        assert len(envelope.payload.description) > 0


def test_roads_to_geodataframe_export():
    """Verify road graph to GeoDataFrame conversion produces valid LineString geometries and CRS."""
    gdf = generate_district_data()
    graph = build_road_graph(gdf)
    roads_gdf = roads_to_geodataframe(graph)

    assert len(roads_gdf) == graph.number_of_edges()
    assert roads_gdf.crs == "EPSG:4326"
    assert (roads_gdf.geometry.geom_type == "LineString").all()
