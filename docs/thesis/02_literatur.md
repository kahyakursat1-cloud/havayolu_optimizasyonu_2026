# Bölüm 2 — Literatür Taraması ve Problem Tanımı

## 2.1 Havayolu Operasyon Planlaması: Bir Hiyerarşi

Havayolu planlama problemleri literatürde genellikle aşağıdaki dört aşamalı bir hiyerarşide ele alınır (Barnhart ve ark., 2003; Ball ve ark., 2007):

1. **Schedule Design** (Uçuş Programı Tasarımı) — Hangi rotalar, hangi saatlerde, hangi frekansla?
2. **Fleet Assignment** (Filo Ataması) — Her uçuşa hangi uçak tipi atanacak?
3. **Aircraft Routing** (Uçak Rotalama) — Her kuyruk numarasının günlük turu nasıl olacak, bakım pencereleri nerede?
4. **Crew Scheduling** (Mürettebat Çizelgelemesi) — Crew pairing (görev çifti oluşturma) ve crew rostering (aylık nöbet atama)

Bu tez, yukarıdaki aşamalardan özellikle **ikinci-dördüncü** basamakların **operasyonel günde** yeniden-optimizasyonuna (recovery/re-optimization) odaklanır. Klasik literatürde ayrık biçimde modellenen bu alt-problemler, operasyonel günde bozulmalara (disruption) tepki verebilmek için **bütünsel** olarak yeniden çözülmek durumundadır (Kohl ve ark., 2007).

## 2.2 Klasik Matematiksel Programlama Yaklaşımları

### 2.2.1 Set Partitioning ve Column Generation

Crew pairing probleminin klasik formülasyonu bir **Set Partitioning Problem (SPP)**'dir (Desrosiers ve Lübbecke, 2005). Her sütun bir mürettebat görev çiftidir (pairing); amaç, tüm uçuşları en az maliyetle kaplayacak pairing kombinasyonunu seçmektir. Pairing sayısı üstel olduğundan **column generation** (sütun üretimi) standart çözüm yöntemidir (Barnhart ve ark., 1998).

**Avantajları:** Doğrusal gevşetmede (LP relaxation) güçlü alt sınırlar; matematiksel olarak optimalite garantisi.
**Dezavantajları:** Büyük ölçekte (3000+ uçuş) saatler mertebesinde çözüm süreleri; canlı operasyonda kullanılamaz.

### 2.2.2 Mixed Integer Linear Programming (MILP)

Fleet assignment problemi tipik olarak MILP olarak modellenir (Hane ve ark., 1995; Abara, 1989). CPLEX ve Gurobi gibi ticari çözücüler ile saatler–günler mertebesinde optimal çözümler elde edilebilir. Rexing ve ark. (2000) zaman pencereli fleet assignment formülasyonuyla ATL-DFW network'ünde %1.4'lük kar artışı raporlamıştır.

### 2.2.3 Stochastic Programming

Havayolu kararlarında belirsizlik (hava, talep, teknik arıza) Yen ve Birge (2006) tarafından iki-aşamalı stokastik programlama çerçevesinde modellenmiştir. Ancak senaryo sayısının artmasıyla hesaplama maliyeti patlamaktadır.

## 2.3 Kısıt Programlama (CP) Yaklaşımları

Kısıt programlama, özellikle çok-kısıtlı çizelgeleme problemlerinde MILP'ye göre daha doğal bir modelleme sağlar (Rossi ve ark., 2006). Google OR-Tools içindeki **CP-SAT** solveri; **lazy clause generation**, **conflict-driven clause learning** ve **portföy arama** tekniklerini birleştirerek, 2020 MiniZinc Challenge dahil birçok kıyaslama testinde birinci olmuştur (Perron ve Furnon, 2023).

Laborie ve ark. (2018) CP Optimizer'ın `interval variable` ve `cumulative function` soyutlamalarının havacılık çizelgelemesinde MILP'ye göre daha kompakt modellemeye olanak tanıdığını göstermiştir. Bu tezde kullanılan CP-SAT model de benzer yaklaşımı benimser (Bölüm 5).

## 2.4 Meta-Heuristik ve Evrimsel Yöntemler

### 2.4.1 Genetik Algoritmalar

Crew pairing için genetik algoritma uygulamaları Levine (1996) ile başlamış; Ozdemir ve Mohan (2001) paralel evrim şemalarıyla bunu genişletmiştir. Genetik algoritmalar optimalite garantisi sağlamaz ancak **zaman sınırlı** operasyonel kararlarda yüksek kaliteli **iyi çözümler** üretebilir.

