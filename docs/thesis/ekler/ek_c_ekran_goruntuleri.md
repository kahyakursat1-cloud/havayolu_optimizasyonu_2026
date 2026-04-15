# Ek C — Ekran Görüntüleri

Bu ekte sistemin temel arayüz bileşenlerinin açıklamalı görüntüleri sunulmuştur.
Görüntüler, `make run` ile başlatılan uygulama üzerinden `http://localhost:8501` adresinde alınmıştır.

---

## C.1 Giriş Sayfası ve Kimlik Doğrulama

**Şekil C.1 — JWT Giriş Ekranı**

```
┌─────────────────────────────────────────────────────────────┐
│  ✈  Aviation Digital Twin — Dispatcher Interface            │
│─────────────────────────────────────────────────────────────│
│                                                             │
│   E-posta:  [ dispatcher@example.com              ]        │
│   Şifre:   [ ••••••••••••                         ]        │
│                                                             │
│             [ Giriş Yap ]                                   │
│                                                             │
│   Role: operator  │  Token: 24 saat geçerli                │
└─────────────────────────────────────────────────────────────┘
```

*Giriş formu, FastAPI `/api/auth/jwt/login` endpoint'ine OAuth2 form-data POST isteği gönderir.
Başarılı girişte JWT token localStorage'a yazılır ve tüm sonraki isteklerde
`Authorization: Bearer <token>` başlığı otomatik eklenir.*

**Rol Dağılımı**:
| Rol | Erişim |
|---|---|
| `viewer` | Senaryo görüntüleme, forecast, XAI |
| `operator` | Tüm viewer hakları + solver çalıştırma + export |
| `admin` | Tüm operator hakları + kullanıcı yönetimi |

---

## C.2 Ana Gösterge Paneli (Dashboard)

**Şekil C.2 — Ana KPI Satırı**

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Toplam Uçuş   Aktif    İptal   Ort. Gecikme   Toplam Kâr     CO₂       │
│     150          142       5      12.3 dk      ₺779,000    45,200 kg    │
│  ████████████  ████████  ████   ████████████  ████████████  ██████████  │
└──────────────────────────────────────────────────────────────────────────┘
```

*KPI kutuları Chart.js bar chart ile anlık güncellenir. Renk kodu:*
- *Yeşil: İyileşme / pozitif eğilim*
- *Sarı: Dikkat eşiği (gecikme > 30 dk)*
- *Kırmızı: Kritik (FTL ihlali, iptal oranı > %15)*

---

## C.3 Uçuş Listesi ve Karar Paneli

**Şekil C.3 — Uçuş Karar Tablosu**

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  Uçuş    Kalkış  Varış  Blok  Durum     Sebep                  Kâr (TL)     │
├──────────────────────────────────────────────────────────────────────────────┤
│  TK1001  IST     ESB    60dk  ✅ Normal  —                      5,200        │
│  TK1045  IST     ADB    75dk  ❌ İptal   CREW_DUTY_SATURATION       0        │
│  TK1089  ESB     IST    65dk  ⚠ Gecikme —                  28 dk  4,100     │
│  TK1102  AYT     IST    90dk  ✅ Normal  —                      8,700        │
│  TK1143  IST     AYT    90dk  ⚠ Gecikme WEATHER_CLOSURE   45 dk  3,600     │
│  ...                                                                          │
├──────────────────────────────────────────────────────────────────────────────┤
│  [ CSV İndir ]  [ PDF Rapor ]  [ Excel Rapor ]          Toplam: ₺779,000    │
└──────────────────────────────────────────────────────────────────────────────┘
```

*Tablo başlıklarına tıklanarak sıralama yapılabilir. "Sebep" sütunundaki ikonlara
tıklandığında XAI paneli açılır (§C.5).*

---

## C.4 Harita Görünümü

### C.4.1 MapLibre 2D Rota Haritası

**Şekil C.4 — Türkiye Rota Ağı**

```
       ┌─────────────────────────────────────────────────────────┐
       │  [TR]                    TZX                            │
       │                          •                              │
       │         IST •─────────────────────────────• ADB        │
       │             │╲          ESB•               │            │
       │             │ ╲────────────╲               │            │
       │             │              ╲               │            │
       │         AYT •               • GZT     DIY •            │
       │                              │              │            │
       │                         MLX •              │            │
       │                                        ERZ •            │
       └─────────────────────────────────────────────────────────┘
       Mavi çizgi: aktif rota │ Kırmızı: iptal │ Sarı: gecikmeli
```

