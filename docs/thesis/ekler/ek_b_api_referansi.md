# Ek B — API Referansı

Tüm endpoint'ler `http://<host>:8501` altında sunulur. Üretimde Caddy TLS terminasyonu
`https://<domain>` adresine yönlendirir.

**Temel URL**: `/`  
**OpenAPI UI**: `/docs` (Swagger UI)  
**ReDoc**: `/redoc`  
**OpenAPI JSON**: `/openapi.json`

---

## B.1 Kimlik Doğrulama

### `POST /api/auth/jwt/login`

OAuth2 `password` grant ile JWT access token alır.

**Request** (form-data):
```
username: dispatcher@example.com
password: S3cur3P@ss!
```

**Response 200**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Response 400** — Hatalı kimlik:
```json
{"detail": "LOGIN_BAD_CREDENTIALS"}
```

Token ömrü: 86 400 saniye (24 saat).  
Tüm korunan endpoint'lerde header gereklidir:
```
Authorization: Bearer <access_token>
```

---

### `POST /api/auth/register`

Yeni kullanıcı kaydı (herkes erişebilir; prod'da kısıtlanmalı).

**Request Body**:
```json
{
  "email": "new.dispatcher@airline.com",
  "password": "M1nimum8Chars!",
  "role": "operator"
}
```

**Response 201**:
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "email": "new.dispatcher@airline.com",
  "is_active": true,
  "is_superuser": false,
  "is_verified": false,
  "role": "operator"
}
```

---

### `POST /api/auth/jwt/logout`

Token'ı geçersiz kılar (server-side blacklist: gelecek çalışma).

**Response 204** — No Content.

---

### `GET /api/users/me`

Mevcut oturum kullanıcısını döndürür.

**Response 200**:
```json
{
  "id": "3fa85f64-...",
  "email": "dispatcher@example.com",
  "role": "operator",
  "is_active": true
}
```

---

## B.2 Senaryo Yönetimi

### `GET /api/scenario`

Mevcut uçuş senaryosunu döndürür. İlk istekte otomatik üretir.

**Yetki**: Tüm authenticated kullanıcılar.

**Query params**:

| Parametre | Tip | Varsayılan | Açıklama |
|---|---|---|---|
| `n` | int | 150 | Uçuş sayısı (50–500) |
| `seed` | int | 42 | Rastgele tohum |

**Response 200**:
```json
{
  "flights": [
    {
      "flight_id": "TK1001",
      "airline": "TK",
      "origin": "IST",
      "destination": "ESB",
      "scheduled_dep": 1714000000,
      "scheduled_arr": 1714003600,
      "block_time": 60,
      "ac_type": "A320",
      "is_canceled": false,
      "assigned_delay": 0,
      "weather_risk": 0.18,
      "crew_base_fatigue": 0.24,
      "decision_reason": null
    }
  ],
  "total_flights": 150,
  "generated_at": "2026-04-15T10:30:00Z",
  "live_data_used": true
}
```

---

### `POST /api/scenario/regenerate`

Senaryoyu yeniden üretir.

**Yetki**: `operator`, `admin`.

**Request Body**:
```json
{
  "n_flights": 150,
  "seed": 99,
  "stress_level": "normal"
}
```

`stress_level`: `"normal"` | `"weather_closure"` | `"crew_strike"` | `"combined"`

**Response 200**: Yukarıdaki senaryo formatı.

---

### `GET /api/scenario/stats`

Senaryo özet istatistikleri.

**Response 200**:
```json
{
  "total_flights": 150,
  "canceled": 5,
  "delayed": 23,
  "mean_delay_min": 12.3,
  "total_profit_tl": 779000,
  "total_co2_kg": 45200,
  "ftl_violations": 0
}
```

---

## B.3 Optimizer

### `POST /api/optimizer/solve`

CP-SAT + QIGA hibrit çözücüyü çalıştırır.

**Yetki**: `operator`, `admin`.

**Query params**:

| Parametre | Tip | Varsayılan | Açıklama |
|---|---|---|---|
| `strategy` | string | `"PROFIT"` | `PROFIT` / `EKO` / `DAYANIKLILIK` |
| `time_limit` | int | 60 | Solver zaman sınırı (saniye, 10–120) |

**Response 200**:
```json
{
  "status": "OPTIMAL",
  "objective_value": 779000,
  "optimality_gap_pct": 1.7,
  "solve_time_s": 58.2,
  "decisions": [
    {
      "flight_id": "TK1001",
      "is_canceled": false,
      "assigned_delay": 0,
      "decision_reason": null,
      "profit_contribution": 5200.0
    },
    {
      "flight_id": "TK1045",
      "is_canceled": true,
      "assigned_delay": 0,
      "decision_reason": "CREW_DUTY_SATURATION",
      "profit_contribution": 0.0
    }
  ],
  "kpis": {
    "total_canceled": 5,
    "total_delayed": 18,
    "mean_delay_min": 12.3,
    "ftl_violations": 0,
    "strategy": "PROFIT"
  }
}
```

**Response 409** — Çözüm bulunamadı ve kurtarma da başarısız:
```json
{"detail": "INFEASIBLE_SCHEDULE: no valid assignment found after recovery"}
```

**Decision Reason Kodları**:

| Kod | Açıklama |
|---|---|
| `CREW_DUTY_SATURATION` | Mürettebat FTL tavanını aşıyor |
| `WEATHER_CLOSURE` | Hava durumu iptal zorunluluğu |
| `AIRCRAFT_UNAVAILABLE` | Uçak bakımda veya havalimanı dışında |
| `GATE_CONFLICT` | Kapı kısıtı çakışması |
| `SLOT_OVERFLOW` | Havalimanı slot kapasitesi aşıldı |
| `LOW_PROFITABILITY` | EKO/DAYANIKLILIK optimizasyonunda zarar |

---

### `GET /api/optimizer/status`

Mevcut çözücü durumunu sorgular.

**Response 200**:
```json
{
  "solver": "CP-SAT + QIGA",
  "last_solve_utc": "2026-04-15T10:45:00Z",
  "last_status": "OPTIMAL",
  "last_gap_pct": 1.7
}
```

---

## B.4 Tahmin (Forecast)

### `GET /api/forecast/seven-day`

XGBoost modeli ile 7 günlük gecikme tahmini.

**Yetki**: Tüm authenticated kullanıcılar.

**Response 200**:
```json
{
  "forecast": [
    {"date": "2026-04-16", "predicted_delay_min": 14.2, "confidence_low": 9.1, "confidence_high": 19.3},
    {"date": "2026-04-17", "predicted_delay_min": 11.8, "confidence_low": 7.5, "confidence_high": 16.1},
    {"date": "2026-04-18", "predicted_delay_min": 22.4, "confidence_low": 15.0, "confidence_high": 29.8},
    {"date": "2026-04-19", "predicted_delay_min": 9.5, "confidence_low": 5.2, "confidence_high": 13.8},
    {"date": "2026-04-20", "predicted_delay_min": 17.1, "confidence_low": 11.4, "confidence_high": 22.7},
    {"date": "2026-04-21", "predicted_delay_min": 13.6, "confidence_low": 8.9, "confidence_high": 18.3},
    {"date": "2026-04-22", "predicted_delay_min": 10.2, "confidence_low": 6.1, "confidence_high": 14.3}
  ],
  "model": "XGBoost",
  "generated_at": "2026-04-15T10:30:00Z"
}
```

---

## B.5 Foresight (Stres Testi)

### `POST /api/foresight/stress-test`

Gelecek 30 güne Monte Carlo simülasyonu uygular.

**Yetki**: `operator`, `admin`.

**Request Body**:
```json
{
  "n_simulations": 500,
  "shock_scenarios": ["weather_closure", "crew_strike_20pct"],
  "horizon_days": 30
}
```

**Response 200**:
```json
{
  "p50_delay_min": 14.1,
  "p95_delay_min": 38.7,
  "p99_delay_min": 62.3,
  "worst_case_cancellation_rate": 0.31,
  "scenarios_run": 500,
  "var_95_tl": -124000
}
```

---

### `GET /api/foresight/risk-matrix`

Havaalanı × risk faktörü matrisi.

**Response 200** — 14 havalimanı × 5 risk faktörü (0–1 normalized):
```json
{
  "airports": ["IST","ESB","ADB","AYT","TZX","GZT","MLX","VAS","KYA","DIY","ERZ","EZS","ASR","GKD"],
  "risk_factors": ["weather","congestion","slot_pressure","crew_availability","tech_failure"],
  "matrix": [[0.18, 0.41, 0.22, 0.15, 0.09], ...]
}
```

---

## B.6 XAI (Açıklanabilir AI)

### `GET /api/xai/explain/{flight_id}`

Belirli bir uçuş kararının SHAP açıklamasını döndürür.

**Yetki**: Tüm authenticated kullanıcılar.

**Path params**: `flight_id` — uçuş kimliği (örn. `TK1045`)

**Response 200**:
```json
{
  "flight_id": "TK1045",
  "decision": "CANCELED",
  "decision_reason": "CREW_DUTY_SATURATION",
  "base_value": 0.42,
  "shap_values": {
    "weather_risk": 0.22,
    "crew_base_fatigue": 0.17,
    "tech_failure_prob": 0.14,
    "dest_congestion": 0.11,
    "slot_pressure_flag": 0.09,
    "aircraft_health": -0.07,
    "load_factor": 0.06,
    "is_night_flight": 0.04
  },
  "counterfactual": "Eğer crew_base_fatigue < 0.20 olsaydı, uçuş iptal edilmezdi.",
  "bayesian_attribution": {
    "direct_cause": "crew_base_fatigue",
    "contributing_factors": ["weather_risk", "slot_pressure_flag"]
  }
}
```

**Response 404**:
```json
{"detail": "Flight TK9999 not found"}
```

---

### `GET /api/xai/aggregate`

Tüm uçuşlar için toplu SHAP önemi.

**Response 200**:
```json
{
  "feature_importance": [
    {"feature": "weather_risk", "mean_abs_shap": 0.22},
    {"feature": "crew_base_fatigue", "mean_abs_shap": 0.17},
    {"feature": "tech_failure_prob", "mean_abs_shap": 0.14},
    {"feature": "dest_congestion", "mean_abs_shap": 0.11},
    {"feature": "slot_pressure_flag", "mean_abs_shap": 0.09}
  ],
  "total_flights_analyzed": 150
}
```

---

## B.7 Dışa Aktarma (Export)

### `GET /api/export/scenario.csv`

Mevcut senaryo CSV olarak indirilir.

**Response 200**:  
`Content-Type: text/csv`  
`Content-Disposition: attachment; filename="scenario.csv"`

Sütunlar: `flight_id, airline, origin, destination, scheduled_dep, is_canceled, assigned_delay, decision_reason, profit_contribution, ...`

---

### `GET /api/export/decision-report.pdf`

**Query params**:

| Parametre | Tip | Varsayılan | Açıklama |
|---|---|---|---|
| `filter` | string | `"all"` | `all` / `canceled` / `delayed` / `on_time` |

**Response 200**:  
`Content-Type: application/pdf`  
`Content-Disposition: attachment; filename="decision_report.pdf"`

PDF içeriği:
- Kapak: "Decision Report — Aviation Digital Twin"
- Özet tablo: KPI'lar (toplam, iptal, gecikme, kâr, CO₂)
- Karar tablosu: tüm uçuşlar (flight_id, durum, sebep, kâr)
- Oluşturma zamanı damgası

---

### `GET /api/export/decision-report.xlsx`

**Query params**: `filter` (yukarıdaki gibi)

**Response 200**:  
`Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`  
`Content-Disposition: attachment; filename="decision_report.xlsx"`

Sekmeler:
1. **Summary** — KPI özeti
2. **Flights** — Tüm uçuş detayları
3. **SHAP** — Feature önem değerleri

---

## B.8 Canlı Veri

### `GET /api/sync/live-traffic`

OpenSky Network'ten canlı ADS-B verisi çeker ve senaryoya zenginleştirir.

**Response 200**:
```json
{
  "aircraft_positions": [
    {
      "icao24": "4b1806",
      "callsign": "THY1001",
      "lat": 40.982,
      "lon": 29.124,
      "altitude_m": 10973,
      "velocity_ms": 245.3,
      "heading": 92.1
    }
  ],
  "count": 47,
  "source": "opensky",
  "cached": false,
  "fetched_at": "2026-04-15T10:30:00Z"
}
```

**Response 206** (fallback):
```json
{
  "aircraft_positions": [...],
  "source": "fallback",
  "reason": "OpenSky circuit breaker OPEN"
}
```

---

### `GET /api/sync/weather/{airport_code}`

Belirli havalimanı için hava durumu.

**Path params**: `airport_code` — IATA kodu (örn. `IST`)

**Response 200**:
```json
{
  "airport": "IST",
  "temperature_c": 18.4,
  "wind_speed_kmh": 24.1,
  "visibility_km": 8.5,
  "ceiling_ft": 3200,
  "weather_risk": 0.18,
  "source": "open-meteo",
  "cached_at": "2026-04-15T10:28:00Z"
}
```

---

## B.9 Sağlık ve İzleme

### `GET /healthz`

Liveness probe. DB ve solver hazır mı?

**Response 200**:
```json
{
  "status": "ok",
  "db": "connected",
  "solver": "ready",
  "version": "27.0.0"
}
```

**Response 503** (DB erişilemez):
```json
{"status": "degraded", "db": "error", "detail": "connection refused"}
```

---

### `GET /readyz`

Readiness probe. İlk istek alınabilir mi?

**Response 200**:
```json
{"ready": true}
```

---

### `GET /metrics`

Prometheus formatında sistem metrikleri.

```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="POST",endpoint="/api/optimizer/solve",status="200"} 142

