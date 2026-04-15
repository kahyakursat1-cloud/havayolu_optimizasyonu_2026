# TEKNOFEST 2026 Proje Durumu

## Mevcut Ürün Durumu
Proje artık konsept seviyesinden çıkıp çalışan bir ürün prototipine dönüştürülmüştür.

- Aktif arayüz hattı: FastAPI + statik web frontend
- Aktif karar motoru: CP-SAT tabanlı optimize edici
- Aktif analitik yüzeyler: KPI, forecast, foresight, stress test, explanation API
- Aktif UX özellikleri: 2D/3D görünüm, karar filtreleri, uçuş bazlı açıklama paneli, otomatik harita odaklama

## Tamamlanan Temel Adımlar
- Eski Streamlit/dashboard yapısı sistemden kaldırıldı.
- Kullanılmayan benchmark ve verify scriptleri temizlendi.
- Solver gerçekçiliği kapasite baskısı ve gate çakışmaları ile artırıldı.
- Karar açıklanabilirliği backend ve frontend katmanına işlendi.
- Test yüzeyi çekirdek, solver ve entegrasyon kapsamında yeşil hale getirildi.

## Tamamlanan İleri Adımlar (v28)
- OpenSky + Open-Meteo canlı entegrasyonu (TTL cache, offline fallback; LIVE_SYNC_ENABLED bayrağı)
- Solver'da EASA FTL uyumlu crew duty tavanı (600dk) + duty kaynaklı iptal decision_reason'ı
- Docker compose'a LIVE_SYNC_ENABLED env değişkeni; .env.example güncellendi
- PDF ve XLSX karar raporu export endpoint'leri (/api/export/decision-report.{pdf,xlsx}) + UI butonları

## Kalan Yüksek Öncelikli İşler
- Gerçek GDS/IATA entegrasyonu (market_intel hâlâ demo katmanda)
- Slot modelinin tactical coordination feed'ine bağlanması
- Prod observability (trace/metrics pipeline dışsallaştırma)

## Teknik Yığın
- Backend: FastAPI, SQLAlchemy, SQLite
- Optimization: OR-Tools CP-SAT
- ML/Analytics: SHAP, XGBoost, RL yardımcı modülleri
- Frontend: Three.js, MapLibre, Chart.js

## Başarı Ölçütü
Bugünkü hedef “çalışan, savunulabilir ve gösterilebilir karar destek ürünü”dür. Bundan sonraki faz “gerçek veri ile ürünleştirme” olacaktır.
