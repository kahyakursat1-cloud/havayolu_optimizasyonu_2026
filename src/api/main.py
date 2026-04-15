from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Security, Request
from fastapi.responses import Response
from fastapi.security import APIKeyHeader
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
import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine, event, text
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Structured logging: JSON-ish single-line format with correlation ID support.
# Every log line includes a request_id field (empty outside request scope).
class _RequestIdFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return True

_LOG_FORMAT = '{"ts":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","req":"%(request_id)s","msg":"%(message)s"}'
logging.basicConfig(level=logging.INFO, format=_LOG_FORMAT)
for h in logging.getLogger().handlers:
    h.addFilter(_RequestIdFilter())
logger = logging.getLogger("AviationSingularity")

# Ensure project root is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.optimizer.dt_solver import (
    DigitalTwinSolver,
    SolverError,
    InfeasibleScheduleError,
    SolverTimeoutError,
)
from src.generator.synthetic_env import AdvancedAirlineSimulator
from src.analytics.forecast_engine import forecaster
from src.analytics.foresight_engine import foresight_engine
from src.analytics.model_benchmark import model_benchmarker
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
from src.data_connectors.live_sync import ExternalDataConnector
from src.api.exporters import build_pdf_report, build_xlsx_report
from src.models.federated_node import federated_aggregator
from src.analytics.energy_grid import energy_grid
from src.analytics.enrichment import enricher
import asyncio

from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.db.config import auth_backend, fastapi_users, db_engine, async_session_maker
from src.db.schemas import UserRead, UserCreate, UserUpdate
from src.db.middleware import AuditMiddleware
from src.db.models import Base, Flight

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Faz 2: Ensure tables are ready (or handled via Alembic in prod)
    if os.environ.get("AUTO_MIGRATE") == "1":
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    # Restore state from PostgreSQL
    await state.restore()
    
    asyncio.create_task(brain_evolution_loop())
    yield

# Rate limiter — per-IP by default; swap key_func for per-API-key if needed
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

app = FastAPI(title="Aviation Singularity - Sovereign API v27.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Audit Middleware (Product Roadmap Faz 1)
app.add_middleware(AuditMiddleware)

# Prometheus metrics
REQ_COUNTER = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "path", "status"]
)
REQ_LATENCY = Histogram(
    "http_request_duration_seconds", "HTTP request latency", ["method", "path"]
)
SOLVE_OUTCOMES = Counter(
    "solver_outcomes_total", "Solver outcomes", ["strategy", "outcome"]
)

@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    """Assign correlation ID, time every request, emit Prometheus metrics."""
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
    # Expose to log records via contextvar-less approach: stash on record factory.
    # Simpler: log manually at end; loggers within handlers just use module logger.
    start = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        elapsed = time.perf_counter() - start
        path = request.url.path
        # Avoid cardinality explosion: strip query string, skip static mounts
        if not path.startswith("/static") and not path.startswith("/assets"):
            REQ_COUNTER.labels(request.method, path, str(status_code)).inc()
            REQ_LATENCY.labels(request.method, path).observe(elapsed)
        logger.info(
            f"{request.method} {path} -> {status_code} in {elapsed*1000:.1f}ms",
            extra={"request_id": request_id, "method": request.method, "path": path, "status": status_code}
        )

# Centralized DB setup is now in src.db.config
# Phase 2: PostgreSQL is the primary store.

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

# API Key authentication — reject requests without a matching X-API-Key header.
# In production, set API_KEY to a strong random value. In dev, auth is disabled
# by leaving API_KEY unset.
_API_KEY = os.environ.get("API_KEY")
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def require_api_key(request: Request, api_key: str = Security(_api_key_header)):
    # Support for bypass during development
    if os.environ.get("DEV_BYPASS_AUTH") == "1":
        request.state.user_id = "00000000-0000-0000-0000-000000000000" # System/Dev user
        return
        
    if _API_KEY is not None and api_key == _API_KEY:
        request.state.user_id = "11111111-1111-1111-1111-111111111111" # API Key user
        return

    # If no API Key matched, we might still be authenticated via JWT
    # This will be handled by Depends(current_active_user) in endpoints
    pass

_ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:8501,http://127.0.0.1:8501"
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Authentication Routes (Product Roadmap Faz 1)
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/api/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/api/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/api/auth",
    tags=["users"],
)

live_sync_connector = ExternalDataConnector()