### 2.4.2 Kuantum-Esinli Evrimsel Algoritmalar (QIEA)

Han ve Kim (2002) tarafından önerilen **Quantum-Inspired Evolutionary Algorithm (QIEA)**, kromozomları kuantum-bit (Q-bit) olarak temsil eder; popülasyon çeşitliliği klasik GA'ya göre daha uzun korunur. Zhang (2011) QIEA'nın büyük kombinatoryal problemlerde **% 15–30** daha hızlı yakınsama sağladığını raporlamıştır. Bu tezde önerilen QIGA, bu çerçeveyi havayolu disruption recovery problemine uyarlar (Bölüm 5.5).

### 2.4.3 Tabu Search, Simulated Annealing

Stojković ve ark. (2002) disruption recovery için **Large Neighborhood Search (LNS)**, Yu ve Qi (2004) simulated annealing uygulamıştır. Bu yöntemler, CP-SAT çekirdeğinin infeasible döndüğü durumlarda hibrit çözücüde tamamlayıcı rol oynar.

## 2.5 Öğrenme Tabanlı Yaklaşımlar

### 2.5.1 Reinforcement Learning (RL)

Reyhani ve ark. (2023) gecikme propagasyonu kontrolünde **Deep Q-Network (DQN)** kullanmıştır. Bu tez, RL'yi optimizasyonun yerine değil, **yardımcı** bir karar önerme modülü olarak konumlandırır; CP-SAT çekirdeği kararı kesinleştirir.

### 2.5.2 Gradient Boosting Trees (XGBoost)

Chen ve Guestrin (2016)'nın XGBoost'u, havacılıkta yolcu no-show tahmini ve gecikme tahmininde yaygın kullanılır (Belcastro ve ark., 2016). Bu tezde forecasting alt sisteminde (Bölüm 6.2) baseline olarak kullanılmıştır.

### 2.5.3 Transformer Tabanlı Seri Tahmini

Li ve ark. (2021) **Informer** mimarisiyle uzun horizonlu uçuş gecikme tahminlerinde LSTM'lere göre %20 RMSE iyileşmesi raporlamıştır. Bu tezde transformer bir gelecek çalışma olarak işaretlenmiştir.

## 2.6 Açıklanabilir Yapay Zeka (XAI)

### 2.6.1 SHAP

Lundberg ve Lee (2017) **SHAP (SHapley Additive exPlanations)** ile oyun teorisi tabanlı Shapley değerlerini ML model açıklamalarına uyarlamıştır. **TreeSHAP** algoritması polinomial zamanda XGBoost açıklamaları üretir (Lundberg ve ark., 2020).

### 2.6.2 LIME ve Counterfactuals

Ribeiro ve ark. (2016) **LIME**, yerel vekil (surrogate) model ile açıklama üretir. Wachter ve ark. (2018) **counterfactual explanation** — "Eğer X yerine Y olsaydı karar değişirdi" — yaklaşımını önermiştir.

### 2.6.3 EASA AMC 20-42 Gereksinimleri

EASA (2023) AMC 20-42, AI/ML tabanlı karar sistemleri için şu başlıkları zorunlu kılar:
- **Explainability**: Kararın özellik bazında açıklanması
- **Traceability**: Girdi–model–çıktı zincirinin izlenebilirliği
- **Robustness**: Adversarial örneklere karşı dayanıklılık
- **Operational boundary**: Modelin geçerli olduğu girdi uzayının açıkça tanımlanması

Bu tezde SHAP + `decision_reason` + audit log kombinasyonu yukarıdaki gereksinimlerin ilk üçünü karşılar.

## 2.7 Dijital İkiz Kavramı

Grieves (2014) tarafından formalize edilen **dijital ikiz (digital twin)** kavramı; fiziksel bir sistemin (uçak, meydan, filo) bilgi-uzayındaki gerçek-zamanlı bir yansımasını ifade eder. Tao ve ark. (2018) havacılıkta dijital ikiz uygulamalarını beş seviyede sınıflandırmıştır:

| Seviye | Açıklama | Örnek |
|---|---|---|
| L1 | Tek bileşen ikizi | Motor sağlığı |
| L2 | Uçak ikizi | Boeing 787 virtual aircraft |
| L3 | Filo ikizi | Airline operations center |
| L4 | Hava sahası ikizi | ATC operations |
| L5 | Küresel hava ağı | IATA-wide simulation |

Bu tez **L3 — Filo ikizi** seviyesinde çalışan bir A-ODSS sunar.

## 2.8 Tablo 2.1 — Akademik Literatürde Havayolu Optimizasyon Yaklaşımları

