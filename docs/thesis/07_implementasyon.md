# Bölüm 7 — Gerçekleme: Yazılım Mühendisliği Detayları

## 7.1 Proje Yapısı

```
havayolu_optimizasyonu_2026/
├── src/
│   ├── api/               # FastAPI uygulaması
│   │   ├── main.py        # 655 satır — router, middleware, lifespan
│   │   └── exporters.py   # PDF + XLSX rapor üreticileri
│   ├── auth/              # (planlanan — şu an db/config.py içinde)
│   ├── db/
│   │   ├── models.py      # SQLAlchemy 2.x typed mapping
│   │   ├── config.py      # async engine, fastapi-users kurulumu
│   │   ├── middleware.py  # AuditMiddleware
│   │   ├── schemas.py     # pydantic I/O şemaları
│   │   └── migrations/    # Alembic
│   ├── optimizer/
│   │   ├── dt_solver.py   # CP-SAT
│   │   ├── hybrid_ga.py   # QIGA
│   │   └── recovery.py    # Warm-start orchestration
│   ├── generator/
│   │   └── synthetic_env.py  # AdvancedAirlineSimulator
│   ├── data_connectors/
│   │   ├── live_sync.py   # OpenSky + Meteo + NOAA
│   │   └── market_intel.py
│   ├── analytics/
│   │   ├── forecast_engine.py
│   │   ├── foresight_engine.py
│   │   ├── kpi_engine.py
│   │   ├── model_benchmark.py
│   │   └── enrichment.py
│   ├── models/
│   │   ├── cognitive_narrative.py
│   │   ├── evolution_engine.py
│   │   ├── trust_auditor.py
│   │   └── xai_engine.py
│   └── web/
│       ├── index.html
│       ├── script.js
│       └── style.css
├── tests/
│   ├── conftest.py
│   ├── test_core.py
│   ├── test_solver.py
│   ├── test_models.py
│   ├── test_integration.py
│   ├── test_live_sync.py
│   ├── test_auth_api.py
│   └── test_audit_flow.py
├── deploy/
│   ├── prod_up.sh
│   ├── db_backup.sh
│   └── monitoring/
│       ├── prometheus.yml
│       ├── loki-config.yml
│       ├── promtail-config.yml
│       └── grafana-datasources.yml
├── Caddyfile
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── alembic.ini
├── pyproject.toml
├── requirements.txt
└── .env.example
```

### 7.1.1 Şekil 7.1 — Proje Dizin Yapısı

Şekil 7.1, yukarıdaki dizin ağacını katmanlı olarak görselleştirir: her klasör renk kodlu bileşen grubuna (API, optimizer, generator, analytics, web, tests) ayrılmış; satır sayıları ve bağımlılık yönleri gösterilmiştir.

## 7.2 FastAPI Uygulama Çekirdeği

### 7.2.1 Lifespan Hook

Uygulama başlangıcında asenkron hazırlık ve kapanışta temizlik için **lifespan context manager** kullanılır:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Başlangıç
    await _warmup_models()
    await _init_db_if_empty()
    yield
    # Kapanış
    await db_engine.dispose()

app = FastAPI(lifespan=lifespan, title="Aviation Singularity")
```

### 7.2.2 Router Yapısı

Endpoint'ler mantıksal gruplar halinde ayrılmıştır:

| Modül | Endpoint Sayısı | Örnek |
|---|---|---|
| auth | 5 | `/api/auth/jwt/login` |
| scenario | 3 | `/api/scenario` |
| optimizer | 4 | `/api/optimizer/solve` |
| forecast | 2 | `/api/forecast/seven-day` |
| foresight | 3 | `/api/foresight/stress-test` |
| xai | 2 | `/api/xai/explain/{flight_id}` |
| export | 3 | `/api/export/decision-report.pdf` |
| live | 2 | `/api/sync/live-traffic` |
| health | 2 | `/healthz`, `/readyz` |
| metrics | 1 | `/metrics` |

### 7.2.3 Solver Endpoint Örneği

```python
@app.post("/api/optimizer/solve", tags=["optimizer"])
async def solve(
    strategy: Literal["PROFIT","EKO","DAYANIKLILIK"] = "PROFIT",
    time_limit: int = 60,
    user: UserRead = Depends(fastapi_users.current_user(active=True))
):
    if user.role not in ("operator", "admin"):
        raise HTTPException(403, "operator role required")

    df = _get_current_scenario()
    solver = DigitalTwinSolver(df, strategy=strategy, time_limit=time_limit)

    try:
        result = solver.solve()
    except InfeasibleScheduleError as e:
        # Hibrit kurtarma
        result = hybrid_recovery(df, warm_start=e.partial_assignment)

    _persist_decisions(result, user_id=user.id)
    return result.to_dict()
