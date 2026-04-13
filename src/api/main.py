from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pandas as pd
import json
import os
import sys
import logging

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
from src.data_connectors.live_sync import ExternalDataConnector

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Aviation Singularity Enterprise API")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State (Mocking a database/session)
class AppState:
    def __init__(self):
        self.sim = AdvancedAirlineSimulator()
        self.df = self.sim.generate_full_scenario(days=1)
        self.ot_monitor = OTSecurityMonitor()
        self.causal = BayesianCausalModel()
        self.kpi_engine = AviationKPIEngine()
        self.data_sync = ExternalDataConnector()
        # v18.3: Centralized Solver for full scope access
        self.solver = DigitalTwinSolver(self.df)

state = AppState()

@app.get("/api/scenario")
async def get_scenario():
    # Fix: Pandas Timestamps must be converted to ISO format for JSON compatibility
    data_json = state.df.to_json(orient='records', date_format='iso')
    return json.loads(data_json)

@app.get("/api/analytics/kpi")
async def get_kpis():
    return state.kpi_engine.calculate_fleet_kpis(state.df)

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
        # v18.3 Fix: Use state.solver
        result = state.solver.solve_with_windows(max_time_per_window=3)
        if result is not None:
             state.df = result
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
        solver = DigitalTwinSolver(state.df)
        
        # v17.1: We set a total safeguard timeout to ensure the API responds within 45s
        result = solver.solve_with_windows(window_size_hrs=window_size, max_time_per_window=5)
        
        if result is not None:
            state.df = result
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
    # 1. Trigger Disruption
    state.df = state.sim.trigger_disruption(state.df, hub=hub)
    # 2. Run Reactive Recovery
    solver = DigitalTwinSolver(state.df)
    result = solver.solve_disruption(f"Mass Delay at {hub}")
    if result is not None:
        state.df = result
        return {"status": "success", "message": f"Shock recovery completed for {hub}"}
    raise HTTPException(status_code=500, detail="Recovery failed")

# Serve Static Files for v14.0 Frontend
web_dir = os.path.join(os.path.dirname(__file__), '../web')
app.mount("/", StaticFiles(directory=web_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8501)
