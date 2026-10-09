"""FastAPI application initialization, middleware configuration, and router registration."""
from contextlib import asynccontextmanager
from typing import Any, Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes_admin import router as admin_router
from src.api.routes_alerts import router as alerts_router
from src.api.routes_audit import router as audit_router
from src.api.routes_engine import router as engine_router
from src.api.routes_responder import router as responder_router
from src.api.routes_routing import router as routing_router
from src.api.routes_telemetry import router as telemetry_router
from src.api.websocket_manager import ws_manager
from src.services.state_manager import get_system_state


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize state singleton on startup
    state = get_system_state()
    print(f"[FastAPI Lifespan] Initialized system state with {state.get_graph().number_of_nodes()} settlements.")
    yield
    print("[FastAPI Lifespan] Shutting down application services.")


app = FastAPI(
    title="Disaster Management Dynamic Routing API",
    description="Real-time multi-hazard telemetry ingestion, dynamic edge risk evaluation, and role-based operational control.",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Core API Routers
app.include_router(routing_router)
app.include_router(telemetry_router)
app.include_router(alerts_router)

# Register Phase 5 Role-Based Controllers
app.include_router(admin_router)
app.include_router(engine_router)
app.include_router(responder_router)
app.include_router(audit_router)


@app.get("/", summary="Root API Health and Status")
def root_status() -> Dict[str, Any]:
    state = get_system_state()
    graph = state.get_graph()
    return {
        "service": "Disaster Management Dynamic Routing API",
        "status": "ONLINE",
        "settlements_count": graph.number_of_nodes(),
        "road_segments_count": graph.number_of_edges(),
        "active_alerts_count": len(state.get_alerts()),
        "endpoints": {
            "route_calculation": "POST /api/v1/route",
            "telemetry_ingestion": "POST /api/v1/telemetry/ingest",
            "active_alerts": "GET /api/v1/alerts",
            "road_segments": "GET /api/v1/network/edges",
            "settlement_nodes": "GET /api/v1/network/nodes",
            "live_websocket": "WS /ws/telemetry",
            "docs": "/docs",
        },
    }


@app.get("/health", summary="Liveness and Readiness Probe")
def health_check() -> Dict[str, str]:
    return {"status": "healthy"}


@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    """
    WebSocket channel for live subscribers (monitoring dashboards, field rescue units).
    Broadcasts real-time risk mutations and emergency alert dispatches.
    """
    await ws_manager.connect(websocket)
    try:
        # Send initial welcome payload with active alerts count
        state = get_system_state()
        await websocket.send_json({
            "event_type": "CONNECTED",
            "message": "Connected to disaster telemetry live stream.",
            "active_alerts": len(state.get_alerts()),
        })
        while True:
            # Keep connection alive; accept any incoming control pings
            data = await websocket.receive_text()
            if data == "PING":
                await websocket.send_text("PONG")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)
