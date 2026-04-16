# Bölüm 8 — Deneysel Bulgular ve Değerlendirme

## 8.1 Deney Kurulumu

| Parametre | Değer |
|---|---|
| Uçuş sayısı (baz) | 150 |
| Uçak kuyruk sayısı | 20 |
| Mürettebat sayısı | 40 |
| Meydan sayısı | 14 |
| Zaman pencere | 24 saat |
| Solver zaman sınırı | 60 s |
| Koşu sayısı (her koşul) | 10 |
| CPU | Intel i7-12700 @ 4.9 GHz |
| RAM | 32 GB DDR5 |
| OR-Tools | 9.11 |

## 8.2 Şekil 8.1 — Solver Zaman–Optimal Yakınsama

CP-SAT çekirdeğinin 150 uçuşluk senaryoda **best bound** ve **best feasible** yakınsaması (tipik koşu):

```
Obj (TL, bin)
800 ┤                                   ████████ upper bound
    │                                ▁▇██
750 ┤                          ▁▃▅▆██
    │                      ▁▃▅█
700 ┤                  ▁▅██
    │              ▄██
650 ┤           ▄██
    │        ▃█
600 ┤      ▃█
    │    ▂█
550 ┤  ▃█                             ▁▁▁▁▁▁▁▁ lower bound
    │ █                        ▁▁▁▁▇█▀
500 ┤▃                    ▁▁▇▇█▀▀
    │              ▁▁▁▇▇█▀
450 ┤       ▁▁▁▇▇▇█▀
    │ ▁▁▇▇▇█▀
400 ┤█▀
    └─┬─────┬─────┬─────┬─────┬─────┬
      0     10    20    30    40   60 s

Optimality gap t=5s:  38%
Optimality gap t=15s: 12%
Optimality gap t=30s: 3.4%
Optimality gap t=60s: 2.1%
```

> *(Gerçek plot: `docs/thesis/gorseller/fig_8_1_convergence.png` — `scripts/gen_figures.py` ile üretilir. Bu ascii yaklaşıklık, 10 koşunun ortalamasıdır.)*

**Bulgu**: 30 saniyede %3.4, 60 saniyede %2.1 optimality gap. Bu, operasyonel karar için yeterli (dispatcher genellikle < 1 dk toleransta).

## 8.3 Tablo 8.1 — Baseline ve Önerilen Yöntem KPI'ları

150 uçuşluk, FTL baskılı senaryoda 10 koşu ortalaması (±95% CI):

| Metrik | B₁ Greedy | B₂ CP-SAT only | B₃ QIGA only | **M Hibrit (önerilen)** |
|---|---|---|---|---|
| Objective (bin TL) | 412 ± 18 | 742 ± 24 | 681 ± 31 | **779 ± 19** |
| Cancellations (adet) | 18.2 | 6.4 | 7.9 | **5.1** |
| Mean delay (dk) | 38.4 | 14.7 | 16.2 | **12.3** |
| Wall-clock (s) | 0.3 | 52.8 | 45.1 | **58.2** |
| FTL violations | 7.1 | 0 | 0.4 | **0** |
| Optimality gap | n/a | 2.1% | n/a | **1.7%** |

**İstatistiksel anlamlılık**: Wilcoxon signed-rank test, M vs B₂: $p = 0.007$ (anlamlı). M, **objective** açısından tek başına CP-SAT'a göre **%5** iyileşme, **cancellation** açısından **%20** iyileşme sağlar. QIGA tek başına (B₃) CP-SAT'tan sağlıksız (FTL ihlal edebilir, optimizasyon daha az sıkı).

**Hibrit'in özü**: CP-SAT optimal yakınında bir çözüm üretir → QIGA bu çözüm etrafında mikro-iyileştirmeler yapar → sonuç genel olarak her iki yöntemin tekil performansını geçer.

## 8.4 Şekil 8.2 — Senaryo Bazlı İptal Oranı

Beş farklı stres senaryosu altında iptal oranı (cancellations / total flights):

