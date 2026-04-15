# Aviation Singularity OS

TEKNOFEST 2026 için geliştirilen bu proje, havayolu operasyonlarını sentetik veri üzerinde optimize eden, sonucu FastAPI tabanlı bir API ve ürünleşmiş web arayüzü üzerinden sunan bir karar destek sistemidir.

## Ürün Ne Yapıyor
- Sentetik operasyon senaryosu üretir.
- CP-SAT tabanlı optimizasyon ile uçuş atama, gecikme ve iptal kararları üretir.
- KPI, forecast, stress test ve live-sync benzeri operasyon yüzeyleri sağlar.
- Uçuş bazında `decision_reason` üretir ve kararların nedenini API ile arayüzde görünür kılar.
- 2D/3D dijital ikiz arayüzünde filtrelenebilir operasyon görünümü sunar.

## Aktif Mimari
- Backend: FastAPI, SQLite, Prometheus metriği, rate limit, websocket güncellemesi
- Optimization: OR-Tools CP-SAT, fatigue-aware ve slot-pressure-aware planlama
- Analytics: KPI, forecast, foresight heatmap, federated/trust/energy yardımcı modülleri
- Frontend: FastAPI tarafından servis edilen statik web UI, Three.js, MapLibre, Chart.js

## Son Geliştirmeler
- Eski Streamlit/dashboard hattı ve kullanılmayan benchmark/verify dosyaları temizlendi.
- Solver tarafına saatlik havalimanı kapasite baskısı ve gate çakışma mantığı eklendi.
- Optimize sonuçlarına `decision_reason`, `slot_pressure_flag` ve `decision_summary` eklendi.
- `/api/optimizer/explanations` endpointi açıldı.
- Arayüzde karar kartı filtreleri, açıklama paneli, otomatik harita odaklama ve boş durum yönetimi eklendi.

## Çalıştırma
Projede aktif çalışma ortamı `src/.venv` içindedir.

```bash
make run
```

Ardından:
- Web UI: `http://localhost:8501`
- Health: `GET /health`
- KPI: `GET /api/analytics/kpi`
- Optimize: `POST /api/optimize`
- Explanations: `GET /api/optimizer/explanations`
- Model Benchmark: `GET /api/analytics/model-benchmark`

## Test
```bash
make test
```

## Veri Uretimi
```bash
make data
```

## Benchmark
```bash
make benchmark
```

## Docker
```bash
make docker-up
```

Production icin:
- `API_KEY` doldur.
- Gerekirse `DATABASE_URL` ile Postgres bagla.
- `ALLOWED_ORIGINS` degerini acikca sinirla.

## Notlar
- `assets/models/gemma-2-2b-it-Q4_K_M.gguf` varsa AI briefing yerel model ile çalışır; yoksa güvenli fallback döner.
- Live-sync ve narrative yüzeylerinde gerçek sistem yerine demo/simülasyon fallback’leri vardır.
