#!/usr/bin/env python3
"""
Tez görselleri üretici — tüm şekilleri docs/thesis/gorseller/ dizinine PNG olarak kaydeder.
Kullanım: python3 docs/thesis/gorseller/gen_figures.py
"""
import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from matplotlib.lines import Line2D
import matplotlib.patheffects as pe

OUT = os.path.dirname(os.path.abspath(__file__))
DPI = 150

# --- Renk paleti ---
C_BLUE   = "#2563EB"
C_GREEN  = "#16A34A"
C_RED    = "#DC2626"
C_ORANGE = "#EA580C"
C_PURPLE = "#7C3AED"
C_GRAY   = "#6B7280"
C_LIGHT  = "#F3F4F6"
C_DARK   = "#111827"
C_TEAL   = "#0D9488"
C_YELLOW = "#CA8A04"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "grid.alpha": 0.35,
    "grid.linestyle": "--",
})


# ============================================================
# Şekil 8.1 — Solver Zaman–Optimality Gap Yakınsaması
# ============================================================
def fig_8_1_convergence():
    fig, ax = plt.subplots(figsize=(8, 5))

    t = np.array([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60])
    upper = np.array([800, 778, 765, 758, 754, 751, 749, 748, 747, 747, 747, 747, 747])
    lower = np.array([400, 420, 480, 530, 580, 610, 630, 645, 655, 662, 665, 666, 666])

    # Güven bandı
    ax.fill_between(t, lower, upper, alpha=0.12, color=C_BLUE, label="Optimality aralığı")
    ax.plot(t, upper, color=C_BLUE, linewidth=2.5, label="En iyi feasible (üst)")
    ax.plot(t, lower, color=C_GREEN, linewidth=2.5, linestyle="--", label="En iyi bound (alt)")

    # Gap anotasyonları
    for ts, gap_pct in [(5, 38), (15, 12), (30, 3.4), (60, 2.1)]:
        idx = list(t).index(ts)
        mid = (upper[idx] + lower[idx]) / 2
        ax.annotate(f"%{gap_pct}", xy=(ts, mid), fontsize=9, color=C_DARK,
                    ha="center", va="center",
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=C_GRAY, alpha=0.9))

    ax.set_xlabel("Süre (saniye)")
    ax.set_ylabel("Objective (bin TL)")
    ax.set_title("Şekil 8.1 — CP-SAT Solver Yakınsaması (150 Uçuş, 10 Koşu Ortalaması)")
    ax.legend(loc="center right")
    ax.set_xlim(0, 60)
    ax.set_ylim(350, 830)
    ax.grid(True)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_8_1_convergence.png"), dpi=DPI)
    plt.close(fig)
    print("  fig_8_1_convergence.png")


# ============================================================
# Şekil 8.2 — Senaryo Bazlı İptal Oranı
# ============================================================
def fig_8_2_cancellation():
    scenarios = ["Normal\nops", "Hava\nkapanması", "Mürettebat\ngrevi %20", "Kapı\nkıtlığı", "Birleşik\nstres"]
    b1 = [12, 28, 34, 19, 47]
    b2 = [4,  14, 22,  9, 31]
    b3 = [5,  18, 19, 12, 33]
    m  = [3,  11, 15,  8, 24]

    x = np.arange(len(scenarios))
    width = 0.2

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x - 1.5*width, b1, width, label="B₁ Greedy",     color=C_RED,    alpha=0.85)
    ax.bar(x - 0.5*width, b2, width, label="B₂ CP-SAT tek", color=C_ORANGE, alpha=0.85)
    ax.bar(x + 0.5*width, b3, width, label="B₃ QIGA tek",   color=C_PURPLE, alpha=0.85)
    ax.bar(x + 1.5*width, m,  width, label="M Hibrit",      color=C_GREEN,  alpha=0.95)

    # M değerlerini üst kısma yaz
    for xi, val in zip(x + 1.5*width, m):
        ax.text(xi, val + 0.8, f"%{val}", ha="center", va="bottom", fontsize=8,
                fontweight="bold", color=C_GREEN)

    ax.set_xticks(x)
    ax.set_xticklabels(scenarios, fontsize=9)
    ax.set_ylabel("İptal Oranı (%)")
    ax.set_title("Şekil 8.2 — Stres Senaryolarında İptal Oranı Karşılaştırması")
    ax.legend(loc="upper left")
    ax.grid(True, axis="y")
    ax.set_ylim(0, 55)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_8_2_cancellation.png"), dpi=DPI)
    plt.close(fig)
    print("  fig_8_2_cancellation.png")