*MapLibre GL JS ile OpenFreeMap vektör tile'ları üzerine GeoJSON rota katmanı çizilmiştir.
Her havalimanı, kapasite durumuna göre renklendirilmiş circle marker ile gösterilir.*

**Filtreler** (sol panel):
- Havayolu kodu
- Uçuş durumu (normal / gecikmeli / iptal)
- Kalkış havalimanı
- Zaman aralığı

### C.4.2 Three.js 3D Hava Sahası

**Şekil C.5 — 3D Hava Sahası Görünümü**

```
        ↑ (yükseklik)
   FL350 │              ●─────────────→
         │    ●                          ●
   FL250 │         ●──────●                    
         │                          ●
   FL100 │    ●───────────────────────→
         └─────────────────────────────→ (mesafe)
                IST          ESB         ADB
```

*Three.js WebGL sahnesinde uçaklar, gerçek zamanlı ADS-B pozisyonlarına göre
3 boyutlu olarak hareket eder. Renk kodu: yeşil=normal, sarı=gecikmeli, kırmızı=iptal.*

*Kamera kontrolü: Mouse ile döndürme (drag), tekerlek ile zoom, çift tıklama ile
belirli uçağa odaklanma.*

---

## C.5 XAI Açıklama Paneli

**Şekil C.6 — SHAP Waterfall Grafiği (TK1045 İptal Kararı)**

```
  Karar: İPTAL — CREW_DUTY_SATURATION
  ─────────────────────────────────────────────────────────
  Temel değer            │████████████████│  0.42
  weather_risk     +0.22 │████████████████████████│
  crew_base_fatigue+0.17 │████████████████████│
  tech_failure_prob+0.14 │████████████████│
  dest_congestion  +0.11 │█████████████│
  slot_pressure    +0.09 │███████████│
  aircraft_health  -0.07 │       ███████│ (azaltıcı)
  load_factor      +0.06 │████████│
  is_night_flight  +0.04 │█████│
  ─────────────────────────────────────────────────────────
  Final skor:             1.18  → İptal (eşik: 0.85)
  
  💡 Counterfactual: crew_base_fatigue < 0.20 olsaydı uçuş
     devam ederdi (skor: 0.81 < eşik).
```

**Bayesian Nedensellik**:
```
  Doğrudan neden: crew_base_fatigue (0.17)
  Katkıda bulunanlar: weather_risk, slot_pressure_flag
  Açıklama: Mürettebatın birikmiş yorgunluğu, zaten yüksek
            olan hava riskiyle birleşince iptal kaçınılmaz oldu.
```

---

## C.6 7 Günlük Tahmin Grafiği

**Şekil C.7 — Forecast Panel**

```
  Ort. Gecikme (dk)
  40 ┤
     │                   ╭─╮
  30 ┤                  ╭╯ ╰╮
     │                 ╭╯   ╰╮
  20 ┤────────────────╯─────╰──────────── ortalama (17.1)
     │         ╭──╮  ╭╯     ╰╮  ╭──╮
  10 ┤─────────╯  ╰──╯       ╰──╯  ╰──── düşük (9.5)
     │
   0 ┼────────────────────────────────────
     16/4  17/4  18/4  19/4  20/4  21/4  22/4
     
  ━━ Tahmin  ▒▒ %95 güven aralığı
```

*Chart.js line chart. Gri band: %95 güven aralığı (bootstrapped).
18 Nisan zirvesi: IST-ESB koridorunda planlı bakım.*

---

## C.7 Stres Testi Paneli

**Şekil C.8 — Monte Carlo Stres Testi Sonuçları**

```
  ┌─────────────────────────────────────────────────────────┐
  │  Stres Senaryosu: Hava + Mürettebat Grevi %20           │
  │  Simülasyon sayısı: 500                                  │
  │─────────────────────────────────────────────────────────│
  │  P50 Gecikme:  14.1 dk    P95:  38.7 dk    P99: 62.3 dk │
  │  En kötü iptal oranı: %31                               │
  │  VaR (%95 güven):  ₺-124,000                            │
  │─────────────────────────────────────────────────────────│
  │  Dağılım (iptal oranı)                                  │
  │  0.1  ▓                                                  │
  │  0.2  ▓▓▓▓▓▓▓▓▓▓▓                                        │
  │  0.3  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓                                  │
  │  0.4  ▓▓▓▓▓▓▓▓▓                                          │
  │  0.5  ▓▓▓                                                │
  └─────────────────────────────────────────────────────────┘
```

