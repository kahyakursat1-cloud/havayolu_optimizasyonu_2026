# Endüstri Standardına Taşıma Yol Haritası

**Mevcut durum**: TEKNOFEST jürisine savunulabilir çalışan prototip (v28).
**Hedef**: Gerçek bir havayolu operasyon merkezinde production olarak koşabilecek ürün.
**Tahmini süre**: 6–12 ay, küçük bir çekirdek takımla.

Bu doküman fazları tamamlama **önceliğine** göre sıralar — önce auth ve veri modeli, sonra FTL derinliği, en sonda ölçek/observability. Her faz kendi başına shippable bir milestone üretir.

---

## Faz A — Güvenlik ve Kimlik (4–6 hafta)

**Neden önce bu**: Gerçek veri akınca kimliksiz API ilk gün kapatılır. Tüm sonraki entegrasyonlar auth gerektirir.

- **Keycloak / Auth0** ile OAuth2 + OIDC; backend'e JWT middleware (python-jose/authlib)
- **RBAC**: `operator`, `dispatcher`, `analyst`, `admin` rolleri; endpoint bazlı scope kontrolü
- **Audit log**: her karar/ değişiklik/ export için `who, what, when, why` — ayrı `audit_events` tablosu
- API key tabanlı `X-API-Key` mevcut auth'ı tamamen kaldır; sadece dev bypass olarak tut
- SSO gate'inden geçmeyen legacy endpoint'leri `410 Gone` yap

**Kritik dosyalar**: yeni `src/auth/` modülü, `src/api/main.py` middleware stack'i
**Çıkış kriteri**: `curl -H "Authorization: Bearer …"` olmadan tüm `/api/*` 401 dönüyor.

---

## Faz B — Veri Modeli ve Persistance (6–8 hafta)

**Neden**: SQLite tek yazar kilitleyici; synthetic simulator veriyi her sefer sıfırdan üretiyor. Endüstride operasyonel veri **kalıcı** ve **çok kullanıcıyla eşzamanlı** değişir.