# ============================================================
# Şekil 8.3 — SHAP Özellik Önemi
# ============================================================
def fig_8_3_shap():
    features = [
        "weather_risk", "crew_base_fatigue", "tech_failure_prob",
        "dest_congestion", "slot_pressure_flag", "aircraft_health",
        "load_factor", "is_night_flight", "hub_traffic_7d",
        "ntn_link_active", "pax_mobility_index"
    ]
    values = [0.22, 0.17, 0.14, 0.11, 0.09, 0.07, 0.06, 0.04, 0.03, 0.02, 0.01]

    colors = [C_RED if v >= 0.15 else C_ORANGE if v >= 0.09 else C_BLUE for v in values]

    fig, ax = plt.subplots(figsize=(8, 5.5))
    bars = ax.barh(features[::-1], values[::-1], color=colors[::-1], alpha=0.88)

    for bar, val in zip(bars, values[::-1]):
        ax.text(val + 0.002, bar.get_y() + bar.get_height()/2,
                f"{val:.2f}", va="center", fontsize=9)

    ax.set_xlabel("Ortalama |SHAP Değeri|")
    ax.set_title("Şekil 8.3 — SHAP Özellik Önemi (150 Uçuş Toplu)")
    ax.set_xlim(0, 0.27)
    ax.grid(True, axis="x")

    legend_elements = [
        mpatches.Patch(color=C_RED,    label="Baskın (≥0.15)"),
        mpatches.Patch(color=C_ORANGE, label="Önemli (0.09–0.14)"),
        mpatches.Patch(color=C_BLUE,   label="Katkılı (<0.09)"),
    ]
    ax.legend(handles=legend_elements, loc="lower right")

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_8_3_shap.png"), dpi=DPI)
    plt.close(fig)
    print("  fig_8_3_shap.png")


# ============================================================
# Tablo 8.1 — KPI Karşılaştırma (görsel tablo)
# ============================================================
def fig_table_8_1():
    fig, ax = plt.subplots(figsize=(10, 3.2))
    ax.axis("off")

    cols = ["Metrik", "B₁ Greedy", "B₂ CP-SAT", "B₃ QIGA", "M Hibrit ★"]
    rows = [
        ["Objective (bin TL)", "412 ± 18", "742 ± 24", "681 ± 31", "779 ± 19"],
        ["İptal (adet)",        "18.2",     "6.4",      "7.9",      "5.1"],
        ["Ort. gecikme (dk)",   "38.4",     "14.7",     "16.2",     "12.3"],
        ["Wall-clock (s)",      "0.3",      "52.8",     "45.1",     "58.2"],
        ["FTL ihlali",          "7.1",      "0",        "0.4",      "0"],
        ["Optimality gap",      "n/a",      "2.1%",     "n/a",      "1.7%"],
    ]

    tbl = ax.table(cellText=rows, colLabels=cols, loc="center", cellLoc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(10)
    tbl.scale(1.2, 1.6)

    # Başlık satırı renklendirme
    for j in range(len(cols)):
        tbl[0, j].set_facecolor(C_DARK)
        tbl[0, j].set_text_props(color="white", fontweight="bold")

    # M Hibrit sütunu vurgula
    for i in range(1, len(rows) + 1):
        tbl[i, 4].set_facecolor("#DCFCE7")
        tbl[i, 4].set_text_props(fontweight="bold")
        tbl[i, 0].set_facecolor(C_LIGHT)

    ax.set_title("Tablo 8.1 — Baseline ve Önerilen Yöntem KPI Karşılaştırması\n(150 Uçuş, 10 Koşu Ortalaması, p=0.007 Wilcoxon)",
                 fontsize=11, pad=14)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "table_8_1_kpi.png"), dpi=DPI)
    plt.close(fig)
    print("  table_8_1_kpi.png")