```
Scenario            Baseline B1 ▓▓▓▓▓▓▓▓▓▓▓▓▓
                     CP only B2 ▓▓▓▓
                        QIGA B3 ▓▓▓▓▓
                      Hybrid M  ▓▓▓  ← minimum

Normal ops:         B1:12% B2:4% B3:5% M:3%
Weather closure:    B1:28% B2:14% B3:18% M:11%
Crew strike 20%:    B1:34% B2:22% B3:19% M:15%
Gate shortage:      B1:19% B2:9% B3:12% M:8%
Combined stress:    B1:47% B2:31% B3:33% M:24%
```

**Yorum**: M, **ağır bozulma** koşullarında (combined stress) B₂'ye göre daha belirgin fark yaratır; bu QIGA'nın infeasibility sonrası iyileştirme gücünü gösterir.

## 8.5 Şekil 8.5 — Canlı Veri Entegrasyonu Gecikme Ölçümleri ve Tablo 8.2

OpenSky + Open-Meteo + NOAA canlı çağrıları (100 istek, p50/p95/p99):

| Kaynak | p50 (ms) | p95 (ms) | p99 (ms) | Fallback oranı |
|---|---|---|---|---|
| OpenSky `/states/all` | 340 | 920 | 2,100 | 1.8% |
| Open-Meteo `/forecast` | 120 | 310 | 540 | 0.4% |
| NOAA `/metar` | 280 | 640 | 1,200 | 1.1% |
| Toplam live_sync turu | 450 | 1,140 | 2,300 | — |

**Circuit breaker etkisi**: 5 ardışık hatada 60 s sonra geri açılır. Fallback oranı < %2, bu ürünleşmeye uygun seviyede.

## 8.6 Şekil 8.3 — SHAP Özellik Önemi Dağılımı

150 uçuşta aggregate mean |SHAP value|:

```
Feature                |SHAP|
weather_risk           ███████████████████████ 0.22
crew_base_fatigue      █████████████████ 0.17
tech_failure_prob      ██████████████ 0.14
dest_congestion        ███████████ 0.11
slot_pressure_flag     █████████ 0.09
aircraft_health        ███████ 0.07
load_factor            ██████ 0.06
is_night_flight        ████ 0.04
hub_traffic_7d         ███ 0.03
ntn_link_active        ██ 0.02
pax_mobility_index     █ 0.01
```

**Bulgu**: Hava riski ve mürettebat yorgunluğu baskın; bu EASA beklentileriyle örtüşür (FTL ve meteorological factors IATA delay codes içinde ilk iki kategoridir).

**Şekil 8.6 — Karar Gerekçe Dağılımı**: 150 uçuşun iptal/gecikme nedenlerinin kategori bazlı dağılımı (CREW_DUTY_SATURATION, WEATHER_CLOSURE, GATE_UNAVAILABLE, SLOT_CONFLICT, TECHNİCAL_FAILURE).

**Şekil 8.9 — Türkiye Hava Yolu Ağı**: 14 havalimanının simülasyon ağı; mavi: aktif rota, kırmızı: IST hub, sarı: yüksek yoğunluklu.

## 8.7 Şekil 8.7 — Ölçeklenebilirlik Deneyleri

Şekil 8.7, uçuş sayısına (50 → 3000) karşı CP-SAT çözüm süresi ve optimality gap eğrisini göstermektedir.

| Uçuş sayısı | Değişken sayısı | CP-SAT süre (s) | Optimality gap @ 60s |
|---|---|---|---|
| 50 | 3,200 | 4.1 | 0.2% |
| 150 | 9,600 | 24.3 | 2.1% |
| 500 | 32,000 | 60.0 (timeout) | 8.4% |
| 1500 | 96,000 | 60.0 (timeout) | 21.6% |
| 3000 | 192,000 | 60.0 (timeout) | 38.2% |

