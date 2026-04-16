#!/usr/bin/env bash
# ============================================================
# Tez PDF + DOCX Derleyici
# Kullanım: bash docs/thesis/compile_pdf.sh
# Çıktı:    docs/thesis/teknofest2026_tez.pdf
#           docs/thesis/teknofest2026_tez.docx
# ============================================================
set -euo pipefail

THESIS_DIR="$(cd "$(dirname "$0")" && pwd)"
IMG_DIR="$THESIS_DIR/gorseller"
OUT_PDF="$THESIS_DIR/teknofest2026_tez.pdf"
OUT_DOCX="$THESIS_DIR/teknofest2026_tez.docx"
WORK_DIR="$(mktemp -d)"

echo "==> Tez dizini: $THESIS_DIR"
echo "==> Görseller üretiliyor..."
VENV_PY="$(dirname "$(dirname "$THESIS_DIR")")/src/.venv/bin/python3"
[ -x "$VENV_PY" ] && "$VENV_PY" "$IMG_DIR/gen_figures.py" || python3 "$IMG_DIR/gen_figures.py"

# ---------- YAML metadata (numbersections kapalı — başlıklarda zaten numara var) ----------
cat > "$WORK_DIR/metadata.yaml" << 'YAML'
---
title: |
  Havayolu Aksaklık Yönetimi için Kısıt Programlama Tabanlı
  Hibrit Karar Destek Sistemi
subtitle: |
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
toc-depth: 2
lof: true
lot: true
numbersections: false
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
  - \floatplacement{figure}{H}
  - \usepackage{caption}
  - \usepackage{amsmath}
  - \usepackage{amssymb}
  - \usepackage{graphicx}
  - \usepackage{listings}
  - \usepackage{xcolor}
  - \definecolor{codebg}{RGB}{248,248,248}
  - \lstset{backgroundcolor=\color{codebg},basicstyle=\ttfamily\small,breaklines=true,frame=single,framesep=3pt,rulecolor=\color{gray!40},breakatwhitespace=true}
  - \usepackage{fancyhdr}
  - \pagestyle{fancy}
  - \fancyhf{}
  - \fancyhead[L]{\small\nouppercase{\leftmark}}
  - \fancyhead[R]{\small TEKNOFEST 2026}
  - \fancyfoot[C]{\thepage}
  - \renewcommand{\headrulewidth}{0.4pt}
  - \setlength{\parindent}{1.5em}
  - \setlength{\parskip}{0.4em}
  - \captionsetup{font=small,labelfont=bf,justification=centering}
  - \usepackage[hang,flushmargin]{footmisc}
  - \usepackage{emptypage}
...
YAML

