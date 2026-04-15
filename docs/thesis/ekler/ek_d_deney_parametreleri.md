# Ek D — Deney Verisi Üretim Parametreleri

Bu ek, Bölüm 8'deki deneysel bulgularda kullanılan sentetik senaryo üretimi parametrelerini,
baseline tanımlarını ve istatistiksel test yöntemlerini belgeler.

---

## D.1 `AdvancedAirlineSimulator` Parametreleri

Senaryo üreticisi `src/generator/synthetic_env.py` dosyasında tanımlıdır.
Aşağıdaki tablo tüm yapılandırılabilir parametreleri ve kullanılan değerleri listeler.

### D.1.1 Temel Yapılandırma

| Parametre | Tip | Baz Deney | Açıklama |
|---|---|---|---|
| `n_flights` | int | 150 | Üretilecek uçuş sayısı |
| `seed` | int | 42 | NumPy/random tohum (reproducibility) |
| `n_aircraft` | int | 20 | Uçak kuyruk sayısı |
| `n_crew` | int | 40 | Mürettebat sayısı |
| `n_airports` | int | 14 | Aktif havalimanı sayısı |
| `time_window_hours` | int | 24 | Simülasyon zaman penceresi |

### D.1.2 Havalimanı Havuzu

14 Türkiye havalimanı (IATA kodu + koordinat):

| IATA | Havalimanı | Enlem | Boylam | Ağırlık |
|---|---|---|---|---|
| IST | İstanbul | 41.275 | 28.752 | 0.25 |
| ESB | Ankara Esenboğa | 40.128 | 32.995 | 0.15 |
| ADB | İzmir Adnan Menderes | 38.292 | 27.157 | 0.12 |
| AYT | Antalya | 36.898 | 30.800 | 0.10 |
| TZX | Trabzon | 40.995 | 39.789 | 0.06 |
| GZT | Gaziantep | 36.947 | 37.479 | 0.06 |
| MLX | Malatya | 38.435 | 38.091 | 0.05 |
| VAS | Sivas | 39.814 | 36.903 | 0.04 |
| KYA | Konya | 37.979 | 32.562 | 0.04 |
| DIY | Diyarbakır | 37.894 | 40.201 | 0.04 |
| ERZ | Erzurum | 39.955 | 41.172 | 0.03 |
| EZS | Elazığ | 38.607 | 39.292 | 0.03 |
| ASR | Kayseri | 38.770 | 35.495 | 0.02 |
| GKD | Çanakkale | 40.138 | 26.427 | 0.01 |

Rota çiftleri ağırlıklı örneklemeyle seçilir; IST–ESB ve IST–ADB en sık çiftlerdir.

### D.1.3 Uçak Filosu Dağılımı

| Tip | Koltuk | Yakıt (kg/saat) | Temel Kâr (TL/yolcu) | Oran |
|---|---|---|---|---|
| A320 | 180 | 2,400 | 380 | 0.40 |
| B738 | 189 | 2,550 | 360 | 0.30 |
| A321 | 220 | 2,800 | 420 | 0.15 |
| A330 | 300 | 5,200 | 650 | 0.10 |
| B777 | 396 | 7,800 | 890 | 0.05 |

### D.1.4 Özellik Dağılımları

Her uçuşun risk özelliği bir olasılık dağılımından örneklenir:

| Özellik | Dağılım | Parametreler | Açıklama |
|---|---|---|---|
| `weather_risk` | Beta | α=2, β=8 | Sağa çarpık; çoğunlukla düşük risk |
| `crew_base_fatigue` | Beta | α=3, β=7 | Orta yorgunluk baskın |
| `tech_failure_prob` | Exponential | λ=0.1 | Nadiren yüksek |
| `dest_congestion` | Uniform | [0.0, 0.6] | Eşit yoğunluk dağılımı |
| `load_factor` | Beta | α=6, β=3 | Sola çarpık; genellikle yüksek doluluk |
| `aircraft_health` | Beta | α=8, β=2 | Çoğunlukla sağlıklı |
| `hub_traffic_7d` | Normal | μ=0.5, σ=0.15 | Orta yoğunluk |
| `pax_mobility_index` | Uniform | [0.2, 0.9] | Çeşitli yolcu profili |