**Bulgu**: 500 uçuşa kadar hibrit pratik. 1500+ için `INDUSTRY_ROADMAP.md` Faz F'de tanımlanan **rolling horizon** + **multi-fleet partition** gereklidir.

## 8.8 Şekil 8.4 — FTL Doğrulama Deneyi

**Senaryo**: Tek mürettebata $c_1$ ait 2 uçuş $f_1, f_2$ her biri 400 dk block_time.
**Beklenen**: $\sum y \cdot \text{block} = 800 > 600$ → en az 1 iptal, `decision_reason="CREW_DUTY_SATURATION"`.

```
Input:  f1 (TK1001, block=400), f2 (TK1002, block=400), crew=c1
Result: f1.is_canceled=False, f2.is_canceled=True
        f2.decision_reason="CREW_DUTY_SATURATION"
        f2.assigned_delay=0  (cancel, not delay)
        FTL violations: 0  ✓
```

`test_solver_enforces_crew_duty_cap` bu davranışı otomatize ediyor; 10/10 deterministik geçiyor.

## 8.9 Şekil 8.8 — API Performans Testi

Locust ile 50 concurrent dispatcher, 10 dakika:

| Endpoint | p50 (ms) | p95 (ms) | p99 (ms) | Error rate |
|---|---|---|---|---|
| GET /api/scenario | 38 | 112 | 218 | 0.0% |
| POST /api/optimizer/solve | 24,300 | 58,900 | 62,100 | 0.8% |
| GET /api/forecast/seven-day | 184 | 410 | 720 | 0.0% |
| GET /api/xai/explain/{id} | 96 | 240 | 480 | 0.0% |
| GET /api/export/decision-report.pdf | 1,420 | 2,880 | 3,900 | 0.0% |

**Yorum**: Solver endpoint'i p99'da zaman sınırına çok yakın. Üretimde Celery worker pool'a çıkarılması önerilir (Faz F).

## 8.10 Şekil 8.10 — XAI Kullanılabilirlik Mini Deneyi

5 havacılık mühendisi (TEKNOFEST değerlendirme jürisi örneklemi dışında) ile anket:

| Soru | Ortalama (1–5 Likert) |
|---|---|
| Karar gerekçesi anlaşılır mı? | 4.4 |
| SHAP grafiği güven verici mi? | 4.2 |
| Counterfactual "Eğer mürettebat..." yardımcı mı? | 3.8 |
| Genel olarak dispatcher UI'sı kullanılabilir mi? | 4.5 |

**Bulgu**: Açıklanabilirlik çıktıları dispeçer güvenini pozitif etkiler; SHAP waterfall tercih edilen görselleştirme.

## 8.11 Şekil 8.11 — Canlı Veri vs Sentetik Senaryo Karşılaştırması

Aynı 150 uçuş, iki koşul:

| KPI | Sentetik (offline) | Canlı-füzyonlu |
|---|---|---|
| Objective (bin TL) | 782 ± 14 | 771 ± 22 |
| Cancellations | 4.9 | 5.6 |
| Mean delay | 11.8 | 13.2 |
| Solver time | 56.4 | 58.1 |

Fark istatistiksel olarak anlamlı değil ($p > 0.3$). Gerçek veri mevcut mimari için pratik bir bozunmaya yol açmıyor; mimari **canlı sağlam**.

## 8.12 Deney Özet

| Deneysel Bulgu | Destekleyen Veri |
|---|---|
| Hibrit yöntem M, tek yöntemlere göre anlamlı iyileşme | Tablo 8.1 (p=0.007) |
| Solver 150 uçuşta 60s altında optimal yakın | Şekil 8.1 |
| EASA FTL tavanı hard-constraint olarak etkili | §8.8 |
| XAI çıktıları kullanıcı güvenini artırıyor | §8.10 |
| Canlı veri entegrasyonu kararları bozmuyor | §8.11 |
| 500+ uçuş için rolling horizon gerekli | Tablo 8.7 |

Bölüm 9, bu bulguları literatür ve endüstri kriterleriyle **tartışır**.
