"""Engine Role Controller: Raw data risk scoring, confidence evaluation, and evidence justifications."""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.risk_engine import calculate_flood_risk, calculate_landslide_risk
from src.services.state_manager import get_system_state

router = APIRouter(prefix="/api/engine", tags=["AI Engine Controller"])


class RiskAssessmentRequest(BaseModel):
    slope_deg: float = Field(25.0, ge=0.0, le=90.0, description="Topographical slope angle in degrees")
    rainfall_mm_hr: float = Field(45.0, ge=0.0, le=500.0, description="Precipitation rate in mm/hour")
    elevation_m: Optional[float] = Field(1200.0, description="Terrain elevation in meters above sea level")
    river_level_m: Optional[float] = Field(2.5, description="Current river water level stage in meters")
    flood_threshold_m: Optional[float] = Field(4.5, description="River flood warning threshold in meters")
    report_confidence: Optional[float] = Field(0.0, ge=0.0, le=1.0, description="Ground truth citizen report confidence")
    road_type: Optional[str] = Field("SECONDARY", description="Road segment classification")


class EvidenceSummaryRequest(BaseModel):
    settlement_id: Optional[str] = Field(None, description="Settlement ID to generate justification for")
    road_segment: Optional[List[str]] = Field(None, description="[source_id, target_id] road segment pair")


@router.post("/risk-assess", summary="Calculate multi-hazard risk score, confidence level, and severity classification")
def assess_risk(request: RiskAssessmentRequest) -> Dict[str, Any]:
    # 1. Landslide Risk
    landslide_risk = calculate_landslide_risk(
        slope_deg=request.slope_deg,
        rainfall_mm_hr=request.rainfall_mm_hr,
        report_confidence=request.report_confidence or 0.0,
    )

    # 2. Flood Risk
    flood_risk = 0.0
    if request.river_level_m is not None and request.flood_threshold_m:
        flood_risk = calculate_flood_risk(
            river_level_m=request.river_level_m,
            threshold_m=request.flood_threshold_m,
            elevation_m=request.elevation_m or 1000.0,
        )

    # 3. Composite score
    primary = max(landslide_risk, flood_risk)
    secondary = min(landslide_risk, flood_risk)
    composite = round(min(1.0, primary + 0.20 * secondary), 4)

    # Severity classification
    if composite >= 0.85:
        severity = "CRITICAL"
    elif composite >= 0.50:
        severity = "HIGH"
    elif composite >= 0.30:
        severity = "MODERATE"
    else:
        severity = "LOW"

    # Confidence level based on available evidence
    factors_count = 2  # slope + rainfall
    if request.river_level_m is not None:
        factors_count += 1
    if (request.report_confidence or 0.0) > 0.0:
        factors_count += 2

    confidence = "HIGH" if factors_count >= 4 else ("MEDIUM" if factors_count >= 2 else "LOW")

    return {
        "risk_score": composite,
        "risk_score_percent": round(composite * 100.0, 2),
        "severity_classification": severity,
        "confidence_level": confidence,
        "breakdown": {
            "landslide_risk": landslide_risk,
            "flood_risk": flood_risk,
            "slope_deg": request.slope_deg,
            "rainfall_mm_hr": request.rainfall_mm_hr,
            "report_confidence": request.report_confidence or 0.0,
        },
    }


@router.post("/evidence-summary", summary="Generate automated text justifications detailing risk contributing factors")
def generate_evidence_summary(request: EvidenceSummaryRequest) -> Dict[str, Any]:
    state = get_system_state()
    graph = state.get_graph()

    summary_items = []

    # If settlement ID provided
    if request.settlement_id:
        sid = request.settlement_id
        if sid in graph:
            node = graph.nodes[sid]
            slope = node.get("slope_deg", 15.0)
            elev = node.get("elevation_m", 1000.0)
            pop = node.get("population", 5000)
            name = node.get("name", sid)

            connected_edges = list(graph.edges(sid, data=True))
            impassable_count = sum(1 for _, _, d in connected_edges if d.get("status") == "IMPASSABLE")
            partially_count = sum(1 for _, _, d in connected_edges if d.get("status") == "PARTIALLY_BLOCKED")

            text = (
                f"Settlement {name} ({sid}) is located at {elev}m elevation with a {slope} deg slope. "
                f"Population: {pop:,}. Current road access status: {len(connected_edges) - impassable_count - partially_count} open, "
                f"{partially_count} delayed, {impassable_count} impassable corridors."
            )
            summary_items.append({
                "target_type": "SETTLEMENT",
                "id": sid,
                "justification": text,
                "slope_deg": slope,
                "elevation_m": elev,
            })

    # If road segment provided
    if request.road_segment and len(request.road_segment) == 2:
        u, v = request.road_segment[0], request.road_segment[1]
        if graph.has_edge(u, v):
            data = graph[u][v]
            status = data.get("status", "ACCESSIBLE")
            risk = data.get("risk_score", 0.0)
            length = data.get("length_km", 0.0)
            road_type = data.get("road_type", "PRIMARY")
            eff_cost = data.get("effective_cost", 0.0)

            u_name = graph.nodes[u].get("name", u)
            v_name = graph.nodes[v].get("name", v)

            text = (
                f"Road Segment {u} ({u_name}) <-> {v} ({v_name}) is classified as {road_type} ({length} km). "
                f"Operational Status: {status} with composite hazard risk {risk:.2f}. "
                f"Effective routing cost weight: {eff_cost} min."
            )
            summary_items.append({
                "target_type": "ROAD_SEGMENT",
                "segment": [u, v],
                "justification": text,
                "risk_score": risk,
                "status": status,
            })

    if not summary_items:
        raise HTTPException(status_code=404, detail="No matching settlement or road segment found for evidence generation.")

    return {
        "total_summaries": len(summary_items),
        "evidence_reports": summary_items,
    }
