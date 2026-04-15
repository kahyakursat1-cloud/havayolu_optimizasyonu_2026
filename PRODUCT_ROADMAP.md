# Ürünleştirme Yol Haritası (Ücretsiz / Self-Hosted)

**Hedef**: TEKNOFEST prototipini gerçek kullanıcıların açıp kullanabileceği, kalıcı veri tutan, canlı feed'li, izlenebilir bir **ürün** haline getirmek.
**Kapsam dışı**: ISO 27001 / SOC 2 sertifikasyonu, ticari GDS (Sabre/Amadeus), SITA/Eurocontrol B2B, kurumsal SLA.
**Tahmini süre**: 8–12 hafta, tek geliştirici.
**Maliyet**: 0 TL (hosting için isteğe bağlı ~4 €/ay Hetzner VPS).

Her faz kendi başına shippable; sırayla gidiyoruz.

---

## Faz 1 — Auth & Kullanıcı (1–2 hafta)

**Neden önce bu**: Veri kalıcı hale gelmeden önce "kim ne yaptı" sorusunu cevaplayabilmek için hafif bir auth yeter.

- **fastapi-users** + JWT (Keycloak overkill; tek servis yeter)
- Roller: `viewer`, `operator`, `admin` — endpoint dekoratörleri
- `audit_events` tablosu: her karar/export için `user_id, action, payload_hash, ts`
- Login sayfası web/ tarafına basit form; token localStorage'ta
- Mevcut API key modunu `DEV_BYPASS_AUTH=1` env'iyle sadece local'a bırak

**Kritik dosyalar**: yeni `src/auth/`, `src/api/main.py` middleware
**Çıkış kriteri**: login olmadan hiçbir `/api/*` endpoint cevap vermiyor.

---

## Faz 2 — PostgreSQL + Migrations (2 hafta)

**Neden**: SQLite tek-yazar; birden çok kullanıcı + audit log + gerçek veri eşzamanlı yazınca kilitleniyor.

- **PostgreSQL** (Docker compose servisi)
- **SQLAlchemy 2.x** + **Alembic** migration chain
- Şema: `users`, `audit_events`, `flights`, `aircraft`, `crews`, `decisions`, `live_snapshots`
- `synthetic_env.py` → "seed loader"a indir; DB'ye yaz, oradan oku
- Redis yerine başlangıçta Postgres + `UNLOGGED TABLE` cache ile idare et (kurulum sadeliği)

**Kritik dosyalar**: yeni `src/db/models/`, `src/db/migrations/`
**Çıkış kriteri**: iki tarayıcıdan eşzamanlı login + scenario fetch çakışmasız.

---

## Faz 3 — Canlı Veri (Ücretsiz Kaynaklar) (1–2 hafta)

**Neden**: v28'de OpenSky + Open-Meteo zaten var ama scenario'ya enjekte edilmiyor; sadece gösterim amaçlı.

- **OpenSky anonim** (mevcut) — uçak pozisyonu
- **Open-Meteo** (mevcut) — havaalanı hava durumu
- **AviationWeather.gov (NOAA)** — METAR/TAF ekle
- Scenario generator'ı canlı veriyle zenginleştir: gerçek havayla gecikme olasılığı, gerçek pozisyonla ETA
- Hepsi TTL cache'li + offline fallback'li (pattern zaten kurulu)
- Circuit breaker (pybreaker) ekle — API timeout'unda scenario yine üretilebilsin

**Kritik dosyalar**: `src/data_connectors/live_sync.py`, yeni `aviation_weather.py`
**Çıkış kriteri**: `/api/scenario` response'unda `weather_source: "metar"` ve gerçek rüzgar/visibility alanları.

---

## Faz 4 — Observability (1 hafta)

**Neden**: Prod'da "neden hata aldık" sorusuna cevap veremeyen ürün, ürün değil.

- **Prometheus** (mevcut metrikler) + **Grafana** — docker-compose'a ekle
- **Loki** + Promtail — structured log ship
- 1 tek Grafana dashboard: solver latency, request rate, 5xx, FTL breach count
- Alarm: **ntfy.sh** veya Telegram bot — free, PagerDuty gerekmez
- `/healthz` + `/readyz` ayrımı; compose healthcheck bağla

**Çıkış kriteri**: Grafana'da son 24 saati gösteren tek ekran; alarm telefona push ediyor.

---

## Faz 5 — Deployment Hijyeni (3–5 gün)

**Neden**: Kendi makinende değil, dışarıdan erişilebilir tek URL olacak.

- Hetzner CX11 VPS (4 €/ay) veya Fly.io free tier
- **Caddy** reverse proxy — otomatik Let's Encrypt TLS
- GitHub Actions CI: lint + test + `docker build` + SSH deploy
- Nightly Postgres dump → **Backblaze B2** (10GB free) veya local encrypted volume
- `.env.production` secrets — `sops` ile git'te şifreli sakla veya `.env.prod.local` gitignore

**Çıkış kriteri**: `https://<domain>` açılıyor, TLS yeşil, restart sonrası state kaybolmuyor.

---

## Faz 6 — Kullanıcı Deneyimi Sıkılaştırma (1 hafta)

**Neden**: Ürünün "kullanılabilir" olması sadece API değil; tarayıcıda 5 dakikada değer vermesi lazım.

- Onboarding: ilk login'de demo scenario otomatik yüklensin
- Loading state'ler, error toast'ları (mevcut UI'da eksik yerler)
- Keyboard shortcut: `R` recover, `E` export, `/` search flight
- Mobile responsive kontrol (Three.js zor ama tablo/rapor çalışsın)
- README'ye 3 dakikalık quickstart GIF

**Çıkış kriteri**: yeni bir kullanıcı dokümana bakmadan iki tıkta scenario + karar görebiliyor.

---

## Özet Tablo

| Faz | Süre | Bağımlılık | Maliyet |
|---|---|---|---|
| 1 — Auth | 1–2 hf | - | 0 |
| 2 — Postgres | 2 hf | 1 | 0 |
| 3 — Canlı veri | 1–2 hf | 2 | 0 |
| 4 — Observability | 1 hf | 2 | 0 |
| 5 — Deploy | 3–5 gün | 1,2,4 | ~4 €/ay (opsiyonel) |
| 6 — UX | 1 hf | 5 | 0 |

**Kritik yol**: 1 → 2 → 5 (~5 hafta minimum viable product).
**Atlanan**: Endüstri Faz C (FTL tam tablosu), F (ölçek), G (sertifikasyon) — ürün için gereksiz.

---

## İlk 3 Gün

1. `fastapi-users` kurulumu + `users` + `audit_events` tabloları
2. Login/logout endpoint'i + basit web form
3. Mevcut API key path'ini `DEV_BYPASS_AUTH` arkasına al

Bu üç adım tamamlanınca Faz 2'ye (Postgres) geçiş temiz olur.
