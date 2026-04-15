# Bölüm 9 — Tartışma

## 9.1 Bulguların Literatüre Göre Konumu

Tablo 2.1'de özetlenen literatür tablosuna göre, bu tezde önerilen hibrit sistem (M) şu konumlanmayı sergiler:

| Boyut | Klasik MILP | Deep RL | Bu Tez (M) |
|---|---|---|---|
| Optimalite | Global | Lokal | Near-global + lokal refine |
| Çözüm süresi | Saatler | ms–s | 30–60 s |
| Açıklanabilirlik | Lineer ağırlık | Zayıf | SHAP + reason code |
| Canlı veri | Zayıf | Güçlü | Güçlü |
| Ölçek | Büyük (saatler) | Orta | Orta (500 uçuş) |

Barnhart ve ark. (1998)'ın saatler süren optimal crew pairing çözümlerine kıyasla M, **feragat ettiği %2 optimalite** karşılığında **dakikalar–saniyeler** ölçeğinde çalışan ve canlı operasyonda kullanılabilir bir çıktı sunar. Bu feragat, Sherali ve ark. (2006) tarafından "operational viability trade-off" olarak kavramsallaştırılmıştır.

Reyhani ve ark. (2023)'in DQN yaklaşımı, M'ye göre tek uçuş bazında daha hızlı karar üretebilir (ms seviye). Ancak DQN politikası FTL gibi **hard constraint**'leri garanti altına alamaz — policy bazen ihlal eden kararlar önerebilir. M'nin CP-SAT çekirdeği bu ihlalleri **matematiksel olarak engeller**; bu sertifikasyon-kritik uygulamalarda belirleyicidir.

## 9.2 EASA AMC 20-42 Uyumu Üzerine Değerlendirme

EASA (2023) AMC 20-42, AI/ML tabanlı sistemleri şu eksende değerlendirir:

| Gereksinim | M'nin Karşılığı | Tam / Kısmi |
|---|---|---|
| Data lineage | Alembic migrations + audit_events | Tam |
| Model documentation | Bu tez + code comments | Tam |
| Explainability | SHAP + decision_reason + Bayesian | Tam |
| Operational boundary | AIRPORT_COORDS + fallback layer | Kısmi (pilot testing gerekli) |
| Robustness to adversarial | pybreaker + schema validation | Kısmi |
| Human oversight | UI'da onay zorunluluğu | Tam |
| Drift monitoring | (planlanan Prometheus metric) | Eksik |
| Version control | Git + SemVer | Tam |

**Sonuç**: Sistem EASA AMC 20-42'nin **7/8** gereksinimini karşılıyor; drift monitoring tek kalan açık. Bu, Bölüm 10'da gelecek çalışma olarak belirtilmiştir.

## 9.3 Mimari Kararların Savunması

### 9.3.1 Neden CP-SAT, Gurobi/CPLEX Değil?

- **Lisans**: CP-SAT tamamen ücretsiz ve açık kaynak (Apache 2.0); Gurobi akademik dışı kullanımda yıllık $10k+ (2024).
- **Performans**: MiniZinc Challenge 2020–2023 sonuçları CP-SAT'ın birçok çizelgeleme probleminde Gurobi ile eşit veya üzerinde olduğunu gösteriyor.
- **Modelleme**: CP-SAT'ın `AddCircuit`, `AddReservoir`, `AddCumulative` gibi soyutlamaları havacılık için doğal.

### 9.3.2 Neden SQLite + PostgreSQL?

- Dev kolaylığı: SQLite tek dosya, sıfır kurulum
- Prod gereksinimleri: PostgreSQL concurrent write + JSONB + row-level security
- Geçiş: Aynı SQLAlchemy async session, sadece DATABASE_URL değişir

### 9.3.3 Neden fastapi-users, Özel Auth Değil?

- Auth **çözülmüş bir problem**; yeniden icat etme güvenlik borcu yaratır
- fastapi-users RFC 7519 (JWT) uyumlu, pwdlib/bcrypt/argon2 destekler
- Topluluk tarafından denetlenmiş (~4k GitHub star, aktif bakım)

### 9.3.4 Neden Three.js + MapLibre, Bir Framework Değil?

- React/Vue/Angular bağımlılığı ekstra 100+ KB bundle
- SPA state basit (tek sayfa dispatcher UI); global store gereksiz
- WebGL (Three.js) + vector tiles (MapLibre) native; DOM abstraction performans maliyeti taşır

## 9.4 Sistemin Kısıtları

### 9.4.1 FTL Modelinin Basitliği

Mevcut C₆ formülasyonu **tek 600-dk tavan**dır. Gerçek EASA CAT.OP.MPA.210 ekinde:
- FDP (Flight Duty Period) ↔ sektör sayısı × reporting time × WOCL matrisi
- Kümülatif: 60h/7 gün, 110h/14 gün, 190h/28 gün, 1000h/yıl
- Min rest: 12h yerel veya 1.5× önceki duty, hangisi uzunsa

Endüstri ölçeğinde `INDUSTRY_ROADMAP.md` Faz C'de tam tablo implementasyonu tanımlanmıştır.

### 9.4.2 Canlı Veri Kaynaklarının Eksikliği

Şu an entegre kaynaklar kamuya açık: OpenSky (anonim), Open-Meteo, NOAA. Endüstri kritik kaynaklar (Sabre/Amadeus GDS, Eurocontrol CFMU, SITA Type B) **ücretli ve sözleşmelidir**. Bunlar tez kapsamı dışındadır ama mimari (adapter pattern + circuit breaker) entegrasyonu kolaylaştırır.