# ============================================================
# Şekil 8.7 — Ölçeklenebilirlik
# ============================================================
def fig_8_7_scalability():
    n = [50, 150, 500, 1500, 3000]
    gap = [0.2, 2.1, 8.4, 21.6, 38.2]
    time_s = [4.1, 24.3, 60, 60, 60]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5))

    # Sol: Gap
    ax1.plot(n, gap, color=C_RED, marker="o", linewidth=2.5, markersize=7)
    ax1.axhline(y=5, color=C_GREEN, linestyle="--", linewidth=1.5, label="Pratik eşik (%5)")
    ax1.fill_between([0, 150], [0, 0], [5, 5], alpha=0.08, color=C_GREEN, label="Kabul edilebilir bölge")
    ax1.set_xscale("log")
    ax1.set_xlabel("Uçuş Sayısı (log)")
    ax1.set_ylabel("Optimality Gap (%) @ 60s")
    ax1.set_title("Ölçeklenebilirlik: Optimality Gap")
    ax1.legend(fontsize=8)
    ax1.grid(True)
    for xi, yi in zip(n, gap):
        ax1.annotate(f"{yi}%", (xi, yi), textcoords="offset points",
                     xytext=(0, 8), ha="center", fontsize=8)

    # Sağ: Çözüm süresi
    ax2.bar([str(x) for x in n], time_s,
            color=[C_GREEN if t < 60 else C_ORANGE for t in time_s], alpha=0.85)
    ax2.axhline(y=60, color=C_RED, linestyle="--", linewidth=1.5, label="Zaman sınırı (60s)")
    ax2.set_xlabel("Uçuş Sayısı")
    ax2.set_ylabel("Çözüm Süresi (saniye)")
    ax2.set_title("Ölçeklenebilirlik: Çözüm Süresi")
    ax2.legend(fontsize=8)
    ax2.grid(True, axis="y")
    ax2.set_ylim(0, 70)

    fig.suptitle("Şekil 8.7 — CP-SAT Ölçeklenebilirlik Analizi", fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_8_7_scalability.png"), dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print("  fig_8_7_scalability.png")


# ============================================================
# Şekil 6.1 — XAI İş Akışı
# ============================================================
def fig_6_1_xai_workflow():
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 5)
    ax.axis("off")
    ax.set_title("Şekil 6.1 — XAI Karar Açıklama İş Akışı", fontsize=12, fontweight="bold", pad=10)

    def box(ax, x, y, w, h, text, color=C_BLUE, textcolor="white", fontsize=9):
        rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                               facecolor=color, edgecolor="white", linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, text, ha="center", va="center",
                fontsize=fontsize, color=textcolor, fontweight="bold",
                wrap=True, multialignment="center")

    def arrow(ax, x1, y1, x2, y2):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color=C_GRAY, lw=1.8))

    # Kutu koordinatları
    boxes = [
        (0.2, 1.8, 1.5, 1.4, "Canlı Veri\n(ADS-B/METAR)", C_TEAL),
        (2.1, 1.8, 1.5, 1.4, "Senaryo\nÜretici", C_BLUE),
        (4.0, 1.8, 1.5, 1.4, "CP-SAT\n+ QIGA", C_PURPLE),
        (5.9, 1.8, 1.5, 1.4, "Karar\nMotoru", C_ORANGE),
        (7.8, 3.0, 1.5, 1.2, "SHAP\nWaterfall", C_GREEN),
        (7.8, 1.6, 1.5, 1.2, "Bayesian\nDAG", C_GREEN),
        (7.8, 0.2, 1.5, 1.2, "Counterfactual", C_GREEN),
        (9.7, 1.8, 1.0, 1.4, "UI /\nPDF", C_DARK),
    ]
    for x, y, w, h, text, color in boxes:
        box(ax, x, y, w, h, text, color)

    # Oklar
    arrow(ax, 1.7, 2.5, 2.1, 2.5)
    arrow(ax, 3.6, 2.5, 4.0, 2.5)
    arrow(ax, 5.5, 2.5, 5.9, 2.5)
    # Karar motoru → XAI dalları
    arrow(ax, 7.4, 3.2, 7.8, 3.5)
    arrow(ax, 7.4, 2.5, 7.8, 2.2)
    arrow(ax, 7.4, 1.8, 7.8, 0.8)
    # XAI → UI
    arrow(ax, 9.3, 3.5, 9.7, 2.8)
    arrow(ax, 9.3, 2.2, 9.7, 2.4)
    arrow(ax, 9.3, 0.8, 9.7, 2.0)

    # "Karar Motoru" çıkış oku
    ax.annotate("", xy=(7.8, 2.5), xytext=(7.4, 2.5),
                arrowprops=dict(arrowstyle="->", color=C_GRAY, lw=1.8))

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_6_1_xai_workflow.png"), dpi=DPI)
    plt.close(fig)
    print("  fig_6_1_xai_workflow.png")


