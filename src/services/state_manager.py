"""In-memory thread-safe state manager holding active NetworkX graph and emergency alerts."""
from pathlib import Path
import threading
from typing import Any, Dict, List, Optional, Tuple
import geopandas as gpd
import networkx as nx

from src.graph_updater import update_graph_weights
from src.services.alert_engine import check_and_raise_alerts
from src.services.failure_guardrails import FailureGuardrailEngine
from src.spatial_builder import build_road_graph, generate_district_data


class SystemState:
    """
    Singleton in-memory system state holding the operational road network graph,
    settlement GIS metadata, and live emergency alerts.
    """
    _instance: Optional["SystemState"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "SystemState":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SystemState, cls).__new__(cls)
                cls._instance._initialize_state()
            return cls._instance

    def _initialize_state(self) -> None:
        """Initialize settlements GIS data, road graph, and alert storage."""
        self._state_lock = threading.RLock()
        self.alerts: List[Dict[str, Any]] = []
        self.guardrail = FailureGuardrailEngine()

        # Attempt to load from data/ GeoJSON or generate afresh
        data_dir = Path("data")
        settlements_path = data_dir / "settlements.geojson"

        if settlements_path.exists():
            try:
                self.settlements_gdf = gpd.read_file(settlements_path)
            except Exception:
                self.settlements_gdf = generate_district_data()
        else:
            self.settlements_gdf = generate_district_data()

        # Build connected road network graph
        self.graph = build_road_graph(self.settlements_gdf)

        # Baseline weather initialization
        baseline_rain = {sid: 5.0 for sid in self.graph.nodes}
        update_graph_weights(self.graph, {"rainfall": baseline_rain})

    def get_graph(self) -> nx.Graph:
        """Get thread-safe reference to the active NetworkX road graph."""
        with self._state_lock:
            return self.graph

    def get_settlements_gdf(self) -> gpd.GeoDataFrame:
        """Get the settlements GeoPandas GeoDataFrame."""
        with self._state_lock:
            return self.settlements_gdf

    def update_telemetry(self, telemetry_payload: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Thread-safely apply incoming telemetry payload to graph weights,
        evaluate edge status mutations, and raise dynamic alerts.
        Applies Failure Guardrail validation to sanitize sensor anomalies.
        """
        with self._state_lock:
            # 1. Apply Failure Guardrail validation
            sanitized_payload, guardrail_results = self.guardrail.validate_telemetry_batch(
                telemetry_payload, self.graph
            )

            # Capture previous edge statuses & risks
            old_edge_states = {}
            for u, v, data in self.graph.edges(data=True):
                old_edge_states[(u, v)] = {
                    "status": data.get("status", "ACCESSIBLE"),
                    "risk_score": float(data.get("risk_score", 0.0)),
                }

            # Mutate graph weights dynamically
            update_graph_weights(self.graph, sanitized_payload)

            # Check for newly triggered or escalated alerts
            new_alerts: List[Dict[str, Any]] = []
            for u, v, data in self.graph.edges(data=True):
                old_state = old_edge_states.get((u, v), {"status": "ACCESSIBLE", "risk_score": 0.0})
                new_status = data.get("status", "ACCESSIBLE")
                new_risk = float(data.get("risk_score", 0.0))

                # If status changed or risk crossed threshold
                if (
                    new_status != old_state["status"]
                    or (new_risk >= 0.50 and old_state["risk_score"] < 0.50)
                    or (new_risk >= 0.85 and old_state["risk_score"] < 0.85)
                ):
                    alert = check_and_raise_alerts(
                        edge_id=[u, v],
                        old_status=old_state["status"],
                        new_status=new_status,
                        risk_score=new_risk,
                    )
                    if alert:
                        new_alerts.append(alert)
                        self.alerts.append(alert)

            summary = {
                "total_nodes": self.graph.number_of_nodes(),
                "total_edges": self.graph.number_of_edges(),
                "new_alerts_count": len(new_alerts),
                "active_alerts_count": len(self.alerts),
            }

            return new_alerts, summary

    def get_alerts(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Return list of active emergency alerts (most recent first)."""
        with self._state_lock:
            reversed_alerts = list(reversed(self.alerts))
            if limit is not None and limit > 0:
                return reversed_alerts[:limit]
            return reversed_alerts

    def clear_alerts(self) -> None:
        """Clear the active alerts buffer."""
        with self._state_lock:
            self.alerts.clear()

    def reset_to_baseline(self) -> None:
        """Reset road graph weights and alerts back to clear weather conditions."""
        with self._state_lock:
            self.alerts.clear()
            baseline_rain = {sid: 5.0 for sid in self.graph.nodes}
            update_graph_weights(
                self.graph,
                {
                    "rainfall": baseline_rain,
                    "river_gauges": [],
                    "reports": [],
                    "edge_overrides": {},
                },
            )


# Global helper accessor
def get_system_state() -> SystemState:
    return SystemState()