| Yaklaşım | Kaynak | Problem | Ölçek | Zaman | Optimalite | XAI |
|---|---|---|---|---|---|---|
| Column Generation | Barnhart ve ark. (1998) | Crew pairing | ≤5000 uçuş | Saatler | Global optimal | — |
| MILP (Gurobi) | Rexing ve ark. (2000) | Fleet assignment | ≤2000 uçuş | Dakikalar | Global optimal | — |
| CP + CBLS | Laborie ve ark. (2018) | Scheduling | Orta ölçek | Dakikalar | Near-optimal | — |
| GA | Levine (1996) | Crew pairing | Orta ölçek | Saniyeler | Heuristic | — |
| QIEA | Han ve Kim (2002) | Genel kombinatoryal | Değişken | Saniyeler | Heuristic | — |
| LNS | Stojković ve ark. (2002) | Disruption recovery | ≤1000 uçuş | Saniyeler | Heuristic | — |
| DQN | Reyhani ve ark. (2023) | Delay propagation | Network | Online | Policy | Kısmen |
| **Bu tez** | — | **IROPS + scheduling** | **≤3000 uçuş** | **≤60s** | **CP-optimal + heuristic warm** | **✓ (SHAP + reason)** |

## 2.9 Literatür Boşluğu ve Tezin Pozisyonu

Yukarıdaki incelemeden çıkan **boşluklar** şunlardır:

1. **Optimalite + Zaman + XAI** üçgeninde dengeli bir çözüm eksikliği. Klasik MILP yaklaşımları optimaliteyi garanti eder ama açıklanabilirlik sunmaz; derin öğrenme yaklaşımları hızlıdır ama optimalite ve sertifikasyon uyumunu sağlayamaz.
2. **EASA FTL**'nin CP modeline doğrudan entegrasyonuna ilişkin açık kaynak referans uygulaması bulunmamaktadır.
3. **Canlı ADS-B + METAR + sentetik simülatör füzyonu** ile dijital ikiz güncelleme hattı, akademik literatürde kapalı-kaynak endüstri projelerinin dışında kamuya açık örneği sınırlıdır.

Bu tez yukarıdaki üç boşluğu doldurmayı hedefler. Bölüm 3'te metodolojik çerçeve sunulur.

## 2.11 Şekil 2.1 — Yaklaşım Karşılaştırması (Radar Analizi)

Şekil 2.1, bu tezin önerdiği hibrit M yöntemini (CP-SAT + QIGA + XAI) Klasik MILP ve Deep RL referanslarıyla yedi boyutta karşılaştırır: Optimalite, Hız, Açıklanabilirlik, Canlı Veri, EASA Uyum, Ölçek. M yöntemi Açıklanabilirlik ve EASA Uyum boyutlarında belirgin üstünlük göstermektedir.

## 2.10 Problem Tanımı — Biçimsel

Operasyonel günde çözülen yeniden-çizelgeleme problemi şu şekilde tanımlanır:

**Girdi**:
- Uçuş kümesi $F = \{f_1, f_2, \ldots, f_n\}$
- Uçak havuzu $K = \{k_1, \ldots, k_m\}$ (her biri tip, kapasite, bakım durumu ile)
- Mürettebat havuzu $C = \{c_1, \ldots, c_p\}$ (her biri sertifika ve FTL durumuyla)
- Havalimanı kümesi $A = \{a_1, \ldots, a_q\}$ (gate kapasitesi, saat başı slot kapasitesi)
- Bozulma vektörü $D$: hava gecikmeleri, teknik arızalar, slot regülasyonları

**Karar Değişkenleri**:
- $x_{f,k} \in \{0,1\}$: Uçuş $f$ uçak $k$'ya atandı mı?
- $y_{f,c} \in \{0,1\}$: Uçuş $f$ mürettebat $c$'ye atandı mı?
- $z_f \in \{0,1\}$: Uçuş $f$ iptal edildi mi?
- $d_f \in \mathbb{Z}_{\geq 0}$: Uçuş $f$'in gecikme süresi (dakika)

**Hedef**:
$$\min \sum_{f \in F} \left( \alpha \cdot z_f \cdot \text{revenue}_f + \beta \cdot d_f \cdot \text{delayCost}_f + \gamma \cdot \text{fuel}_{f,k} \cdot x_{f,k} \right)$$

**Kısıtlar**: Aircraft continuity, crew continuity, EASA FTL, gate capacity, slot capacity, MCT. Detaylar Bölüm 5'te.

Bölüm 3, bu problemin çözümü için seçilen metodolojiyi tanımlar.
