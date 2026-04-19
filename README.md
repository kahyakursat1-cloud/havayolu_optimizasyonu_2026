# 🛫 Aviation Singularity v2026.4
### Hybrid Optimization and Digital Twin Framework for Airline Disruption Recovery

Aviation Singularity is an advanced Digital Twin and Tactical Optimization engine designed for resilient airline operations. It combines MILP, Quantum-Inspired GA, and Neuro-Evolutionary agents to solve complex disruption scenarios in seconds.

## 🚀 Key Features (v27.0 Roadmap Complete)

- **Quantum Tactical Resolver**: Hybrid GA/MILP engine with EASA-compliant crew and maintenance constraints.
- **Neural Enlightenment**: Cognitive operational briefings provided by a locally hosted Gemma-2B LLM.
- **Tactical Weather Telemetry**: Real-time NOAA METAR integration with industrial-grade circuit breakers.
- **Industrial Observability**: Full Prometheus, Grafana, and Loki stack for operational transparency.
- **Sovereign Security**: JWT-based RBAC with persistent PostgreSQL audit logging.
- **Deployment Hygiene**: Automatic TLS via Caddy and automated nightly database backups.

## 🛠️ Tech Stack

- **Backend**: Python 3.12 (FastAPI, SQLAlchemy, Pydantic)
- **Database**: PostgreSQL 16 (Primary) / Redis 7 (Caching)
- **Monitoring**: Prometheus, Grafana, Loki, Promtail
- **Frontend**: Vanilla JS (Three.js, MapLibre GL, TailwindCSS)
- **Proxy**: Caddy (Automatic HTTPS)

## 📦 Getting Started (Production)

1. **Clone & Setup**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

2. **Launch with Productive Hygiene**:
   ```bash
   ./deploy/prod_up.sh
   ```

3. **Access**:
   - **Dashboard**: `http://localhost:80` (or your domain)
   - **Grafana**: `http://localhost:3000` (User: admin / Pass: admin)
   - **Prometheus**: `http://localhost:9090`

## ⌨️ Tactical Shortcuts

- `R`: **Resolve** - Trigger an optimization cycle.
- `E`: **Export** - Download the Tactical PDF Briefing.
- `/`: **Foresight** - Toggle Predictive Heatmap Analysis.
- `B`: **Sidebar** - Collapse/Expand Tactical Monitoring Panel.

---
*Built for the future of resilient aviation. (c) 2026 Skylogic Dynamics.*
