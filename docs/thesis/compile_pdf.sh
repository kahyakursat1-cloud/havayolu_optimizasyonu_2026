#!/usr/bin/env bash
# ============================================================
# Tez PDF Derleyici
# Kullanım: bash docs/thesis/compile_pdf.sh
# Çıktı:    docs/thesis/teknofest2026_tez.pdf
# Gereksinim: pandoc + xelatex (TeX Live)
# ============================================================
set -euo pipefail

THESIS_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT="$THESIS_DIR/teknofest2026_tez.pdf"
WORK_DIR="$(mktemp -d)"

echo "==> Tez dizini: $THESIS_DIR"
echo "==> Geçici dizin: $WORK_DIR"

# ---------- Bölüm dosyalarını sırala ----------
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
  - \usepackage{fontenc}
  - \usepackage{polyglossia}
  - \setmainlanguage{turkish}
  - \usepackage{microtype}
  - \usepackage{booktabs}
  - \usepackage{longtable}
  - \usepackage{array}
  - \usepackage{multirow}
  - \usepackage{float}
  - \usepackage{caption}
  - \usepackage{subcaption}
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
  - \usepackage{setspace}
  - \captionsetup{font=small,labelfont=bf}
  - \usepackage[hang,flushmargin]{footmisc}
...
YAML

echo "==> Metadata oluşturuldu"

# ---------- Mermaid diyagramlarını kaldır (xelatex tanımaz) ----------
# ve code block'ları temizle
MERGED="$WORK_DIR/merged.md"
> "$MERGED"

for f in "${CHAPTERS[@]}"; do
    if [ -f "$f" ]; then
        echo "" >> "$MERGED"
        echo "\\newpage" >> "$MERGED"
        echo "" >> "$MERGED"
        # Mermaid bloklarını metin açıklamaya dönüştür
        python3 - "$f" >> "$MERGED" << 'PYEOF'
import sys, re

with open(sys.argv[1], encoding="utf-8") as fh:
    content = fh.read()

# Mermaid kod bloklarını açıklama notuna dönüştür
def replace_mermaid(m):
    code = m.group(1).strip()
    # İlk satırı başlık olarak kullan
    first_line = code.split('\n')[0]
    return f"\n> **[Diyagram]** *{first_line} — Tam diyagram için kaynak koda bakınız.*\n"

content = re.sub(r'```mermaid\n(.*?)```', replace_mermaid, content, flags=re.DOTALL)

# ASCII art blokları (```...```) düz olarak bırak
print(content)
PYEOF
        echo "" >> "$MERGED"
    else
        echo "UYARI: $f bulunamadı, atlanıyor"
    fi
done

echo "==> Bölümler birleştirildi ($(wc -l < "$MERGED") satır)"

# ---------- Pandoc ile PDF üret ----------
echo "==> Pandoc + XeLaTeX ile PDF derleniyor..."

pandoc \
    "$WORK_DIR/metadata.yaml" \
    "$MERGED" \
    --pdf-engine=xelatex \
    --pdf-engine-opt="-interaction=nonstopmode" \
    --pdf-engine-opt="-halt-on-error" \
    --from=markdown+raw_tex+tex_math_dollars+lists_without_preceding_blankline \
    --to=pdf \
    --highlight-style=tango \
    --resource-path="$THESIS_DIR/gorseller" \
    -o "$OUTPUT" \
    2>&1 | tail -20

echo ""
echo "==> Temizlik..."
rm -rf "$WORK_DIR"

if [ -f "$OUTPUT" ]; then
    SIZE=$(du -h "$OUTPUT" | cut -f1)
    PAGES=$(pdfinfo "$OUTPUT" 2>/dev/null | grep "Pages:" | awk '{print $2}' || echo "?")
    echo ""
    echo "============================================="
    echo "  PDF HAZIR: $OUTPUT"
    echo "  Boyut: $SIZE   Sayfa: $PAGES"
    echo "============================================="
else
    echo "HATA: PDF oluşturulamadı!"
    exit 1
fi