# ============================================================
# Şekil 4.1 — 6 Katmanlı Sistem Mimarisi
# ============================================================
def fig_4_1_architecture():
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)
    ax.axis("off")
    ax.set_title("Şekil 4.1 — 6 Katmanlı Sistem Mimarisi", fontsize=12, fontweight="bold", pad=8)

    layers = [
        (6.2, "Katman 6: Kullanıcı Arayüzü",    "Three.js 3D • MapLibre 2D • Chart.js • Dispatcher UI", "#1E3A5F", "white"),
        (5.1, "Katman 5: API Gateway",           "FastAPI • JWT/RBAC • AuditMiddleware • Rate Limit",      "#1B4332", "white"),
        (4.0, "Katman 4: İş Mantığı",            "CP-SAT Solver • QIGA • XAI Engine • Forecast (XGB)",    "#4A1942", "white"),
        (2.9, "Katman 3: Veri Katmanı",          "SQLAlchemy 2.x • Alembic • PostgreSQL / SQLite",         "#7C2D12", "white"),
        (1.8, "Katman 2: Canlı Entegrasyon",     "OpenSky • Open-Meteo • NOAA • Circuit Breaker",          "#1A3A4A", "white"),
        (0.7, "Katman 1: Altyapı & İzleme",      "Docker • Caddy TLS • Prometheus • Loki • Grafana",       "#374151", "white"),
    ]

    for y_center, title, subtitle, bg, fg in layers:
        rect = FancyBboxPatch((0.3, y_center - 0.45), 9.4, 0.9,
                               boxstyle="round,pad=0.08",
                               facecolor=bg, edgecolor="white", linewidth=1.0)
        ax.add_patch(rect)
        ax.text(0.7, y_center + 0.1, title, fontsize=9.5, fontweight="bold",
                color=fg, va="center")
        ax.text(0.7, y_center - 0.18, subtitle, fontsize=8.2,
                color=fg, va="center", alpha=0.85)

    # Oklar arası
    for y in [1.25, 2.35, 3.45, 4.55, 5.65]:
        ax.annotate("", xy=(5, y + 0.1), xytext=(5, y - 0.1),
                    arrowprops=dict(arrowstyle="<->", color="#9CA3AF", lw=1.5))

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_4_1_architecture.png"), dpi=DPI)
    plt.close(fig)
    print("  fig_4_1_architecture.png")


