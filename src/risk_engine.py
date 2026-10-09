"""Hazard risk calculation engine for landslides, floods, and composite edge risk."""
import math
from typing import Any, Dict, List, Optional, Tuple


def calculate_landslide_risk(
    slope_deg: float,
    rainfall_mm_hr: float,
    report_confidence: float = 0.0,
) -> float:
    """
    Calculate normalized landslide susceptibility index [0.0, 1.0].
    Steep slopes (>25 deg) and intense precipitation (>30 mm/hr) drive non-linear exponential risk escalation.
    Crowdsourced report confidence provides direct ground confirmation multiplier.
    """
    # 1. Slope susceptibility factor: S-curve transition around 25-35 degrees
    slope_clamped = max(0.0, min(60.0, slope_deg))
    if slope_clamped <= 10.0:
        slope_factor = slope_clamped / 50.0  # Minimal risk for flat areas
    elif slope_clamped <= 25.0:
        slope_factor = 0.2 + ((slope_clamped - 10.0) / 15.0) * 0.35  # Moderate risk (0.2 -> 0.55)
    else:
        # Steep terrain (>25 deg) triggers rapid escalation
        slope_factor = 0.55 + min(0.45, ((slope_clamped - 25.0) / 20.0) ** 0.85 * 0.45)

    # 2. Rainfall intensity factor: exponential trigger above threshold of 30 mm/hr
    rain_clamped = max(0.0, min(150.0, rainfall_mm_hr))
    if rain_clamped < 10.0:
        rain_factor = (rain_clamped / 10.0) * 0.15
    elif rain_clamped < 30.0:
        rain_factor = 0.15 + ((rain_clamped - 10.0) / 20.0) * 0.35  # Up to 0.50
    else:
        # Heavy storm > 30 mm/hr
        excess = min(120.0, rain_clamped - 30.0)
        rain_factor = 0.50 + 0.50 * (1.0 - math.exp(-excess / 35.0))

    # 3. Non-linear coupled environmental risk
    env_risk = (slope_factor ** 0.85) * (rain_factor ** 0.85)

    # 4. Integrate citizen ground validation report
    conf_clamped = max(0.0, min(1.0, report_confidence))
    if conf_clamped > 0.0:
        # Ground truth observation directly indicates physical occurrence
        report_impact = conf_clamped * 0.90
        composite = max(env_risk, report_impact) + (env_risk * conf_clamped * 0.20)
    else:
        composite = env_risk

    return round(float(max(0.0, min(1.0, composite))), 4)


def calculate_flood_risk(
    river_level_m: float,
    threshold_m: float,
    elevation_m: float,
) -> float:
    """
    Calculate normalized riverine flood susceptibility index [0.0, 1.0].
    Stage levels approaching or exceeding flood thresholds in low elevation valleys (<1000m)
    dramatically increase inundation hazard.
    """
    if threshold_m <= 0.0:
        return 0.0

    # 1. Hydrometric stage ratio
    stage_ratio = max(0.0, river_level_m / threshold_m)
    if stage_ratio < 0.6:
        stage_risk = (stage_ratio / 0.6) * 0.15
    elif stage_ratio < 1.0:
        stage_risk = 0.15 + ((stage_ratio - 0.6) / 0.4) * 0.45  # 0.15 -> 0.60
    else:
        # Over threshold
        overflow = min(1.5, stage_ratio - 1.0)
        stage_risk = 0.60 + 0.40 * (1.0 - math.exp(-overflow * 2.5))

    # 2. Topographical elevation vulnerability (Valley basins < 1000m are most vulnerable)
    elev_clamped = max(400.0, min(3500.0, elevation_m))
    if elev_clamped <= 1000.0:
        elev_multiplier = 1.0 - (elev_clamped - 400.0) / 3000.0  # 1.0 -> 0.80
    elif elev_clamped <= 2000.0:
        elev_multiplier = 0.80 - ((elev_clamped - 1000.0) / 1000.0) * 0.45  # 0.80 -> 0.35
    else:
        elev_multiplier = max(0.1, 0.35 - ((elev_clamped - 2000.0) / 1500.0) * 0.25)

    composite = stage_risk * elev_multiplier
    return round(float(max(0.0, min(1.0, composite))), 4)