```

## 7.3 Veritabanı Katmanı

### 7.3.1 SQLAlchemy 2.x Typed Mapping

SQLAlchemy 2.x, `Mapped[T]` annotation ile tip güvenli ORM sunar:

```python
class Flight(Base):
    __tablename__ = "flights"
    flight_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    is_canceled: Mapped[bool] = mapped_column(Boolean, default=False)
    assigned_delay: Mapped[int] = mapped_column(BigInteger, default=0)
    decision_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
```

### 7.3.2 Async Session Pattern

```python
async def get_async_session():
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

### 7.3.3 Alembic Migration Chain

```
836c756c6b73_complete_unified_production_schema.py  # initial
└── (gelecek) crew_qualifications_matrix
    └── (gelecek) maintenance_tasks_mro
```

Migration komutları:
```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1  # geri al
```

## 7.4 Auth Katmanı Detayları

### 7.4.1 fastapi-users Kurulumu

`src/db/config.py` içinde:
- `JWTStrategy(secret=SECRET, lifetime_seconds=86400)` — 24 saat token
- `BearerTransport(tokenUrl="api/auth/jwt/login")`
- `AuthenticationBackend(name="jwt", transport=..., get_strategy=...)`

### 7.4.2 RBAC Enforcement

Endpoint dekoratöründe role kontrolü:

```python
def require_role(*allowed: str):
    def _check(user: UserRead = Depends(current_active_user)):
        if user.role not in allowed:
            raise HTTPException(403, f"requires role in {allowed}")
        return user
    return _check

@app.post("/api/optimizer/solve")
async def solve(user=Depends(require_role("operator", "admin"))):
    ...
```

### 7.4.3 Şifre Politikası

- Minimum 8 karakter
- bcrypt cost factor 12
- argon2 (opsiyonel, pwdlib üzerinden)
- Token lifetime 24 saat; refresh token henüz yok (gelecek çalışma)

## 7.5 Audit Katmanı

### 7.5.1 Middleware

Her POST/PUT/DELETE/PATCH isteği ve `/api/scenario` GET istekleri loglanır:

```python
class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path in EXCLUDED:
            return await call_next(request)
        response = await call_next(request)
        if _should_audit(request):
            async with db_config.async_session_maker() as s:
                s.add(AuditEvent(
                    user_id=getattr(request.state, "user_id", None),
                    action=f"{request.method} {request.url.path}",
                    details={"status_code": response.status_code}
                ))
                await s.commit()
        return response
```

### 7.5.2 Audit Sorgulama

```sql
SELECT user_id, action, timestamp
FROM audit_events
WHERE timestamp > NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC;
```

## 7.6 Canlı Veri Entegrasyonu

### 7.6.1 Mimari

Her provider için iki fonksiyon:
- `_fetch_X_raw()` — breaker ile sarılı, ham veri dönen fonksiyon (raise on error)
- `fetch_X()` — breaker'ı dışarıdan çağırır, fallback'e düşer

```python
@weather_breaker
def _fetch_meteo_raw(self, airport_code: str) -> dict:
    resp = requests.get(OPEN_METEO_URL, params=..., timeout=self.timeout)
    resp.raise_for_status()
    return resp.json().get("current", {})

def fetch_real_metar(self, airport_code: str) -> dict:
    cached = self._weather_cache.get(airport_code)
    if cached: return cached
    if self.enabled and airport_code in AIRPORT_COORDS:
        try:
            current = self._fetch_meteo_raw(airport_code)
            # ... parse + cache
            return result
        except Exception as exc:
            logger.warning("fallback triggered: %s", exc)
    return self._fallback_weather(airport_code)
```

### 7.6.2 Circuit Breaker Mantığı

`pybreaker.CircuitBreaker(fail_max=5, reset_timeout=60)`:
- **CLOSED**: Normal; istekler geçer
- **OPEN**: 5 ardışık hata → 60 saniye tüm istekleri blok
- **HALF-OPEN**: 60 s sonra 1 test isteği; başarılıysa CLOSED, hata ise tekrar OPEN