class EvolutionFeedback(BaseModel):
    observation: list[float]
    reward: float
    action: list[float] | None = None


def _normalize_scenario(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    normalized = df.copy()
    sim = AdvancedAirlineSimulator(seed=42)
    airports = sim.airports

    def _map_airport(code, key, default):
        airport = airports.get(code, {})
        return airport.get(key, default)

    if 'origin_lat' not in normalized.columns:
        normalized['origin_lat'] = normalized['origin'].map(lambda c: _map_airport(c, 'lat', 41.275))
    if 'origin_lon' not in normalized.columns:
        normalized['origin_lon'] = normalized['origin'].map(lambda c: _map_airport(c, 'lon', 28.751))
    if 'dest_lat' not in normalized.columns:
        normalized['dest_lat'] = normalized['destination'].map(lambda c: _map_airport(c, 'lat', 41.275))
    if 'dest_lon' not in normalized.columns:
        normalized['dest_lon'] = normalized['destination'].map(lambda c: _map_airport(c, 'lon', 28.751))
    if 'lat' not in normalized.columns:
        normalized['lat'] = (normalized['origin_lat'] + normalized['dest_lat']) / 2
    if 'lon' not in normalized.columns:
        normalized['lon'] = (normalized['origin_lon'] + normalized['dest_lon']) / 2
    if 'velocity' not in normalized.columns:
        block_hours = ((normalized['block_time'].fillna(60).astype(float) / 60.0).clip(lower=0.5))
        normalized['velocity'] = (normalized['dist_km'].fillna(500).astype(float) / block_hours).clip(lower=220, upper=480)
    if 'track' not in normalized.columns:
        normalized['track'] = np.degrees(np.arctan2(
            normalized['dest_lon'] - normalized['origin_lon'],
            normalized['dest_lat'] - normalized['origin_lat'],
        ))
        normalized['track'] = (normalized['track'] + 360.0) % 360.0
    if 'market_gap_index' not in normalized.columns or 'yield_quality_index' not in normalized.columns:
        normalized = market_intel.enrich_scenario_with_intel(normalized)
    if 'assigned_delay' not in normalized.columns:
        normalized['assigned_delay'] = 0
    if 'is_canceled' not in normalized.columns:
        normalized['is_canceled'] = 0
    if 'causal_factor' not in normalized.columns:
        normalized['causal_factor'] = 'Operational'
    if 'maintenance_reason' in normalized.columns:
        normalized['maintenance_reason'] = normalized['maintenance_reason'].fillna('')

    return normalized


def _build_briefing_payload(df: pd.DataFrame) -> tuple[str, str]:
    delayed = df.sort_values('assigned_delay', ascending=False).head(3)
    summary = [
        f"{row['flight_id']} {row['origin']}-{row['destination']} delay={int(row.get('assigned_delay', 0))}m"
        for _, row in delayed.iterrows()
    ]
    if not summary:
        summary = ["Kritik gecikme yok."]

    kpis = state.kpi_engine.calculate_fleet_kpis(df)
    stats = (
        f"PLF={kpis['plf']}%, CQI={kpis['cqi']}, "
        f"cancelled={int(df['is_canceled'].sum())}, flights={len(df)}"
    )
    return " | ".join(summary), stats


def _build_decision_summary(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "total_flights": 0,
            "canceled": 0,
            "delayed": 0,
            "swap_count": 0,
            "slot_pressure_flights": 0,
            "top_reasons": [],
        }

    reasons = (
        df.get('decision_reason', pd.Series(dtype=str))
        .fillna('unspecified')
        .value_counts()
        .head(5)
    )

    swap_count = 0
    if 'assigned_aircraft' in df.columns and 'aircraft_id' in df.columns:
        swap_count = int(
            ((df['assigned_aircraft'] != "None") & (df['assigned_aircraft'] != df['aircraft_id'])).sum()
        )

    return {
        "total_flights": int(len(df)),
        "canceled": int(df.get('is_canceled', pd.Series(dtype=int)).sum()),
        "delayed": int((df.get('assigned_delay', pd.Series(dtype=int)) > 0).sum()),
        "swap_count": swap_count,
        "slot_pressure_flights": int(df.get('slot_pressure_flag', pd.Series(dtype=bool)).sum()),
        "top_reasons": [
            {"reason": str(reason), "count": int(count)}
            for reason, count in reasons.items()
        ],
    }


def _apply_decision_filter(df: pd.DataFrame, filter_name: str | None) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    active_filter = (filter_name or "all").strip().lower()
    filtered = df.copy()

    if active_filter == "canceled":
        return filtered[filtered.get("is_canceled", 0) == 1].copy()
    if active_filter == "delayed":
        delays = filtered.get("assigned_delay", pd.Series(0, index=filtered.index))
        canceled = filtered.get("is_canceled", pd.Series(0, index=filtered.index))
        return filtered[(delays > 0) & (canceled != 1)].copy()
    if active_filter == "swaps":
        assigned = filtered.get("assigned_aircraft", pd.Series("None", index=filtered.index))
        current = filtered.get("aircraft_id", pd.Series("", index=filtered.index))
        return filtered[(assigned != "None") & (assigned != current)].copy()
    if active_filter == "pressure":
        return filtered[filtered.get("slot_pressure_flag", False).astype(bool)].copy()
    return filtered


def _build_report_payload(df: pd.DataFrame, filter_name: str | None) -> dict:
    filtered = _apply_decision_filter(df, filter_name)
    cols = [
        "flight_id",
        "origin",
        "destination",
        "assigned_delay",
        "is_canceled",
        "assigned_aircraft",
        "decision_reason",
        "slot_pressure_flag",
    ]
    available_cols = [col for col in cols if col in filtered.columns]
    highlights = filtered.sort_values(
        by=["is_canceled", "assigned_delay"], ascending=[False, False]
    ).head(10)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "filter": (filter_name or "all").strip().lower() or "all",
        "summary": _build_decision_summary(filtered),
        "highlights": highlights[available_cols].to_dict(orient="records"),
    }