- **PostgreSQL + Alembic migrations** (SQLite'ı tamamen çıkar)
- **Şema**: `aircraft`, `crews`, `flights`, `maintenance_events`, `slot_allocations`, `decisions` ayrı tablolar — synthetic'in tek "fat dataframe"i yerine normalize edilmiş model
- **Crew qualification matrix**: `crew_qualifications(crew_id, ac_type, role, valid_from, valid_to)` — Captain/FO/Cabin ayrımı, recency tracking
- **MRO veri modeli**: `maintenance_tasks`, `part_inventory`, `engine_health_readings` — AMOS/Trax export formatını al
- SQLAlchemy 2.x async session + connection pool tuning
- **Redis** cache: live_sync + market_intel TTL cache'ini taşı

**Kritik dosyalar**: yeni `src/db/models/`, `src/db/migrations/`, `src/generator/` → seed olarak rebranded
**Çıkış kriteri**: 10k uçuş + 500 mürettebat DB'de; multi-user concurrent okuma yapabiliyor.

---

## Faz C — FTL ve Mürettebat Derinliği (8–10 hafta)

**Neden**: Mevcut 600dk tek tavan EASA regülasyonunu **karşılamaz**. Gerçek dispatcher'lar FDP tablosu + cumulative'e göre karar verir.

- **EASA CAT.OP.MPA.210 tam tablo**: FDP ↔ sector count × reporting time × duty start time matrisi
- **WOCL (Window of Circadian Low)** hesabı; night duty reduction
- **Cumulative limits**: 60h/7 gün, 110h/14 gün, 190h/28 gün, 1000h/yıl — CP-SAT'a hard constraint
- **Standby + reserve crew** state machine (airport / home standby)
- **Min rest**: 12h yerel veya 1.5× önceki duty, hangisi uzunsa
- Pilot-in-command (PIC), First Officer (FO), Senior Cabin Crew (SCC) ayrı eşleşmeler
- **Recency tracking**: 90 günde 3 takeoff/landing kuralı
- Pairing/rostering: tek gün yerine **7 günlük rolling roster** solver'ı

**Kritik dosyalar**: `src/optimizer/dt_solver.py` yeniden yazılmalı; yeni `src/optimizer/ftl_rules.py`, `src/optimizer/pairing.py`
**Çıkış kriteri**: Gerçek bir EASA denetçisi tablo bazlı senaryoları doğrulayabilir.

---

## Faz D — Gerçek Operasyonel Veri Entegrasyonu (6–8 hafta)

**Neden**: OpenSky (anonim) + Open-Meteo göstermelik. Operasyon merkezinde **authoritative** veri gerekir.

- **AviationWeather.gov / NOAA METAR+TAF**: XML/JSON parser, IFR/VFR karar eşiği
- **OpenSky OAuth tier** veya **FlightAware Firehose** (ücretli) — 1sn'lik pozisyon feed
- **Sabre / Amadeus GDS**: PNR + schedule, `market_intel.py` demo'yu kaldır
- **Eurocontrol CFMU (B2B web services)**: ATFM slot + regulation feeds
- **IATA SSIM** dosya formatı import/export — havayolları arasında schedule değişimi
- **SITA Type B** veya ACARS bridge (messaging broker üzerinden) — operasyonel mesajlar
- Tüm entegrasyonlar için **circuit breaker** (pybreaker) + **retry with backoff** (tenacity zaten var)

**Kritik dosyalar**: `src/data_connectors/` tamamen genişler — her provider için ayrı modül + adapter pattern
**Çıkış kriteri**: Üretimde 24 saat kesintisiz canlı veri akışı; fallback sadece degradation mode için.

---

## Faz E — Observability ve SLO (3–4 hafta)

**Neden**: Üretim'de "neden 03:00'da crash oldu" sorusu telemetri olmadan cevaplanmaz.

- **OpenTelemetry** (traces + metrics + logs) — şu anki Prometheus'u tamamla
- **Structured logs** zaten var; Loki/Elasticsearch'e ship et
- **Grafana dashboard**: solver latency, cancellation rate, FTL breach warnings, API 5xx
- **Alerting**: PagerDuty/Opsgenie — SLO ihlalinde; burn rate alarmları
- **SLO**: 99.9% availability, p95 solver latency < 30s, p99 < 60s
- **Synthetic probes**: health + sample optimize her dakika dışarıdan koşuluyor
- **Distributed tracing**: solver → DB → external API zinciri uçtan uca görünür

**Çıkış kriteri**: Geceleri çıkan bir sorunda oncall 5 dakikada sebebi bulabiliyor.

---

## Faz F — Ölçek ve Çalışma Kipi (4–6 hafta)

**Neden**: 150 uçuş / 60sn solver, 3000 uçuş / gerçek zamanlı'a ölçeklenmez.

- **Rolling horizon**: 15 dakikada bir 4 saatlik pencereyi yeniden çöz; tam günü cold-solve'a bırakma
- **Solver iş havuzu**: Celery/Dramatiq ile CP-SAT işleri ayrı worker'lara git
- **Incremental solve**: sadece değişen uçuşlar için warm start (constraint programming continuation)
- **Multi-fleet**: Narrow / Wide / Regional ayrı solver instance'ları, final birleştirme
- **Horizontal scale**: API pod'ları stateless; oturum state Redis'te; Kubernetes Deployment + HPA
- **Load test**: Locust ile 100 concurrent dispatcher, 3000 uçuş / gün

**Çıkış kriteri**: gündelik operasyon yükünde p95 solver SLO'su karşılanıyor.

---

## Faz G — Sertifikasyon ve Uyum (sürekli)

**Neden**: Sivil havacılık tedarikçileri bu kutuları işaretlemeden içeri giremez.

- **ISO 27001** (bilgi güvenliği yönetim sistemi) — doküman + denetim
- **SOC 2 Type II** — kontrol + 6 aylık denetim
- **GDPR / KVKK** — kişisel veri envanteri (passenger PNR temasında zorunlu)
- **DO-326A / ED-202A** havacılık siber güvenliği (varsa aviation sertifikalı müşteri için)
- **EASA AMC 20-42** — AI/ML karar sistemleri rehberi; explainability zorunlu (XAI zaten var ✓)
- **Penetration test** yıllık; vulnerability scan CI/CD hattına

**Çıkış kriteri**: RFP'lerde "compliance attestation" isteyen müşteriye cevap verebiliyoruz.

---

## Yol Haritası Özet Tablosu

| Faz | Süre | Bağımlılık | Başarı Metriği |
|---|---|---|---|
| A — Auth & RBAC | 4–6 hf | - | 100% endpoint auth'lı |
| B — Persistance | 6–8 hf | A | Postgres, Redis, migration chain |
| C — FTL derinlik | 8–10 hf | B | EASA denetçi onayı |
| D — Canlı veri | 6–8 hf | A, B | 24h kesintisiz akış |
| E — Observability | 3–4 hf | A | SLO dashboard + alerting |
| F — Ölçek | 4–6 hf | B, E | 3000 uçuş/gün p95 SLO |
| G — Sertifikasyon | sürekli | Hepsi | ISO 27001, SOC 2 |

**Kritik yol**: A → B → C (24–30 hafta). D ve E paralel gidebilir.

---

## Şu an Endüstri Skalasında Nerede Duruyoruz?

| Boyut | Şimdi | Endüstri | Fark |
|---|---|---|---|
| Ölçeklenebilirlik | ~150 uçuş / tek pod | 3000+ / HA cluster | Faz B, F |
| FTL gerçekçiliği | Tek 600dk tavan | Tam EASA tablosu | Faz C |
| Veri | Synthetic + demo API'ler | SITA/GDS/CFMU canlı | Faz D |
| Güvenlik | API key opsiyonel | OAuth/SSO + RBAC + audit | Faz A |
| Gözlemlenebilirlik | Prom counter | OTel + SLO + alerting | Faz E |
| Sertifikasyon | Yok | ISO 27001 + SOC 2 | Faz G |
| Karar açıklanabilirliği | SHAP + decision_reason ✓ | EASA AMC 20-42 uyumlu | Yakın — kanıt yeterli |
| Solver yaklaşımı | CP-SAT + GA recovery ✓ | Aynı sınıf teknoloji | **Paritede** |

**Takma puan**: Yarışma 9/10, endüstri 4/10.
CP-SAT/GA çekirdeği ve XAI zaten doğru yolda; gap **çevresel katmanda** (auth, DB, canlı veri, FTL tam derinlik, observability).

---

## İlk Bir Hafta Ne Yapılmalı?

Gerçek bir endüstri adımı atmak istersen ilk sprintte şunları yaparsın:

1. PostgreSQL + Alembic kurulumu (Faz B'nin ilk adımı)
2. Keycloak local dev + FastAPI JWT middleware PoC (Faz A)
3. `audit_events` tablosu + her decision/export'a 1 satır yazan hook
4. Mevcut synthetic simulator'ı "seed loader"a indirme — DB'ye yaz, oradan oku

Bu dört adım tamamlanınca geri kalan tüm fazlar DB-backed bir temel üzerine oturur.
