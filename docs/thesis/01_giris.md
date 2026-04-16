# Bölüm 1 — Giriş

## 1.1 Motivasyon ve Problem Tanımı

Küresel ticari havacılık, 2023 yılında Uluslararası Hava Taşımacılığı Birliği (IATA) tarafından raporlandığı üzere yaklaşık **4.5 milyar yolcu** taşımış; **8.8 milyon düzenli uçuş** icra edilmiştir (IATA, 2024). Bu ölçek; uçuş programlaması, uçak-mürettebat atamaları, meydan slot koordinasyonu, bakım pencereleri ve yolcu bağlantıları gibi birbirine kenetlenmiş alt-problemlerin her birinin tek başına kombinatoryal karmaşıklığa sahip olduğu **karar uzayları** doğurmaktadır (Ball ve ark., 2007).

Uçuş iptal ve gecikmelerinin yol açtığı doğrudan maliyet, 2023 yılı itibarıyla ABD piyasasında yıllık **35 milyar ABD Doları**'nın üzerindedir (FAA ACI, 2023). Bu maliyetin yalnızca bir kısmı hava koşulları gibi **dışsal** nedenlerden kaynaklanırken, önemli bir bölümü **operasyonel kararların gecikmesi**, dispeçerin eksik bilgiyle karar vermesi ve **kaynak tahsisindeki sub-optimalite**den doğmaktadır (Barnhart ve Cohn, 2004). Nitekim AhmadBeygi ve ark. (2008) gecikmelerin ağ üzerinde yayılmasında (delay propagation) mürettebat görev zinciri sürekliliğinin kritik rol oynadığını göstermiştir.

Buna ek olarak, Avrupa Havacılık Emniyeti Ajansı (EASA) **CAT.OP.MPA.210** kapsamındaki **Flight Time Limitations (FTL)** çerçevesi; mürettebat azami görev süresi, asgari dinlenme süresi ve kümülatif görev yoğunluğu gibi zorunlu kısıtları tanımlamaktadır (EASA, 2022). Ticari bir dispeçer sisteminin yasal meşruiyet kazanabilmesi için bu kısıtları **hard constraint** olarak kodlaması zorunludur.

Öte yandan, 2023 yılında EASA tarafından yayımlanan **AMC 20-42 Guidance on the development, use, and approval of AI and ML items for aviation** yönergesi, sivil havacılıkta kullanılan karar-destek amaçlı yapay zeka sistemlerinin **açıklanabilirlik (explainability)** ve **izlenebilirlik (traceability)** gereksinimlerini tanımlamıştır (EASA, 2023). Bu, kara-kutu (black-box) derin öğrenme modellerinin üretim ortamında doğrudan kabul görmesini engellemekte; **SHAP** (Lundberg ve Lee, 2017), **LIME** (Ribeiro ve ark., 2016) ve **counterfactual explanations** (Wachter ve ark., 2018) gibi post-hoc açıklanabilirlik yöntemlerini zorunlu kılmaktadır.

### 1.1.1 Tez Sorusu

Bu tez, aşağıdaki temel soruya yanıt aramaktadır:

> **RQ₁**: EASA FTL ve AMC 20-42 kısıtlarını hard-constraint olarak ifade eden, canlı ADS-B ve METAR veri akışlarıyla beslenen ve dispeçere açıklanabilir karar gerekçeleri sunan hibrit bir havayolu operasyon karar destek sistemi, baseline yaklaşımlara kıyasla **optimalite-zaman-açıklanabilirlik üçgeninde** savunulabilir bir Pareto iyileşmesi sağlayabilir mi?

Bu ana sorunun altında üç alt soru tanımlanmıştır:

- **RQ₁.₁**: CP-SAT tabanlı kısıt programlama çekirdeği ile kuantum-esinli genetik algoritma (QIGA) tabanlı yerel arama, **warm-start** protokolü ile birleştirildiğinde kar (profit) hedefinde ne kadar iyileşme sağlar?
- **RQ₁.₂**: Gerçek zamanlı OpenSky Network + Open-Meteo + NOAA METAR füzyonu, sentetik simülatör tabanlı senaryolara göre karar kalitesini ne ölçüde etkiler?
- **RQ₁.₃**: Dispeçer arayüzüne entegre SHAP açıklanabilirlik katmanı, dispeçerin karara güven düzeyini (user trust) ve müdahale doğruluğunu nasıl değiştirir?

## 1.2 Katkılar

Bu tezin özgün katkıları aşağıdaki gibi özetlenebilir:

1. **Hibrit Optimizasyon Çerçevesi**: Google OR-Tools CP-SAT ile QIGA'nın **warm-start continuation** mekanizmasıyla birleştirildiği, infeasibility durumunda otomatik olarak heuristik kurtarmaya geçen bir iki-aşamalı çözücü iskeleti.
2. **EASA-Uyumlu Kısıt Formülasyonu**: CAT.OP.MPA.210 FTL tavanının (ilk seviye model: 600 dk; tez kapsamında genişletilebilir cumulative model) CP-SAT'a doğrudan entegre edilmesi ve `decision_reason` etiketi üretilmesi.
3. **Dijital İkiz Güncelleme Hattı**: OpenSky Network ADS-B feed'inin TTL-cache'li, circuit-breaker korumalı bir bağlantı katmanıyla **AdvancedAirlineSimulator** sentetik verisine füzyonu.
4. **Açıklanabilirlik Katmanı**: SHAP değer dağılımlarının FastAPI backend'inden JSON olarak dispeçer arayüzüne servis edilmesi ve PDF/XLSX karar raporlarına otomatik gömülmesi.
5. **Sivil Havacılık Yazılım Mühendisliği Örneği**: FastAPI + async SQLAlchemy 2.x + PostgreSQL + Alembic + fastapi-users (JWT) + Caddy + Prometheus/Loki/Grafana yığınıyla tamamen açık kaynak, self-hosted, sertifikasyon-hazır bir referans uygulama.

