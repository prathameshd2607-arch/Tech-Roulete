"""Emergency alerts query and management endpoints."""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query

from src.services.state_manager import get_system_state

router = APIRouter(prefix="/api/v1/alerts", tags=["Emergency Alerts"])


@router.get("", summary="Retrieve active disaster emergency alerts")
def get_alerts(
    limit: Optional[int] = Query(None, ge=1, le=100, description="Maximum alerts to retrieve"),
    severity: Optional[str] = Query(None, description="Filter by severity: 'CRITICAL', 'WARNING', 'INFO'"),
) -> Dict[str, Any]:
    state = get_system_state()
    all_alerts = state.get_alerts(limit=None)

    if severity:
        filtered = [a for a in all_alerts if a.get("severity") == severity.upper()]
    else:
        filtered = all_alerts

    if limit is not None:
        filtered = filtered[:limit]

    return {
        "total_active_alerts": len(filtered),
        "alerts": filtered,
    }


@router.delete("", summary="Clear all active emergency alerts")
def clear_alerts() -> Dict[str, Any]:
    state = get_system_state()
    state.clear_alerts()
    return {
        "status": "SUCCESS",
        "message": "All emergency alerts cleared.",
    }
