"""WebSocket connection manager for real-time telemetry and emergency alert broadcasting."""
from typing import Any, Dict, List
from fastapi import WebSocket


class ConnectionManager:
    """Manages active WebSocket client connections and provides broadcast capabilities."""

    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept incoming client WebSocket connection and register."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Unregister disconnected client WebSocket."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcast structured JSON payload to all connected subscribers."""
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(dead)


# Global singleton manager
ws_manager = ConnectionManager()
