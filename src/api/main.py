from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pandas as pd
import json
import os
import sys
import logging
import httpx
from sqlalchemy import create_engine, event, text
# Configure v18.3 Industrial Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AviationSingularity")

# Ensure project root is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.optimizer.dt_solver import DigitalTwinSolver
from src.generator.synthetic_env import AdvancedAirlineSimulator
from src.optimizer.trajectory_a_star import TrajectoryPlannerAStar
from src.security.ot_monitor import OTSecurityMonitor
from src.models.causal_intelligence import BayesianCausalModel
from src.analytics.kpi_engine import AviationKPIEngine
from src.analytics.foresight_engine import foresight_engine
from src.data_connectors.live_sync import ExternalDataConnector
from src.models.evolution_engine import evolution_engine
from src.models.cognitive_narrative import narrator
import asyncio

from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(brain_evolution_loop())
    yield

app = FastAPI(title="Aviation Singularity Enterprise API", lifespan=lifespan)

# SQLite with WAL journal mode for concurrent read/write performance
engine = create_engine(
    'sqlite:///aviation.db',
    echo=False,
    connect_args={"check_same_thread": False},
)

@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_conn, _record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")   # concurrent readers don't block writers
    cursor.execute("PRAGMA synchronous=NORMAL")  # safe + faster than FULL
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# v38.0: Strategic Geographic Registry
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
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

# CORS: restrict to explicitly allowed origins via environment variable.
# Set ALLOWED_ORIGINS="http://localhost:8501,https://yourdomain.com" in production.
# Falls back to localhost only when the variable is unset.
_raw_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

# Global State (Mocking a database/session)
class AppState:
    def __init__(self):
        self.ot_monitor = OTSecurityMonitor()
        self.causal = BayesianCausalModel()
        self.kpi_engine = AviationKPIEngine()
        self.data_sync = ExternalDataConnector()
        self._load_or_generate()
        self.solver = DigitalTwinSolver(self.df)

    def _load_or_generate(self):
        try:
            self.df = pd.read_sql('flights', engine)
            self.df['departure_time'] = pd.to_datetime(self.df['departure_time'])
            self.df['arrival_time'] = pd.to_datetime(self.df['arrival_time'])
            logger.info("📦 DB Loaded: Operational state retrieved from aviation.db")
        except Exception:
            logger.info("Initializing fresh scenario...")
            from src.generator.synthetic_env import AdvancedAirlineSimulator
            self.sim = AdvancedAirlineSimulator()
            self.df = self.sim.generate_full_scenario(days=1)
            self.save()

    def save(self):
        try:
            self.df.to_sql('flights', engine, if_exists='replace', index=False)
            # Notify connected clients about State changes
        except Exception as e:
            logger.warning(f"DB Save Error: {e}")

state = AppState()

@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# v22.0: Background Evolution Task (Every 15 Minutes)
async def brain_evolution_loop():
    while True:
        await asyncio.sleep(15 * 60) # 15 Minutes
        success = evolution_engine.evolve_model()
        if success:
            logger.info("🧠 NEURAL EVOLUTION: Policy improved based on real-world trajectories.")

# Lifespan task created via asynccontextmanager (v18.4 Fix)

@app.get("/api/scenario")
async def get_scenario():
    # v38.0: Enrich Scenario with Geographic Context
    df_copy = state.df.copy()
    
    # Inject O&D Coordinates for Tactical Visualization
    df_copy['origin_lat'] = df_copy['origin'].map(lambda x: AIRPORTS.get(x, {}).get('lat'))
    df_copy['origin_lon'] = df_copy['origin'].map(lambda x: AIRPORTS.get(x, {}).get('lon'))
    df_copy['dest_lat'] = df_copy['destination'].map(lambda x: AIRPORTS.get(x, {}).get('lat'))
    df_copy['dest_lon'] = df_copy['destination'].map(lambda x: AIRPORTS.get(x, {}).get('lon'))
    
    # v38.1: Provide current positional estimates for the 3D Engine
    df_copy['lat'] = df_copy['origin_lat']
    df_copy['lon'] = df_copy['origin_lon']
    
    data_json = df_copy.to_json(orient='records', date_format='iso')
    return json.loads(data_json)

@app.get("/api/airports")
async def get_airports():
    return AIRPORTS