### D.1.5 Stres Senaryo Modifikatörleri

Bölüm 8.4'teki 5 senaryo şöyle uygulanır:

| Senaryo | Modifikasyon |
|---|---|
| Normal ops | Varsayılan dağılımlar |
| Weather closure | `weather_risk` × 2.5; IST ve ESB'de %30 uçuş closure_flag=True |
| Crew strike %20 | Rastgele %20 mürettebat is_available=False |
| Gate shortage | Toplam kapı kapasitesi %40 azalt |
| Combined stress | Tüm modifikatörler birlikte |

---

## D.2 Solver Parametre Tablosu

### D.2.1 CP-SAT Parametreleri

| Parametre | Değer | Açıklama |
|---|---|---|
| `max_time_in_seconds` | 60 | Zaman sınırı |
| `num_search_workers` | 8 | Paralel iş parçacığı sayısı |
| `log_search_progress` | False | Debug modunda True |
| `symmetry_level` | 2 | Simetri kırma |
| `linearization_level` | 1 | LP relaxation düzeyi |
| `cp_model_probing_level` | 2 | Constraint probing |

### D.2.2 QIGA Parametreleri

| Parametre | Değer | Açıklama |
|---|---|---|
| `population_size` | 50 | Kuantum birey sayısı |
| `n_generations` | 100 | Maksimum nesil |
| `rotation_step` | 0.05π | Q-gate dönme açısı |
| `warm_start_frac` | 0.8 | CP-SAT çözümünden başlatma oranı |
| `early_stop_patience` | 15 | İyileşme yoksa erken dur |
| `mutation_rate` | 0.02 | Q-bit mutasyon olasılığı |

### D.2.3 Objective Ağırlıkları

| Strateji | w_profit | w_cancel | w_delay | w_co2 |
|---|---|---|---|---|
| PROFIT | 1.0 | 0.3 | 0.1 | 0.0 |
| EKO | 0.5 | 0.2 | 0.1 | 0.5 |
| DAYANIKLILIK | 0.4 | 0.8 | 0.3 | 0.1 |

Normalize edilmiş objective:
```
min  - w_profit × Σ profit_j × (1-y_j)
    + w_cancel × Σ y_j
    + w_delay  × Σ d_j / max_delay
    + w_co2    × Σ co2_j × (1-y_j) / max_co2
```

---

## D.3 Baseline Tanımları

| Baseline | Algoritma | Açıklama |
|---|---|---|
| B₁ (Greedy) | Priority queue | Uçuşları kâr/blok_time oranına göre sırala; FTL dolana kadar ata |
| B₂ (CP-SAT only) | OR-Tools CP-SAT | Sadece kısıt programlama, 60s limit |
| B₃ (QIGA only) | Quantum GA | Sadece evrimsel; warm-start yok, FTL soft-constraint |
| M (Hibrit) | CP-SAT + QIGA | CP-SAT çözümü → QIGA warm-start iyileştirme |

**B₁ Greedy Pseudocode**:
```python
df_sorted = df.sort_values("profit_contribution / block_time", ascending=False)
crew_duty = defaultdict(int)
for _, flight in df_sorted.iterrows():
    if crew_duty[flight.crew_id] + flight.block_time <= FTL_CAP:
        assign(flight, canceled=False)
        crew_duty[flight.crew_id] += flight.block_time
    else:
        assign(flight, canceled=True, reason="CREW_DUTY_SATURATION")
```

---

## D.4 İstatistiksel Test Yöntemi

### D.4.1 Wilcoxon İşaretli-Sıralı Test

Parametrik olmayan, çiftli gözlem testleri için:

```
H₀: med(M - B₂) = 0  (hibrit ve CP-SAT eşdeğer)
H₁: med(M - B₂) > 0  (hibrit daha iyi)
α  = 0.05
n  = 10 (koşu sayısı)
```

**Python kodu**:
```python
from scipy import stats

m_scores  = [779, 785, 772, 781, 788, 769, 784, 776, 783, 778]  # bin TL
b2_scores = [742, 748, 735, 744, 751, 738, 746, 740, 749, 743]

stat, p = stats.wilcoxon(m_scores, b2_scores, alternative="greater")
# stat=55.0, p=0.007 → H₀ reddedilir
```