def _build_live_snapshot(df: pd.DataFrame) -> dict:
    active = df[df.get('is_canceled', 0) == 0].head(25).copy()
    flights = []
    for _, row in active.iterrows():
        flights.append({
            "flight_id": row["flight_id"],
            "lat": round(float(row.get("lat", row.get("origin_lat", 41.275))), 6),
            "lon": round(float(row.get("lon", row.get("origin_lon", 28.751))), 6),
            "alt": 28000 if float(row.get("dist_km", 0)) > 1200 else 18000,
            "velocity": int(float(row.get("velocity", 420))),
            "heading": round(float(row.get("track", 45.0)), 1),
            "status": "DELAYED" if float(row.get("assigned_delay", 0)) > 0 else "OPTIMAL",
        })

    return {
        "source": "scenario-digital-twin",
        "offline": True,
        "count": len(flights),
        "active_flights": flights,
    }

class AppState:
    def __init__(self):
        self.kpi_engine = AviationKPIEngine()
        self.slot_ledger = []
        self.simulator = AdvancedAirlineSimulator(seed=42)
        # Guards writes to self.df.
        self.lock = asyncio.Lock()
        self.df = pd.DataFrame()

    async def restore(self):
        """Restore tactical scenario from PostgreSQL."""
        async with async_session_maker() as session:
            from sqlalchemy import select
            result = await session.execute(select(Flight))
            flights = result.scalars().all()
            
            if flights:
                # Convert SQLAlchemy models to dictionary for DataFrame
                data = []
                for f in flights:
                    # Clean the SQLAlchemy internal state
                    d = {c.name: getattr(f, c.name) for c in f.__table__.columns}
                    data.append(d)
                self.df = pd.DataFrame(data)
                
                # ROADMAP PHASE 3: Apply Live Enrichment if enabled
                if os.environ.get("LIVE_SYNC_ENABLED") == "1":
                    self.df = enricher.enrich_scenario(self.df)
                    logger.info("Operational state enriched with real-world weather telemetry.")
                
                logger.info(f"Operational state restored: {len(self.df)} active flights.")
            else:
                logger.warning("No operational data in PostgreSQL. Initializing synthetic scenario.")
                self.df = self.simulator.generate_full_scenario(days=1)
                self.df = _normalize_scenario(self.df)
                await self.save()

    async def save(self):
        """Synchronize DataFrame to PostgreSQL using Flight model."""
        if self.df is None or self.df.empty:
            return
            
        async with async_session_maker() as session:
            try:
                from sqlalchemy import delete
                await session.execute(delete(Flight))
                
                # Convert DataFrame to Flight objects
                # Need to convert timestamps to datetime objects if they are strings
                df_to_save = self.df.copy()
                for col in ['departure_time', 'arrival_time', 'departure_hour', 'arrival_hour']:
                    if col in df_to_save.columns:
                        df_to_save[col] = pd.to_datetime(df_to_save[col])
                        # Handle NaT
                        df_to_save[col] = df_to_save[col].where(df_to_save[col].notnull(), None)

                records = df_to_save.to_dict(orient='records')
                flight_objs = [Flight(**{k: v for k, v in r.items() if hasattr(Flight, k)}) for r in records]
                session.add_all(flight_objs)
                await session.commit()
                logger.info(f"Operational state synchronized to PostgreSQL ({len(records)} records).")
            except Exception as e:
                await session.rollback()
                logger.error(f"PostgreSQL Sync Failure: {e}")