@app.get("/api/analytics/kpi")
async def get_kpis():
    return state.kpi_engine.calculate_fleet_kpis(state.df)

@app.get("/api/sync/live-traffic")
async def get_live_traffic():
    """
    v35.4 Resilient Radar: Fetch real-time ADS-B with Synthetic Fallback.
    """
    # IST Bounding Box (Lat/Lon)
    params = {"lamin": 39.0, "lamax": 43.5, "lomin": 24.5, "lomax": 32.5}
    url = "https://opensky-network.org/api/states/all"
    
    async with httpx.AsyncClient() as client:
        try:
            # v35.4: Reduced timeout to fail fast and trigger fallback
            response = await client.get(url, params=params, timeout=8)
            if response.status_code == 200:
                data = response.json()
                states = data.get("states", [])
                flights = []
                for s in (states or []):
                    if s[5] is None or s[6] is None: continue # Skip invalid position
                    raw_flight = {
                        "flight_id": s[1].strip() if s[1] else s[0],
                        "lat": s[6],
                        "lon": s[5],
                        "alt": s[7] or 3000,
                        "on_ground": s[8],
                        "velocity": s[9] or 250,
                        "heading": s[10] or 0
                    }
                    
                    # v22.0: Neural Inference
                    intel = evolution_engine.infer_flight_meta(raw_flight, None, len(states))
                    raw_flight.update(intel)
                    flights.append(raw_flight)
                
                logger.info(f"OpenSky Sync: {len(flights)} aircraft ingested.")
                return {"active_flights": flights, "count": len(flights), "source": "OpenSky Live"}
        except Exception as e:
            logger.warning(f"OpenSky Node Offline: {str(e)}. Engaging Synthetic Radar System...")

    # v35.4 Fallback: Generate Realistic Synthetic Traffic for IST Hub
    import random
    sync_flights = []
    for i in range(25):
        raw_flight = {
            "flight_id": f"S-{random.randint(100, 999)}",
            "lat": 41.27 + random.uniform(-1.5, 1.5),
            "lon": 28.74 + random.uniform(-2.0, 2.0),
            "alt": random.randint(2000, 10000),
            "on_ground": False,
            "velocity": random.randint(200, 450),
            "heading": random.randint(0, 359)
        }
        intel = evolution_engine.infer_flight_meta(raw_flight, None, 25)
        raw_flight.update(intel)
        sync_flights.append(raw_flight)
    
    return {
        "active_flights": sync_flights, 
        "count": len(sync_flights), 
        "source": "Synthetic Radar (Fallback Active)",
        "offline": True
    }

@app.get("/api/evolution/summary")
async def get_evolution_summary():
    """
    v23.0 Brain Stats: Report online learning progress.
    """
    return evolution_engine.get_stats()

class EvidenceData(BaseModel):
    observation: list
    reward: float

@app.post("/api/evolution/summary")
async def post_evolution_evidence(data: EvidenceData):
    """
    v32.0 Intelligence Bridge: Receive real-world experiences from the tactical map.
    """
    evolution_engine.collect_experience(data.observation, [0], data.reward)
    return {"status": "success", "buffered": len(evolution_engine.experience_buffer)}

from src.analytics.forecast_engine import forecaster
from src.api.report_generator import auditor

@app.get("/api/analytics/forecast")
async def get_forecast():
    """
    v18.0 Oracle: Deliver 7-day predictive operational outlook.
    """
    try:
        # Convert df to records if get_current_scenario is internal
        scenario = state.df.to_dict(orient='records')
        return forecaster.get_forecast(scenario)
    except Exception as e:
        logger.error(f"Oracle Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai/narrative")
async def get_ai_narrative():
    """
    v34.0 Cognitive Briefing: Gemma local LLM report based on real-time tactical state.
    """
    # v34.1: Tactical Filtering - Only send critical fields to save context tokens
    filtered_flights = []
    if state.df is not None:
        for _, row in state.df.head(5).iterrows():
            filtered_flights.append({
                "ID": row.get("flight_id"),
                "Stat": row.get("status"),
                "Delay": row.get("assigned_delay", 0),
                "LF": row.get("load_factor", 0)
            })
    
    # 🧠 Generate local inference report (Offloaded to thread to prevent blocking)
    # v35.1: Adding a random seed for variety
    import random
    report = await asyncio.to_thread(
        narrator.generate_briefing, 
        str(filtered_flights), 
        "Active Fleet: " + str(len(state.df) if state.df is not None else 0) + " | Foresight: T+30 Prediction Active",
        seed=random.randint(1, 1000000)
    )
    return {"report": report, "agent": "Gemma-2-2B-Cognitive"}

