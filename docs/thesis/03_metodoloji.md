# Bölüm 3 — Metodoloji

## 3.1 Metodolojik Çerçeve

Bu tez, **tasarım bilimi araştırması (design science research)** paradigmasını takip eder (Hevner ve ark., 2004). Peffers ve ark. (2007)'nin altı aşamalı DSR metodolojisi uyarlanmıştır:

| Aşama | Bu Tezde Karşılığı |
|---|---|
| 1. Problem tanımı ve motivasyon | Bölüm 1 ve 2 |
| 2. Çözüm hedeflerinin belirlenmesi | Bölüm 2.9, RQ₁.₁–₃ |
| 3. Tasarım ve geliştirme | Bölüm 4–7 |
| 4. Demonstrasyon | Bölüm 8 (sentetik + gerçek veri deneyleri) |
| 5. Değerlendirme | Bölüm 8.4–8.6, Tablo 8.1 |
| 6. Yayınlama ve iletişim | Tez + açık kaynak GitHub deposu |

### 3.1.1 Şekil 3.1 — DSR Metodoloji Aşamaları

Şekil 3.1, Peffers ve ark. (2007) çerçevesinin bu teze uyarlanmış beş aşamasını gösterir: Problem Tanımı → Hedef Tanımı → Tasarım & Geliştirme → Demo & Değerlendirme → İletişim. İteratif geri besleme oku, aşamalar arasındaki döngüsel geliştirme sürecini yansıtır.

## 3.2 Teknoloji Yığını ve Seçim Gerekçeleri

Tablo 3.1, projede kullanılan her teknolojiyi **seçim gerekçesi** ile birlikte listeler.

### Tablo 3.1 — Kullanılan Teknoloji Yığını