#### Şekil 7.2 — Circuit Breaker Durum Diyagramı

Şekil 7.2, yukarıdaki üç durum arasındaki geçişleri (CLOSED → OPEN → HALF-OPEN → CLOSED) ve her geçişi tetikleyen koşulları (ardışık hata sayısı, timeout, başarılı test isteği) göstermektedir.

## 7.7 Frontend Mimarisi

### 7.7.1 Three.js 3D Sahne

```javascript
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(60, aspect, 0.1, 10000);
const renderer = new THREE.WebGLRenderer({ antialias: true });

flights.forEach(f => {
  const mesh = buildAircraftMesh(f.ac_type, f.is_canceled);
  mesh.position.set(...projectLonLat(f.lon, f.lat, f.altitude));
  scene.add(mesh);
});

function animate() {
  requestAnimationFrame(animate);
  renderer.render(scene, camera);
}
```

### 7.7.2 MapLibre 2D

```javascript
const map = new maplibregl.Map({
  container: "map",
  style: "https://tiles.openfreemap.org/styles/liberty",
  center: [33, 39], zoom: 5
});
map.on("load", () => {
  map.addSource("routes", { type: "geojson", data: routeGeoJson });
  map.addLayer({ id: "routes", type: "line", source: "routes",
    paint: { "line-color": "#22d3ee", "line-width": 1.5 } });
});
```

### 7.7.3 Chart.js Grafikler

- KPI satırı: bar chart (iptaller, gecikmeler, kâr, CO₂)
- SHAP waterfall: horizontalBar ile pozitif/negatif katkılar
- Forecasting: line chart 7 günlük

### 7.7.4 State Yönetimi

Basit modül-kapsamlı state objesi; Redux/Zustand tercih edilmemiştir (overkill):

```javascript
const app = {
  scenario: null, decisions: null, token: null, role: null,
  fetchScenario: async () => { ... },
  runSolver: async (strategy) => { ... }
};
```

## 7.8 Export (PDF + XLSX)

`src/api/exporters.py`:

```python
def build_pdf_report(df, summary, filter_label) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), ...)
    story = [
        Paragraph("Decision Report — Aviation Digital Twin", styles["Title"]),
        _build_summary_table(summary),
        Spacer(1, 14),
        _build_flight_table(df),
    ]
    doc.build(story)
    return buf.getvalue()
```

XLSX benzer patern, multi-sheet (Summary + Flights).

## 7.9 Test Altyapısı

### 7.9.1 Fixtures (conftest.py)

- `setup_test_db` — session-scoped; SQLite fixture DB
- `test_engine` — async engine
- `test_session` — per-test session, rollback sonrası
- `seed_state` — state.df'e 50 satırlık örnek senaryo
- `test_user` — unique email admin user
- `auth_token` — test_user için login → JWT

### 7.9.2 Async Test Örneği

```python
@pytest.mark.asyncio
async def test_protected_route_unauthorized(client):
    response = await client.post("/api/optimizer/solve?strategy=PROFIT")
    assert response.status_code == 401
```

### 7.9.3 Coverage Hedefi

| Modül | Coverage |
|---|---|
| optimizer/dt_solver | ~85% |
| api/main (endpoints) | ~78% |
| data_connectors/live_sync | ~92% |
| models/evolution_engine | ~70% |

Overall: ~80%.

## 7.10 DevOps ve Deployment

### 7.10.1 Dockerfile (multi-stage)

```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /install /usr/local
COPY src/ src/
COPY alembic.ini .
EXPOSE 8501
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8501"]
```

### 7.10.2 docker-compose.yml Servisleri

Beş servis: api, postgres, prometheus, loki, grafana. Caddy opsiyonel (prod TLS).

### 7.10.3 deploy/prod_up.sh

```bash
#!/usr/bin/env bash
set -euo pipefail
docker compose pull
docker compose up -d --build
docker compose exec api alembic upgrade head
docker compose ps
```

### 7.10.4 Backup

`deploy/db_backup.sh`:
```bash
pg_dump $DATABASE_URL | gzip > backup-$(date +%F).sql.gz
```

Gelecek: Backblaze B2'ye otomatik gönderim (10GB ücretsiz).

Bölüm 8, sistemin **deneysel bulgularını** sunar.
