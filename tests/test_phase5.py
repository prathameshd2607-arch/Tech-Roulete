"""Integration tests for Phase 5 Multi-Role REST API Controllers (Admin, Engine, Responder, Audit)."""
import pytest
from fastapi.testclient import TestClient

from src.app import app
from src.services.state_manager import get_system_state


@pytest.fixture(autouse=True)
def reset_state():
    """Reset system state before each test run."""
    state = get_system_state()
    state.reset_to_baseline()
    yield
    state.reset_to_baseline()


def test_admin_endpoints():
    """Verify Admin scenario triggers, rainfall sliders, and ground data uploads."""
    client = TestClient(app)

    # 1. Trigger Scenario
    scenario_payload = {
        "scenario_name": "Test Flash Flood Scenario",
        "rainfall_mm_hr": 85.0,
        "river_surge_meters": 5.2,
        "target_settlements": ["S01", "S02"],
    }
    res_scen = client.post("/api/admin/scenario/trigger", json=scenario_payload)
    assert res_scen.status_code == 200
    data_scen = res_scen.json()
    assert data_scen["status"] == "SCENARIO_TRIGGERED"
    assert data_scen["targeted_settlements"] == 2

    # 2. Adjust Rainfall Sliders
    slider_payload = {
        "rainfall_rate_mm_hr": 40.0,
        "regional_zones": {"S01": 70.0},
        "global_multiplier": 1.2,
    }
    res_slider = client.post("/api/admin/config/rainfall", json=slider_payload)
    assert res_slider.status_code == 200
    assert res_slider.json()["status"] == "CONFIG_UPDATED"

    # 3. Ground Data Upload
    upload_payload = {
        "dataset_type": "TELEMETRY_STREAM",
        "records": [
            {"settlement_id": "S01", "intensity_mm_hr": 55.0},
            {"settlement_id": "S02", "intensity_mm_hr": 60.0},
        ],
    }
    res_up = client.post("/api/admin/ground-data/upload", json=upload_payload)
    assert res_up.status_code == 200
    assert res_up.json()["status"] == "UPLOAD_SUCCESS"


def test_engine_risk_assessment_and_evidence():
    """Verify Engine raw data risk scoring, confidence classification, and evidence summaries."""
    client = TestClient(app)

    # 1. Raw risk assessment
    assess_payload = {
        "slope_deg": 35.0,
        "rainfall_mm_hr": 80.0,
        "elevation_m": 850.0,
        "river_level_m": 4.8,
        "flood_threshold_m": 4.0,
        "report_confidence": 0.90,
    }
    res_assess = client.post("/api/engine/risk-assess", json=assess_payload)
    assert res_assess.status_code == 200
    data = res_assess.json()
    assert 0.0 <= data["risk_score"] <= 1.0
    assert 0.0 <= data["risk_score_percent"] <= 100.0
    assert data["severity_classification"] in ["CRITICAL", "HIGH", "MODERATE", "LOW"]
    assert data["confidence_level"] in ["HIGH", "MEDIUM", "LOW"]
    assert "breakdown" in data

    # 2. Evidence summary
    evidence_payload = {
        "settlement_id": "S01",
        "road_segment": ["S01", "S02"],
    }
    res_ev = client.post("/api/engine/evidence-summary", json=evidence_payload)
    assert res_ev.status_code == 200
    data_ev = res_ev.json()
    assert data_ev["total_summaries"] >= 1
    assert len(data_ev["evidence_reports"]) >= 1
    assert len(data_ev["evidence_reports"][0]["justification"]) > 0


def test_responder_workflow():
    """Verify settlement priority ranking, open corridors query, and field report invalidation."""
    client = TestClient(app)

    # 1. Prioritized settlements ranking
    res_prio = client.get("/api/responder/settlements/prioritized")
    assert res_prio.status_code == 200
    data_prio = res_prio.json()
    assert data_prio["total_settlements"] == 10
    assert len(data_prio["prioritized_settlements"]) == 10

    first_target = data_prio["prioritized_settlements"][0]
    assert "vulnerability_score" in first_target
    assert "isolation_status" in first_target
    assert "access_corridors" in first_target

    # 2. Open corridors
    res_open = client.get("/api/responder/routes/open")
    assert res_open.status_code == 200
    assert "open_corridors" in res_open.json()

    # 3. Field Report Ingestion & Real-Time Rerouting
    field_payload = {
        "reporter_id": "RESCUE-PATROL-01",
        "edge": ["S01", "S02"],
        "hazard_type": "LANDSLIDE",
        "description": "Massive mudslide over highway.",
        "user_reliability_score": 0.98,
    }
    res_field = client.post("/api/responder/field-report", json=field_payload)
    assert res_field.status_code == 200
    data_field = res_field.json()
    assert data_field["status"] == "FIELD_REPORT_INGESTED"
    assert data_field["resulting_status"] in ["IMPASSABLE", "PARTIALLY_BLOCKED"]
    assert "alternate_evacuation_route" in data_field


def test_audit_endpoints():
    """Verify impact analytics ledger, baseline comparison matrix, and guardrail stress tests."""
    client = TestClient(app)

    # 1. Impact Analytics
    res_impact = client.get("/api/audit/impact-analytics")
    assert res_impact.status_code == 200
    data_impact = res_impact.json()
    assert data_impact["status"] == "SUCCESS"
    assert data_impact["summary"]["total_missions"] >= 1
    assert data_impact["summary"]["total_time_saved_minutes"] >= 0.0
    assert data_impact["summary"]["total_fuel_saved_liters"] >= 0.0

    # 2. Baseline Model Comparison
    res_comp = client.get("/api/audit/baseline-comparison")
    assert res_comp.status_code == 200
    data_comp = res_comp.json()
    assert data_comp["status"] == "SUCCESS"
    assert "static_non_ml_baseline" in data_comp
    assert "ai_context_fused_engine" in data_comp
    assert data_comp["ai_context_fused_engine"]["accuracy"] > data_comp["static_non_ml_baseline"]["accuracy"]
    assert data_comp["ai_context_fused_engine"]["recall"] > data_comp["static_non_ml_baseline"]["recall"]

    # 3. Guardrail Stress Test
    stress_payload = {
        "test_sensor_id": "RAIN-STRESS-GLITCH-01",
        "settlement_id": "S01",
        "simulated_spike_value": 500.0,
        "simulated_neighbor_values": [15.0, 18.0, 12.0],
    }
    res_stress = client.post("/api/audit/stress-test", json=stress_payload)
    assert res_stress.status_code == 200
    data_stress = res_stress.json()
    assert data_stress["status"] == "STRESS_TEST_COMPLETED"
    outcome = data_stress["validation_outcome"]
    assert outcome["status"] == "PHYSICAL_LIMIT_EXCEEDED"
    assert outcome["sanitized_value"] < 300.0
