# Yapay Zeka Destekli Havayolu Dijital İkizi

## Ürün Özeti
Bu proje, havayolu operasyonları için çalışan bir karar destek sistemi prototipidir. Uçuş senaryosu üretir, optimize eder, sonucu API üzerinden servis eder ve 2D/3D dijital ikiz arayüzünde görünür hale getirir.

## Bugün Sağlanan Yetenekler
- Sentetik operasyon senaryosu üretimi
- CP-SAT tabanlı taktik optimizasyon
- Karar açıklaması üretimi (`decision_reason`)
- Forecast ve foresight yüzeyleri
- Stress test ve live-sync benzeri demo operasyonları
- Üst seviye karar kartları ile filtrelenebilir ürün arayüzü

## Ürünün Ayrıştırıcı Noktaları
- Kararın sadece sonucu değil, nedeni de gösteriliyor
- Aynı veri hem API hem 2D/3D arayüzde kullanılıyor
- Slot baskısı ve ağ kararlılığı odaklı taktik görünürlük sunuluyor

## Sonraki Faz
- Gerçek ADS-B / weather / market data entegrasyonu
- Deployment, kullanıcı yönetimi ve rapor export
- Solver kısıtlarının daha derin operasyon modeline genişletilmesi