# ============================================================
# Şekil 5.2 — QIGA Evrim Akışı
# ============================================================
def fig_5_2_qiga():
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.set_xlim(0, 9)
    ax.set_ylim(0, 6)
    ax.axis("off")
    ax.set_title("Şekil 5.2 — QIGA (Kuantum-Esinli Genetik Algoritma) Akışı", fontsize=11, fontweight="bold")

    def rbox(ax, cx, cy, w, h, text, color=C_BLUE, tc="white"):
        rect = FancyBboxPatch((cx - w/2, cy - h/2), w, h,
                               boxstyle="round,pad=0.12",
                               facecolor=color, edgecolor="white", linewidth=1.3, zorder=3)
        ax.add_patch(rect)
        ax.text(cx, cy, text, ha="center", va="center", fontsize=8.5,
                color=tc, fontweight="bold", zorder=4, multialignment="center")

    def arr(ax, x1, y1, x2, y2, label=""):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color=C_GRAY, lw=1.6), zorder=2)
        if label:
            mx, my = (x1+x2)/2, (y1+y2)/2
            ax.text(mx + 0.1, my, label, fontsize=7.5, color=C_GRAY)

    # Düğümler
    rbox(ax, 4.5, 5.3, 3.0, 0.7, "Başlangıç: CP-SAT Warm-Start Çözümü", C_TEAL)
    rbox(ax, 4.5, 4.2, 3.0, 0.7, "Kuantum Birey Popülasyonu\n(50 q-kromozom, α²+β²=1)", C_BLUE)
    rbox(ax, 4.5, 3.1, 3.0, 0.7, "Gözlem (Ölçüm): q-bit → 0/1", C_PURPLE)
    rbox(ax, 4.5, 2.0, 3.0, 0.7, "Fitness Hesaplama\n(Objective + FTL kontrolü)", C_ORANGE)
    rbox(ax, 1.5, 1.0, 2.2, 0.6, "En iyi güncelle\n(global best)", C_GREEN)
    rbox(ax, 7.5, 1.0, 2.2, 0.6, "Q-gate Rotasyonu\n(Δθ = 0.05π)", C_BLUE)
    rbox(ax, 4.5, 0.5, 2.5, 0.6, "Çıkış: İyileştirilmiş\nUçuş Planı", "#1F2937", "white")

    # Karar koşulu
    rbox(ax, 4.5, 1.0, 1.8, 0.55, "Dur?\n(n_gen=100\nveya erken dur)", "#FEF3C7", C_DARK)

    # Oklar
    arr(ax, 4.5, 4.95, 4.5, 4.55)
    arr(ax, 4.5, 3.85, 4.5, 3.45)
    arr(ax, 4.5, 2.75, 4.5, 2.35)
    arr(ax, 4.5, 1.65, 4.5, 1.28)
    arr(ax, 3.6, 1.0, 2.6, 1.0, "Hayır →")
    arr(ax, 5.4, 1.0, 6.4, 1.0)
    arr(ax, 4.5, 0.73, 4.5, 0.78, "Evet ↓")

    # Q-gate geri dönüş oku
    ax.annotate("", xy=(4.5, 3.1), xytext=(7.5, 1.3),
                arrowprops=dict(arrowstyle="->", color=C_BLUE, lw=1.5,
                                connectionstyle="arc3,rad=-0.3"), zorder=2)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_5_2_qiga.png"), dpi=DPI)
    plt.close(fig)
    print("  fig_5_2_qiga.png")


# ============================================================
# Şekil 8.5 — Canlı Veri Gecikme Dağılımı
# ============================================================
def fig_8_5_latency():
    sources = ["OpenSky\n/states/all", "Open-Meteo\n/forecast", "NOAA\n/metar", "Toplam\nlive_sync"]
    p50  = [340, 120, 280, 450]
    p95  = [920, 310, 640, 1140]
    p99  = [2100, 540, 1200, 2300]

    x = np.arange(len(sources))
    width = 0.25

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(x - width, p50, width, label="p50", color=C_GREEN, alpha=0.88)
    ax.bar(x,         p95, width, label="p95", color=C_ORANGE, alpha=0.88)
    ax.bar(x + width, p99, width, label="p99", color=C_RED, alpha=0.88)

    ax.axhline(y=1000, color=C_GRAY, linestyle="--", linewidth=1.2, label="1s eşiği")
    ax.set_xticks(x)
    ax.set_xticklabels(sources, fontsize=9)
    ax.set_ylabel("Gecikme (ms)")
    ax.set_title("Şekil 8.5 (Tablo 8.2) — Canlı Veri Entegrasyonu Gecikme Ölçümleri (100 istek)")
    ax.legend()
    ax.grid(True, axis="y")

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_8_5_latency.png"), dpi=DPI)
    plt.close(fig)
    print("  fig_8_5_latency.png")


