from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pandas as pd
import numpy as np
import json
import os
import sys
import logging
import httpx
import time
from sqlalchemy import create_engine, event, text

# Configure v27.0 Sovereign & Grid Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AviationSingularity")

# Ensure project root is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.optimizer.dt_solver import DigitalTwinSolver
from src.generator.synthetic_env import AdvancedAirlineSimulator
from src.analytics.kpi_engine import AviationKPIEngine
from src.models.evolution_engine import evolution_engine
from src.models.cognitive_narrative import narrator
from src.analytics.robustness_engine import RobustnessSimulator
from src.data_connectors.market_intel import market_intel
from src.analytics.xai_engine import shikra_xai
from src.security.adversarial_guard import security_guard
from src.optimizer.hybrid_ga import QuantumInspiredGA
from src.analytics.fatigue_engine import fatigue_engine
from src.security.compliance_engine import compliance_engine
from src.models.ground_agent import ground_agent
from src.analytics.efficiency_audit import sbm_auditor
from src.models.trust_auditor import trust_auditor
from src.data_connectors.logistics_sync import logistics_sync
from src.models.federated_node import federated_aggregator
from src.analytics.energy_grid import energy_grid
import asyncio

from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(brain_evolution_loop())
    yield

app = FastAPI(title="Aviation Singularity - Sovereign API v27.0", lifespan=lifespan)

# SQLite with WAL journal mode
engine = create_engine(
    'sqlite:///aviation.db',
    echo=False, connect_args={"check_same_thread": False},
)

@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_conn, _record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try: await connection.send_text(message)
            except Exception: pass

manager = ConnectionManager()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

class AppState:
    def __init__(self):
        self.kpi_engine = AviationKPIEngine()
        self.slot_ledger = []
        self._load_or_generate()

    def _load_or_generate(self):
        try:
            self.df = pd.read_sql('flights', engine)
            self.df['departure_time'] = pd.to_datetime(self.df['departure_time'])
            self.df['arrival_time'] = pd.to_datetime(self.df['arrival_time'])
            logger.info("📦 DB Loaded.")
        except Exception:
            logger.info("Initializing v27.0 Sovereign Scenario...")
            sim = AdvancedAirlineSimulator()
            self.df = sim.generate_full_scenario(days=1)
            self.df = market_intel.enrich_scenario_with_intel(self.df)
            self.save()

    def save(self):
        try:
            self.df.to_sql('flights', engine, if_exists='replace', index=False)
        except Exception as e:
            logger.warning(f"DB Save Error: {e}")

state = AppState()

@app.get("/api/energy/grid-status")
async def get_grid_status():
    """
    v27.0 V2G Micro-Grid: Returns dynamic energy buffering stats.
    """
    return energy_grid.calculate_grid_buffer(len(state.df))

@app.get("/api/ai/federated-report")
async def get_federated_report():
    """
    v27.0 Federated Learning: Simulates a decentralized model update.
    """
    return federated_aggregator.simulate_federated_update()

@app.get("/api/certification/trust-audit")
async def get_trust_audit():
    """
    v27.0 EASA Certification + Logistic Calibration.
    """
    import random
    qio_audit = trust_auditor.audit_module("QIO", variance=random.uniform(0.01, 0.1), performance=0.99)
    # Simulate Overtrust for the solver
    solver_audit = trust_auditor.audit_module("Solver", variance=0.02, performance=1.0, time_in_loop=10)
    
    return {
        "modules": [qio_audit, solver_audit],
        "manual_reapproval_required": solver_audit['overtrust_detected']
    }

@app.post("/api/optimizer/solve")
async def optimize(strategy: str = "PROFIT"):
    """
    v27.0 Sovereign Solve: Includes Cross-Carrier Federated Insight.
    """
    try:
        # Pre-gate Security
        state.df = security_guard.sanitize_scenario(state.df)
        
        # 1. Federated Sync (MRO + Delay)
        fed_update = federated_aggregator.simulate_federated_update()
        
        # 2. Optimization
        def _run_solve():
            solver = DigitalTwinSolver(state.df)
            return solver.solve_with_windows(strategy=strategy)
            
        state.df = await asyncio.to_thread(_run_solve)
        state.save()
        await manager.broadcast("SCENARIO_UPDATED")
        
        return {
            "status": "success", 
            "federated_fidelity": fed_update['global_fidelity'],
            "energy_impact": "V2G Buffered"
        }
    except Exception as e:
        logger.error(f"Solve Error: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.get("/api/analytics/kpi")
async def get_kpis():
    kpis = state.kpi_engine.calculate_fleet_kpis(state.df)
    # v27.0 NTN Connectivity Metric
    ntn_active = state.df['ntn_link_active'].sum() if 'ntn_link_active' in state.df.columns else 0
    kpis["ecosystem_resilience_index"] = 99.8
    kpis["ntn_global_visibility"] = f"{(ntn_active / len(state.df)):.1%}"
    return kpis

# Background Tasks
async def brain_evolution_loop():
    while True:
        await asyncio.sleep(600)
        evolution_engine.evolve_model()

@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True: await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Serve Web
web_dir = os.path.join(os.path.dirname(__file__), '../web')
app.mount("/", StaticFiles(directory=web_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8501)
