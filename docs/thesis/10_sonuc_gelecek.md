# Bölüm 10 — Sonuç ve Gelecek Çalışmalar

## 10.1 Tezin Özeti

Bu tez; havayolu operasyonlarında aksaklık yönetimi (IROPS) problemine, **kısıt programlama tabanlı bir çekirdek + kuantum-esinli genetik algoritma iyileştirici + açıklanabilir yapay zeka katmanı** üçlüsünden oluşan hibrit bir karar destek sistemi önermiştir. Sistem:

1. **Matematiksel rigor**: EASA CAT.OP.MPA.210 FTL tavanı hard-constraint olarak CP-SAT modeline gömülmüş; sertifikasyon kritik yasal sınırlar ihlal edilememiştir.
2. **Pratik performans**: 150 uçuşluk bir senaryoda 60 saniye içinde %2.1 optimality gap'le sonuç üretmiş; hibrit yaklaşım tek başına CP-SAT'a göre %5 objective, %20 iptal azalması sağlamıştır.
3. **Açıklanabilirlik**: SHAP + Bayesian causal attribution + `decision_reason` etiketleri ile her karar dispeçere gerekçelendirilmiş olarak sunulmuştur. Mini kullanıcı testinde Likert 4.2–4.5 güven skoru elde edilmiştir.
4. **Canlı veri füzyonu**: OpenSky, Open-Meteo, NOAA feed'leri TTL cache + circuit breaker ile entegre edilmiş; fallback oranı %2 altında tutulmuştur.
5. **Açık kaynak mühendislik**: Tüm teknoloji yığını ücretsiz ve self-hosted; tez kapsamında üretilen kod, konfigürasyon ve dokümantasyon kamuya açık depolarda bulunmaktadır.

## 10.2 Katkıların Yeniden İfade Edilmesi

1. **Hibrit CP-SAT + QIGA warm-start çerçevesi**: Tek yöntemlerin güçlü yönlerini sentez eden, infeasibility durumunda otomatik kurtarmaya geçen bir iki-aşamalı çözücü.
2. **EASA-uyumlu kısıt formülasyonu**: FTL tavanının doğrudan CP-SAT'ta ifade edilmesi ve iptal sebebinin otomatik etiketlenmesi.
3. **Dijital ikiz güncelleme hattı**: ADS-B + METAR + sentetik füzyonu üzerine inşa edilmiş TTL-cache'li, fault-tolerant veri katmanı.
4. **XAI + export entegrasyonu**: SHAP değerlerinin UI + PDF + XLSX çıktılarında birleşik sunumu.
5. **Referans uygulama**: Sivil havacılık için tamamen açık kaynaklı, sertifikasyon-hazır (ama henüz sertifikalı değil) bir ürün iskeleti.

## 10.3 RQ Cevaplarının Konsolidasyonu

| RQ | Cevap |
|---|---|
| RQ₁.₁ (Hibrit kâr) | **Evet**, M, B₂'ye göre %5 objective iyileşmesi (p=0.007). |
| RQ₁.₂ (Canlı veri etkisi) | **Mevcut feed'lerle** sentetik kadar iyi. GDS entegrasyonu sonrası tekrar ölçülmeli. |
| RQ₁.₃ (XAI güven etkisi) | **Evet**, Likert 4.2–4.5. Büyük örneklemle doğrulanmalı. |
| RQ₁ (Genel) | **Evet**, tez optimalite–zaman–açıklanabilirlik Pareto iyileşmesini kanıtlar. |

## 10.4 Gelecek Çalışmalar

### 10.4.1 Kısa Vadeli (3–6 ay)

- **FTL Tam Tablosu (Faz C)**: `src/optimizer/ftl_rules.py` modülü; FDP × sektör × reporting × WOCL matrisi. 60h/7d cumulative limit.
- **Gerçek GDS Bağlantısı (Faz D)**: Sabre/Amadeus PNR + schedule import. Legal/ticari sözleşme gerekli.
- **Drift Monitoring**: XGBoost forecaster için population stability index (PSI); Grafana alert.
- **Refresh Token**: JWT rotation + revocation list.
- **Keycloak**: fastapi-users yerine enterprise-grade OIDC provider.

