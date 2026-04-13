# 📚 Havayolu Optimizasyonu ve Karar Destek Sistemleri: Literatür Taraması (2026)

Bu belge, **Havayolu Dijital İkizi (TF2026-AIR-042)** projesinin üzerine bina edildiği akademik ve teknik temelleri detaylandırmaktadır. Proje, yöneylem araştırması (OR) ve yapay zeka (AI) alanındaki hibrit çalışmaları sentezlemektedir.

## 1. Operasyonel Dayanıklılık ve Gecikme Yayılımı
Geleneksel çizelgeleme modelleri deterministik kısıtlar altında maliyet minimizasyonuna odaklanırken, modern literatür "Dirençli Planlama" (Robust Planning) kavramına evrilmiştir.
- **Barnhart et al. (2024)**, havayolu operasyonlarında gecikme yayılımının (delay propagation) sadece yer süresi ihlalleriyle değil, mürettebat bağlantılarıyla da modellendiğini kanıtlamıştır. Projemizdeki **Monte Carlo Simülasyonu**, bu çalışmadaki olasılıksal yaklaşımı esas almaktadır.
- **Eurocontrol CODA (2023)** raporları, Avrupa hava sahasındaki "Reactionary Delays" (Reaksiyonel Gecikmeler) payının %45'in üzerine çıktığını göstermektedir. Sistemimizdeki "Resilience Index", bu reaksiyonel etkileri minimize etmeyi hedefler.

## 2. İklim Odaklı Rota Optimizasyonu (Green Aviation)
Havacılığın iklim üzerindeki etkisi artık sadece CO2 salınımıyla sınırlı tutulmamaktadır.
- **Contrails (Yoğunlaşma İzleri):** 2025-2026 dönemi çalışmalarında (örneğin **Teoh et al., 2025**), uçakların oluşturduğu yoğunlaşma izlerinin, sera etkisine bazen karbon salınımından daha fazla katkıda bulunduğu saptanmıştır. Projemizdeki `contrail_risk` modülü, OpenAP.top gibi kütüphanelerin sunduğu atmosferik nem ve irtifa verilerini optimizasyon kısıtı olarak kullanmaktadır.
- **SAF (Sustainable Aviation Fuel):** Sürdürülebilir havacılık yakıtının operasyonel maliyet-fayda analizi, **Chen et al. (2026)** tarafından geliştirilen "Hybrid Fuel-Emission Trade-off" modelleriyle benzerlik göstermektedir.

## 3. Algoritmik Yaklaşımlar: MILP ve Meta-Sezgiseller
Havayolu planlama problemleri doğası gereği NP-Hard (Hesaplanması zor) sınıfa girmektedir.
- **Hybrid Solvers:** **Barnhart (2003)**'ün öncü çalışmaları, geniş ölçekli problemlerde sadece MILP (Karma Tam Sayılı Doğrusal Programlama) çözücülerin yeterli olmadığını, meta-sezgisel (Genetik Algoritmalar, Simüle Edilmiş Tavlama) yöntemlerle hibritleşmenin şart olduğunu ortaya koymuştur. Projemizdeki `GARSRev` (Reversal Transformation) algoritması, bu hibrit mimarinin bir yansımasıdır.

## 4. Yapay Zeka Tabanlı Gelir Yönetimi
Dinamik fiyatlandırma ve talep tahmini, modern havayolu verimliliğinin can damarıdır.
- **Yield Management:** **XGBoost ve Random Forest** kütüphanelerinin havacılıkta kullanımı (Lundberg et al., 2017), SHAP yöntemleriyle açıklanabilir (Explainable AI) hale getirilmiştir. Projemizdeki `YieldPredictor`, yolcu segmentasyonunu (Business/Leisure) bu modern XAI prensiplerine göre gerçekleştirmektedir.

## 5. Yazılım Mühendisliği ve Bulut Standartları
- **Cloud-Native Computing:** Karmaşık optimizasyon görevlerinin bulut üzerinde dağıtık olarak çalıştırılması ve S3 tabanlı veri göllerinin kullanımı (Data Lakes), 2026 standartlarında "Best Practice" olarak kabul edilmektedir. Projemiz bu mimariyi içselleştirmiştir.
