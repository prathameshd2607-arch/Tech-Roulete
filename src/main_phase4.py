"""Phase 4 Demo Runner: Impact Ledger Analytics, Evaluation Matrix & Failure Guardrails."""
import json

from src.services.failure_guardrails import FailureGuardrailEngine
from src.services.impact_ledger import ImpactLedger, evaluate_model
from src.spatial_builder import build_road_graph, generate_district_data


def run_phase4_demo():
    print("=" * 85)
    print("PHASE 4: IMPACT LEDGER, EVALUATION MATRIX & FAILURE GUARDRAILS")
    print("=" * 85)

    # ---------------------------------------------------------
    # PART 1: Impact Ledger Metrics (Time, Distance, Fuel Savings)
    # ---------------------------------------------------------
    print("\n[+] 1. COMPUTING MISSION IMPACT LEDGER ANALYTICS (Emergency Response Scenarios):")
    print("-" * 85)

    ledger = ImpactLedger(default_fuel_rate_l_km=0.28)

    sample_missions = [
        # (mission_id, baseline_time_min, optimized_time_min, baseline_dist_km, optimized_dist_km)
        # Baseline includes turnaround delays / dead ends due to impassable roads
        ("MISSION-VALLEY-EVAC-01", 145.0, 58.0, 78.5, 46.2),
        ("MISSION-MEDICAL-RELIEF-02", 92.0, 41.5, 54.0, 33.8),
        ("MISSION-FOOD-AIRDROP-SUPP-03", 210.0, 85.0, 112.0, 68.4),
        ("MISSION-BRIDGE-COLLAPSE-REROUTE-04", 175.0, 72.0, 95.0, 58.0),
        ("MISSION-HIGH-ALTITUDE-RESCUE-05", 130.0, 64.0, 68.0, 42.5),
    ]

    print(f"{'Mission ID':<35} | {'Time Saved':<12} | {'Dist Saved':<12} | {'Fuel Saved':<12}")
    print("-" * 85)
    for mid, b_time, o_time, b_dist, o_dist in sample_missions:
        entry = ledger.record_mission(
            mission_id=mid,
            baseline_time_minutes=b_time,
            optimized_time_minutes=o_time,
            baseline_distance_km=b_dist,
            optimized_distance_km=o_dist,
            fuel_consumption_rate_l_km=0.28,
        )
        print(f"{entry.mission_id:<35} | {entry.time_saved_minutes:>8.1f} min | {entry.distance_saved_km:>8.1f} km | {entry.fuel_saved_liters:>8.1f} L")

    summary = ledger.get_summary()
    print("-" * 85)
    print(f"Cumulative Missions Evaluated:    {summary.total_missions}")
    print(f"Total Response Time Reduction:    {summary.total_time_saved_minutes:.1f} minutes ({summary.total_time_saved_minutes/60.0:.2f} hours saved)")
    print(f"Total Wasted Distance Avoided:    {summary.total_distance_saved_km:.1f} km")
    print(f"Total Rescue Fuel Conserved:      {summary.total_fuel_saved_liters:.1f} Liters")
    print(f"Average Response Time Saved:      {summary.average_time_saved_minutes:.1f} minutes / mission")
    print(f"Average Fuel Saved:               {summary.average_fuel_saved_liters:.1f} Liters / mission")

    # ---------------------------------------------------------
    # PART 2: Evaluation Matrix: Non-ML Static vs AI Context-Fused
    # ---------------------------------------------------------
    print("\n[+] 2. EVALUATION MATRIX: STATIC NON-ML BASELINE vs AI CONTEXT-FUSED ENGINE:")
    print("-" * 85)

    # 50 Ground Truth road corridor hazard observations during monsoon event
    # 1 = Hazardous/Impassable, 0 = Safe/Navigable
    ground_truth = [
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    ]  # 20 Impassable, 30 Safe

    # Static Non-ML Baseline (Static shortest distance, oblivious to real-time rainfall/floods)
    # Frequently drives into disasters (many False Negatives, misses 14 of 20 hazards)
    static_baseline_preds = [
        1, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0,
        0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    ]

    # AI Context-Fused Risk Engine (Fuses slope topography, gauge stage, live rain, citizen reports)
    # Correctly flags almost all hazards with minimal false alarms
    ai_risk_engine_preds = [
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1,
        0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    ]

    matrix_static = evaluate_model(static_baseline_preds, ground_truth, model_name="Static Non-ML Baseline")
    matrix_ai = evaluate_model(ai_risk_engine_preds, ground_truth, model_name="AI Context-Fused Risk Engine")

    header = f"{'Metric / Feature':<30} | {'Static Non-ML Baseline':<24} | {'AI Context-Fused Engine':<24}"
    print(header)
    print("-" * 85)
    print(f"{'Total Corridor Samples':<30} | {matrix_static.total_samples:<24} | {matrix_ai.total_samples:<24}")
    print(f"{'True Positives (TP)':<30} | {matrix_static.true_positives:<24} | {matrix_ai.true_positives:<24}")
    print(f"{'False Positives (FP False Alarms)':<30} | {matrix_static.false_positives:<24} | {matrix_ai.false_positives:<24}")
    print(f"{'False Negatives (FN Missed Hazards)':<30} | {matrix_static.false_negatives:<24} | {matrix_ai.false_negatives:<24}")
    print(f"{'True Negatives (TN)':<30} | {matrix_static.true_negatives:<24} | {matrix_ai.true_negatives:<24}")
    print(f"{'Precision':<30} | {matrix_static.precision:<24.4f} | {matrix_ai.precision:<24.4f}")
    print(f"{'Recall (Hazard Sensitivity)':<30} | {matrix_static.recall:<24.4f} | {matrix_ai.recall:<24.4f}")
    print(f"{'F1 Score':<30} | {matrix_static.f1_score:<24.4f} | {matrix_ai.f1_score:<24.4f}")
    print(f"{'Overall Accuracy':<30} | {matrix_static.accuracy:<24.4f} | {matrix_ai.accuracy:<24.4f}")

    # ---------------------------------------------------------
    # PART 3: Failure Guardrails & Anomaly Suppression
    # ---------------------------------------------------------
    print("\n[+] 3. FAILURE GUARDRAILS STRESS TEST (Hardware Glitch & Spatial Neighbor Suppression):")
    print("-" * 85)

    guardrail = FailureGuardrailEngine(
        max_physical_rainfall_mm_hr=300.0,
        spatial_divergence_threshold_mm_hr=60.0,
        spatial_divergence_ratio=4.0,
    )

    gdf = generate_district_data()
    graph = build_road_graph(gdf)

    # Test Case A: Glitched 500 mm/hr hardware short circuit
    print("--> Test Case A: 500.0 mm/hr Sensor Hardware Malfunction:")
    glitch_result = guardrail.validate_rainfall_reading(
        sensor_id="RAIN-GLITCH-01",
        settlement_id="S01",
        value=500.0,
        neighbor_readings=[15.0, 18.5, 12.0],
    )
    print(f"    Raw Reading:       {glitch_result.original_value} mm/hr")
    print(f"    Guardrail Status:  {glitch_result.status}")
    print(f"    Sanitized Value:   {glitch_result.sanitized_value} mm/hr")
    print(f"    Audit Message:     {glitch_result.message}")

    # Test Case B: Isolated sensor divergence (140 mm/hr reported in isolated point while neighbors show 10 mm/hr)
    print("\n--> Test Case B: Isolated Spatial Neighbor Divergence:")
    spatial_result = guardrail.validate_rainfall_reading(
        sensor_id="RAIN-ISOLATED-02",
        settlement_id="S02",
        value=140.0,
        neighbor_readings=[8.0, 11.0, 9.5],
    )
    print(f"    Raw Reading:       {spatial_result.original_value} mm/hr")
    print(f"    Guardrail Status:  {spatial_result.status}")
    print(f"    Sanitized Value:   {spatial_result.sanitized_value} mm/hr")
    print(f"    Audit Message:     {spatial_result.message}")

    # Test Case C: Valid extreme widespread monsoon storm
    print("\n--> Test Case C: Valid Regional Storm (All neighbors confirm high precipitation):")
    valid_result = guardrail.validate_rainfall_reading(
        sensor_id="RAIN-STORM-03",
        settlement_id="S03",
        value=95.0,
        neighbor_readings=[88.0, 92.0, 105.0],
    )
    print(f"    Raw Reading:       {valid_result.original_value} mm/hr")
    print(f"    Guardrail Status:  {valid_result.status}")
    print(f"    Sanitized Value:   {valid_result.sanitized_value} mm/hr")
    print(f"    Audit Message:     {valid_result.message}")

    print("\n" + "=" * 85)
    print("Phase 4 Impact Analytics, Evaluation Matrix & Guardrail validation complete.")
    print("=" * 85)


if __name__ == "__main__":
    run_phase4_demo()