### 10.4.2 Orta Vadeli (6–18 ay)

- **Rolling Horizon Solver (Faz F)**: 15 dakikalık pencerelerde incremental re-solve; Celery worker pool.
- **Multi-Fleet Partition**: Narrow/Wide/Regional ayrı solver instance + global coordinator.
- **CFMU Slot Feed (Faz D)**: Eurocontrol B2B web services; tactical ATFM slots.
- **Crew Pairing vs Rostering Decoupling**: 7 günlük rolling roster solver'ı.
- **Transformer-based Delay Prediction**: Informer / Autoformer (Zhou ve ark., 2021) ile uzun horizon tahminleri.

### 10.4.3 Uzun Vadeli (18+ ay)

- **DO-326A / ED-202A Sertifikasyonu**: Havacılık siber güvenliği formal audit; penetration testing.
- **ISO 27001 + SOC 2 Type II**: Enterprise compliance için 6 aylık denetim döngüsü.
- **Federated Learning**: Çoklu havayolu arası model paylaşımı (data sovereignty korunarak).
- **Quantum Hardware**: QIGA'nın gerçek kuantum donanımında (IBM Q, Rigetti) prototiplemesi.
- **V2X / NTN Entegrasyonu**: Uçak–altyapı iletişim protokolleri (5G NTN) ile gerçek-zamanlı airspace tel koordinasyonu.

### 10.4.4 Akademik Uzantılar

- **Multi-objective Optimization (Pareto Frontier)**: Kâr, CO₂, mürettebat yorgunluğu ve yolcu memnuniyeti arasında Pareto-optimal küme.
- **Bayesian Optimization of Solver Hyperparameters**: CP-SAT arama stratejisi için AutoML.
- **Counterfactual Explanations via Integer Programming**: MILP formülü ile "what-if" türetme.
- **Robust Optimization**: Belirsizlik kümesi tanımlama; Bertsimas ve ark. (2004)'un Γ-robust yaklaşımı.
- **Game-Theoretic Multi-Airline Coordination**: Havayolları arası slot pazarlığında mekanizma tasarımı.

## 10.5 Tezin Pratik Etkisi

Bu tezde geliştirilen sistem:

- **TEKNOFEST 2026** Havayolu Optimizasyonu yarışmasının değerlendirilmesinde kullanılacak
- Açık kaynak olarak yayımlanarak diğer araştırmacıların yararına sunulacak
- Türkiye'de sivil havacılık AI/XAI sertifikasyonu çalışmalarına somut bir referans olacak
- Endüstri tarafından "yol haritası" (PRODUCT_ROADMAP.md + INDUSTRY_ROADMAP.md) ile izlenebilir bir ürünleştirme şablonu sağlayacak

## 10.6 Kapanış

Ticari havacılık, bu tezin yazıldığı dönemde önemli bir **dönüşüm eşiğindedir**: AI/ML regülasyonları yeni olgunlaşmakta (EASA AMC 20-42, 2023), sürdürülebilirlik baskısı artmakta (CORSIA, CO₂ hedefleri), ve operasyonel karmaşıklık düşmemektedir. Bu tezin savunduğu temel tez: **açıklanabilir, kısıt-matematiksel, heuristik ile desteklenen hibrit karar sistemleri, sertifikasyon uyumunu pragmatik ölçeklenebilirlikle birleştirebilir**.

Bir sonraki adım, endüstriyle olan köprüdür: GDS/CFMU/SITA erişimi sözleşmelerle açılan, gerçek operasyonel veriyle beslenen bir pilot deployment. Bu tez, o pilota hazır bir teknik temel bırakır.

---

*Bölüm 11, bu tezde atıfta bulunulan çalışmaların tam kaynakçasını sunar.*
