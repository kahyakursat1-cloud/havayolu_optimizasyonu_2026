# Dijital İkiz ve Kısıt Programlama Tabanlı Hibrit Bir Havayolu Operasyon Karar Destek Sistemi: EASA Uyumlu, Açıklanabilir Yapay Zeka ile Güçlendirilmiş Bir Uçuş Optimizasyon Platformu

**Yazar**: Kürşat Kahya
**Kurum**: Havacılık Ağ Optimizasyonu ve Karar Destek Sistemleri Araştırma Grubu
**Tarih**: 2026

---

## Özet

Ticari havayolu operasyonları; uçuş gecikmeleri, mürettebat görev sürelerine ilişkin regülasyonlar (EASA FTL), meydan slot kapasiteleri, bakım pencereleri, yolcu bağlantıları ve hava koşulları gibi birbirine sıkıca bağlı çok-kısıtlı bir karar uzayında işlemektedir. Günlük 1.000–3.000 uçuşluk orta ölçekli bir havayolunda bu uzayın hesaplama karmaşıklığı **NP-zor** sınıftadır (Barnhart ve ark., 2003). Bu tez, söz konusu uzayı **dijital ikiz (digital twin)** mimarisinde somutlaştıran, **Google OR-Tools CP-SAT** tabanlı bir tam-sayı programlama çekirdeği ile **kuantum-esinli genetik algoritma (QIGA)** iyileştiricisini birleştiren, **SHAP** tabanlı açıklanabilir yapay zeka (XAI) çıktılarıyla EASA AMC 20-42 yönergesine uyum sağlayan bir **havayolu operasyon karar destek sistemi (A-ODSS)** sunmaktadır.

Geliştirilen sistem; gerçek zamanlı OpenSky Network (ADS-B), Open-Meteo ve NOAA AviationWeather.gov METAR/TAF feed'leri ile beslenir, kısıt ihlalleri (crew duty saturation, gate conflict, slot overflow) tespitinde **karar gerekçesi (decision_reason)** üretir ve bu gerekçeleri FastAPI üzerinden sunulan bir web arayüzünde Three.js + MapLibre 3D/2D görselleriyle uçuş dispeçerine iletir. Deneysel değerlendirmede **150 uçuşluk** sentetik bir senaryoda CP-SAT çekirdeği **60 saniyelik** zaman sınırında optimaliteye %97 yakınsayan çözümler üretmiş; **yerel arama yalnızca** yaklaşıma göre **kâr (profit objective)** açısından **%14** iyileşme sağlamıştır. EASA FTL tavanı (600 dk) ihlal edilen senaryolarda sistem, mürettebat kaynaklı iptalleri `decision_reason="CREW_DUTY_SATURATION"` olarak otomatik etiketlemekte ve dispeçer müdahalesi için arayüzde vurgulamaktadır.

Tezin katkıları: (i) endüstriyel tam-sayı modeller ile heuristik arama algoritmalarının **warm-start** ile entegre edildiği hibrit bir çerçeve; (ii) ADS-B canlı veri akışının sentetik simülatör ile füzyonuna dayalı bir **dijital ikiz güncelleme hattı**; (iii) SHAP değer dağılımlarını hem dispeçer arayüzüne hem de PDF/XLSX karar raporlarına entegre eden bir **XAI katmanı**; (iv) EASA CAT.OP.MPA.210 Flight Time Limitations tavanını kısıt programlamada hard-constraint olarak ifade eden model formülasyonudur.

**Anahtar Kelimeler**: Havayolu Operasyon Yönetimi, Kısıt Programlama, OR-Tools CP-SAT, Dijital İkiz, Açıklanabilir Yapay Zeka, EASA FTL, Kuantum-Esinli Genetik Algoritma, Uçuş Aksaklık Yönetimi (IROPS), SHAP

---

## Abstract

Commercial airline operations involve tightly coupled, multi-constrained decision spaces comprising flight delays, crew flight-time limitations (EASA FTL), airport slot capacities, maintenance windows, passenger connections, and weather. For a mid-size carrier operating 1,000–3,000 flights per day, this space is computationally **NP-hard** (Barnhart et al., 2003). This thesis presents an **Airline Operations Decision Support System (A-ODSS)** that materializes this space within a **digital twin** architecture, couples a **Google OR-Tools CP-SAT** integer programming core with a **Quantum-Inspired Genetic Algorithm (QIGA)** refiner, and achieves compliance with the EASA AMC 20-42 guideline on AI/ML decision systems through **SHAP**-based Explainable AI (XAI) outputs.

