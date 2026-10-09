"""Unit & Integration tests for Phase 4 Impact Ledger, Evaluation Matrix & Failure Guardrails."""
import pytest

from src.services.failure_guardrails import FailureGuardrailEngine
from src.services.impact_ledger import ImpactLedger, evaluate_model


def test_impact_ledger_formulas():
    """Verify exact mathematical correctness of response time reduction, distance avoided, and fuel saved."""
    ledger = ImpactLedger(default_fuel_rate_l_km=0.28)

    # Mission 1: 120 min baseline vs 45 min AI route, 60 km baseline vs 40 km AI route
    entry1 = ledger.record_mission(
        mission_id="TEST-MISSION-01",
        baseline_time_minutes=120.0,
        optimized_time_minutes=45.0,
        baseline_distance_km=60.0,
        optimized_distance_km=40.0,
        fuel_consumption_rate_l_km=0.28,
    )

    # Assertions on entry 1
    assert entry1.time_saved_minutes == pytest.approx(75.0, rel=1e-3)
    assert entry1.distance_saved_km == pytest.approx(20.0, rel=1e-3)
    # Fuel saved = 20.0 km * 0.28 L/km = 5.60 Liters
    assert entry1.fuel_saved_liters == pytest.approx(5.60, rel=1e-3)

    # Mission 2: Custom fuel rate 0.35 L/km
    entry2 = ledger.record_mission(
        mission_id="TEST-MISSION-02",
        baseline_time_minutes=80.0,
        optimized_time_minutes=50.0,
        baseline_distance_km=50.0,
        optimized_distance_km=30.0,
        fuel_consumption_rate_l_km=0.35,
    )

    assert entry2.time_saved_minutes == pytest.approx(30.0, rel=1e-3)
    assert entry2.distance_saved_km == pytest.approx(20.0, rel=1e-3)
    # Fuel saved = 20.0 * 0.35 = 7.00 Liters
    assert entry2.fuel_saved_liters == pytest.approx(7.00, rel=1e-3)

    # Summary aggregations
    summary = ledger.get_summary()
    assert summary.total_missions == 2
    assert summary.total_time_saved_minutes == pytest.approx(105.0, rel=1e-3)
    assert summary.total_distance_saved_km == pytest.approx(40.0, rel=1e-3)
    assert summary.total_fuel_saved_liters == pytest.approx(12.60, rel=1e-3)
    assert summary.average_time_saved_minutes == pytest.approx(52.5, rel=1e-3)
    assert summary.average_fuel_saved_liters == pytest.approx(6.30, rel=1e-3)


def test_evaluation_matrix():
    """Verify Confusion Matrix metrics: TP, FP, FN, TN, precision, recall, F1, and accuracy."""
    # 10 ground truth samples: 6 positive (hazards), 4 negative (safe)
    ground_truth = [1, 1, 1, 1, 1, 1, 0, 0, 0, 0]

    # Model predictions:
    # 5 TP (indices 0, 1, 2, 3, 4)
    # 1 FN (index 5)
    # 1 FP (index 6)
    # 3 TN (indices 7, 8, 9)
    predictions  = [1, 1, 1, 1, 1, 0, 1, 0, 0, 0]

    matrix = evaluate_model(predictions, ground_truth, model_name="Test Risk Model")

    assert matrix.total_samples == 10
    assert matrix.true_positives == 5
    assert matrix.false_negatives == 1
    assert matrix.false_positives == 1
    assert matrix.true_negatives == 3

    # Precision = 5 / (5 + 1) = 5/6 = 0.8333
    assert matrix.precision == pytest.approx(5 / 6, rel=1e-3)
    # Recall = 5 / (5 + 1) = 5/6 = 0.8333
    assert matrix.recall == pytest.approx(5 / 6, rel=1e-3)
    # F1 Score = 5/6 = 0.8333
    assert matrix.f1_score == pytest.approx(5 / 6, rel=1e-3)
    # Accuracy = (5 + 3) / 10 = 0.80
    assert matrix.accuracy == pytest.approx(0.80, rel=1e-3)


def test_failure_guardrail_sensor_spike():
    """Confirm that physical maximum spikes (500 mm/hr) are flagged as PHYSICAL_LIMIT_EXCEEDED and sanitized."""
    guardrail = FailureGuardrailEngine(max_physical_rainfall_mm_hr=300.0)

    # 500 mm/hr hardware short circuit with calm spatial neighbors
    result = guardrail.validate_rainfall_reading(
        sensor_id="RAIN-GLITCH-01",
        settlement_id="S01",
        value=500.0,
        neighbor_readings=[20.0, 25.0, 15.0],
    )

    assert result.is_valid is False
    assert result.status == "PHYSICAL_LIMIT_EXCEEDED"
    assert result.original_value == 500.0
    # Sanitized to neighborhood average (20.0)
    assert result.sanitized_value == pytest.approx(20.0, rel=1e-2)
    assert "Physical limit violation" in result.message


def test_failure_guardrail_spatial_divergence():
    """Confirm isolated sensor divergence from surrounding neighbors is suppressed."""
    guardrail = FailureGuardrailEngine(
        max_physical_rainfall_mm_hr=300.0,
        spatial_divergence_threshold_mm_hr=60.0,
        spatial_divergence_ratio=4.0,
    )

    # 135 mm/hr in isolated hamlet while all surrounding stations report ~10 mm/hr
    result = guardrail.validate_rainfall_reading(
        sensor_id="RAIN-ANOMALY-02",
        settlement_id="S02",
        value=135.0,
        neighbor_readings=[10.0, 12.0, 8.0],
    )

    assert result.is_valid is False
    assert result.status == "SPATIAL_ANOMALY_SUPPRESSED"
    assert result.original_value == 135.0
    assert result.sanitized_value == pytest.approx(10.0, rel=1e-2)
    assert "Spatial anomaly suppressed" in result.message


def test_failure_guardrail_valid_regional_storm():
    """Confirm true regional storms validated by neighboring stations pass unchanged."""
    guardrail = FailureGuardrailEngine(max_physical_rainfall_mm_hr=300.0)

    # Severe widespread storm where all stations report 85-95 mm/hr
    result = guardrail.validate_rainfall_reading(
        sensor_id="RAIN-STORM-03",
        settlement_id="S03",
        value=90.0,
        neighbor_readings=[85.0, 92.0, 88.0],
    )

    assert result.is_valid is True
    assert result.status == "VALID"
    assert result.original_value == 90.0
    assert result.sanitized_value == 90.0
