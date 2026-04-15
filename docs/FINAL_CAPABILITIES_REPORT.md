# Final Capabilities Report

## Ürünleşmiş Çekirdek Yetenekler
- Sentetik uçuş senaryosu üretimi
- CP-SAT tabanlı uçuş atama ve taktik re-optimizasyon
- Kapasite, bakım, crew uygunluğu ve slot-pressure farkındalığı
- CP-SAT başarısız pencerelerde hibrit GA + local-search recovery
- Forecast, foresight heatmap, stress test ve trust/federated yardımcı modülleri
- Web arayüzünde 2D/3D karar görünümü
- 3 modelli benchmark yüzeyi: Logistic Regression, XGBoost, LSTM

## Açıklanabilirlik Katmanı
Sistem yalnızca karar üretmez; her uçuş için karar gerekçesi de üretir.

- `decision_reason`: uçuş bazında neden gecikme/iptal/koruma kararı verildiğini açıklar
- `slot_pressure_flag`: slot baskısı altında kalan uçuşları işaretler
- `decision_summary`: optimize çağrısından sonra iptal, gecikme, swap ve baskın karar nedenlerini özetler
- `/api/optimizer/explanations`: arayüz ve dış istemciler için açıklama yüzeyi sağlar

## Ürün Arayüzü Yetenekleri
- Karar kartlarına tıklanabilir filtreler
- Filtreye göre 3D görünümde otomatik harita odaklama
- Uçuş detay panelinde karar açıklaması
- Boş durum ve filtre temizleme akışları
- Websocket üzerinden senaryo yenileme

## Operasyonel API Yüzeyi
- `/api/scenario`
- `/api/optimize`
- `/api/ai/optimize`
- `/api/optimizer/explanations`
- `/api/export/scenario.csv`
- `/api/reports/decision-summary`
- `/api/analytics/kpi`
- `/api/analytics/forecast`
- `/api/analytics/model-benchmark`
- `/api/analytics/foresight-heatmap`
- `/api/stress-test`
- `/api/sync/live-traffic`
- `/health`
- `/metrics`

## Kalite Durumu
- Eski Streamlit ve kullanılmayan benchmark/verify dosyaları kaldırıldı.
- Çekirdek test seti aktif tutuldu.
- Docker, compose ve `.env` standardizasyonu yapıldı.
- Doğrulama sonucu: `49 passed`

## Sonraki Ürün Fazı
- Gerçek operasyon verisi entegrasyonu
- Benchmark sonuçlarının kalıcı rapor/artifact olarak saklanması
- Kullanıcı rol/kimlik doğrulama akışlarının genişletilmesi
- Gerçek veri ile model kalibrasyonu
