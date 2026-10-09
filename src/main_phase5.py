"""Phase 5 Demo Runner: Multi-Role REST API Controller & End-to-End Operational Workflow."""
import json
from fastapi.testclient import TestClient

from src.app import app


def run_phase5_demo():
    print("=" * 85)
    print("PHASE 5: MULTI-ROLE REST API CONTROLLER (ADMIN, ENGINE, RESPONDER, AUDIT)")
    print("=" * 85)

    client = TestClient(app)

    # ---------------------------------------------------------
    # 1. ADMIN ROLE CONTROLLER
    # ---------------------------------------------------------
    print("\n[ROLE 1: ADMIN] -> Triggering Crisis Scenario & Adjusting Regional Sliders:")
    print("-" * 85)

    scenario_req = {
        "scenario_name": "Severe Monsoon Torrential Flash Flood",
        "rainfall_mm_hr": 92.0,
        "river_surge_meters": 5.6,
        "target_settlements": ["S01", "S02", "S03", "S10"],
    }
    admin_res = client.post("/api/admin/scenario/trigger", json=scenario_req)
    print(f"[*] POST /api/admin/scenario/trigger (HTTP {admin_res.status_code})")
    print(f"    Scenario Name:     {admin_res.json().get('scenario_name')}")
    print(f"    Target Settlements: {admin_res.json().get('targeted_settlements')}")
    print(f"    Alerts Generated:   {admin_res.json().get('alerts_generated')}")

    slider_req = {
        "regional_zones": {"S01": 85.0, "S10": 95.0},
        "global_multiplier": 1.15,
    }
    slider_res = client.post("/api/admin/config/rainfall", json=slider_req)
    print(f"[*] POST /api/admin/config/rainfall (HTTP {slider_res.status_code})")
    print(f"    Updated Rainfall Zones: {slider_res.json().get('applied_rainfall')}")

    # ---------------------------------------------------------
    # 2. AI ENGINE ROLE CONTROLLER
    # ---------------------------------------------------------
    print("\n[ROLE 2: AI ENGINE] -> Real-Time Risk Assessment & Evidence Justification:")
    print("-" * 85)

    assess_req = {
        "slope_deg": 38.5,
        "rainfall_mm_hr": 88.0,
        "elevation_m": 850.0,
        "river_level_m": 5.1,
        "flood_threshold_m": 4.5,
        "report_confidence": 0.95,
        "road_type": "PRIMARY",
    }
    engine_res = client.post("/api/engine/risk-assess", json=assess_req)
    data_e = engine_res.json()
    print(f"[*] POST /api/engine/risk-assess (HTTP {engine_res.status_code})")
    print(f"    Computed Risk Score:   {data_e.get('risk_score_percent')}% (Score: {data_e.get('risk_score')})")
    print(f"    Severity Class:        {data_e.get('severity_classification')}")
    print(f"    Confidence Level:      {data_e.get('confidence_level')}")
    print(f"    Contributing Landslide: {data_e.get('breakdown', {}).get('landslide_risk')}")
    print(f"    Contributing Flood:     {data_e.get('breakdown', {}).get('flood_risk')}")

    evidence_req = {
        "settlement_id": "S01",
        "road_segment": ["S01", "S10"],
    }
    evidence_res = client.post("/api/engine/evidence-summary", json=evidence_req)
    print(f"[*] POST /api/engine/evidence-summary (HTTP {evidence_res.status_code})")
    for rep in evidence_res.json().get("evidence_reports", []):
        print(f"    [{rep['target_type']}] {rep['justification']}")

    # ---------------------------------------------------------
    # 3. RESPONDER ROLE CONTROLLER
    # ---------------------------------------------------------
    print("\n[ROLE 3: RESPONDER] -> Prioritized Targets, Open Corridors & Field Reports:")
    print("-" * 85)

    prio_res = client.get("/api/responder/settlements/prioritized")
    top_prio = prio_res.json().get("prioritized_settlements", [])[:3]
    print(f"[*] GET /api/responder/settlements/prioritized (Top 3 Critical Targets):")
    for p in top_prio:
        print(f"    * {p['settlement_id']} ({p['name']}): Vulnerability {p['vulnerability_score']:.2f} | Status: {p['isolation_status']} | Risk: {p['max_connecting_risk']:.2f}")

    open_res = client.get("/api/responder/routes/open")
    print(f"[*] GET /api/responder/routes/open -> Verified Open Corridors: {open_res.json().get('total_open_corridors')}")

    field_rep_req = {
        "reporter_id": "RESCUE-BRAVO-44",
        "edge": ["S01", "S10"],
        "hazard_type": "BRIDGE_COLLAPSE",
        "description": "Trishuli river bridge abutment sheared off by flood waters. 100% impassable.",
        "user_reliability_score": 0.99,
    }
    field_res = client.post("/api/responder/field-report", json=field_rep_req)
    data_f = field_res.json()
    print(f"[*] POST /api/responder/field-report (HTTP {field_res.status_code})")
    print(f"    Affected Corridor:    {data_f.get('affected_edge')}")
    print(f"    New Status:           {data_f.get('resulting_status')}")
    print(f"    Emergency Alerts:     {data_f.get('alerts_triggered')}")
    alt_route = data_f.get("alternate_evacuation_route", {})
    print(f"    Alternate Evac Route: {' -> '.join(alt_route.get('path', []))} ({alt_route.get('total_distance_km')} km)")

    # ---------------------------------------------------------
    # 4. AUDIT ROLE CONTROLLER
    # ---------------------------------------------------------
    print("\n[ROLE 4: AUDIT] -> Impact Ledger, Model Benchmark & Guardrail Stress Tests:")
    print("-" * 85)

    audit_res = client.get("/api/audit/impact-analytics")
    summary = audit_res.json().get("summary", {})
    print(f"[*] GET /api/audit/impact-analytics:")
    print(f"    Cumulative Missions:  {summary.get('total_missions')}")
    print(f"    Total Time Saved:     {summary.get('total_time_saved_minutes')} min")
    print(f"    Total Fuel Conserved: {summary.get('total_fuel_saved_liters')} Liters")

    comp_res = client.get("/api/audit/baseline-comparison")
    lift = comp_res.json().get("performance_lift", {})
    print(f"[*] GET /api/audit/baseline-comparison:")
    print(f"    Accuracy Gain:        +{lift.get('accuracy_gain_percent')}%")
    print(f"    Sensitivity Gain:     +{lift.get('recall_sensitivity_gain_percent')}%")
    print(f"    Missed Hazards Saved: -{lift.get('missed_hazards_reduction')} critical incidents")

    stress_req = {
        "test_sensor_id": "RAIN-HW-GLITCH-99",
        "settlement_id": "S02",
        "simulated_spike_value": 500.0,
        "simulated_neighbor_values": [12.0, 16.5, 14.0],
    }
    stress_res = client.post("/api/audit/stress-test", json=stress_req)
    outcome = stress_res.json().get("validation_outcome", {})
    print(f"[*] POST /api/audit/stress-test (500 mm/hr Sensor Glitch Injection):")
    print(f"    Raw Spike Input:      {outcome.get('original_value')} mm/hr")
    print(f"    Guardrail Outcome:    {outcome.get('status')}")
    print(f"    Sanitized Value:      {outcome.get('sanitized_value')} mm/hr")
    print(f"    Audit Note:           {outcome.get('message')}")

    print("\n" + "=" * 85)
    print("Phase 5 Multi-Role REST API Controller demo completed successfully.")
    print("=" * 85)


if __name__ == "__main__":
    run_phase5_demo()