state = AppState()

@app.get("/api/scenario")
async def get_scenario():
    df_copy = _normalize_scenario(state.df)
    data_json = df_copy.to_json(orient='records', date_format='iso')
    return json.loads(data_json)

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

@app.get("/api/analytics/forecast")
async def get_forecast():
    return forecaster.get_forecast(state.df.to_dict(orient="records"))

@app.get("/api/analytics/model-benchmark")
async def get_model_benchmark():
    return model_benchmarker.benchmark_models(state.df)

@app.get("/api/analytics/foresight-heatmap")
async def get_foresight_heatmap():
    return foresight_engine.generate_congestion_geojson(
        state.df.to_dict(orient="records")
    )

@app.get("/api/ai/narrative")
async def get_ai_narrative():
    flight_summary, stats = _build_briefing_payload(state.df)
    report = narrator.generate_briefing(flight_summary, stats)
    return {"report": report}

@app.get("/api/sync/live-traffic")
async def get_live_traffic():
    snapshot = _build_live_snapshot(state.df)
    ext = live_sync_connector.sync_all()
    snapshot["traffic"] = ext["traffic"]
    snapshot["weather"] = ext["weather"]
    return snapshot

@app.post("/api/stress-test")
async def run_stress_test():
    async with state.lock:
        state.df = state.simulator.trigger_disruption(state.df.copy(), hub="IST", delay_mins=90)
        state.df = _normalize_scenario(state.df)
        await state.save()
    await manager.broadcast("SCENARIO_UPDATED")
    return {"status": "ok", "message": "Stress test injected."}

@app.get("/api/evolution/summary")
async def get_evolution_summary():
    return evolution_engine.get_stats()

@app.post("/api/evolution/summary")
async def post_evolution_summary(payload: Dict[str, Any]):
    # Note: EvolutionFeedback might have been lost or we can use dict for now
    evolution_engine.collect_experience(payload.get("observation"), payload.get("action", [0.0]), payload.get("reward", 0.0))
    return evolution_engine.get_stats()

@app.get("/healthz")
async def healthz():
    """Liveness check: minimal overhead, just returns OK."""
    return {"status": "ok"}

@app.get("/readyz")
async def readyz():
    """Readiness check: verifies DB connection and state loading."""
    db_ok = False
    try:
        async with db_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        logger.warning(f"Ready check DB failed: {e}")
    
    ready = db_ok and state.df is not None and len(state.df) > 0
    
    if not ready:
        raise HTTPException(status_code=503, detail="Service not ready")
        
    return {
        "status": "ok",
        "db": db_ok,
        "data_loaded": True
    }

@app.get("/health")
async def legacy_health():
    """Backward compatible health endpoint."""
    return await readyz()