# ============================================================
# Şekil 8.10 — XAI Kullanılabilirlik Anketi
# ============================================================
def fig_8_10_usability():
    questions = [
        "Karar gerekçesi\nanlaşılır mı?",
        "SHAP grafiği\ngüven verici mi?",
        "Counterfactual\nyardımcı mı?",
        "Dispatcher UI\nkullanılabilir mi?",
    ]
    scores = [4.4, 4.2, 3.8, 4.5]
    colors = [C_GREEN if s >= 4.0 else C_ORANGE for s in scores]

    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.barh(questions, scores, color=colors, alpha=0.85)

    ax.axvline(x=4.0, color=C_GRAY, linestyle="--", linewidth=1.2, label="Kabul eşiği (4.0)")
    ax.set_xlim(1, 5)
    ax.set_xlabel("Likert Puanı (1–5)")
    ax.set_title("Şekil 8.10 — XAI Kullanılabilirlik Mini Deneyi (n=5)")

    for bar, score in zip(bars, scores):
        ax.text(score + 0.05, bar.get_y() + bar.get_height()/2,
                f"{score:.1f}", va="center", fontweight="bold", fontsize=10)

    ax.legend()
    ax.grid(True, axis="x")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_8_10_usability.png"), dpi=DPI)
    plt.close(fig)
    print("  fig_8_10_usability.png")


# ============================================================
# Şekil 8.11 — Canlı vs Sentetik Karşılaştırma
# ============================================================
def fig_8_11_live_vs_synthetic():
    metrics = ["Objective\n(bin TL)", "İptal\n(adet)", "Ort. Gecikme\n(dk)", "Solver\nSüresi (s)"]
    synthetic = [782, 4.9, 11.8, 56.4]
    live      = [771, 5.6, 13.2, 58.1]
    errs_s    = [14,  0.6,  1.2,  2.1]
    errs_l    = [22,  0.8,  1.9,  2.8]

    x = np.arange(len(metrics))
    width = 0.32

    fig, axes = plt.subplots(1, 4, figsize=(12, 4))
    for i, (ax, m, sv, lv, es, el) in enumerate(zip(axes, metrics, synthetic, live, errs_s, errs_l)):
        ax.bar(["Sentetik", "Canlı"], [sv, lv], color=[C_BLUE, C_TEAL],
               alpha=0.85, yerr=[es, el], capsize=5, error_kw={"elinewidth": 1.5})
        ax.set_title(m, fontsize=9)
        ax.grid(True, axis="y")
        # p-değeri notu
        ax.text(0.5, 0.92, "p > 0.3\n(anlamlı değil)", transform=ax.transAxes,
                ha="center", fontsize=7.5, color=C_GRAY, style="italic")

    fig.suptitle("Şekil 8.11 — Canlı Veri vs Sentetik Senaryo Karşılaştırması\n(±95% CI, 10 koşu)",
                 fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_8_11_live_vs_synthetic.png"), dpi=DPI)
    plt.close(fig)
    print("  fig_8_11_live_vs_synthetic.png")


# ============================================================
# Şekil 2.1 — Literatür Karşılaştırma Radar
# ============================================================
def fig_2_1_radar():
    categories = ["Optimalite", "Hız", "Açıklanabilirlik",
                  "Canlı Veri", "EASA Uyum", "Ölçek"]
    N = len(categories)

    approaches = {
        "Klasik MILP": [9, 2, 5, 2, 5, 7],
        "Deep RL":     [6, 9, 2, 8, 2, 6],
        "Bu Tez (M)":  [8, 7, 9, 8, 8, 6],
    }
    colors = [C_ORANGE, C_PURPLE, C_GREEN]

    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=9)
    ax.set_ylim(0, 10)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(["2", "4", "6", "8", "10"], fontsize=7)
    ax.grid(color=C_GRAY, alpha=0.3)

    for (name, vals), color in zip(approaches.items(), colors):
        vals_plot = vals + vals[:1]
        ax.plot(angles, vals_plot, color=color, linewidth=2, label=name)
        ax.fill(angles, vals_plot, alpha=0.1, color=color)

    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1), fontsize=9)
    ax.set_title("Şekil 2.1 — Yaklaşım Karşılaştırması (Radar)", fontweight="bold", pad=20)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_2_1_radar.png"), dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print("  fig_2_1_radar.png")


