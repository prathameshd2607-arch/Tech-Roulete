"""Phase 2 CLI Entrypoint: Risk Assessment Engine & Dynamic Routing Optimization."""
import json
from src.simulation_phase2 import run_phase2_simulation


def main():
    print("=" * 80)
    print("PHASE 2: RISK ASSESSMENT ENGINE & DYNAMIC ROUTING OPTIMIZATION")
    print("=" * 80)

    # Run the dynamic rerouting simulation
    simulation_result = run_phase2_simulation(source_id="S01", target_id="S10")

    endpoints = simulation_result["endpoints"]
    initial_route = simulation_result["initial_route"]
    disaster = simulation_result["disaster_event"]
    rerouted_route = simulation_result["rerouted_route"]
    comparison = simulation_result["comparison"]

    print("\n[+] Mission Endpoints:")
    print(f"    Origin:      {endpoints['source']['id']} - {endpoints['source']['name']} ({endpoints['source']['elevation_m']}m)")
    print(f"    Destination: {endpoints['target']['id']} - {endpoints['target']['name']} ({endpoints['target']['elevation_m']}m)")

    print("\n[+] Step 1: Baseline Route Calculated (Clear Weather)")
    print(f"    Path:             {comparison['initial_path']}")
    print(f"    Distance:         {initial_route['total_distance_km']} km")
    print(f"    Est. Travel Time: {initial_route['total_time_minutes']} min")
    print(f"    Max Risk Score:   {initial_route['max_risk_encountered']}")

    print("\n[+] Step 2: Disaster Event Injected (Real-Time Telemetry)")
    print(f"    Target Segment:   {disaster['affected_edge'][0]} <-> {disaster['affected_edge'][1]}")
    print(f"    Hazard Category:  {disaster['hazard_type']} & Extreme Rain ({disaster['local_rainfall_mm_hr']} mm/hr)")
    print(f"    Risk Score:       {disaster['resulting_edge_risk_score']} -> Status: {disaster['resulting_edge_status']}")
    print(f"    Effective Cost:   {disaster['resulting_effective_cost']} (Pathfinding Weight: INF)")

    print("\n[+] Step 3: Dynamic Disaster-Aware Rerouting Triggered")
    print(f"    Rerouted Path:    {comparison['rerouted_path']}")
    print(f"    Status:           {rerouted_route['status']}")
    print(f"    Distance:         {rerouted_route['total_distance_km']} km (Delta: +{comparison['distance_delta_km']} km)")
    print(f"    Est. Travel Time: {rerouted_route['total_time_minutes']} min (Delta: +{comparison['time_delta_minutes']} min)")
    print(f"    Max Risk on Path: {rerouted_route['max_risk_encountered']}")
    print(f"    Blocked Segment Avoided: {comparison['blocked_edge_avoided']}")

    print("\n[+] Complete Structured Output Payload (JSON):")
    print("-" * 80)
    print(json.dumps(simulation_result, indent=2))
    print("-" * 80)

    print("\n" + "=" * 80)
    print("Dynamic rerouting simulation completed successfully.")
    print("=" * 80)


if __name__ == "__main__":
    main()