def aggregate_edge_risk(
    road_segment_data: Dict[str, Any],
    source_node_data: Dict[str, Any],
    target_node_data: Dict[str, Any],
    rainfall_data: Optional[Dict[str, float]] = None,
    river_gauge_data: Optional[List[Dict[str, Any]]] = None,
    reports_data: Optional[List[Dict[str, Any]]] = None,
) -> float:
    """
    Synthesize environmental telemetry and ground reports into a unified edge risk score [0.0, 1.0].
    """
    rainfall_data = rainfall_data or {}
    river_gauge_data = river_gauge_data or []
    reports_data = reports_data or []

    source_id = road_segment_data.get("source_id", "")
    target_id = road_segment_data.get("target_id", "")

    # Topographical context from endpoints
    avg_slope = (source_node_data.get("slope_deg", 15.0) + target_node_data.get("slope_deg", 15.0)) / 2.0
    min_elevation = min(source_node_data.get("elevation_m", 1000.0), target_node_data.get("elevation_m", 1000.0))

    # Rainfall at endpoints
    rain_src = rainfall_data.get(source_id, 0.0)
    rain_tgt = rainfall_data.get(target_id, 0.0)
    effective_rain = max(rain_src, rain_tgt)

    # Check for relevant crowdsourced reports impacting this edge or nodes
    max_report_conf = 0.0
    direct_edge_report = False
    for rep in reports_data:
        rep_edge_raw = rep.get("edge")
        rep_edge = tuple(rep_edge_raw) if isinstance(rep_edge_raw, (list, tuple)) and len(rep_edge_raw) == 2 else None
        if rep_edge in [(source_id, target_id), (target_id, source_id)]:
            conf = float(rep.get("user_reliability_score", 0.90))
            max_report_conf = max(max_report_conf, conf)
            direct_edge_report = True
        elif rep.get("settlement_id") in [source_id, target_id]:
            conf = float(rep.get("user_reliability_score", 0.70)) * 0.8
            max_report_conf = max(max_report_conf, conf)

    # Calculate Landslide Risk
    landslide_risk = calculate_landslide_risk(
        slope_deg=avg_slope,
        rainfall_mm_hr=effective_rain,
        report_confidence=max_report_conf,
    )

    # Calculate Flood Risk across monitoring stations
    flood_risk = 0.0
    for gauge in river_gauge_data:
        lvl = gauge.get("level_meters", 0.0)
        thresh = gauge.get("flood_threshold_meters", 5.0)
        f_risk = calculate_flood_risk(river_level_m=lvl, threshold_m=thresh, elevation_m=min_elevation)
        flood_risk = max(flood_risk, f_risk)

    # Road type vulnerability modifier
    road_type = str(road_segment_data.get("road_type", "SECONDARY"))
    type_multiplier = {
        "HIGHWAY": 0.92,
        "PRIMARY": 0.98,
        "SECONDARY": 1.05,
        "DIRT_TRACK": 1.25,
    }.get(road_type, 1.0)

    # Composite maximum hazard rule + additive multi-hazard stress
    primary_hazard = max(landslide_risk, flood_risk)
    secondary_hazard = min(landslide_risk, flood_risk)

    if direct_edge_report and max_report_conf >= 0.90:
        # A confirmed direct physical blockage overrides road design mitigation
        raw_composite = max(primary_hazard, 0.88 + 0.10 * max_report_conf)
    else:
        raw_composite = (primary_hazard + 0.20 * secondary_hazard) * type_multiplier

    # Direct manual hazard override if explicitly set
    if "hazard_risk_override" in road_segment_data:
        raw_composite = max(raw_composite, float(road_segment_data["hazard_risk_override"]))

    return round(float(max(0.0, min(1.0, raw_composite))), 4)