@app.get("/api/analytics/foresight-heatmap")
async def get_foresight_heatmap():
    """
    v35.0 Prediction Heatmap: Provides GeoJSON heatmap data for T+30 congestion zones.
    """
    fleet = state.df.to_dict(orient="records") if state.df is not None else []
    geojson = foresight_engine.generate_congestion_geojson(fleet)
    return geojson

@app.get("/api/report")
async def get_operational_report():
    """
    v18.3 Strategic Audit: Generate a structured operational integrity report.
    """
    try:
        scenario = state.df.to_dict(orient='records')
        kpis = state.kpi_engine.calculate_fleet_kpis(state.df)
        report_text = auditor.generate_summary(scenario, kpis)
        return {"report": report_text}
    except Exception as e:
        logger.error(f"Report Generation Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/optimize")
async def ai_optimize():
    """
    v18.0 Neural Commander: Execute autonomous disruption recovery 
    using the trained Reinforcement Learning agent.
    """
    try:
        # v18.3 Fix: Use state.solver non-blocking
        def _run_ai_solve():
            return state.solver.solve_with_windows(max_time_per_window=3)
        
        result = await asyncio.to_thread(_run_ai_solve)
        if result is not None:
             state.df = result
             state.save()
             await manager.broadcast("SCENARIO_UPDATED")
        return {
            "status": "success",
            "agent": "Neural Commander v1 (PPO)",
            "decisions": len(result) if result is not None else 0,
            "message": "AI-Driven reactive plan deployed."
        }
    except Exception as e:
        logger.error(f"AI Optimize Error: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.get("/api/sync/live")
async def sync_live():
    # 🌐 v17.0 Real-World Data Sync
    sync_result = state.data_sync.sync_all()
    # Logic: Injection of live weather risk into the current scenario could go here
    return sync_result

@app.post("/api/optimize")
async def optimize(window_size: int = 6):
    try:
        logger.info(f"⚡ [v17.1] Re-Optimization Triggered. Window Size: {window_size}h")
        
        def _run_solve():
            solver = DigitalTwinSolver(state.df)
            return solver.solve_with_windows(window_size_hrs=4, max_time_per_window=3)
            
        result = await asyncio.to_thread(_run_solve)
        
        if result is not None:
            state.df = result
            state.save()
            await manager.broadcast("SCENARIO_UPDATED")
            logger.info("✅ Optimization Success.")
            return {"status": "success", "message": f"Optimization complete for {len(result)} legs."}
        else:
            raise ValueError("Solver returned null result.")
            
    except Exception as e:
        logger.error(f"❌ Optimization Error: {str(e)}")
        # Even if optimization fails, we return a success status to unblock the UI 
        # but with the old data preserved.
        return {"status": "partial_success", "error": str(e), "message": "Optimization encountered an issue; original plan preserved."}

@app.post("/api/stress-test")
async def stress_test(hub: str = 'IST'):
    try:
        # 1. Trigger Disruption
        from src.generator.synthetic_env import AdvancedAirlineSimulator
        sim = AdvancedAirlineSimulator()
        state.df = sim.trigger_disruption(state.df, hub=hub)
        
        # 2. Run Reactive Recovery Non-Blocking
        def _run_shock():
            solver = DigitalTwinSolver(state.df)
            return solver.solve_disruption(f"Mass Delay at {hub}")
            
        result = await asyncio.to_thread(_run_shock)
        if result is not None:
            state.df = result
            state.save()
            await manager.broadcast("SCENARIO_UPDATED")
            return {"status": "success", "message": f"Shock recovery completed for {hub}"}
        raise HTTPException(status_code=500, detail="Recovery failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve Static Files for v14.0 Frontend
web_dir = os.path.join(os.path.dirname(__file__), '../web')
app.mount("/", StaticFiles(directory=web_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8501)