The system ingests real-time feeds from OpenSky Network (ADS-B), Open-Meteo, and NOAA AviationWeather.gov METAR/TAF, generates **decision reasons** upon detecting constraint violations (crew duty saturation, gate conflicts, slot overflow), and surfaces these to flight dispatchers through a FastAPI-served web interface featuring Three.js + MapLibre 3D/2D views. In experimental evaluation on a synthetic 150-flight scenario, the CP-SAT core converged to solutions within 97% of optimality under a 60-second time limit; the hybrid QIGA approach yielded a **14% improvement** in the profit objective over local-search-only baselines. Under EASA FTL breach scenarios (600-minute duty ceiling), the system automatically tags crew-driven cancellations as `decision_reason="CREW_DUTY_SATURATION"` and highlights them for dispatcher intervention in the UI.

**Keywords**: Airline Operations Management, Constraint Programming, OR-Tools CP-SAT, Digital Twin, Explainable AI, EASA FTL, Quantum-Inspired Genetic Algorithm, Irregular Operations (IROPS), SHAP

---

## Teşekkür

Bu çalışma, havayolu operasyonel verimliliği ve aksaklık yönetimi üzerine yürütülen bağımsız bir araştırma projesi kapsamında geliştirilmiş ve açık kaynaklı kütüphaneler (Google OR-Tools, FastAPI, PostgreSQL, Three.js, MapLibre, OpenSky Network, Open-Meteo, NOAA) kullanılarak doğrulanmıştır. Araştırma topluluğuna ve havacılık veri sağlayıcılarına teşekkür edilir.

---

## İçindekiler

| Bölüm | Başlık | Sayfa |
|---|---|---|
| 1 | Giriş | 3 |
| 2 | Literatür Taraması ve Problem Tanımı | 12 |
| 3 | Metodoloji | 28 |
| 4 | Sistem Mimarisi | 44 |
| 5 | Matematiksel Model ve Optimizasyon | 62 |
| 6 | Yapay Zeka, ML ve Açıklanabilirlik Katmanı | 80 |
| 7 | Gerçekleme: Yazılım Mühendisliği Detayları | 98 |
| 8 | Deneysel Bulgular ve Değerlendirme | 118 |
| 9 | Tartışma | 140 |
| 10 | Sonuç ve Gelecek Çalışmalar | 154 |
| 11 | Kaynakça | 162 |
| Ek A | Veritabanı Şeması | 174 |
| Ek B | API Referansı | 182 |
| Ek C | Ekran Görüntüleri | 190 |
| Ek D | Deney Verisi Üretim Parametreleri | 200 |

---

## Şekil Listesi (özet)

| No | Başlık | Bölüm |
|---|---|---|
| 4.1 | Katmanlı Sistem Mimarisi | 4.2 |
| 4.2 | Veri Akış Diyagramı | 4.3 |
| 4.3 | Dijital İkiz Döngüsü | 4.4 |
| 5.1 | CP-SAT Değişken İlişki Grafı | 5.3 |
| 5.2 | QIGA Popülasyon Evrim Şeması | 5.5 |
| 6.1 | XAI Katmanı İş Akışı | 6.3 |
| 8.1 | Solver Zaman–Optimal Yakınsama | 8.2 |
| 8.2 | Senaryo Bazlı İptal Oranı Karşılaştırması | 8.4 |
| 8.3 | SHAP Özellik Önemi Dağılımı | 8.6 |
| C.1–C.8 | Web Arayüzü Ekran Görüntüleri | Ek C |

---

## Tablo Listesi (özet)

| No | Başlık | Bölüm |
|---|---|---|
| 2.1 | Akademik Literatürde Havayolu Optimizasyon Yaklaşımları | 2.2 |
| 3.1 | Kullanılan Teknoloji Yığını | 3.1 |
| 5.1 | CP-SAT Karar Değişkenleri | 5.2 |
| 5.2 | Modeldeki Kısıt Kümeleri | 5.3 |
| 6.1 | ML Modellerinin Karşılaştırması | 6.2 |
| 8.1 | Baseline ve Önerilen Yöntem KPI'ları | 8.3 |
| 8.2 | Canlı Veri Entegrasyonu Gecikme Ölçümleri | 8.5 |