## 1.3 Tezin Yapısı

Tezin geri kalanı şu şekilde düzenlenmiştir:

- **Bölüm 2** literatür taramasını sunar; havayolu optimizasyon probleminin klasik formülasyonlarını (Set Partitioning, Column Generation, MILP), son on yılda önerilen meta-heuristik ve öğrenme-tabanlı yaklaşımları karşılaştırmalı olarak tartışır.
- **Bölüm 3** metodolojik çerçeveyi, teknoloji seçimlerini ve deneysel tasarımı tanımlar.
- **Bölüm 4** sistem mimarisini katman katman inceler; veri akış diyagramlarını ve dijital ikiz döngüsünü sunar.
- **Bölüm 5** matematiksel modeli, karar değişkenlerini, hedef fonksiyonunu ve kısıt kümelerini biçimsel olarak verir.
- **Bölüm 6** yapay zeka, ML ve açıklanabilirlik katmanını; SHAP, XGBoost, Bayesian causal attribution ve trajectory A* modüllerini detaylandırır.
- **Bölüm 7** implementasyon seçimlerini; FastAPI endpoint tasarımı, SQLAlchemy 2.x async session yönetimi, Alembic migration zinciri ve web frontend (Three.js + MapLibre + Chart.js) tasarımını inceler.
- **Bölüm 8** deneysel sonuçları; solver zaman-optimalite yakınsaması, iptal oranı karşılaştırmaları, SHAP özellik önemi dağılımları ve canlı veri gecikme ölçümleri üzerinden sunar.
- **Bölüm 9** bulguları literatür ışığında tartışır; sistemin kısıtlarını ve endüstriyel olgunluk düzeyini değerlendirir.
- **Bölüm 10** sonuçları özetler ve gelecek çalışma yönlerini işaretler.
- **Ekler** veritabanı şeması, API referansı, ekran görüntüleri ve deney parametrelerini içerir.

## 1.4 Kapsam Dışı

Aşağıdaki konular tezin kapsamı dışında tutulmuştur:

- **Uzun dönem filo planlaması** (fleet planning) ve uçak satın alma kararları
- **Fiyatlandırma ve gelir yönetimi** (revenue management) mikro-iktisadi modelleri
- **Bakım MRO** ayrıntılı görev çizelgeleme (system hazır veri modeli sunar; detaylı MRO optimizasyonu bir sonraki faza bırakılmıştır)
- **DO-326A / ED-202A** havacılık siber güvenliği sertifikasyonu (altyapı hazırdır, formal denetim kapsam dışıdır)
- **ISO 27001 / SOC 2 Type II** denetim dokümantasyonu

Bu konular, tezde sunulan mimarinin üzerine inşa edilebilecek doğal uzantılar olup, Bölüm 10 Gelecek Çalışmalar kısmında değinilmiştir.

## 1.6 Şekil 1.1 — Sistem Bağlam Diyagramı

Şekil 1.1, geliştirilen sistemin dış aktörler ve servislerle ilişkisini gösterir: sol tarafta üç kullanıcı rolü (Dispeçer, Yönetici, Sistem Yöneticisi), ortada altı katmanlı platform mimarisi, sağda gerçek zamanlı veri kaynakları (OpenSky ADS-B, Open-Meteo, NOAA METAR) ve izleme katmanı (Prometheus + Grafana).

## 1.5 Terminoloji

| Terim | Tanım |
|---|---|
| **A-ODSS** | Airline Operations Decision Support System — Havayolu Operasyon Karar Destek Sistemi |
| **ADS-B** | Automatic Dependent Surveillance–Broadcast — Uçakların kendi GPS konumunu yayınladığı protokol |
| **CP-SAT** | Constraint Programming — Satisfiability solver (Google OR-Tools içindeki tam-sayı programlama motoru) |
| **EASA FTL** | European Union Aviation Safety Agency Flight Time Limitations — Mürettebat görev süresi sınırlamaları |
| **IROPS** | Irregular Operations — Aksaklık yönetimi (gecikme, iptal, yön değiştirme) |
| **METAR** | Meteorological Aerodrome Report — Meydan hava raporu |
| **MCT** | Minimum Connection Time — Yolcu bağlantılarında zorunlu asgari aktarma süresi |
| **QIGA** | Quantum-Inspired Genetic Algorithm — Kuantum-esinli genetik algoritma |
| **SHAP** | SHapley Additive exPlanations — Model çıktılarını özellik bazında açıklayan post-hoc yöntem |
| **TAF** | Terminal Aerodrome Forecast — Meydan tahmin raporu |
| **WOCL** | Window of Circadian Low — Sirkadiyen ritmin düşük olduğu saat aralığı (genellikle 02:00–06:00 lokal) |

Bölüm 2, problemin akademik literatürde nasıl ele alındığını ve önerilen yöntemin bu literatürdeki yerini tanımlar.