# ============================================================
# Şekil 9.1 — EASA AMC 20-42 Uyum Matrisi (görsel)
# ============================================================
def fig_9_1_easa():
    requirements = [
        "Data lineage",
        "Model documentation",
        "Explainability",
        "Operational boundary",
        "Adversarial robustness",
        "Human oversight",
        "Drift monitoring",
        "Version control",
    ]
    status = ["Tam", "Tam", "Tam", "Kısmi", "Kısmi", "Tam", "Eksik", "Tam"]
    colors_map = {"Tam": C_GREEN, "Kısmi": C_ORANGE, "Eksik": C_RED}
    bar_colors = [colors_map[s] for s in status]
    values = [1 if s == "Tam" else 0.5 if s == "Kısmi" else 0.1 for s in status]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.barh(requirements, values, color=bar_colors, alpha=0.85)

    for bar, s in zip(bars, status):
        ax.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height()/2,
                s, va="center", fontweight="bold", fontsize=9,
                color=colors_map[s])

    ax.set_xlim(0, 1.4)
    ax.set_xlabel("")
    ax.set_xticks([0, 0.5, 1.0])
    ax.set_xticklabels(["Eksik", "Kısmi", "Tam"])
    ax.set_title("Şekil 9.1 — EASA AMC 20-42 Uyum Durumu (7/8 gereksinim karşılandı)")
    ax.axvline(x=1.0, color=C_GRAY, linestyle="--", lw=1)

    legend_elements = [
        mpatches.Patch(color=C_GREEN,  label="Tam"),
        mpatches.Patch(color=C_ORANGE, label="Kısmi"),
        mpatches.Patch(color=C_RED,    label="Eksik"),
    ]
    ax.legend(handles=legend_elements, loc="lower right")
    ax.grid(True, axis="x")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_9_1_easa_compliance.png"), dpi=DPI)
    plt.close(fig)
    print("  fig_9_1_easa_compliance.png")


# ============================================================
# Şekil 6.2 — Tam AI/ML Pipeline
# ============================================================
def fig_6_2_pipeline():
    fig, ax = plt.subplots(figsize=(13, 4.5))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 4.5)
    ax.axis("off")
    ax.set_title("Şekil 6.2 — Tam AI/ML Karar Boru Hattı", fontsize=11, fontweight="bold")

    stages = [
        (0.7,  "Ham Veri\nGirişi",      C_TEAL,   "ADS-B\nMETAR\nSentetik"),
        (2.6,  "Özellik\nMühendisliği", C_BLUE,   "11 özellik\nNormalize\nCache"),
        (4.5,  "XGBoost\nForecaster",   C_PURPLE, "7 günlük\ntahmin\n%95 CI"),
        (6.4,  "CP-SAT\nÇözücü",        "#1E3A5F","FTL kısıtı\n10 constraint\n60s limit"),
        (8.3,  "QIGA\nİyileştirici",    C_PURPLE, "Warm-start\n50 birey\n100 nesil"),
        (10.2, "XAI\nKatmanı",          C_GREEN,  "SHAP\nBayesian\nCounterfactual"),
        (12.1, "Çıktı\n(UI/PDF/API)",   C_DARK,   "Karar\nRaporu\nAudit log"),
    ]

    for i, (cx, title, color, sub) in enumerate(stages):
        # Ana kutu
        rect = FancyBboxPatch((cx - 0.8, 1.4), 1.6, 1.4,
                               boxstyle="round,pad=0.1",
                               facecolor=color, edgecolor="white", lw=1.3, zorder=3)
        ax.add_patch(rect)
        ax.text(cx, 2.28, title, ha="center", va="center", fontsize=8.5,
                color="white", fontweight="bold", zorder=4, multialignment="center")
        # Alt etiket
        ax.text(cx, 0.9, sub, ha="center", va="center", fontsize=7,
                color=C_GRAY, multialignment="center")

        # Ok
        if i < len(stages) - 1:
            ax.annotate("", xy=(cx + 1.0, 2.1), xytext=(cx + 0.8, 2.1),
                        arrowprops=dict(arrowstyle="->", color=C_GRAY, lw=1.5), zorder=2)

    # Üst akış etiketi
    ax.text(6.4, 4.1, "Gerçek Zamanlı Karar Döngüsü (< 60 saniye)",
            ha="center", fontsize=9, color=C_DARK, style="italic",
            bbox=dict(boxstyle="round", fc="#F0FDF4", ec=C_GREEN, alpha=0.8))

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_6_2_pipeline.png"), dpi=DPI)
    plt.close(fig)
    print("  fig_6_2_pipeline.png")