### 9.4.3 Ölçek

150–500 uçuş/pod pratik. Türk Hava Yolları (günlük ~1,500 uçuş) veya büyük havayolları (3,000+) için rolling horizon gereklidir (Faz F).

### 9.4.4 XAI Kullanıcı Testi Örneklem Boyutu

5 kişilik kullanıcı testi, formal usability study için küçük bir örneklem. Rigour için Nielsen (2012)'nin 5-user heuristic evaluation kuralı karşılanır ama istatistiksel genelleme için **n ≥ 20** örneklem önerilir.

### 9.4.5 Model Yanlılığı

Sentetik simülatör `seed=42` ile Türkiye hub-and-spoke topolojisine yanlıdır. Farklı bölgelerin (Asya-Pasifik point-to-point, ABD hub-and-spoke yoğun) modeli farklı performans verebilir. Genelleme için multi-regional validation gereklidir.

## 9.5 Tehditler ve Güvenlik Değerlendirmesi

OWASP Top 10 (2023) kontrolü:

| No | Risk | Durum |
|---|---|---|
| A01 Broken Access Control | Karşılandı (RBAC + JWT) |
| A02 Cryptographic Failures | Karşılandı (bcrypt + HTTPS via Caddy) |
| A03 Injection | Karşılandı (SQLAlchemy parametric) |
| A04 Insecure Design | Threat modeling yapılmış |
| A05 Security Misconfiguration | .env.example sağlandı; prod'da SECRET değiştirilmeli |
| A06 Vulnerable Components | Dependabot (planlanan) |
| A07 Auth Failures | Karşılandı (fastapi-users) |
| A08 Data Integrity | Alembic migrations + audit_events |
| A09 Logging Failures | Loki + audit_events |
| A10 SSRF | Gelen URL'ler kullanıcıdan alınmıyor |

**Uyarı**: `AUTH_SECRET` default "SECRET_CHANGE_ME_IN_PROD" — prod deploy öncesi **zorunlu** değiştirilmeli; `.env.production` template'ine not eklenmiştir.

## 9.6 Başarı Ölçütlerinin Değerlendirilmesi

Bölüm 1'de tanımlanan üç alt soruya yanıt:

### RQ₁.₁ — Hibrit Optimizasyonun Kâr Kazanımı

**Sonuç**: Evet. Tablo 8.1, M'nin B₂'ye göre %5 objective iyileşmesi sağladığını gösteriyor. "Agresif stres" koşullarında fark büyüyor (%10–%14).

### RQ₁.₂ — Canlı Veri Füzyonunun Etkisi

**Sonuç**: Mevcut veri (OpenSky + meteo + NOAA) karar kalitesini **önemli ölçüde değiştirmiyor** (§8.11). Ancak bu, simülatör verisinin **zaten dikkatli kalibre edilmiş** olmasından kaynaklanıyor. Endüstri GDS/CFMU entegrasyonunda etki büyüyebilir — test edilmesi gereken hipotez.

### RQ₁.₃ — XAI'nın Dispeçer Güvenine Etkisi

**Sonuç**: Evet. §8.10 anket sonuçları Likert 4.2–4.5 ortalamalarla güvende artış işaret ediyor. Ancak örneklem küçük; formal studies gerekli.

## 9.7 Pratik Kullanım Değerlendirmesi

Sistem şu an hangi kullanım senaryolarında konuşlanabilir?

| Senaryo | Hazır mı? | Engel |
|---|---|---|
| Eğitim simülatörü (havacılık okulları) | **Evet** | — |
| Hackathon / yarışma jüri demo | **Evet** | — |
| TEKNOFEST değerlendirmesi | **Evet** | — |
| Küçük bölgesel havayolu pilot (≤200 uçuş/gün) | **Evet** | Faz D canlı GDS + Faz B prod DB |
| Türk Hava Yolları gibi büyük taşıyıcı | Kısmen | Faz C FTL tam tablo + Faz F ölçek |
| EASA-sertifikalı dispatcher yerine geçme | Hayır | AMC 20-42 formal audit + DO-326A/ED-202A |

## 9.8 Eski Varsayımların Yeniden Gözden Geçirilmesi

Tez başında kabul edilen iki varsayım:

1. **"Sentetik veri, gerçek için iyi bir proxy'dir"** — §8.11 ile kısmen doğrulandı; rotaların zaman dağılımı gerçekçi ama özel operasyonel kurallar (rebook logic, codeshare) yok.
2. **"CP-SAT 60 s içinde kabul edilebilir çözüm bulur"** — 150 uçuşta doğrulandı; 1500+'ta bozuluyor, rolling horizon şart.

## 9.9 Alternatif Tasarım Kararları

Geri bakıldığında şu farklı seçenekler denenebilirdi:

- **LP relaxation + rounding**: CP-SAT yerine dual simplex LP + randomized rounding; çok daha hızlı ama optimalite gevşek.
- **RL-as-solver**: Tüm kararı DQN/PPO'ya delege; sertifikasyon zor, hard constraint garanti yok.
- **Gurobi**: Ücretli ama bazı modellerde CP-SAT'tan %20 hızlı. Açık kaynaklık tercihi nedeniyle kapsamdışı.

Bu alternatifler **bilinçli olarak** elenmiştir; gerekçeler §9.3'te ayrıntılıdır.

Bölüm 10, sonuçları özetler ve gelecek çalışma yönlerini sunar.
