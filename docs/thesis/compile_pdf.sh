#!/usr/bin/env bash
# ============================================================
# Tez PDF + DOCX Derleyici
# Kullanım: bash docs/thesis/compile_pdf.sh
# Çıktı:    docs/thesis/teknofest2026_tez.pdf
#           docs/thesis/teknofest2026_tez.docx
# Gereksinim: pandoc + xelatex (TeX Live)
# ============================================================
set -euo pipefail

THESIS_DIR="$(cd "$(dirname "$0")" && pwd)"
IMG_DIR="$THESIS_DIR/gorseller"
OUT_PDF="$THESIS_DIR/teknofest2026_tez.pdf"
OUT_DOCX="$THESIS_DIR/teknofest2026_tez.docx"
WORK_DIR="$(mktemp -d)"

echo "==> Tez dizini: $THESIS_DIR"
echo "==> Geçici dizin: $WORK_DIR"

# ---------- Görselleri üret ----------
echo "==> Görseller üretiliyor..."
python3 "$IMG_DIR/gen_figures.py"

# ---------- Bölüm dosyaları ----------
CHAPTERS=(
    "$THESIS_DIR/00_kapak_ozet.md"
    "$THESIS_DIR/01_giris.md"
    "$THESIS_DIR/02_literatur.md"
    "$THESIS_DIR/03_metodoloji.md"
    "$THESIS_DIR/04_sistem_mimarisi.md"
    "$THESIS_DIR/05_matematiksel_model.md"
    "$THESIS_DIR/06_ai_ml_xai.md"
    "$THESIS_DIR/07_implementasyon.md"
    "$THESIS_DIR/08_bulgular.md"
    "$THESIS_DIR/09_tartisma.md"
    "$THESIS_DIR/10_sonuc_gelecek.md"
    "$THESIS_DIR/11_kaynakca.md"
    "$THESIS_DIR/ekler/ek_a_veritabani_semasi.md"
    "$THESIS_DIR/ekler/ek_b_api_referansi.md"
    "$THESIS_DIR/ekler/ek_c_ekran_goruntuleri.md"
    "$THESIS_DIR/ekler/ek_d_deney_parametreleri.md"
)

# ---------- YAML metadata ----------
cat > "$WORK_DIR/metadata.yaml" << 'YAML'
---
title: |
  Havayolu Aksaklık Yönetimi için Kısıt Programlama Tabanlı
  Hibrit Karar Destek Sistemi:
  CP-SAT, Kuantum-Esinli Genetik Algoritma ve
  Açıklanabilir Yapay Zeka Entegrasyonu
author:
  - TEKNOFEST 2026 Havayolu Optimizasyonu Takımı
date: "Nisan 2026"
lang: tr
documentclass: report
classoption:
  - a4paper
  - 12pt
  - oneside
geometry:
  - top=30mm
  - bottom=25mm
  - left=35mm
  - right=25mm
fontsize: 12pt
mainfont: "DejaVu Serif"
sansfont: "DejaVu Sans"
monofont: "DejaVu Sans Mono"
linestretch: 1.5
toc: true
toc-depth: 3
lof: true
lot: true
numbersections: true
colorlinks: true
linkcolor: NavyBlue
urlcolor: NavyBlue
citecolor: NavyBlue
header-includes:
  - \usepackage{polyglossia}
  - \setmainlanguage{turkish}
  - \usepackage{microtype}
  - \usepackage{booktabs}
  - \usepackage{longtable}
  - \usepackage{array}
  - \usepackage{float}
  - \usepackage{caption}
  - \usepackage{amsmath}
  - \usepackage{amssymb}
  - \usepackage{graphicx}
  - \usepackage{listings}
  - \usepackage{xcolor}
  - \definecolor{codebg}{RGB}{248,248,248}
  - \lstset{backgroundcolor=\color{codebg},basicstyle=\ttfamily\small,breaklines=true,frame=single,framesep=3pt,rulecolor=\color{gray!40}}
  - \usepackage{fancyhdr}
  - \pagestyle{fancy}
  - \fancyhf{}
  - \fancyhead[L]{\small\leftmark}
  - \fancyhead[R]{\small TEKNOFEST 2026}
  - \fancyfoot[C]{\thepage}
  - \renewcommand{\headrulewidth}{0.4pt}
  - \setlength{\parindent}{1.5em}
  - \setlength{\parskip}{0.5em}
  - \captionsetup{font=small,labelfont=bf}
...
YAML

# ---------- Markdown ön-işlemci ----------
# Mermaid → açıklama; ASCII art bırak; görsel referansları gerçek img'e çevir
MERGED="$WORK_DIR/merged.md"
> "$MERGED"

IMG_ABS="$IMG_DIR"

for f in "${CHAPTERS[@]}"; do
    if [ -f "$f" ]; then
        echo "" >> "$MERGED"
        echo "\\newpage" >> "$MERGED"
        echo "" >> "$MERGED"
        python3 - "$f" "$IMG_ABS" >> "$MERGED" << 'PYEOF'
import sys, re, os

src_file = sys.argv[1]
img_dir  = sys.argv[2]

with open(src_file, encoding="utf-8") as fh:
    content = fh.read()

# 1. Mermaid bloklarını açıklama notuna dönüştür
def replace_mermaid(m):
    code = m.group(1).strip()
    first_line = code.split('\n')[0]
    return f"\n> **[Diyagram — {first_line}]** *Görsel kaynak kodda mermaid formatında mevcuttur.*\n"
