"""Integration tests for Phase 3 FastAPI endpoints, telemetry ingestion, and alerts."""
import pytest
from fastapi.testclient import TestClient

from src.app import app
from src.services.state_manager import get_system_state


@pytest.fixture(autouse=True)
def reset_system_state():
    """Reset system state before each test run for deterministic results."""
    state = get_system_state()
    state.reset_to_baseline()
    yield
    state.reset_to_baseline()


def test_root_and_health_endpoints():
    """Verify root API discovery and health probe endpoints."""
    client = TestClient(app)

    res_root = client.get("/")
    assert res_root.status_code == 200
    data = res_root.json()
    assert data["status"] == "ONLINE"
    assert data["settlements_count"] == 10
    assert "endpoints" in data

    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json() == {"status": "healthy"}


def test_get_route_endpoint():
    """Verify /api/v1/route returns status 200 and valid JSON route payload."""
    client = TestClient(app)

    # Valid route request
    req_body = {
        "source": "S01",
        "target": "S10",
        "max_risk": 0.80,
    }
    response = client.post("/api/v1/route", json=req_body)
    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "SUCCESS"
    assert isinstance(payload["path"], list)
    assert len(payload["path"]) >= 2
    assert payload["path"][0] == "S01"
    assert payload["path"][-1] == "S10"
    assert payload["total_distance_km"] > 0.0
    assert payload["total_time_minutes"] > 0.0
    assert payload["max_risk_encountered"] <= 0.80

    # Also test settlement alias normalization (e.g. SETTLE_001 -> S01)
    req_alias = {
        "source": "SETTLE_001",
        "target": "SETTLE_010",
        "max_risk": 0.80,
    }
    res_alias = client.post("/api/v1/route", json=req_alias)
    assert res_alias.status_code == 200
    assert res_alias.json()["status"] == "SUCCESS"


def test_get_route_endpoint_invalid_node():
    """Verify /api/v1/route returns 404 for invalid node IDs."""
    client = TestClient(app)
    req_body = {
        "source": "INVALID_NODE_99",
        "target": "S10",
    }
    response = client.post("/api/v1/route", json=req_body)
    assert response.status_code == 404


def test_telemetry_ingest_triggers_alert():
    """Ingest high rainfall payload (>80mm/hr), confirm graph update and alert creation in /api/v1/alerts."""
    client = TestClient(app)

    disaster_payload = {
        "provenance": "SIMULATED",
        "rainfall": {"S01": 95.0, "S10": 90.0},
        "reports": [
            {
                "report_id": "TEST-DISASTER-ALERT-01",
                "hazard_type": "LANDSLIDE",
                "user_reliability_score": 0.98,
                "description": "Massive rockfall blocking S01 <-> S10.",
                "edge": ["S01", "S10"],
            }
        ],
    }

    # 1. Ingest telemetry
    ingest_res = client.post("/api/v1/telemetry/ingest", json=disaster_payload)
    assert ingest_res.status_code == 200
    ingest_data = ingest_res.json()
    assert ingest_data["status"] == "INGESTED"
    assert ingest_data["alerts_triggered"] >= 1

    # Check alert structure
    alert = ingest_data["alerts"][0]
    assert alert["severity"] in ["CRITICAL", "WARNING"]
    assert alert["affected_edge"] == ["S01", "S10"] or alert["affected_edge"] == ["S10", "S01"]

    # 2. Query alerts endpoint
    alerts_res = client.get("/api/v1/alerts")
    assert alerts_res.status_code == 200
    alerts_data = alerts_res.json()
    assert alerts_data["total_active_alerts"] >= 1


def test_envelope_wrapped_telemetry_ingestion():
    """Verify ingestion of Pydantic Envelope formatted payload."""
    client = TestClient(app)

    envelope_payload = {
        "provenance": "SIMULATED",
        "ingestion_timestamp": "2026-10-09T08:00:00Z",
        "payload": {
            "sensor_id": "RAIN-SN-01",
            "settlement_id": "S01",
            "intensity_mm_hr": 85.0,
            "timestamp": "2026-10-09T08:00:00Z",
        },
    }

    res = client.post("/api/v1/telemetry/ingest", json=envelope_payload)
    assert res.status_code == 200
    assert res.json()["status"] == "INGESTED"


def test_network_edges_status():
    """Validate list of edges, status flags, and risk scores from /api/v1/network/edges."""
    client = TestClient(app)

    res = client.get("/api/v1/network/edges")
    assert res.status_code == 200
    data = res.json()

    assert "total_edges" in data
    assert data["total_edges"] > 0
    assert "edges" in data
    assert len(data["edges"]) == data["total_edges"]

    first_edge = data["edges"][0]
    assert "source_id" in first_edge
    assert "target_id" in first_edge
    assert "status" in first_edge
    assert "risk_score" in first_edge
    assert "effective_cost" in first_edge


def test_network_nodes_status():
    """Validate list of settlement nodes from /api/v1/network/nodes."""
    client = TestClient(app)

    res = client.get("/api/v1/network/nodes")
    assert res.status_code == 200
    data = res.json()

    assert data["total_nodes"] == 10
    assert len(data["nodes"]) == 10
    assert data["nodes"][0]["id"] == "S01"


def test_websocket_telemetry_connection():
    """Verify WebSocket connection and welcome handshake."""
    client = TestClient(app)

    with client.websocket_connect("/ws/telemetry") as websocket:
        data = websocket.receive_json()
        assert data["event_type"] == "CONNECTED"
        assert "disaster telemetry" in data["message"]

        websocket.send_text("PING")
        pong = websocket.receive_text()
        assert pong == "PONG"
