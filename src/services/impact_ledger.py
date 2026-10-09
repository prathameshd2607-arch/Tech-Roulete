"""Impact Ledger & Evaluation Matrix Engine for Disaster Management Routing."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RouteImpactEntry(BaseModel):
    mission_id: str = Field(..., description="Unique emergency mission identifier")
    baseline_time_minutes: float = Field(..., description="Traversed time via static baseline route")
    optimized_time_minutes: float = Field(..., description="Traversed time via AI disaster-aware route")
    baseline_distance_km: float = Field(..., description="Traversed distance via static baseline route")
    optimized_distance_km: float = Field(..., description="Traversed distance via AI disaster-aware route")
    fuel_rate_l_per_km: float = Field(0.28, description="Vehicle fuel consumption rate (L/km)")
    time_saved_minutes: float = Field(..., description="Response time reduction in minutes")
    distance_saved_km: float = Field(..., description="Wasted distance avoided in km")
    fuel_saved_liters: float = Field(..., description="Fuel saved in liters")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ImpactLedgerSummary(BaseModel):
    total_missions: int = Field(0, description="Total number of evaluated response missions")
    total_time_saved_minutes: float = Field(0.0, description="Cumulative response time reduction")
    total_distance_saved_km: float = Field(0.0, description="Cumulative wasted distance avoided")
    total_fuel_saved_liters: float = Field(0.0, description="Cumulative fuel saved in liters")
    average_time_saved_minutes: float = Field(0.0, description="Average time saved per mission")
    average_fuel_saved_liters: float = Field(0.0, description="Average fuel saved per mission")


class EvaluationMatrix(BaseModel):
    model_name: str = Field(..., description="Name of the evaluated routing model")
    total_samples: int = Field(..., description="Total ground truth hazard evaluations")
    true_positives: int = Field(..., description="Correctly detected hazardous impassable routes")
    false_positives: int = Field(..., description="False alarms (safe routes marked impassable)")
    false_negatives: int = Field(..., description="Missed hazards (hazardous routes marked safe)")
    true_negatives: int = Field(..., description="Correctly identified safe navigable routes")
    precision: float = Field(..., description="TP / (TP + FP)")
    recall: float = Field(..., description="TP / (TP + FN)")
    f1_score: float = Field(..., description="Harmonic mean of precision and recall")
    accuracy: float = Field(..., description="(TP + TN) / Total")


def evaluate_model(
    predictions: List[int],
    ground_truth: List[int],
    model_name: str,
) -> EvaluationMatrix:
    """
    Compute full classification Confusion Matrix metrics:
    1 = Hazardous / Impassable corridor
    0 = Safe / Navigable corridor
    """
    if len(predictions) != len(ground_truth):
        raise ValueError("Predictions and ground truth lists must have identical lengths")

    n = len(predictions)
    if n == 0:
        return EvaluationMatrix(
            model_name=model_name,
            total_samples=0,
            true_positives=0,
            false_positives=0,
            false_negatives=0,
            true_negatives=0,
            precision=0.0,
            recall=0.0,
            f1_score=0.0,
            accuracy=0.0,
        )

    tp = sum(1 for p, g in zip(predictions, ground_truth) if p == 1 and g == 1)
    fp = sum(1 for p, g in zip(predictions, ground_truth) if p == 1 and g == 0)
    fn = sum(1 for p, g in zip(predictions, ground_truth) if p == 0 and g == 1)
    tn = sum(1 for p, g in zip(predictions, ground_truth) if p == 0 and g == 0)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / n

    return EvaluationMatrix(
        model_name=model_name,
        total_samples=n,
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        true_negatives=tn,
        precision=round(precision, 4),
        recall=round(recall, 4),
        f1_score=round(f1, 4),
        accuracy=round(accuracy, 4),
    )


class ImpactLedger:
    """
    Tracks and aggregates dynamic response metrics:
      - Response Time Reduction = Baseline Route Time - Optimized Route Time
      - Wasted Distance Avoided = Baseline Distance - Optimized Distance
      - Fuel Saved = Wasted Distance Avoided * Fuel Rate (L/km)
    """

    def __init__(self, default_fuel_rate_l_km: float = 0.28) -> None:
        self.default_fuel_rate = default_fuel_rate_l_km
        self.entries: List[RouteImpactEntry] = []

    def record_mission(
        self,
        mission_id: str,
        baseline_time_minutes: float,
        optimized_time_minutes: float,
        baseline_distance_km: float,
        optimized_distance_km: float,
        fuel_consumption_rate_l_km: Optional[float] = None,
    ) -> RouteImpactEntry:
        rate = fuel_consumption_rate_l_km if fuel_consumption_rate_l_km is not None else self.default_fuel_rate

        time_saved = max(0.0, baseline_time_minutes - optimized_time_minutes)
        dist_saved = max(0.0, baseline_distance_km - optimized_distance_km)
        fuel_saved = dist_saved * rate

        entry = RouteImpactEntry(
            mission_id=mission_id,
            baseline_time_minutes=round(baseline_time_minutes, 2),
            optimized_time_minutes=round(optimized_time_minutes, 2),
            baseline_distance_km=round(baseline_distance_km, 2),
            optimized_distance_km=round(optimized_distance_km, 2),
            fuel_rate_l_per_km=round(rate, 3),
            time_saved_minutes=round(time_saved, 2),
            distance_saved_km=round(dist_saved, 2),
            fuel_saved_liters=round(fuel_saved, 2),
        )

        self.entries.append(entry)
        return entry

    def get_summary(self) -> ImpactLedgerSummary:
        if not self.entries:
            return ImpactLedgerSummary()

        total_missions = len(self.entries)
        total_time_saved = sum(e.time_saved_minutes for e in self.entries)
        total_dist_saved = sum(e.distance_saved_km for e in self.entries)
        total_fuel_saved = sum(e.fuel_saved_liters for e in self.entries)

        return ImpactLedgerSummary(
            total_missions=total_missions,
            total_time_saved_minutes=round(total_time_saved, 2),
            total_distance_saved_km=round(total_dist_saved, 2),
            total_fuel_saved_liters=round(total_fuel_saved, 2),
            average_time_saved_minutes=round(total_time_saved / total_missions, 2),
            average_fuel_saved_liters=round(total_fuel_saved / total_missions, 2),
        )