---

## C.8 Optimizer Çalıştırma Ekranı

**Şekil C.9 — Solver Kontrol Paneli**

```
  ┌─────────────────────────────────────────────────────────┐
  │  Optimizasyon Stratejisi                                 │
  │  ○ PROFIT (Kâr Maksimizasyonu)                          │
  │  ● EKO (CO₂ Minimizasyonu)                              │
  │  ○ DAYANIKLILIK (İptal Minimizasyonu)                   │
  │                                                         │
  │  Zaman Sınırı: [60] saniye                              │
  │                                                         │
  │  [ ▶ Optimizasyonu Başlat ]                             │
  │─────────────────────────────────────────────────────────│
  │  ✅ Durum: OPTIMAL  │  Gap: 1.7%  │  Süre: 58.2 s      │
  │  Objective: ₺779,000  │  İptal: 5  │  FTL ihlali: 0   │
  └─────────────────────────────────────────────────────────┘
```

*Solver çalışırken buton devre dışı kalır ve animasyonlu spinner görünür.
CP-SAT zaman sınırına ulaştığında otomatik QIGA iyileştirme başlar.*

---

## C.9 PDF / Excel Rapor Çıktısı

**Şekil C.10 — Karar Raporu PDF (Ön Sayfa)**

```
  ┌─────────────────────────────────────────────────────────┐
  │              KARAR RAPORU                               │
  │         Aviation Digital Twin v27.0                     │
  │─────────────────────────────────────────────────────────│
  │  Tarih: 2026-04-15 10:45 UTC                            │
  │  Strateji: PROFIT │ Süre: 58.2s │ Gap: 1.7%            │
  │─────────────────────────────────────────────────────────│
  │  KPI ÖZETİ                                              │
  │  Toplam Uçuş:   150   Kâr: ₺779,000                    │
  │  İptal:           5   CO₂: 45,200 kg                   │
  │  Ort. Gecikme: 12.3 dk                                  │
  │  FTL İhlali:     0                                      │
  │─────────────────────────────────────────────────────────│
  │  [Uçuş Detay Tablosu...]                                │
  └─────────────────────────────────────────────────────────┘
```

*ReportLab ile landscape A4 PDF üretilir. İndirme butonu (operator/admin):
`GET /api/export/decision-report.pdf`*

---

## C.10 Prometheus / Grafana İzleme

**Şekil C.11 — Grafana Solver Performans Panosu**

```
  Solver Çözüm Süresi (son 1 saat)             Fallback Oranı
  ┌───────────────────────────┐    ┌─────────────────────────┐
  │ p50  p95  p99             │    │ opensky:  1.8%           │
  │ 52s  61s  63s             │    │ meteo:    0.4%           │
  │  │    │    │              │    │ noaa:     1.1%           │
  │  █    █    █              │    │                          │
  │  █    █    █              │    └─────────────────────────┘
  └───────────────────────────┘
  
  HTTP İstek Dağılımı (son 24 saat)
  ┌────────────────────────────────────────────────────────┐
  │ /api/scenario            ████████████████ 284 istek    │
  │ /api/optimizer/solve     ████████         142 istek    │
  │ /api/xai/explain         ██████           108 istek    │
  │ /api/forecast/seven-day  █████             89 istek    │
  │ /api/export/pdf          ████              67 istek    │
  └────────────────────────────────────────────────────────┘
```

*Grafana `http://localhost:3000` üzerinde çalışır. Prometheus scrape interval: 15 saniye.
Loki log aggregation: structured JSON format.*

---

## C.11 Uygulama Başlatma

```bash
# Geliştirme ortamı
make run
# → http://localhost:8501 (API)
# → http://localhost:8501/docs (Swagger UI)

# Docker Compose (üretim)
make docker-up
# → http://localhost:8501 (API, Caddy arkasında)
# → http://localhost:3000 (Grafana)
# → http://localhost:9090 (Prometheus)
```

---

*Not: Bu ekteki ASCII görseller, gerçek ekran görüntülerinin metin temsilidir.
Gerçek PNG ekran görüntüleri `docs/thesis/gorseller/` dizinine yerleştirilmiştir.
`scripts/take_screenshots.py` scripti Playwright ile otomatik ekran görüntüsü alır.*