# ---------- Bölüm dosyaları ----------
FRONTMATTER=(
    "$THESIS_DIR/00_kapak_ozet.md"
)
CHAPTERS=(
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

# ---------- Python ön-işlemci ----------
preprocess() {
    local f="$1"
    local is_frontmatter="${2:-false}"
    python3 - "$f" "$IMG_DIR" "$is_frontmatter" << 'PYEOF'
import sys, re, os

src_file     = sys.argv[1]
img_dir      = sys.argv[2]
is_frontmatter = sys.argv[3] == "true"

with open(src_file, encoding="utf-8") as fh:
    content = fh.read()

# -------- Mermaid → kısa açıklama --------
def replace_mermaid(m):
    code = m.group(1).strip()
    diagram_type = code.split('\n')[0].strip()
    return f"\n> *[{diagram_type} diyagramı — kaynak kodda Mermaid formatında mevcuttur.]*\n"
content = re.sub(r'```mermaid\n(.*?)```', replace_mermaid, content, flags=re.DOTALL)

# -------- ASCII art blokları → kısa not --------
def replace_ascii(m):
    code = m.group(1)
    box_chars = '│┤┼└┬─╲╭╯╰╮┌┐┘┗┛╔╗╚╝▓█▁▂▃▄▅▆▇▀◆◇'
    if any(c in code for c in box_chars) and len(code.strip()) > 80:
        return '\n*[Görsel temsil — PDF sürümünde ilgili şekil olarak sunulmaktadır.]*\n'
    return m.group(0)
content = re.sub(r'```\n(.*?)```', replace_ascii, content, flags=re.DOTALL)

# -------- Görsel eşleme tablosu --------
figure_map = {
    r'Şekil\s+1\.1': 'fig_1_1_context.png',
    r'Şekil\s+2\.1': 'fig_2_1_radar.png',
    r'Şekil\s+3\.1': 'fig_3_1_dsr.png',
    r'Şekil\s+3\.2': 'fig_3_2_test_pyramid.png',
    r'Şekil\s+4\.1': 'fig_4_1_architecture.png',
    r'Şekil\s+4\.2': 'fig_4_2_auth_flow.png',
    r'Şekil\s+4\.3': 'fig_4_3_docker_topology.png',
    r'Şekil\s+5\.1': 'fig_5_1_constraint_graph.png',
    r'Şekil\s+5\.2': 'fig_5_2_qiga.png',
    r'Şekil\s+6\.1': 'fig_6_1_xai_workflow.png',
    r'Şekil\s+6\.2': 'fig_6_2_pipeline.png',
    r'Şekil\s+7\.1': 'fig_7_1_project_tree.png',
    r'Şekil\s+7\.2': 'fig_7_2_circuit_breaker.png',
    r'Şekil\s+8\.1': 'fig_8_1_convergence.png',
    r'Şekil\s+8\.2': 'fig_8_2_cancellation.png',
    r'Şekil\s+8\.3': 'fig_8_3_shap.png',
    r'Şekil\s+8\.4': 'fig_8_4_ftl_validation.png',
    r'Şekil\s+8\.5': 'fig_8_5_latency.png',
    r'Şekil\s+8\.6': 'fig_8_6_decision_reasons.png',
    r'Şekil\s+8\.7': 'fig_8_7_scalability.png',
    r'Şekil\s+8\.8': 'fig_8_8_api_perf.png',
    r'Şekil\s+8\.9': 'fig_8_9_map_turkey.png',
    r'Şekil\s+8\.10': 'fig_8_10_usability.png',
    r'Şekil\s+8\.11': 'fig_8_11_live_vs_synthetic.png',
    r'Şekil\s+9\.1': 'fig_9_1_easa_compliance.png',
    r'Şekil\s+10\.1': 'fig_10_1_roadmap.png',
    r'Tablo\s+8\.1': 'table_8_1_kpi.png',
    r'Şekil\s+C\.6': 'fig_shap_waterfall.png',
}

for pattern, fname in figure_map.items():
    img_path = os.path.join(img_dir, fname)
    if not os.path.exists(img_path):
        continue
    # Herhangi bir satırda "Şekil X.Y" veya "Tablo X.Y" geçiyorsa altına görsel ekle
    def make_repl(p, pat):
        def repl(m):
            full_line = m.group(1)
            cap_m = re.search(pat + r'[^\n]*', full_line)
            caption = cap_m.group(0).strip() if cap_m else full_line.lstrip('# *').strip()
            return m.group(0) + f'\n\n![{caption}]({p}){{width=90%}}\n'
        return repl
    content = re.sub(
        rf'(?m)^([^\n]*{pattern}[^\n]*)\n(?!\s*!\[)',
        make_repl(img_path, pattern),
        content
    )

# -------- Frontmatter başlığını gizle (kapak sayfası) --------
if is_frontmatter:
    # İlk # başlığı pandoc'un title'ı olarak zaten geliyor, kaldır
    content = re.sub(r'^#\s+[^\n]+\n', '', content, count=1)

print(content)
PYEOF
}

# ---------- Birleştir ----------
MERGED="$WORK_DIR/merged.md"
> "$MERGED"

# Frontmatter (kapak + özet) — chapter numarası olmadan
echo '\pagenumbering{roman}' >> "$MERGED"
for f in "${FRONTMATTER[@]}"; do
    [ -f "$f" ] && preprocess "$f" "true" >> "$MERGED"
done

# Asıl bölümler
echo '' >> "$MERGED"
echo '\pagenumbering{arabic}' >> "$MERGED"
echo '' >> "$MERGED"
for f in "${CHAPTERS[@]}"; do
    if [ -f "$f" ]; then
        echo '' >> "$MERGED"
        echo '\newpage' >> "$MERGED"
        echo '' >> "$MERGED"
        preprocess "$f" "false" >> "$MERGED"
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
    2>&1 | grep -v "^$" | grep -v "^\[" | grep -v "^(/" | tail -10 || true

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
    2>&1 | grep -v "^\[WARNING\].*Table" | tail -5 || true

echo "==> Temizlik..."
rm -rf "$WORK_DIR"

echo ""
echo "============================================================"
[ -f "$OUT_PDF" ]  && echo "  PDF : $OUT_PDF  ($(du -h "$OUT_PDF" | cut -f1), $(pdfinfo "$OUT_PDF" 2>/dev/null | grep Pages: | awk '{print $2}') sayfa)"
[ -f "$OUT_DOCX" ] && echo "  DOCX: $OUT_DOCX  ($(du -h "$OUT_DOCX" | cut -f1))"
echo "============================================================"