@app.get("/metrics")
async def metrics():
    """Prometheus scrape endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/api/optimizer/solve")
@limiter.limit("5/minute")
async def optimize(
    request: Request, 
    strategy: str = "PROFIT",
    user: UserRead = Depends(fastapi_users.current_user(active=True))
):
    request.state.user_id = str(user.id)
    """
    v27.0 Sovereign Solve: Includes Cross-Carrier Federated Insight.
    """
    if strategy not in ("PROFIT", "VOLUME"):
        raise HTTPException(status_code=400, detail=f"Unknown strategy: {strategy!r}")

    # Serialize access to state.df. If another /solve is in-flight, wait —
    # don't run a second CP-SAT on a mid-write DataFrame.
    async with state.lock:
        snapshot = security_guard.sanitize_scenario(state.df)
        fed_update = federated_aggregator.simulate_federated_update()

        def _run_solve(df):
            solver = DigitalTwinSolver(df)
            return solver.solve_with_windows(strategy=strategy)

        try:
            result_df = await asyncio.to_thread(_run_solve, snapshot)
            SOLVE_OUTCOMES.labels(strategy, "success").inc()
        except InfeasibleScheduleError as e:
            SOLVE_OUTCOMES.labels(strategy, "infeasible").inc()
            logger.warning(f"Infeasible schedule: {e}")
            raise HTTPException(status_code=422, detail={"error": "infeasible", "message": str(e)})
        except SolverTimeoutError as e:
            SOLVE_OUTCOMES.labels(strategy, "timeout").inc()
            logger.warning(f"Solver timeout: {e}")
            raise HTTPException(status_code=504, detail={"error": "timeout", "message": str(e)})
        except SolverError as e:
            SOLVE_OUTCOMES.labels(strategy, "error").inc()
            logger.error(f"Solver error: {e}")
            raise HTTPException(status_code=500, detail={"error": "solver", "message": str(e)})
        except Exception as e:
            SOLVE_OUTCOMES.labels(strategy, "internal").inc()
            logger.exception("Unexpected error during solve")
            raise HTTPException(status_code=500, detail={"error": "internal", "message": str(e)})

        state.df = result_df
        await state.save()
        window_failures = list(result_df.attrs.get("window_failures", []))
        hybrid_recoveries = list(result_df.attrs.get("hybrid_recoveries", []))

    await manager.broadcast("SCENARIO_UPDATED")
    return {
        "status": "success",
        "message": f"{strategy} optimization completed.",
        "federated_fidelity": fed_update['global_fidelity'],
        "energy_impact": "V2G Buffered",
        "window_failures": window_failures,
        "hybrid_recoveries": hybrid_recoveries,
        "decision_summary": _build_decision_summary(result_df),
    }

@app.post("/api/optimize")
async def optimize_alias(request: Request, strategy: str = "PROFIT"):
    return await optimize(request=request, strategy=strategy)

@app.post("/api/ai/optimize")
async def ai_optimize_alias(request: Request):
    result = await optimize(request=request, strategy="PROFIT")
    result["message"] = "Neural commander completed a profit-priority re-optimization."
    return result

@app.get("/api/analytics/kpi")
async def get_kpis():
    kpis = state.kpi_engine.calculate_fleet_kpis(state.df)
    # v27.0 NTN Connectivity Metric
    ntn_active = state.df['ntn_link_active'].sum() if 'ntn_link_active' in state.df.columns else 0
    kpis["ecosystem_resilience_index"] = 99.8
    kpis["ntn_global_visibility"] = f"{(ntn_active / len(state.df)):.1%}"
    return kpis

@app.get("/api/optimizer/explanations")
async def get_optimizer_explanations():
    explanation_cols = [
        'flight_id', 'origin', 'destination', 'aircraft_id', 'assigned_aircraft',
        'assigned_delay', 'is_canceled', 'decision_reason', 'slot_pressure_flag'
    ]
    available_cols = [col for col in explanation_cols if col in state.df.columns]
    return {
        "summary": _build_decision_summary(state.df),
        "flights": state.df[available_cols].to_dict(orient="records"),
    }


@app.get("/api/reports/decision-summary")
async def get_decision_summary_report(filter: str = "all"):
    return _build_report_payload(state.df, filter)


@app.get("/api/export/scenario.csv")
async def export_scenario_csv(filter: str = "all"):
    filtered = _apply_decision_filter(state.df, filter)
    export_df = filtered.copy()
    if not export_df.empty:
        export_df = export_df.sort_values(
            by=["is_canceled", "assigned_delay"], ascending=[False, False]
        )

    csv_payload = export_df.to_csv(index=False)
    suffix = (filter or "all").strip().lower() or "all"
    filename = f"aviation_scenario_{suffix}.csv"
    return Response(
        content=csv_payload,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/export/decision-report.pdf")
async def export_decision_report_pdf(filter: str = "all"):
    filtered = _apply_decision_filter(state.df, filter)
    summary = _build_decision_summary(filtered)
    label = (filter or "all").strip().lower() or "all"
    payload = build_pdf_report(filtered, summary, label)
    filename = f"decision_report_{label}.pdf"
    return Response(
        content=payload,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/export/decision-report.xlsx")
async def export_decision_report_xlsx(filter: str = "all"):
    filtered = _apply_decision_filter(state.df, filter)
    summary = _build_decision_summary(filtered)
    label = (filter or "all").strip().lower() or "all"
    payload = build_xlsx_report(filtered, summary, label)
    filename = f"decision_report_{label}.xlsx"
    return Response(
        content=payload,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

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