content = re.sub(r'```mermaid\n(.*?)```', replace_mermaid, content, flags=re.DOTALL)

# 2. Görsel yer tutucularını gerçek ![](path) referanslarına dönüştür
# "Şekil X.Y" / "Fig X.Y" geçen satırlarda ilgili PNG varsa ekle
figure_map = {
    "8.1": "fig_8_1_convergence.png",
    "8.2": "fig_8_2_cancellation.png",
    "8.3": "fig_8_3_shap.png",
    "8.1_tablo": "table_8_1_kpi.png",
    "8.7": "fig_8_7_scalability.png",
    "6.1": "fig_6_1_xai_workflow.png",
    "4.1": "fig_4_1_architecture.png",
    "5.2": "fig_5_2_qiga.png",
    "8.5": "fig_8_5_latency.png",
    "8.10": "fig_8_10_usability.png",
    "8.11": "fig_8_11_live_vs_synthetic.png",
    "2.1": "fig_2_1_radar.png",
    "9.1": "fig_9_1_easa_compliance.png",
    "6.2": "fig_6_2_pipeline.png",
    "C.6": "fig_shap_waterfall.png",
}

# ASCII art bloklarını kaldır (```...``` içindeki satır çizgileri)
def replace_ascii_art(m):
    code = m.group(1)
    # Sadece gerçek code blokları değil, görsel temsil blokları
    has_box_chars = any(c in code for c in ['│','┤','┼','└','┬','─','╲','╭','╯','╰','╮','▓','█','▁','▂','▃','▄','▅','▆','▇','▀','┌','┐','┘','┗','┛','╔','╗','╚','╝'])
    if has_box_chars and len(code) > 100:
        return f"\n*[ASCII görsel temsil — PDF/DOCX sürümünde görsel olarak sunulmaktadır]*\n"
    return m.group(0)  # Gerçek kod bloklarını bırak

content = re.sub(r'```\n(.*?)```', replace_ascii_art, content, flags=re.DOTALL)

# Şekil başlıklarının hemen altına PNG referansı ekle
for fig_key, fname in figure_map.items():
    img_path = os.path.join(img_dir, fname)
    if not os.path.exists(img_path):
        continue
    # "Şekil X.Y" veya "Fig X.Y" geçen satırın altına ekle
    pattern = rf'((?:Şekil|Figure|Fig\.?)\s*{re.escape(fig_key)}[^\n]*\n)'
    replacement = r'\1' + f'\n![Şekil {fig_key}]({img_path}){{width=90%}}\n'
    content = re.sub(pattern, replacement, content)

# Tablo 8.1 için özel ekleme
tbl_path = os.path.join(img_dir, "table_8_1_kpi.png")
if os.path.exists(tbl_path):
    content = re.sub(
        r'(Tablo 8\.1[^\n]*\n)',
        r'\1' + f'\n![Tablo 8.1]({tbl_path}){{width=95%}}\n',
        content
    )

# Şekil C.6 için ek SHAP waterfall
shap_path = os.path.join(img_dir, "fig_shap_waterfall.png")
if os.path.exists(shap_path):
    content = re.sub(
        r'(Şekil C\.6[^\n]*\n)',
        r'\1' + f'\n![Şekil C.6 — SHAP Waterfall]({shap_path}){{width=90%}}\n',
        content
    )

print(content)
PYEOF
        echo "" >> "$MERGED"
    else
        echo "UYARI: $f bulunamadı"
    fi
done

echo "==> Birleştirme tamamlandı ($(wc -l < "$MERGED") satır)"

# ---------- PDF ----------
echo "==> PDF derleniyor (xelatex)..."
pandoc \
    "$WORK_DIR/metadata.yaml" \
    "$MERGED" \
    --pdf-engine=xelatex \
    --pdf-engine-opt="-interaction=nonstopmode" \
    --from=markdown+raw_tex+tex_math_dollars+implicit_figures \
    --to=pdf \
    --highlight-style=tango \
    --resource-path="$IMG_DIR:$THESIS_DIR" \
    -o "$OUT_PDF" \
    2>&1 | grep -v "^$" | grep -v "^\[" | tail -15 || true

# ---------- DOCX ----------
echo "==> DOCX derleniyor..."
pandoc \
    "$WORK_DIR/metadata.yaml" \
    "$MERGED" \
    --from=markdown+implicit_figures \
    --to=docx \
    --highlight-style=tango \
    --resource-path="$IMG_DIR:$THESIS_DIR" \
    --toc \
    -o "$OUT_DOCX" \
    2>&1 | tail -5 || true

# ---------- Temizlik ----------
echo "==> Temizlik..."
rm -rf "$WORK_DIR"

echo ""
echo "============================================================"
if [ -f "$OUT_PDF" ]; then
    SZ=$(du -h "$OUT_PDF" | cut -f1)
    PG=$(pdfinfo "$OUT_PDF" 2>/dev/null | grep "Pages:" | awk '{print $2}' || echo "?")
    echo "  PDF : $OUT_PDF  (${SZ}, ${PG} sayfa)"
else
    echo "  PDF : HATA — oluşturulamadı"
fi
if [ -f "$OUT_DOCX" ]; then
    SZ=$(du -h "$OUT_DOCX" | cut -f1)
    echo "  DOCX: $OUT_DOCX  (${SZ})"
else
    echo "  DOCX: HATA — oluşturulamadı"
fi
echo "============================================================"
