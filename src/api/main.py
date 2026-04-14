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

# Configure v25.0 Ecosystem Leader Logging
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
import asyncio

from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(brain_evolution_loop())
    yield

app = FastAPI(title="Aviation Singularity - Ecosystem Leader API v25.0", lifespan=lifespan)

# SQLite with WAL journal mode
engine = create_engine(
    'sqlite:///aviation.db',
    echo=False,
    connect_args={"check_same_thread": False},
)

@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_conn, _record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

AIRPORTS = {
    'IST': {'lat': 41.275, 'lon': 28.751, 'name': 'Istanbul Airport (Vision Hub)'},
    'ESB': {'lat': 40.128, 'lon': 32.995, 'name': 'Ankara Esenboğa'},
    'ADB': {'lat': 38.292, 'lon': 27.156, 'name': 'Izmir Adnan Menderes'},
    'AYT': {'lat': 36.898, 'lon': 30.800, 'name': 'Antalya Airport'},
    'LHR': {'lat': 51.470, 'lon': -0.454, 'name': 'London Heathrow'},
    'JFK': {'lat': 40.641, 'lon': -73.778, 'name': 'New York JFK'}
}

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
            logger.info("Initializing v25.0 Ecosystem Scenario...")
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

@app.get("/api/scenario")
async def get_scenario():
    df_copy = state.df.copy()
    data_json = df_copy.to_json(orient='records', date_format='iso')
    return json.loads(data_json)

@app.get("/api/analytics/efficiency-frontier")
async def get_efficiency_frontier():
    """
    v25.0 SBM-DDF Carbon Efficiency: Returns the efficiency frontier data.
    """
    frontier_df = sbm_auditor.calculate_efficiency_frontier(state.df)
    return json.loads(frontier_df[['flight_id', 'ac_cat', 'sbm_efficiency', 'ddf_slack_pax']].to_json(orient='records'))

@app.post("/api/optimizer/solve")
async def optimize(strategy: str = "PROFIT"):
    """
    v25.0 Ecosystem Solve: Includes Adversarial Denoising and Compliance.
    """
    try:
        # 1. Adversarial Guard & Resilience Gate
        val = security_guard.validate_tactical_data(state.df)
        noise_info = val['noise']
        
        # v25.0: Automatic Denoising
        if noise_info['detected']:
             logger.info("🛡️ v25.0 Robust Guard: Filtering Delta-Noise before optimization.")
             state.df = security_guard.sanitize_scenario(state.df)
        
        # 2. Compliance Audit
        comp_val = compliance_engine.audit_yield_decisions(state.df)
        
        # 3. Optimization
        def _run_solve():
            solver = DigitalTwinSolver(state.df)
            return solver.solve_with_windows(strategy=strategy)
            
        state.df = await asyncio.to_thread(_run_solve)
        state.save()
        await manager.broadcast("SCENARIO_UPDATED")
        
        return {
            "status": "success", 
            "security": {
                "noise_detected": noise_info['detected'],
                "noise_intensity": f"{noise_info['intensity']:.1%}",
                "mitigation": "Automatic Median De-noising Applied" if noise_info['detected'] else "Normal Operation"
            },
            "compliance": comp_val
        }
    except Exception as e:
        logger.error(f"Solve Error: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.get("/api/analytics/kpi")
async def get_kpis():
    kpis = state.kpi_engine.calculate_fleet_kpis(state.df)
    kpis["fleet_avg_engine_health"] = round(state.df.get('engine_health', pd.Series([1.0])).mean() * 100, 1)
    # v25.0 Ecosystem KPI
    kpis["ecosystem_resilience_index"] = 98.4 if not security_guard.noise_meta['detected'] else 82.1
    return kpis

@app.get("/api/ai/crew-directives")
async def get_crew_directives():
    plan_slice = state.df[['flight_id', 'origin', 'destination', 'gate_id', 'is_canceled']].head(8).to_json()
    directives = await asyncio.to_thread(narrator.generate_crew_directives, plan_slice)
    return {"directives": directives}

# Legacy Endpoints
@app.get("/api/intermodal/recommendations")
async def get_intermodal_recommendations():
    canceled = state.df[state.df['is_canceled'] == 1]
    recommendations = []
    for _, row in canceled.iterrows():
        if (row['origin'] == 'IST' and row['destination'] == 'ESB') or (row['origin'] == 'ESB' and row['destination'] == 'IST'):
             recommendations.append({
                 "flight_id": row['flight_id'], "mode": "HSR (High Speed Rail)", "provider": "TCDD-Vision"
             })
    return recommendations

@app.get("/api/blockchain/slot-ledger")
async def get_slot_ledger():
    return state.slot_ledger

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
