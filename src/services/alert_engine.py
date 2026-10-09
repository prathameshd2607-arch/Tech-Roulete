"""Dynamic alert engine for real-time hazard severity evaluation and notification generation."""
from datetime import datetime, timezone
import uuid
from typing import Any, Dict, Optional, Tuple, Union


def check_and_raise_alerts(
    edge_id: Union[Tuple[str, str], list],
    old_status: str,
    new_status: str,
    risk_score: float,
) -> Optional[Dict[str, Any]]:
    """
    Evaluate edge transition and risk score to generate emergency alert payloads:
      - CRITICAL: new_status == 'IMPASSABLE' or risk_score >= 0.85
      - WARNING: new_status == 'PARTIALLY_BLOCKED' or 0.50 <= risk_score < 0.85
      - None: if edge remains safe and ACCESSIBLE with low risk (< 0.50)
    """
    u, v = edge_id[0], edge_id[1]
    norm_edge = [u, v]
    timestamp_str = datetime.now(timezone.utc).isoformat()

    if new_status == "IMPASSABLE" or risk_score >= 0.85:
        severity = "CRITICAL"
        message = (
            f"CRITICAL DISASTER ALERT: Road corridor {u} <-> {v} is IMPASSABLE! "
            f"Risk score reached {risk_score:.2f}. Emergency rerouting required."
        )
    elif new_status == "PARTIALLY_BLOCKED" or (0.50 <= risk_score < 0.85):
        severity = "WARNING"
        message = (
            f"HAZARD WARNING: Road corridor {u} <-> {v} is PARTIALLY_BLOCKED. "
            f"Elevated risk score {risk_score:.2f}. Expect severe travel delays."
        )
    elif old_status in ["IMPASSABLE", "PARTIALLY_BLOCKED"] and new_status == "ACCESSIBLE":
        severity = "INFO"
        message = f"ALL-CLEAR: Road corridor {u} <-> {v} has returned to ACCESSIBLE status (Risk: {risk_score:.2f})."
    else:
        # Normal safe status without warning
        return None

    alert_id = f"ALERT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"

    return {
        "alert_id": alert_id,
        "severity": severity,
        "affected_edge": norm_edge,
        "risk_score": round(float(risk_score), 4),
        "old_status": old_status,
        "new_status": new_status,
        "message": message,
        "timestamp": timestamp_str,
    }