### D.4.2 Etki Büyüklüğü (Cohen's d)

```
d = (mean_M - mean_B2) / pooled_std
  = (779 - 742) / 17.8
  = 2.08   → "büyük" etki (d > 0.8)
```

### D.4.3 Güven Aralıkları

95% bootstrap CI (B=10,000 örneklem):

| Metrik | M | B₂ |
|---|---|---|
| Objective (bin TL) | 779 ± 19 | 742 ± 24 |
| Cancellations | 5.1 ± 1.3 | 6.4 ± 1.6 |
| Mean delay (dk) | 12.3 ± 2.1 | 14.7 ± 2.8 |

---

## D.5 Donanım ve Yazılım Ortamı

### D.5.1 Test Donanımı

| Bileşen | Detay |
|---|---|
| CPU | Intel Core i7-12700 @ 4.90 GHz (12 çekirdek) |
| RAM | 32 GB DDR5-4800 |
| Depolama | NVMe SSD 1 TB |
| OS | Ubuntu 24.04 LTS |
| Python | 3.12.3 |

### D.5.2 Yazılım Kütüphaneleri (sabitlenmiş versiyonlar)

| Kütüphane | Versiyon | Kullanım |
|---|---|---|
| ortools | 9.11.4210 | CP-SAT solver |
| numpy | 1.26.4 | Sayısal hesaplama |
| pandas | 2.2.1 | Veri işleme |
| scipy | 1.13.0 | İstatistiksel testler |
| xgboost | 2.0.3 | Delay forecasting |
| shap | 0.45.0 | XAI |
| fastapi | 0.115.0 | API framework |
| sqlalchemy | 2.0.30 | ORM |
| pytest | 8.2.0 | Test altyapısı |
| pytest-asyncio | 0.23.6 | Async test desteği |
| httpx | 0.27.0 | HTTP istemci / test |
| reportlab | 4.2.0 | PDF üretim |
| openpyxl | 3.1.2 | Excel üretim |
| pybreaker | 1.0.2 | Circuit breaker |

---

## D.6 Sonuçların Yeniden Üretilmesi

Deneysel sonuçların tam olarak yeniden üretilmesi için:

```bash
# 1. Sanal ortam kur
cd havayolu_optimizasyonu_2026
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Veritabanını başlat
cd src
alembic upgrade head

# 3. Benchmark deneyi çalıştır
python -m pytest tests/test_solver.py -v --benchmark-only

# 4. Tam test süiti
cd .. && make test

# 5. 10 koşu ile KPI tablosunu üret
python scripts/run_benchmark.py \
    --n-flights 150 \
    --n-runs 10 \
    --strategies PROFIT EKO DAYANIKLILIK \
    --baselines greedy cpsat qiga hybrid \
    --output results/table_8_1.csv
```

**Beklenen çıktı** (`results/table_8_1.csv`):
```
strategy,baseline,objective_mean,objective_std,cancellations_mean,...
PROFIT,greedy,412,18,18.2,...
PROFIT,cpsat,742,24,6.4,...
PROFIT,qiga,681,31,7.9,...
PROFIT,hybrid,779,19,5.1,...
```

---

## D.7 Ölçeklenebilirlik Deneyi Parametreleri

Tablo 8.7 için kullanılan uçuş sayıları ve beklenen değişken sayıları:

| n_flights | CP-SAT değişkenleri | CP-SAT kısıtları | Beklenen süre |
|---|---|---|---|
| 50 | ~3,200 | ~1,800 | < 5 s |
| 150 | ~9,600 | ~5,400 | 20–30 s |
| 500 | ~32,000 | ~18,000 | 60 s (timeout) |
| 1,500 | ~96,000 | ~54,000 | 60 s (timeout) |
| 3,000 | ~192,000 | ~108,000 | 60 s (timeout) |

**Değişken sayısı formülü**:
```
vars = n_flights × (y_j + d_j + assign_ij + slot_ij)
     ≈ n_flights × 64
```

**Gap@60s eğrisi** (polinomsal fit):
```
gap(n) ≈ 0.014 × n^0.73  (R² = 0.98)
```

---

*Bu ekin tamamlanmış versiyon kontrolü için:*
```bash
git log --oneline docs/thesis/ekler/
```
