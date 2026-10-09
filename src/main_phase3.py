"""Phase 3 Demo Runner: Real-Time Telemetry Ingestion, Dynamic Alerting & API Services."""
import json
import time
from fastapi.testclient import TestClient

from src.app import app
from src.config import DataProvenance, HazardType
from src.schemas import Envelope, RainfallMeasurement, RiverGaugeMeasurement


def run_phase3_demo():
    print("=" * 80)
    print("PHASE 3: REAL-TIME TELEMETRY INGESTION, DYNAMIC ALERTING & API SERVICES")
    print("=" * 80)

    client = TestClient(app)

    # 1. Health & Status Check
    print("\n[+] 1. Checking API Root Status (GET /)...")
    res = client.get("/")
    print("    Response HTTP", res.status_code)
    print("    Status Payload:", json.dumps(res.json(), indent=2))

    # 2. Query Baseline Optimal Route
    print("\n[+] 2. Querying Baseline Evacuation Route (POST /api/v1/route)...")
    route_req = {"source": "S01", "target": "S10", "max_risk": 0.80}
    res = client.post("/api/v1/route", json=route_req)
    print(f"    Origin: S01 -> Destination: S10")
    print(f"    Path: {' -> '.join(res.json().get('path', []))}")
    print(f"    Distance: {res.json().get('total_distance_km')} km | Time: {res.json().get('total_time_minutes')} min | Risk: {res.json().get('max_risk_encountered')}")

    # 3. Simulate Ingestion #1: Severe Landslide & Torrential Rain on S01 <-> S10
    print("\n[+] 3. Ingesting Severe Disaster Telemetry (POST /api/v1/telemetry/ingest)...")
    disaster_telemetry_1 = {
        "provenance": "SIMULATED",
        "rainfall": {"S01": 88.0, "S10": 85.0},
        "reports": [
            {
                "report_id": "CITIZEN-REP-DISASTER-01",
                "hazard_type": "LANDSLIDE",
                "user_reliability_score": 0.98,
                "description": "Massive debris flow and boulder collapse completely shutting down S01 <-> S10 pass.",
                "edge": ["S01", "S10"],
            }
        ],
    }
    res1 = client.post("/api/v1/telemetry/ingest", json=disaster_telemetry_1)
    print("    Response HTTP", res1.status_code)
    print("    Alerts Triggered:", res1.json().get("alerts_triggered"))
    for alert in res1.json().get("alerts", []):
        print(f"    [{alert['severity']}] {alert['message']}")

    # 4. Re-query Route (Dynamic Real-Time Rerouting)
    print("\n[+] 4. Recalculating Dynamic Disaster-Aware Route (POST /api/v1/route)...")
    res_reroute = client.post("/api/v1/route", json=route_req)
    reroute_data = res_reroute.json()
    print(f"    Rerouted Path: {' -> '.join(reroute_data.get('path', []))}")
    print(f"    Distance: {reroute_data.get('total_distance_km')} km | Time: {reroute_data.get('total_time_minutes')} min | Max Risk: {reroute_data.get('max_risk_encountered')}")
    print(f"    Avoided Blocked Segment: {'S01 -> S10' not in ' -> '.join(reroute_data.get('path', []))}")

    # 5. Simulate Ingestion #2: River Flood Gauge Exceedance
    print("\n[+] 5. Ingesting Hydrometric River Surge Telemetry (POST /api/v1/telemetry/ingest)...")
    flood_telemetry = {
        "provenance": "SIMULATED",
        "river_gauges": [
            {
                "station_id": "RG-MELAMCHI-02",
                "river_name": "Melamchi River",
                "level_meters": 5.4,
                "flood_threshold_meters": 4.0,
            }
        ],
    }
    res2 = client.post("/api/v1/telemetry/ingest", json=flood_telemetry)
    print("    Response HTTP", res2.status_code)
    print("    Alerts Triggered:", res2.json().get("alerts_triggered"))
    for alert in res2.json().get("alerts", []):
        print(f"    [{alert['severity']}] {alert['message']}")

    # 6. Query Active Emergency Alerts
    print("\n[+] 6. Querying Active Emergency Alerts (GET /api/v1/alerts)...")
    alerts_res = client.get("/api/v1/alerts")
    print(f"    Total Active Alerts: {alerts_res.json().get('total_active_alerts')}")
    for a in alerts_res.json().get("alerts", []):
        print(f"    * [{a['severity']}] {a['alert_id']}: {a['message']}")

    # 7. Query Network Edges Operational Summary
    print("\n[+] 7. Inspecting Live Network Edges (GET /api/v1/network/edges)...")
    edges_res = client.get("/api/v1/network/edges")
    edges_data = edges_res.json().get("edges", [])
    print(f"    Total Tracked Segments: {len(edges_data)}")
    disrupted = [e for e in edges_data if e["status"] != "ACCESSIBLE"]
    print(f"    Active Disrupted Segments ({len(disrupted)}):")
    for d in disrupted:
        print(f"      - {d['source_id']} <-> {d['target_id']} [{d['status']}] (Risk: {d['risk_score']:.2f}, Cost: {d['effective_cost']})")

    print("\n" + "=" * 80)
    print("Phase 3 API Services and Dynamic Alerting demo completed successfully.")
    print("=" * 80)


if __name__ == "__main__":
    run_phase3_demo()