| Katman | Teknoloji | Versiyon | Seçim Gerekçesi |
|---|---|---|---|
| **Backend API** | FastAPI | 0.x | Async-native, OpenAPI otomatik şema, pydantic entegrasyonu |
| **ASGI Server** | Uvicorn | 0.44 | FastAPI referans sunucusu; HTTP/2 desteği |
| **Optimization Core** | OR-Tools | 9.x | CP-SAT; 2020 MiniZinc Challenge birincisi (Perron ve Furnon, 2023) |
| **Meta-heuristic** | NumPy + özel QIGA | — | Han & Kim (2002) çerçevesi uyarlaması |
| **ML / Forecasting** | XGBoost | 2.x | TreeSHAP polinomial zamanda çalışır (Lundberg ve ark., 2020) |
| **XAI** | SHAP | 0.45+ | EASA AMC 20-42 uyumu |
| **Causal Analytics** | pgmpy (opsiyonel) | — | Bayesian network inference |
| **RL Experiments** | Stable-Baselines3 | 2.x | PPO/DQN referans implementasyonları |
| **Primary DB** | PostgreSQL | 15 | Concurrent write; JSONB type; row-level security |
| **ORM** | SQLAlchemy | 2.0+ | Async session; typed mapping (Mapped[T]) |
| **Migrations** | Alembic | 1.18 | SQLAlchemy 2.x async compatible |
| **Auth** | fastapi-users | 15.0 | JWT out-of-the-box; RBAC ile uyumlu |
| **Password Hashing** | bcrypt / argon2 | — | OWASP önerisi |
| **Cache (opsiyonel)** | Redis / TTL in-memory | — | Live-sync TTL |
| **Circuit Breaker** | pybreaker | 1.4 | Fault tolerance (Nygard, 2007) |
| **Retry** | tenacity | 8.x | Exponential backoff |
| **Rate Limit** | slowapi | 0.1 | FastAPI entegre |
| **Logging** | Python stdlib + JSON formatter | — | Loki uyumlu |
| **Metrics** | Prometheus client | 0.x | SRE standartı (Beyer ve ark., 2016) |
| **Observability** | Prometheus + Loki + Grafana + Promtail | — | Cloud-native, self-hosted |
| **Reverse Proxy** | Caddy | 2.x | Otomatik TLS (Let's Encrypt) |
| **Containerization** | Docker + Compose | 24+ | Ortam tutarlılığı |
| **Frontend** | Three.js + MapLibre GL + Chart.js | — | WebGL 3D, harita, grafik |
| **PDF** | ReportLab | 4.4 | Platypus flowable API |
| **XLSX** | openpyxl | 3.1 | Multi-sheet workbook |
| **Testing** | pytest + pytest-asyncio + httpx | — | Async TestClient |
| **Live Data** | OpenSky API, Open-Meteo API, NOAA AviationWeather.gov | — | Ücretsiz, API key gerektirmez (OpenSky anonim) |
| **Notifications** | ntfy.sh / Telegram Bot | — | Ücretsiz alerting |

## 3.3 Geliştirme Süreci ve Yazılım Mühendisliği Prensipleri

### 3.3.1 Versiyonlama

Semantik versiyonlama (SemVer 2.0.0) kullanılmıştır. Git tag'leri her faz tamamlandığında atılır (`v25.0`, `v26.0`, ..., `v28.0`).

### 3.3.2 Test Stratejisi

**Test piramidi** (Cohn, 2009) uyarlanmıştır:

```
         /\
        /  \    e2e (web + API)
       /----\
      /      \  integration (test_integration.py, test_audit_flow.py)
     /--------\
    /          \ unit (test_core, test_solver, test_models, test_live_sync)
   /____________\
```

Mevcut test suite'te **62 test** yeşil durumda; her commit öncesi `make test` ile tetiklenmektedir. `pytest-asyncio` ile async koroutinler desteklenir.

#### Şekil 3.2 — Test Piramidi

Şekil 3.2, mevcut test mimarisini görselleştirir: tabanda 62 birim testi (test_core, test_solver, test_models, test_live_sync), ortada entegrasyon testleri (circuit breaker, audit flow), üstte API/Auth testleri (httpx AsyncClient) ve en üstte planlanan E2E Playwright akışları.

### 3.3.3 Sürekli Entegrasyon

GitHub Actions üzerinde lint (`ruff`), tip kontrolü (`mypy --strict`), test (`pytest`) ve Docker imaj yapım-yayın hattı tanımlıdır (Ek D).

### 3.3.4 Kodlama Standartları

- **PEP 8** + `ruff format` ile biçimlendirme
- **Type hints** zorunlu (mypy strict)
- **Docstring**: PEP 257, Google-style
- **Trunk-based development**: kısa ömürlü feature branch'ler, squash merge

## 3.4 Deneysel Tasarım

### 3.4.1 Senaryo Kümesi

Deneyler iki kaynaklı veri üzerinde yürütülür:

1. **Sentetik Senaryolar** (`AdvancedAirlineSimulator`, seed=42): 50, 150, 500, 1500 uçuş; Türkiye hub-and-spoke topolojisi (IST, SAW, ESB, ADB, AYT, TZX, GZT) + Avrupa spoke'ları.
2. **Canlı Veri Enjekte Edilmiş Senaryolar**: Aynı topoloji, ancak `LIVE_SYNC_ENABLED=1` ile OpenSky + Open-Meteo + NOAA METAR gerçek çağrılarıyla zenginleştirilmiş.

### 3.4.2 Deneysel Koşullar

| Koşul | Donanım | Software |
|---|---|---|
| **Local dev** | Intel i7-12700, 32 GB RAM, Ubuntu 24.04 | Python 3.12, OR-Tools 9.11 |
| **CI** | GitHub Actions `ubuntu-latest`, 2 vCPU, 7 GB RAM | Aynı |
| **Canlı** | (Hetzner CX11, planlanan) 1 vCPU, 4 GB RAM | Aynı |

### 3.4.3 Metrikler

Tablo 8.1'de listelenecek temel KPI'lar:

- **Solver wall-clock time** (saniye)
- **Objective value** (TL cinsinden kâr)
- **Optimality gap** (% — CP-SAT'ın raporladığı bound'a göre)
- **Cancellation rate** (iptal edilen uçuş / toplam uçuş)
- **Mean flight delay** (dakika)
- **EASA FTL violations** (adet, beklenen: 0)
- **API p95 latency** (ms)
- **Live-sync fallback ratio** (API hatasında fallback'e düşme oranı)

### 3.4.4 Baseline Yaklaşımlar

Karşılaştırma için üç baseline tanımlanmıştır:

- **B₁ — Greedy First-Feasible**: Her uçuşu sırayla ilk uygun kuyruk ve mürettebata atar.
- **B₂ — CP-SAT only**: Sadece CP-SAT; heuristik kurtarma yok.
- **B₃ — QIGA only**: Sadece genetik algoritma; CP çekirdeği yok.
- **M — Hybrid (bu tez)**: CP-SAT + QIGA warm-start.

### 3.4.5 İstatistiksel Değerlendirme

Her koşul için **10 bağımsız koşu** yapılır; ortalama ve %95 güven aralığı raporlanır. **Wilcoxon signed-rank test** ile yöntemler arası anlamlı fark kontrol edilir ($\alpha = 0.05$).

## 3.5 Etik ve Veri Gizliliği

Canlı OpenSky ADS-B feed'i **anonimdir** (uçak tail number public). Open-Meteo ve NOAA feed'leri kişisel veri içermez. Yolcu verileri (PNR) bu tezde **sentetik** olarak üretilir; gerçek KVKK/GDPR kapsamı ürün fazında (Faz 2 Postgres kalıcılığı + audit) ele alınacaktır.

Bölüm 4, bu metodoloji üzerine inşa edilen **sistem mimarisini** sunar.
