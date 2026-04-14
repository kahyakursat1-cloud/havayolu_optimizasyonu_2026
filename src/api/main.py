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

# Configure v23.0 Aero-Ecosystem Logging
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
import asyncio

from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(brain_evolution_loop())
    yield

app = FastAPI(title="Aviation Singularity - Aero-Ecosystem API v23.0", lifespan=lifespan)

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
    'IST': {'lat': 41.275, 'lon': 28.751, 'name': 'Istanbul Airport'},
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
        self.slot_ledger = [
            {"id": "BL-001", "time": "2026-06-01 10:00", "p1": "AC_001", "p2": "AC_042", "asset": "Slot IST-1400", "price": "500 CR"},
            {"id": "BL-002", "time": "2026-06-01 10:15", "p1": "AC_005", "p2": "AC_012", "asset": "Slot ESB-1130", "price": "320 CR"}
        ]
        self._load_or_generate()

    def _load_or_generate(self):
        try:
            self.df = pd.read_sql('flights', engine)
            self.df['departure_time'] = pd.to_datetime(self.df['departure_time'])
            self.df['arrival_time'] = pd.to_datetime(self.df['arrival_time'])
            logger.info("📦 DB Loaded.")
        except Exception:
            logger.info("Initializing fresh scenario...")
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

@app.get("/api/intermodal/recommendations")
async def get_intermodal_recommendations():
    """
    v23.0 Intermodal Sync: Recommend HSR (Train) alternatives for canceled flights.
    """
    canceled = state.df[state.df['is_canceled'] == 1]
    recommendations = []
    
    for _, row in canceled.iterrows():
        # Check if IST-ESB or IST-ADB corridor
        if (row['origin'] == 'IST' and row['destination'] == 'ESB') or (row['origin'] == 'ESB' and row['destination'] == 'IST'):
             recommendations.append({
                 "flight_id": row['flight_id'],
                 "mode": "HSR (High Speed Rail)",
                 "provider": "TCDD-Vision",
                 "departure": row['departure_time'].isoformat(),
                 "duration_mins": 210,
                 "seats_available": 45,
                 "co2_saving": row['co2_kg']
             })
             
    return recommendations

@app.get("/api/blockchain/slot-ledger")
async def get_slot_ledger():
    """
    v23.0 Decentralized Slot Market: Returns the simulated blockchain ledger.
    """
    return state.slot_ledger

@app.post("/api/optimizer/solve")
async def optimize(strategy: str = "PROFIT"):
    try:
        # Pre-gate
        validation = security_guard.validate_tactical_data(state.df)
        if not validation['is_safe']:
             state.df = security_guard.sanitize_scenario(state.df)
        
        # Optimization
        def _run_solve():
            solver = DigitalTwinSolver(state.df)
            return solver.solve_with_windows(strategy=strategy)
            
        state.df = await asyncio.to_thread(_run_solve)
        
        # Simulate a Blockchain Slot Swap during solve for visual demo
        import random
        new_trade = {
            "id": f"BL-{random.randint(100,999)}",
            "time": pd.Timestamp.now().isoformat(),
            "p1": f"AC_{random.randint(1,50):03d}",
            "p2": f"AC_{random.randint(1,50):03d}",
            "asset": f"Slot {random.choice(['IST','ESB','ADB'])}-{random.randint(10,22)}00",
            "price": f"{random.randint(100,800)} CR"
        }
        state.slot_ledger.insert(0, new_trade)
        
        state.save()
        await manager.broadcast("SCENARIO_UPDATED")
        return {"status": "success", "strategy": strategy, "security": validation}
    except Exception as e:
        logger.error(f"Solve Error: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.get("/api/analytics/kpi")
async def get_kpis():
    kpis = state.kpi_engine.calculate_fleet_kpis(state.df)
    # v23.0: Add Biological Risk Index (Fatigue)
    kpis["fleet_biological_fatigue"] = round(state.df.get('fatigue_score', pd.Series([0])).mean(), 2)
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
