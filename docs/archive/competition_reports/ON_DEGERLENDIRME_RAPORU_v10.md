# 🏅 TEKNOFEST 2026 | Havayolu Operasyonel Dijital İkizi
## ÖN DEĞERLENDİRME RAPORU (v10.0 SCIENTIFIC)

**Proje Başlığı:** Belirsizlik Koşullarında Havayolu Operasyonel Verimliliği için Bulut Tabanlı ve Dayanıklı Karar Destek Sistemi  
**Proje ID:** TF2026-AIR-042  

---

### 1. PROJE ÖZETİ (ABSTRACT)

Yirmibirinci yüzyılın ilk çeyreğinde havacılık sektörü, bir yandan rekor uçuş talepleriyle başa çıkmaya çalışırken diğer yandan katı çevresel düzenlemeler ve karmaşık operasyonel gecikme zincirleriyle mücadele etmektedir. Sunulan bu çalışma, modern havacılık operasyonlarının en büyük sorunu olan plan dışı aksaklıkları ve çevresel etkileri yönetebilmek amacıyla geliştirilmiş, karmaşık tam sayılı doğrusal programlama ve ileri seviye evrimsel algoritmaları birleştiren bütünleşik bir platformdur. Geleneksel modellerden farklı olarak bu sistem, sadece geçmiş verileri kullanmak yerine, anlık değişimlere ve olası gelecek risklerine karşı kendini sürekli güncelleyen bir dijital kopya niteliği taşımaktadır. Çalışma kapsamında geliştirilen yöntemler, operasyonel sürekliliği sağlarken aynı zamanda uçakların atmosferde bıraktığı yoğunlaşma izlerini ve karbon salınımını minimize eden, sürdürülebilir bir gelecek vizyonuna sahip teknolojileri içermektedir.

---

### 2. PROBLEM TANIMI VE MOTİVASYON

#### 2.1. Problemin Mevcut Durumu  
2026 yılı itibarıyla, küresel havacılık ağındaki yoğunluk, tek bir noktada meydana gelen 15 dakikalık bir gecikmenin dahi tüm ağa yayılarak milyonlarca dolarlık kayba ve binlerce yolcunun bağlantılı uçuşunu kaçırmasına yol açmaktadır. Mevcut sistemler bu problemleri genellikle deterministik (sabit) ve statik yöntemlerle çözmeye çalışmakta, bu da gerçek dünyadaki belirsizlikler karşısında planların hızla başarısız olmasına neden olmaktadır.

#### 2.2. Projenin Hedefleri  
- **Dayanıklılık (Resilience):** Operasyonel kriz anlarında gecikmelerin yayılmasını (propagation) engellemek.  
- **Sürdürülebilirlik:** Sürdürülebilir havacılık yakıtı (SAF) ve yoğunlaşma izi (contrail) optimizasyonu ile çevresel etkiyi azaltmak.  
- **Ekonomik Verimlilik:** Makine öğrenmesi tabanlı gelir yönetimi ile kârlılığı maksimize etmek.

---

### 3. ÇÖZÜM YAKLAŞIMI (METHODOLOGY)

Sistem, "Hibrit Çözücü" mimarisi üzerine inşa edilmiştir:
1.  **Tahmin Katmanı:** Yapay zeka tabanlı modeller ile her uçuş için dinamik talep ve gecikme riski öngörür.
2.  **Optimizasyon Katmanı:** Karma Tam Sayılı Doğrusal Programlama (MILP) ile yasal ve teknik kısıtları %100 sağlar; Genetik Algoritma (GA) ile saniyeler içinde esnek çözümler üretir.
3.  **Bulut Veri Boru Hattı:** AWS S3 entegrasyonu ile verileri gerçek zamanlı temizler ve merkezileştirir.

---

### 4. YENİLİKÇİ YÖNLER (NOVELTY)

Bu proje, literatürdeki benzerlerinden şu yönleriyle ayrılmaktadır:
- **Monte Carlo Tabanlı Direnç:** Gecikmeleri sadece "olduktan sonra" değil, "olma olasılığına göre" optimize eden ilk yerli sistemlerden biridir.
- **SI Standartları ve Hassasiyet:** Tüm dahili hesaplamalarda SI (metre, kilogram, saniye) birim sistemini kullanarak hata payını minimize etmektedir.
- **İklim Farkındalığı:** Sadece karbon salınımı değil, bilimsel olarak daha zararlı olabilen yoğunlaşma izlerini (contrails) optimize eden inovatif bir modüle sahiptir.

---

### 5. SONUÇ VE BEKLENEN ETKİ

Projenin hayata geçirilmesiyle, bir havayolu işletmesinin operasyonel geri toplama (recovery) süresinin **%80 oranında kısalması**, yakıt maliyetlerinin ise SAF optimizasyonu sayesinde çevresel uyumla dengelenmesi hedeflenmektedir. Bu sistem, Türkiye'nin 2026 vizyonunda stratejik bir yerli havacılık yazılımı olma adaylığıyla geliştirilmiştir.