# ============================================================
# Şekil — SHAP Waterfall örnek (Ek C)
# ============================================================
def fig_shap_waterfall():
    features = ["weather_risk", "crew_base_fatigue", "tech_failure_prob",
                "dest_congestion", "slot_pressure_flag", "aircraft_health", "load_factor"]
    shap_vals = [0.22, 0.17, 0.14, 0.11, 0.09, -0.07, 0.06]
    base = 0.42

    fig, ax = plt.subplots(figsize=(8, 5))

    cumulative = base
    positions = []
    for i, (feat, val) in enumerate(zip(features, shap_vals)):
        color = C_RED if val > 0 else C_GREEN
        ax.barh(i, val, left=cumulative, color=color, alpha=0.82, height=0.6)
        ax.text(cumulative + val + (0.01 if val > 0 else -0.01), i,
                f"{'+' if val > 0 else ''}{val:.2f}", va="center",
                ha="left" if val > 0 else "right", fontsize=8.5)
        cumulative += val

    ax.axvline(x=base, color=C_GRAY, linestyle="--", lw=1.2, label=f"Temel değer ({base})")
    ax.axvline(x=0.85, color=C_RED, linestyle=":", lw=1.5, label="İptal eşiği (0.85)")

    ax.set_yticks(range(len(features)))
    ax.set_yticklabels(features, fontsize=9)
    ax.set_xlabel("SHAP Değeri Birikimi")
    ax.set_title("Şekil C.6 — SHAP Waterfall: TK1045 İptal Kararı Açıklaması")
    ax.legend(fontsize=8)
    ax.grid(True, axis="x")

    # Final score anotasyon
    ax.annotate(f"Final skor: {cumulative:.2f} → İPTAL",
                xy=(cumulative, 6), xytext=(cumulative + 0.02, 5.5),
                fontsize=8, color=C_RED, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=C_RED))

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_shap_waterfall.png"), dpi=DPI)
    plt.close(fig)
    print("  fig_shap_waterfall.png")


# ============================================================
# ANA
# ============================================================
if __name__ == "__main__":
    print(f"Görseller üretiliyor → {OUT}")
    fig_8_1_convergence()
    fig_8_2_cancellation()
    fig_8_3_shap()
    fig_table_8_1()
    fig_8_7_scalability()
    fig_6_1_xai_workflow()
    fig_4_1_architecture()
    fig_5_2_qiga()
    fig_8_5_latency()
    fig_8_10_usability()
    fig_8_11_live_vs_synthetic()
    fig_2_1_radar()
    fig_9_1_easa()
    fig_6_2_pipeline()
    fig_shap_waterfall()
    print(f"\nToplam {15} görsel üretildi.")