# HELP solver_solve_duration_seconds Solver wall-clock time
# TYPE solver_solve_duration_seconds histogram
solver_solve_duration_seconds_bucket{le="30.0"} 38
solver_solve_duration_seconds_bucket{le="60.0"} 142
solver_solve_duration_seconds_sum 7841.2
solver_solve_duration_seconds_count 142

# HELP live_sync_fallback_total Circuit breaker fallback count
# TYPE live_sync_fallback_total counter
live_sync_fallback_total{source="opensky"} 3
live_sync_fallback_total{source="open-meteo"} 1
```

---

## B.10 Hata Kodları

| HTTP Kodu | Durum | Açıklama |
|---|---|---|
| 200 | OK | Başarılı |
| 201 | Created | Kullanıcı kaydı başarılı |
| 204 | No Content | Logout başarılı |
| 206 | Partial Content | Canlı veri fallback |
| 400 | Bad Request | Geçersiz parametre / kimlik |
| 401 | Unauthorized | Token eksik veya geçersiz |
| 403 | Forbidden | Rol yetersiz |
| 404 | Not Found | Kaynak bulunamadı |
| 409 | Conflict | Optimizer infeasible |
| 422 | Unprocessable Entity | Pydantic validation hatası |
| 500 | Internal Server Error | Beklenmedik sunucu hatası |
| 503 | Service Unavailable | DB veya kritik servis erişilemez |

---

## B.11 Rate Limiting

Şu an uygulama düzeyinde rate limiting aktif değildir. Üretim için Caddy `rate_limit` direktifi önerilir:

```caddyfile
rate_limit {
    zone api {
        match path /api/*
        key {remote_host}
        events 100
        window 1m
    }
}
```

---

*Tüm endpoint'lerin interaktif belgelenmesi için uygulama çalışırken `/docs` adresini ziyaret edin.*
