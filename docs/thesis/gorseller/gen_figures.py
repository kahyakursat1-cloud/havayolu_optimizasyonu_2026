#!/usr/bin/env python3
"""
TEKNOFEST 2026 — Tez Görselleri (Profesyonel Sürüm)
Kütüphaneler: matplotlib 3.10, seaborn 0.13, plotly 6 + kaleido
Kullanım: python3 docs/thesis/gorseller/gen_figures.py
"""
import os
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import matplotlib.ticker as mticker
import seaborn as sns
import plotly.graph_objects as go
from plotly.subplots import make_subplots

OUT = os.path.dirname(os.path.abspath(__file__))
DPI = 180

# ═══════════════════════════════════════════════════════════
# TASARIM SİSTEMİ
# ═══════════════════════════════════════════════════════════
PALETTE = {
    "primary":   "#1D4ED8",   # Koyu mavi
    "secondary": "#0F766E",   # Teal
    "success":   "#15803D",   # Yeşil
    "danger":    "#B91C1C",   # Kırmızı
    "warning":   "#B45309",   # Amber
    "purple":    "#6D28D9",   # Mor
    "slate":     "#334155",   # Slate
    "muted":     "#64748B",   # Gri
    "surface":   "#F8FAFC",   # Arka plan
    "border":    "#E2E8F0",   # Kenarlık
    "text":      "#0F172A",   # Başlık metin
}

ACCENT_SEQ = [
    PALETTE["primary"], PALETTE["secondary"], PALETTE["purple"],
    PALETTE["warning"], PALETTE["danger"], PALETTE["success"],
]


def hex_to_rgba(hex_color: str, alpha: float = 0.12) -> str:
    """Convert #RRGGBB to rgba(R,G,B,alpha)."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

# Seaborn genel tema
sns.set_theme(
    style="ticks",
    palette=ACCENT_SEQ,
    font="DejaVu Sans",
    font_scale=1.05,
    rc={
        "axes.facecolor":     PALETTE["surface"],
        "figure.facecolor":   "white",
        "axes.edgecolor":     PALETTE["border"],
        "axes.linewidth":     0.8,
        "axes.grid":          True,
        "grid.color":         PALETTE["border"],
        "grid.linewidth":     0.6,
        "axes.spines.top":    False,
        "axes.spines.right":  False,
        "xtick.color":        PALETTE["muted"],
        "ytick.color":        PALETTE["muted"],
        "text.color":         PALETTE["text"],
        "axes.labelcolor":    PALETTE["text"],
        "axes.titlepad":      12,
        "figure.dpi":         DPI,
    }
)

PLOTLY_TEMPLATE = dict(
    layout=dict(
        font=dict(family="DejaVu Sans, Arial", color=PALETTE["text"]),
        paper_bgcolor="white",
        plot_bgcolor=PALETTE["surface"],
        title_font=dict(size=14, color=PALETTE["text"]),
        colorway=ACCENT_SEQ,
        xaxis=dict(showgrid=True, gridcolor=PALETTE["border"], gridwidth=0.6,
                   linecolor=PALETTE["border"], ticks="outside", ticklen=4),
        yaxis=dict(showgrid=True, gridcolor=PALETTE["border"], gridwidth=0.6,
                   linecolor=PALETTE["border"], ticks="outside", ticklen=4),
        margin=dict(l=60, r=40, t=60, b=60),
    )
)


def save_mpl(fig, name, tight=True):
    if tight:
        fig.tight_layout()
    fig.savefig(os.path.join(OUT, name), dpi=DPI, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    print(f"  {name}")


def save_plotly(fig, name, w=900, h=500):
    fig.write_image(os.path.join(OUT, name), width=w, height=h, scale=2)
    print(f"  {name}")


# ═══════════════════════════════════════════════════════════
# 1. Sistem Bağlam Diyagramı
# ═══════════════════════════════════════════════════════════
def fig_1_1_context():
    fig, ax = plt.subplots(figsize=(11, 6.5))
    ax.set_xlim(0, 11); ax.set_ylim(0, 6.5); ax.axis("off")
    ax.set_facecolor("white")

    def node(cx, cy, w, h, label, sub, color, alpha=1.0):
        r = FancyBboxPatch((cx-w/2, cy-h/2), w, h,
                           boxstyle="round,pad=0.12", linewidth=0,
                           facecolor=color, alpha=alpha, zorder=3)
        shadow = FancyBboxPatch((cx-w/2+0.06, cy-h/2-0.06), w, h,
                                boxstyle="round,pad=0.12", linewidth=0,
                                facecolor="#00000018", zorder=2)
        ax.add_patch(shadow); ax.add_patch(r)
        ax.text(cx, cy+0.13, label, ha="center", va="center",
                fontsize=9, color="white", fontweight="bold", zorder=4, multialignment="center")
        ax.text(cx, cy-0.22, sub, ha="center", va="center",
                fontsize=7.5, color="white", alpha=0.85, zorder=4, multialignment="center")

    def arrow(x1, y1, x2, y2, label="", bidirectional=False):
        style = "<->" if bidirectional else "->"
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle=style, color=PALETTE["muted"],
                                   lw=1.4, mutation_scale=14), zorder=1)
        if label:
            mx, my = (x1+x2)/2, (y1+y2)/2
            ax.text(mx, my+0.18, label, ha="center", fontsize=7.5,
                    color=PALETTE["muted"], style="italic",
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=PALETTE["border"], alpha=0.85))

    # Aktörler (sol)
    node(1.2, 5.2, 1.8, 0.75, "Dispeçer", "Operator", PALETTE["slate"])
    node(1.2, 3.5, 1.8, 0.75, "Jüri / Yönetici", "Viewer", PALETTE["slate"])
    node(1.2, 1.8, 1.8, 0.75, "Sistem Yöneticisi", "Admin", PALETTE["slate"])

    # Merkez platform
    cx, cy, pw, ph = 5.5, 3.5, 3.6, 4.2
    rect_outer = FancyBboxPatch((cx-pw/2-0.08, cy-ph/2-0.08), pw+0.16, ph+0.16,
                                boxstyle="round,pad=0.15", linewidth=1.5,
                                edgecolor=PALETTE["primary"], facecolor="#EFF6FF", zorder=2)
    ax.add_patch(rect_outer)
    node(5.5, 5.3, 3.2, 0.75, "Kullanıcı Arayüzü", "Three.js · MapLibre · Chart.js", PALETTE["primary"])
    node(5.5, 4.2, 3.2, 0.75, "API Gateway", "FastAPI · JWT/RBAC · Audit", PALETTE["secondary"])
    node(5.5, 3.1, 3.2, 0.75, "Solver + XAI", "CP-SAT · QIGA · SHAP · XGBoost", PALETTE["purple"])
    node(5.5, 2.0, 3.2, 0.75, "Veri Katmanı", "PostgreSQL · Alembic · SQLAlchemy", PALETTE["warning"])
    ax.text(5.5, 0.65, "Aviation Digital Twin  v27.0",
            ha="center", fontsize=9.5, color=PALETTE["primary"], fontweight="bold")

    # Dış servisler (sağ)
    node(9.8, 5.2, 1.8, 0.75, "OpenSky ADS-B", "Gerçek zamanlı", PALETTE["secondary"])
    node(9.8, 4.0, 1.8, 0.75, "Open-Meteo", "Hava durumu", PALETTE["secondary"])
    node(9.8, 2.8, 1.8, 0.75, "NOAA METAR", "Havalimanı", PALETTE["secondary"])
    node(9.8, 1.6, 1.8, 0.75, "Prometheus\n+ Grafana", "İzleme", PALETTE["warning"])

    # Oklar
    for ay in [5.2, 3.5, 1.8]:
        arrow(2.1, ay, 3.7, 3.5, bidirectional=True)
    arrow(7.3, 5.3, 8.9, 5.2, "ADS-B")
    arrow(7.3, 4.2, 8.9, 4.0, "Meteo")
    arrow(7.3, 3.1, 8.9, 2.8, "METAR")
    arrow(7.3, 2.0, 8.9, 1.7)

    ax.set_title("Şekil 1.1 — Sistem Bağlam Diyagramı",
                 fontsize=13, fontweight="bold", color=PALETTE["text"], pad=14)
    save_mpl(fig, "fig_1_1_context.png", tight=False)


# ═══════════════════════════════════════════════════════════
# 2. Literatür Radar (Plotly)
# ═══════════════════════════════════════════════════════════
def fig_2_1_radar():
    categories = ["Optimalite", "Hız", "Açıklanabilirlik",
                  "Canlı Veri", "EASA Uyum", "Ölçek", "Optimalite"]
    fig = go.Figure()
    data = [
        ("Klasik MILP",  [9,2,5,2,5,7,9], PALETTE["warning"]),
        ("Deep RL",      [6,9,2,8,2,6,6], PALETTE["purple"]),
        ("Bu Tez (M)",   [8,7,9,8,8,6,8], PALETTE["success"]),
    ]
    for name, vals, color in data:
        fig.add_trace(go.Scatterpolar(
            r=vals, theta=categories, fill="toself",
            name=name, line=dict(color=color, width=2.5),
            fillcolor=hex_to_rgba(color, 0.12) if color.startswith("#") else color,
            opacity=0.85,
        ))
    fig.update_layout(
        **PLOTLY_TEMPLATE["layout"],
        polar=dict(
            bgcolor=PALETTE["surface"],
            radialaxis=dict(visible=True, range=[0,10], tickfont=dict(size=9)),
            angularaxis=dict(tickfont=dict(size=11, color=PALETTE["text"])),
        ),
        title=dict(text="Şekil 2.1 — Yaklaşım Karşılaştırması (Radar Analizi)", x=0.5),
        legend=dict(orientation="h", y=-0.12, font=dict(size=11)),
        showlegend=True,
    )
    save_plotly(fig, "fig_2_1_radar.png", w=700, h=600)


# ═══════════════════════════════════════════════════════════
# 3.1 DSR Metodoloji
# ═══════════════════════════════════════════════════════════
def fig_3_1_dsr():
    fig, ax = plt.subplots(figsize=(12, 4.5))
    ax.set_xlim(0, 12); ax.set_ylim(0, 4.5); ax.axis("off")
    ax.set_facecolor("white")

    phases = [
        (1.1,  "1", "Problem\nTanımı",    "IROPS & FTL\ntanımları",    PALETTE["danger"]),
        (3.2,  "2", "Hedef\nTanımı",      "RQ₁ & KPI\nsetleri",        PALETTE["warning"]),
        (5.4,  "3", "Tasarım &\nGeliştirme","CP-SAT+QIGA\nXAI+FastAPI",  PALETTE["primary"]),
        (7.6,  "4", "Demo &\nDeğerlendirme","Deneyler\np=0.007",         PALETTE["secondary"]),
        (9.8,  "5", "İletişim",            "TEKNOFEST\n2026 Sunumu",     PALETTE["purple"]),
    ]

    for cx, num, title, sub, color in phases:
        # Gölge + daire
        shadow = plt.Circle((cx+0.06, 2.25-0.06), 0.72, color="#00000015", zorder=1)
        circ   = plt.Circle((cx, 2.25), 0.72, color=color, zorder=3)
        ax.add_patch(shadow); ax.add_patch(circ)
        ax.text(cx, 2.5, num,  ha="center", va="center", fontsize=20,
                color="white", fontweight="bold", alpha=0.35, zorder=4)
        ax.text(cx, 2.2, title, ha="center", va="center", fontsize=8.5,
                color="white", fontweight="bold", zorder=5, multialignment="center")
        # Alt açıklama
        ax.text(cx, 0.9, sub, ha="center", va="center", fontsize=8,
                color=PALETTE["muted"], multialignment="center",
                bbox=dict(boxstyle="round,pad=0.25", fc=PALETTE["surface"],
                          ec=color, lw=1.0, alpha=0.9))
        # Üst bağlantı noktası
        if cx < 9.8:
            ax.annotate("", xy=(cx+1.08, 2.25), xytext=(cx+0.72, 2.25),
                        arrowprops=dict(arrowstyle="-|>", color=PALETTE["muted"],
                                       lw=1.8, mutation_scale=14), zorder=2)

    # Geri besleme oku
    ax.annotate("", xy=(1.1, 1.55), xytext=(9.8, 1.55),
                arrowprops=dict(arrowstyle="-|>", color=PALETTE["primary"],
                               lw=1.5, linestyle="dashed", mutation_scale=14,
                               connectionstyle="arc3,rad=0.0"))
    ax.text(5.5, 1.22, "İteratif Geri Besleme & Revizyon",
            ha="center", fontsize=9, color=PALETTE["primary"], style="italic")

    ax.set_title("Şekil 3.1 — DSR (Tasarım Bilimi Araştırması) Metodoloji Aşamaları",
                 fontsize=13, fontweight="bold", color=PALETTE["text"], pad=10)
    save_mpl(fig, "fig_3_1_dsr.png", tight=False)


# ═══════════════════════════════════════════════════════════
# 3.2 Test Piramidi
# ═══════════════════════════════════════════════════════════
def fig_3_2_test_pyramid():
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.axis("off")
    ax.set_facecolor("white")

    levels = [
        (5, 0.7, 9.0, 0.95, PALETTE["success"],
         "Birim Testleri — 62 test",  "test_core · test_solver · test_models · test_live_sync"),
        (5, 2.2, 6.5, 0.95, PALETTE["warning"],
         "Entegrasyon Testleri",      "test_integration · test_audit_flow · circuit breaker"),
        (5, 3.7, 4.2, 0.95, PALETTE["primary"],
         "API / Auth Testleri",       "test_auth_api · httpx AsyncClient"),
        (5, 5.1, 2.2, 0.85, PALETTE["danger"],
         "E2E (planlanan)",           "Playwright UI akışı"),
    ]
    for cx, cy, w, h, color, title, sub in levels:
        left = cx - w/2 - 0.02
        pts = [(left+0.35, cy-h/2), (left+w-0.35, cy-h/2),
               (left+w+0.2,  cy+h/2), (left-0.2,   cy+h/2)]
        from matplotlib.patches import Polygon as MPoly
        poly = MPoly(pts, closed=True, facecolor=color, alpha=0.88,
                     edgecolor="white", linewidth=1.5, zorder=3)
        shadow = MPoly([(x+0.05, y-0.05) for x,y in pts], closed=True,
                       facecolor="#00000012", zorder=2)
        ax.add_patch(shadow); ax.add_patch(poly)
        ax.text(cx, cy+0.14, title, ha="center", va="center",
                fontsize=9, color="white", fontweight="bold", zorder=4)
        ax.text(cx, cy-0.2, sub, ha="center", va="center",
                fontsize=7.5, color="white", alpha=0.9, zorder=4)

    # Etiketler
    for y, label in [(0.7,"Çok / Hızlı"), (5.1,"Az / Yavaş")]:
        ax.text(9.6, y, label, ha="center", va="center", fontsize=8,
                color=PALETTE["muted"], rotation=90)
    ax.annotate("", xy=(9.6, 5.7), xytext=(9.6, 0.2),
                arrowprops=dict(arrowstyle="-|>", color=PALETTE["muted"],
                               lw=1.3, mutation_scale=11))
    ax.text(9.9, 3.0, "Maliyet", ha="left", fontsize=8.5,
            color=PALETTE["muted"], rotation=90)

    ax.set_title("Şekil 3.2 — Test Piramidi", fontsize=13,
                 fontweight="bold", color=PALETTE["text"], pad=10)
    save_mpl(fig, "fig_3_2_test_pyramid.png", tight=False)


# ═══════════════════════════════════════════════════════════
# 4.1 6 Katmanlı Mimari
# ═══════════════════════════════════════════════════════════
def fig_4_1_architecture():
    fig, ax = plt.subplots(figsize=(11, 7.5))
    ax.set_xlim(0, 11); ax.set_ylim(0, 7.5); ax.axis("off")
    ax.set_facecolor("white")

    layers = [
        (6.5,  "Katman 6 — Kullanıcı Arayüzü",
         "Three.js 3D  ·  MapLibre GL  ·  Chart.js  ·  Dispatcher Dashboard",
         PALETTE["primary"],   "#DBEAFE"),
        (5.3,  "Katman 5 — API Gateway",
         "FastAPI  ·  JWT Bearer  ·  RBAC  ·  AuditMiddleware  ·  Rate Limit",
         PALETTE["secondary"], "#CCFBF1"),
        (4.1,  "Katman 4 — İş Mantığı",
         "CP-SAT Solver  ·  QIGA  ·  XAI Engine (SHAP/Bayesian)  ·  XGBoost Forecast",
         PALETTE["purple"],    "#EDE9FE"),
        (2.9,  "Katman 3 — Veri Katmanı",
         "SQLAlchemy 2.x  ·  Alembic  ·  PostgreSQL 15  /  SQLite",
         PALETTE["warning"],   "#FEF3C7"),
        (1.7,  "Katman 2 — Canlı Entegrasyon",
         "OpenSky ADS-B  ·  Open-Meteo  ·  NOAA METAR  ·  Circuit Breaker",
         "#0369A1",            "#E0F2FE"),
        (0.5,  "Katman 1 — Altyapı & İzleme",
         "Docker Compose  ·  Caddy TLS  ·  Prometheus  ·  Loki  ·  Grafana",
         PALETTE["slate"],     "#F1F5F9"),
    ]
    for y_mid, title, sub, accent, bg in layers:
        r = FancyBboxPatch((0.25, y_mid-0.52), 10.5, 1.04,
                           boxstyle="round,pad=0.1", linewidth=1.5,
                           edgecolor=accent, facecolor=bg, zorder=2)
        shadow = FancyBboxPatch((0.31, y_mid-0.58), 10.5, 1.04,
                                boxstyle="round,pad=0.1", linewidth=0,
                                facecolor="#00000010", zorder=1)
        ax.add_patch(shadow); ax.add_patch(r)
        # Renkli sol şerit
        bar = FancyBboxPatch((0.25, y_mid-0.52), 0.18, 1.04,
                             boxstyle="square,pad=0", linewidth=0,
                             facecolor=accent, zorder=3)
        ax.add_patch(bar)
        ax.text(0.65, y_mid+0.15, title, fontsize=10, fontweight="bold",
                color=PALETTE["text"], va="center")
        ax.text(0.65, y_mid-0.2, sub, fontsize=8.5, color=PALETTE["muted"], va="center")

    # Çift yönlü oklar
    for y in [1.21, 2.41, 3.61, 4.81, 5.97]:
        ax.annotate("", xy=(5.5, y+0.1), xytext=(5.5, y-0.1),
                    arrowprops=dict(arrowstyle="<|-|>", color=PALETTE["muted"],
                                   lw=1.4, mutation_scale=10), zorder=5)

    ax.set_title("Şekil 4.1 — 6 Katmanlı Sistem Mimarisi",
                 fontsize=13, fontweight="bold", color=PALETTE["text"], pad=10)
    save_mpl(fig, "fig_4_1_architecture.png", tight=False)


# ═══════════════════════════════════════════════════════════
# 4.2 Auth Flow
# ═══════════════════════════════════════════════════════════
def fig_4_2_auth_flow():
    fig = go.Figure()
    # Sequence diagram benzeri Sankey
    # Basit flow şeması olarak çiz — matplotlib daha uygun
    plt.close("all")
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.set_xlim(0, 11); ax.set_ylim(0, 5); ax.axis("off")
    ax.set_facecolor("white")

    def rbox(cx, cy, w, h, text, color, tc="white", alpha=1.0):
        s = FancyBboxPatch((cx-w/2+0.05, cy-h/2-0.05), w, h,
                           boxstyle="round,pad=0.1", facecolor="#00000015",
                           linewidth=0, zorder=2)
        r = FancyBboxPatch((cx-w/2, cy-h/2), w, h,
                           boxstyle="round,pad=0.1", facecolor=color,
                           edgecolor="white", linewidth=0, alpha=alpha, zorder=3)
        ax.add_patch(s); ax.add_patch(r)
        ax.text(cx, cy, text, ha="center", va="center", fontsize=8.5,
                color=tc, fontweight="bold", zorder=4, multialignment="center")

    def arr(x1, y1, x2, y2, lbl="", color=PALETTE["muted"]):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color=color,
                                   lw=1.5, mutation_scale=13))
        if lbl:
            ax.text((x1+x2)/2, (y1+y2)/2+0.2, lbl, ha="center",
                    fontsize=7.5, color=color, style="italic",
                    bbox=dict(boxstyle="round,pad=0.15", fc="white",
                              ec=PALETTE["border"], alpha=0.85))

    rbox(1.1, 4.0, 1.8, 0.7, "Kullanıcı\n(Tarayıcı)", PALETTE["slate"])
    rbox(3.2, 4.0, 2.0, 0.7, "POST /auth\n/jwt/login", PALETTE["primary"])
    rbox(5.6, 4.0, 2.2, 0.7, "fastapi-users\nbcrypt doğrula", PALETTE["secondary"])
    rbox(8.2, 4.0, 1.8, 0.7, "JWT Token\n(24 saat)", PALETTE["success"])

    rbox(3.2, 2.2, 2.0, 0.7, "Korunan\nEndpoint", PALETTE["primary"])
    rbox(5.6, 2.2, 2.2, 0.7, "require_role()\nKontrolü", PALETTE["warning"])
    rbox(8.2, 2.2, 1.8, 0.7, "İş Mantığı\n(Solver vb.)", PALETTE["success"])
    rbox(5.6, 0.65, 2.2, 0.65, "403 Forbidden", PALETTE["danger"])

    arr(2.0, 4.0, 2.2, 4.0, "kimlik")
    arr(4.2, 4.0, 4.5, 4.0)
    arr(6.7, 4.0, 7.3, 4.0, "JWT")
    arr(1.1, 3.65, 3.2, 2.55, "Bearer Token")
    arr(4.2, 2.2, 4.5, 2.2)
    ax.annotate("", xy=(7.3, 2.2), xytext=(6.7, 2.2),
                arrowprops=dict(arrowstyle="-|>", color=PALETTE["success"], lw=1.5, mutation_scale=13))
    ax.text(7.0, 2.55, "Evet", fontsize=8, color=PALETTE["success"])
    ax.annotate("", xy=(5.6, 0.98), xytext=(5.6, 1.85),
                arrowprops=dict(arrowstyle="-|>", color=PALETTE["danger"], lw=1.5, mutation_scale=13))
    ax.text(5.85, 1.4, "Hayır", fontsize=8, color=PALETTE["danger"])

    # Rol kutusu
    ax.text(5.5, -0.05,
            "viewer → sadece okuma    ·    operator → solver + export    ·    admin → tam yetki",
            ha="center", fontsize=9, color=PALETTE["text"],
            bbox=dict(boxstyle="round,pad=0.3", fc="#EFF6FF", ec=PALETTE["primary"], lw=1.2))

    ax.set_title("Şekil 4.2 — JWT Kimlik Doğrulama ve RBAC Akışı",
                 fontsize=13, fontweight="bold", color=PALETTE["text"], pad=10)
    save_mpl(fig, "fig_4_2_auth_flow.png", tight=False)


# ═══════════════════════════════════════════════════════════
# 4.3 Docker Topolojisi
# ═══════════════════════════════════════════════════════════
def fig_4_3_docker_topology():
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.set_xlim(0, 11); ax.set_ylim(0, 6); ax.axis("off")
    ax.set_facecolor("white")

    def sbox(cx, cy, w, h, title, sub, color, bg):
        s = FancyBboxPatch((cx-w/2+0.05, cy-h/2-0.05), w, h,
                           boxstyle="round,pad=0.1", facecolor="#00000015",
                           linewidth=0, zorder=2)
        r = FancyBboxPatch((cx-w/2, cy-h/2), w, h,
                           boxstyle="round,pad=0.1", facecolor=bg,
                           edgecolor=color, linewidth=1.5, zorder=3)
        ax.add_patch(s); ax.add_patch(r)
        ax.text(cx, cy+0.12, title, ha="center", va="center", fontsize=9.5,
                color=color, fontweight="bold", zorder=4)
        ax.text(cx, cy-0.2, sub, ha="center", va="center",
                fontsize=8, color=PALETTE["muted"], zorder=4)

    def conn(x1, y1, x2, y2, lbl="", color=PALETTE["muted"]):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color=color,
                                   lw=1.4, mutation_scale=12))
        if lbl:
            ax.text((x1+x2)/2+0.08, (y1+y2)/2+0.15, lbl,
                    fontsize=7.5, color=color, style="italic")

    sbox(1.5, 5.2, 2.2, 0.8, "Internet", "Kullanıcılar / Tarayıcı", PALETTE["slate"], "#F8FAFC")
    sbox(1.5, 3.7, 2.2, 0.8, "caddy", ":443 TLS termination", PALETTE["muted"], "#F1F5F9")
    sbox(5.5, 3.7, 2.4, 0.8, "api", "uvicorn :8501", PALETTE["primary"], "#DBEAFE")
    sbox(9.2, 3.7, 2.2, 0.8, "postgres", ":5432 · DB", PALETTE["secondary"], "#CCFBF1")
    sbox(3.5, 1.6, 2.2, 0.8, "prometheus", ":9090", PALETTE["warning"], "#FEF3C7")
    sbox(6.2, 1.6, 2.2, 0.8, "loki", ":3100 · Logs", PALETTE["warning"], "#FEF3C7")
    sbox(9.2, 1.6, 2.2, 0.8, "grafana", ":3000 · UI", "#DC2626", "#FEE2E2")

    conn(1.5, 4.8, 1.5, 4.1)
    conn(2.6, 3.7, 4.3, 3.7, "reverse proxy")
    conn(6.7, 3.7, 8.1, 3.7, "SQL / async")
    conn(5.5, 3.3, 3.8, 2.0, "metrics scrape")
    conn(5.5, 3.3, 6.2, 2.0, "log push")
    conn(7.3, 1.6, 8.1, 1.6)
    conn(9.2, 3.3, 9.2, 2.0, "health")

    # Network sınırı
    net = FancyBboxPatch((2.9, 1.1), 6.8, 3.2,
                         boxstyle="round,pad=0.1", facecolor="none",
                         edgecolor=PALETTE["primary"], linewidth=1.5, linestyle="--", zorder=1)
    ax.add_patch(net)
    ax.text(6.3, 0.82, "Docker Network — aviation_net (bridge)",
            ha="center", fontsize=8.5, color=PALETTE["primary"],
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=PALETTE["primary"], lw=1))
    ax.text(0.3, 0.5,
            "Volumes: postgres_data  ·  prometheus_data  ·  grafana_data",
            fontsize=8, color=PALETTE["muted"])

    ax.set_title("Şekil 4.3 — Docker Compose Servis Topolojisi",
                 fontsize=13, fontweight="bold", color=PALETTE["text"], pad=10)
    save_mpl(fig, "fig_4_3_docker_topology.png", tight=False)


# ═══════════════════════════════════════════════════════════
# 5.1 Kısıt Grafiği
# ═══════════════════════════════════════════════════════════
def fig_5_1_constraint_graph():
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.axis("off")
    ax.set_facecolor("white")

    var_nodes = [
        (1.5, 5.2, "y_j",   "İptal kararı",       PALETTE["primary"]),
        (1.5, 3.8, "d_j",   "Gecikme (dk)",        PALETTE["primary"]),
        (1.5, 2.4, "x_ij",  "Uçak atama",          PALETTE["purple"]),
        (1.5, 1.0, "z_ij",  "Kapı atama",          PALETTE["purple"]),
    ]
    con_nodes = [
        (7.5, 5.4, "C₁", "Zaman Penceresi",    PALETTE["danger"]),
        (7.5, 4.4, "C₂", "Tek Uçak / Uçuş",   PALETTE["danger"]),
        (7.5, 3.4, "C₃", "EASA FTL Tavanı",    PALETTE["danger"]),
        (7.5, 2.4, "C₄", "Kapı Çakışması",     PALETTE["warning"]),
        (7.5, 1.4, "C₅", "Slot Kapasitesi",    PALETTE["warning"]),
        (4.5, 0.4, "OBJ","Objective Fonksiyon", PALETTE["success"]),
    ]

    for cx, cy, sym, label, color in var_nodes:
        circ = plt.Circle((cx, cy), 0.5, color=color, zorder=3)
        shadow = plt.Circle((cx+0.06, cy-0.06), 0.5, color="#00000018", zorder=2)
        ax.add_patch(shadow); ax.add_patch(circ)
        ax.text(cx, cy+0.08, sym, ha="center", va="center",
                fontsize=10, color="white", fontweight="bold", zorder=4)
        ax.text(cx+0.7, cy, label, va="center", fontsize=8.5, color=PALETTE["muted"])

    for cx, cy, sym, label, color in con_nodes:
        if sym == "OBJ":
            r = FancyBboxPatch((cx-1.2, cy-0.35), 2.4, 0.7,
                               boxstyle="round,pad=0.1", facecolor=color,
                               edgecolor="white", linewidth=0, zorder=3)
        else:
            r = FancyBboxPatch((cx-1.2, cy-0.35), 2.4, 0.7,
                               boxstyle="round,pad=0.1", facecolor=color,
                               edgecolor="white", linewidth=0, alpha=0.9, zorder=3)
        shadow = FancyBboxPatch((cx-1.14, cy-0.41), 2.4, 0.7,
                                boxstyle="round,pad=0.1", facecolor="#00000015",
                                linewidth=0, zorder=2)
        ax.add_patch(shadow); ax.add_patch(r)
        ax.text(cx-0.8, cy, sym, ha="center", va="center",
                fontsize=9, color="white", fontweight="bold", zorder=4)
        ax.text(cx+0.15, cy, label, va="center",
                fontsize=8.5, color="white", zorder=4)

    edges = [
        (0,0,0.5),(0,1,0.3),(0,2,0.4),(0,4,0.4),
        (1,0,0.3),(1,2,0.4),(1,4,0.3),
        (2,1,0.3),(2,2,0.4),(2,3,0.3),
        (3,3,0.3),(3,4,0.3),
    ]
    for vi, ci, alpha in edges:
        vx, vy = var_nodes[vi][0]+0.5, var_nodes[vi][1]
        cx2, cy2 = con_nodes[ci][0]-1.2, con_nodes[ci][1]
        ax.plot([vx, cx2], [vy, cy2], color=PALETTE["muted"],
                lw=1.2, alpha=alpha, zorder=1)

    # Tüm değişkenler → OBJ
    for vx, vy, _, _, _ in var_nodes:
        ax.plot([vx+0.5, 4.5-1.2], [vy, 0.4], color=PALETTE["success"],
                lw=1.0, alpha=0.4, linestyle="--", zorder=1)

    ax.text(1.5, 5.9, "Karar Değişkenleri",
            ha="center", fontsize=10, fontweight="bold", color=PALETTE["primary"])
    ax.text(7.5, 6.0, "Kısıtlar",
            ha="center", fontsize=10, fontweight="bold", color=PALETTE["danger"])
    ax.text(4.5, 1.0, "Amaç Fonksiyonu",
            ha="center", fontsize=10, fontweight="bold", color=PALETTE["success"])

    ax.set_title("Şekil 5.1 — Karar Değişkeni–Kısıt İlişki Grafiği",
                 fontsize=13, fontweight="bold", color=PALETTE["text"], pad=10)
    save_mpl(fig, "fig_5_1_constraint_graph.png", tight=False)


# ═══════════════════════════════════════════════════════════
# 5.2 QIGA
# ═══════════════════════════════════════════════════════════
def fig_5_2_qiga():
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.set_xlim(0, 9); ax.set_ylim(0, 7); ax.axis("off")
    ax.set_facecolor("white")

    def rbox(cx, cy, w, h, text, color, tc="white"):
        s = FancyBboxPatch((cx-w/2+0.05, cy-h/2-0.05), w, h,
                           boxstyle="round,pad=0.12", facecolor="#00000015",
                           linewidth=0, zorder=2)
        r = FancyBboxPatch((cx-w/2, cy-h/2), w, h,
                           boxstyle="round,pad=0.12", facecolor=color,
                           edgecolor="white", linewidth=0, zorder=3)
        ax.add_patch(s); ax.add_patch(r)
        ax.text(cx, cy, text, ha="center", va="center", fontsize=9,
                color=tc, fontweight="bold", zorder=4, multialignment="center")

    def arr(x1, y1, x2, y2, lbl="", color=PALETTE["muted"]):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color=color,
                                   lw=1.6, mutation_scale=14))
        if lbl:
            ax.text((x1+x2)/2+0.1, (y1+y2)/2+0.15, lbl,
                    fontsize=8, color=color)

    rbox(4.5, 6.3, 3.4, 0.75, "CP-SAT Warm-Start Çözümü", PALETTE["secondary"])
    rbox(4.5, 5.1, 3.4, 0.75, "Kuantum Popülasyon Başlat\n(50 birey · α²+β²=1)", PALETTE["primary"])
    rbox(4.5, 3.9, 3.4, 0.75, "Q-bit Ölçümü → 0/1 Çözüm", PALETTE["purple"])
    rbox(4.5, 2.7, 3.4, 0.75, "Fitness = Objective − FTL Cezası", PALETTE["warning"])
    rbox(4.5, 1.6, 2.0, 0.65, "Durdurma?\n(n=100 / erken dur)", "#FEF3C7", PALETTE["text"])
    rbox(1.8, 1.6, 2.0, 0.65, "Global Best\nGüncelle", PALETTE["success"])
    rbox(7.2, 1.6, 2.0, 0.65, "Q-gate Rotasyonu\nΔθ = 0.05π", PALETTE["primary"])
    rbox(4.5, 0.5, 2.8, 0.65, "Çıktı: İyileştirilmiş Uçuş Planı", PALETTE["slate"])

    arr(4.5, 5.93, 4.5, 5.48)
    arr(4.5, 4.73, 4.5, 4.28)
    arr(4.5, 3.53, 4.5, 3.08)
    arr(4.5, 2.33, 4.5, 1.93)
    arr(3.5, 1.6, 2.8, 1.6, "Hayır")
    arr(5.5, 1.6, 6.2, 1.6)
    arr(4.5, 1.28, 4.5, 0.83, "Evet", PALETTE["success"])
    ax.annotate("", xy=(4.5, 3.9), xytext=(7.2, 1.93),
                arrowprops=dict(arrowstyle="-|>", color=PALETTE["primary"],
                               lw=1.5, mutation_scale=13,
                               connectionstyle="arc3,rad=-0.4"))

    ax.set_title("Şekil 5.2 — QIGA Evrim Akışı",
                 fontsize=13, fontweight="bold", color=PALETTE["text"], pad=10)
    save_mpl(fig, "fig_5_2_qiga.png", tight=False)


# ═══════════════════════════════════════════════════════════
# 6.1 XAI Workflow
# ═══════════════════════════════════════════════════════════
def fig_6_1_xai_workflow():
    fig, ax = plt.subplots(figsize=(13, 5.5))
    ax.set_xlim(0, 13); ax.set_ylim(0, 5.5); ax.axis("off")
    ax.set_facecolor("white")

    def stage(cx, cy, w, h, title, sub, color, bg):
        s = FancyBboxPatch((cx-w/2+0.05, cy-h/2-0.05), w, h,
                           boxstyle="round,pad=0.1", facecolor="#00000018",
                           linewidth=0, zorder=2)
        r = FancyBboxPatch((cx-w/2, cy-h/2), w, h,
                           boxstyle="round,pad=0.1", facecolor=bg,
                           edgecolor=color, linewidth=1.8, zorder=3)
        ax.add_patch(s); ax.add_patch(r)
        ax.text(cx, cy+0.15, title, ha="center", va="center",
                fontsize=9.5, color=color, fontweight="bold", zorder=4)
        ax.text(cx, cy-0.25, sub, ha="center", va="center",
                fontsize=8, color=PALETTE["muted"], zorder=4, multialignment="center")

    def arr(x1, y1, x2, y2, lbl=""):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color=PALETTE["muted"],
                                   lw=1.6, mutation_scale=14))
        if lbl:
            ax.text((x1+x2)/2, (y1+y2)/2+0.22, lbl, ha="center",
                    fontsize=7.5, color=PALETTE["muted"], style="italic")

    stage(1.2, 2.8, 2.0, 1.4, "Canlı Veri",
          "ADS-B · METAR\nOpenSky · NOAA", PALETTE["secondary"], "#CCFBF1")
    stage(3.6, 2.8, 2.0, 1.4, "Senaryo\nÜretici",
          "AdvancedAirline\nSimulator", PALETTE["primary"], "#DBEAFE")
    stage(6.0, 2.8, 2.0, 1.4, "CP-SAT\n+ QIGA",
          "Hibrit Çözücü\n60s · 1.7% gap", PALETTE["purple"], "#EDE9FE")
    stage(8.4, 2.8, 2.0, 1.4, "Karar\nMotoru",
          "FTL · decision\nreason kodu", PALETTE["warning"], "#FEF3C7")

    # XAI sütunu
    stage(11.0, 4.5, 2.0, 0.9, "SHAP Waterfall",  "Özellik etkileri", PALETTE["success"], "#F0FDF4")
    stage(11.0, 3.1, 2.0, 0.9, "Bayesian DAG",    "Nedensel atıf",    PALETTE["success"], "#F0FDF4")
    stage(11.0, 1.7, 2.0, 0.9, "Counterfactual",  "\"Ya olsaydı?\"",  PALETTE["success"], "#F0FDF4")

    arr(2.2, 2.8, 2.6, 2.8, "TTL cache")
    arr(4.6, 2.8, 5.0, 2.8)
    arr(7.0, 2.8, 7.4, 2.8)
    arr(9.4, 3.4, 10.0, 4.5)
    arr(9.4, 2.8, 10.0, 3.1)
    arr(9.4, 2.2, 10.0, 1.7)

    # Çıktı
    ax.text(11.0, 0.8, "UI · PDF · XLSX · Audit Log",
            ha="center", fontsize=9, color=PALETTE["text"],
            bbox=dict(boxstyle="round,pad=0.3", fc=PALETTE["surface"],
                      ec=PALETTE["primary"], lw=1.5))
    for y in [4.5, 3.1, 1.7]:
        ax.annotate("", xy=(11.0, 1.13), xytext=(11.0, y-0.45),
                    arrowprops=dict(arrowstyle="-", color=PALETTE["success"],
                                   lw=1.0, linestyle="dotted"))

    ax.set_title("Şekil 6.1 — XAI Karar Açıklama İş Akışı",
                 fontsize=13, fontweight="bold", color=PALETTE["text"], pad=10)
    save_mpl(fig, "fig_6_1_xai_workflow.png", tight=False)


# ═══════════════════════════════════════════════════════════
# 6.2 Pipeline
# ═══════════════════════════════════════════════════════════
def fig_6_2_pipeline():
    fig = go.Figure()
    stages = ["Ham Veri", "Özellik\nMühendisliği", "XGBoost\nForecast",
              "CP-SAT\nÇözücü", "QIGA\nİyileştirici", "XAI\nKatmanı", "Çıktı"]
    colors_hex = [PALETTE["secondary"], PALETTE["primary"], PALETTE["purple"],
                  "#1E3A5F", PALETTE["purple"], PALETTE["success"], PALETTE["slate"]]
    fig = go.Figure(go.Funnel(
        y=stages, x=[100, 92, 88, 85, 83, 80, 78],
        textinfo="label",
        marker=dict(color=colors_hex, line=dict(width=1, color="white")),
        connector=dict(line=dict(color=PALETTE["muted"], width=1, dash="dot")),
        opacity=0.9,
    ))
    fig.update_layout(
        **PLOTLY_TEMPLATE["layout"],
        title=dict(text="Şekil 6.2 — Tam AI/ML Karar Boru Hattı", x=0.5),
    )
    save_plotly(fig, "fig_6_2_pipeline.png", w=750, h=520)


# ═══════════════════════════════════════════════════════════
# 7.1 Proje Ağacı
# ═══════════════════════════════════════════════════════════
def fig_7_1_project_tree():
    fig, ax = plt.subplots(figsize=(10, 7.5))
    ax.set_xlim(0, 10); ax.set_ylim(0, 7.5); ax.axis("off")
    ax.set_facecolor("white")

    tree = [
        (0.2, 7.1, "havayolu_optimizasyonu_2026/", "#111827", True, 12),
        (0.5, 6.65, "src/",                         PALETTE["primary"], True, 11),
        (0.85,6.25, "api/",                          PALETTE["primary"], False, 9.5),
        (1.2, 5.95, "main.py  ·  exporters.py",      PALETTE["muted"],  False, 8.5),
        (0.85,5.60, "optimizer/",                    PALETTE["purple"], False, 9.5),
        (1.2, 5.30, "dt_solver.py  ·  hybrid_ga.py  ·  recovery.py", PALETTE["muted"], False, 8.5),
        (0.85,4.95, "db/",                           PALETTE["warning"],False, 9.5),
        (1.2, 4.65, "models.py  ·  config.py  ·  middleware.py  ·  migrations/", PALETTE["muted"], False, 8.5),
        (0.85,4.30, "analytics/ · models/ · data_connectors/ · generator/ · web/",PALETTE["secondary"],False, 9.0),
        (0.5, 3.80, "tests/",                        PALETTE["success"], True, 11),
        (0.85,3.45, "conftest.py  ·  test_core.py  ·  test_solver.py", PALETTE["muted"], False, 8.5),
        (0.85,3.10, "test_integration.py  ·  test_auth_api.py  ·  test_audit_flow.py", PALETTE["muted"], False, 8.5),
        (0.5, 2.65, "deploy/",                       PALETTE["warning"], True, 11),
        (0.85,2.30, "prod_up.sh  ·  db_backup.sh  ·  monitoring/",  PALETTE["muted"], False, 8.5),
        (0.5, 1.85, "docs/thesis/",                  PALETTE["danger"],  True, 11),
        (0.85,1.50, "00-11_bolum.md  ·  ekler/  ·  gorseller/  ·  *.pdf  ·  *.docx", PALETTE["muted"], False, 8.5),
        (0.5, 1.00, "Dockerfile  ·  docker-compose.yml  ·  pyproject.toml", PALETTE["slate"], False, 9),
        (0.5, 0.60, "Caddyfile  ·  alembic.ini  ·  Makefile  ·  requirements.txt", PALETTE["slate"], False, 9),
    ]

    for x, y, text, color, bold, fs in tree:
        ax.text(x, y, text, fontsize=fs, color=color,
                fontweight="bold" if bold else "normal",
                fontfamily="DejaVu Sans Mono")

    # Sağ stats
    stats = [
        ("Python satır", "~4,500"),
        ("Test sayısı",  "62"),
        ("API endpoint", "27"),
        ("Tez sayfası",  "~150"),
        ("Görsel",       "28"),
        ("Commit",       "10+"),
    ]
    ax.text(7.2, 7.2, "Proje İstatistikleri",
            fontsize=10, fontweight="bold", color=PALETTE["primary"])
    for i, (k, v) in enumerate(stats):
        y = 6.7 - i*0.58
        ax.add_patch(FancyBboxPatch((6.9, y-0.22), 2.8, 0.44,
                                    boxstyle="round,pad=0.08",
                                    facecolor=PALETTE["surface"],
                                    edgecolor=PALETTE["border"], lw=1))
        ax.text(7.1, y, k, fontsize=8.5, color=PALETTE["muted"], va="center")
        ax.text(9.5, y, v, fontsize=9, color=PALETTE["primary"],
                fontweight="bold", va="center", ha="right")

    ax.set_title("Şekil 7.1 — Proje Dizin Yapısı ve İstatistikler",
                 fontsize=13, fontweight="bold", color=PALETTE["text"], pad=10)
    save_mpl(fig, "fig_7_1_project_tree.png", tight=False)


# ═══════════════════════════════════════════════════════════
# 7.2 Circuit Breaker
# ═══════════════════════════════════════════════════════════
def fig_7_2_circuit_breaker():
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.set_xlim(0, 10); ax.set_ylim(0, 5.5); ax.axis("off")
    ax.set_facecolor("white")

    def state_node(cx, cy, r, label, sub, color, bg):
        shadow = plt.Circle((cx+0.08, cy-0.08), r, color="#00000018", zorder=1)
        circ = plt.Circle((cx, cy), r, color=bg, zorder=2,
                          linewidth=2.5, fill=True)
        ring = plt.Circle((cx, cy), r, color=color, zorder=3,
                          linewidth=2.5, fill=False)
        ax.add_patch(shadow); ax.add_patch(circ); ax.add_patch(ring)
        ax.text(cx, cy+0.2, label, ha="center", va="center",
                fontsize=11, color=color, fontweight="bold", zorder=4)
        ax.text(cx, cy-0.35, sub, ha="center", va="center",
                fontsize=8, color=color, alpha=0.85, zorder=4, multialignment="center")

    state_node(1.8, 3.0, 1.0, "CLOSED", "Normal\nOPerasyon", PALETTE["success"], "#F0FDF4")
    state_node(8.2, 3.0, 1.0, "OPEN", "Tüm\nİstekler Bloke", PALETTE["danger"], "#FEF2F2")
    state_node(5.0, 4.8, 0.85, "HALF\nOPEN", "Test İsteği\nGönder", PALETTE["warning"], "#FFFBEB")

    def curved_arrow(x1, y1, x2, y2, rad, label, color, lbl_off=(0, 0.25)):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=2.0,
                                   mutation_scale=15,
                                   connectionstyle=f"arc3,rad={rad}"))
        mx = (x1+x2)/2 + lbl_off[0]; my = (y1+y2)/2 + lbl_off[1]
        ax.text(mx, my, label, ha="center", fontsize=8.5, color=color, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=color, lw=1.0, alpha=0.9))

    curved_arrow(2.7, 3.3, 7.1, 3.3, -0.4, "5 ardışık hata", PALETTE["danger"], (0, -0.55))
    curved_arrow(7.3, 3.6, 5.7, 4.4, 0.2,  "reset_timeout = 60s", PALETTE["warning"])
    curved_arrow(4.2, 4.4, 2.5, 3.8, 0.2,  "Test başarılı ✓", PALETTE["success"])
    curved_arrow(5.9, 4.4, 7.5, 3.8, -0.2, "Test başarısız ✗", PALETTE["danger"])

    # Fallback
    ax.add_patch(FancyBboxPatch((2.5, 0.3), 5.0, 0.75,
                                boxstyle="round,pad=0.12",
                                facecolor="#FFFBEB", edgecolor=PALETTE["warning"], lw=1.5))
    ax.text(5.0, 0.68, "Fallback: Sentetik / cache veri döndür",
            ha="center", fontsize=9.5, color=PALETTE["warning"], fontweight="bold")
    ax.text(5.0, 0.43, "Fallback oranı < %2  ·  OPEN durumda tüm istekler yönlenir",
            ha="center", fontsize=8, color=PALETTE["muted"])
    ax.annotate("", xy=(5.0, 1.05), xytext=(8.2, 2.0),
                arrowprops=dict(arrowstyle="-|>", color=PALETTE["warning"],
                               lw=1.3, linestyle="dashed", mutation_scale=11))

    ax.set_title("Şekil 7.2 — Circuit Breaker Durum Makinesi (pybreaker)",
                 fontsize=13, fontweight="bold", color=PALETTE["text"], pad=10)
    save_mpl(fig, "fig_7_2_circuit_breaker.png", tight=False)


# ═══════════════════════════════════════════════════════════
# 8.1 CP-SAT Yakınsama
# ═══════════════════════════════════════════════════════════
def fig_8_1_convergence():
    t = np.array([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60])
    upper = np.array([800, 778, 765, 758, 754, 751, 749, 748, 747, 747, 747, 747, 747])
    lower = np.array([400, 420, 480, 530, 580, 610, 630, 645, 655, 662, 665, 666, 666])

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.fill_between(t, lower, upper, alpha=0.10, color=PALETTE["primary"])
    ax.plot(t, upper, color=PALETTE["primary"], lw=2.5, label="En iyi feasible çözüm")
    ax.plot(t, lower, color=PALETTE["success"], lw=2.5,
            linestyle="--", label="En iyi lower bound")

    for ts, gap, va_ in [(5, 38, "top"), (15, 12, "top"), (30, 3.4, "bottom"), (60, 2.1, "bottom")]:
        idx = list(t).index(ts)
        mid = (upper[idx] + lower[idx]) / 2
        ax.annotate(f" %{gap} gap", xy=(ts, mid), fontsize=9, color=PALETTE["text"],
                    ha="left", va=va_,
                    bbox=dict(boxstyle="round,pad=0.3", fc="white",
                              ec=PALETTE["border"], lw=1.0, alpha=0.92))

    ax.set_xlabel("Süre (saniye)", fontsize=11)
    ax.set_ylabel("Objective Değeri (bin TL)", fontsize=11)
    ax.set_title("Şekil 8.1 — CP-SAT Solver Yakınsama Eğrisi\n"
                 "(150 uçuş, 10 koşu ortalaması, zaman sınırı 60s)", fontsize=12)
    ax.legend(fontsize=10, framealpha=0.9)
    ax.set_xlim(0, 60); ax.set_ylim(350, 830)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}k"))
    sns.despine(ax=ax, trim=True)
    save_mpl(fig, "fig_8_1_convergence.png")


# ═══════════════════════════════════════════════════════════
# 8.2 İptal Oranı (Grouped Bar — Plotly)
# ═══════════════════════════════════════════════════════════
def fig_8_2_cancellation():
    scenarios = ["Normal", "Hava Kapanması", "Mürettebat\nGrevi %20", "Kapı\nKıtlığı", "Birleşik Stres"]
    data = {
        "B₁ Greedy": [12, 28, 34, 19, 47],
        "B₂ CP-SAT": [ 4, 14, 22,  9, 31],
        "B₃ QIGA":   [ 5, 18, 19, 12, 33],
        "M Hibrit":  [ 3, 11, 15,  8, 24],
    }
    colors = [PALETTE["danger"], PALETTE["warning"], PALETTE["purple"], PALETTE["success"]]

    fig = go.Figure()
    for (name, vals), color in zip(data.items(), colors):
        fig.add_trace(go.Bar(
            name=name, x=scenarios, y=vals,
            marker_color=color, marker_line_width=0,
            opacity=0.88, text=vals, textposition="outside",
            textfont=dict(size=10),
        ))
    fig.update_layout(
        **PLOTLY_TEMPLATE["layout"],
        barmode="group",
        title=dict(text="Şekil 8.2 — Stres Senaryolarında İptal Oranı Karşılaştırması (%)", x=0.5),
        yaxis_title="İptal Oranı (%)",
        xaxis_title="Senaryo",
        legend=dict(orientation="h", y=-0.22, font=dict(size=11)),
    )
    fig.update_layout(margin=dict(l=60, r=40, t=70, b=110))
    fig.update_yaxes(range=[0, 60])
    fig.update_xaxes(tickangle=-20)
    save_plotly(fig, "fig_8_2_cancellation.png", w=980, h=540)


# ═══════════════════════════════════════════════════════════
# 8.3 SHAP Önem (seaborn)
# ═══════════════════════════════════════════════════════════
def fig_8_3_shap():
    features = ["weather_risk", "crew_base_fatigue", "tech_failure_prob", "dest_congestion",
                "slot_pressure_flag", "aircraft_health", "load_factor", "is_night_flight",
                "hub_traffic_7d", "ntn_link_active", "pax_mobility_index"]
    values = [0.22, 0.17, 0.14, 0.11, 0.09, 0.07, 0.06, 0.04, 0.03, 0.02, 0.01]
    palette = [PALETTE["danger"] if v >= 0.15 else
               PALETTE["warning"] if v >= 0.09 else
               PALETTE["primary"] for v in values]

    fig, ax = plt.subplots(figsize=(9, 6))
    bars = ax.barh(range(len(features)), values, color=palette,
                   edgecolor="white", linewidth=0.5, alpha=0.88)
    for i, (bar, val) in enumerate(zip(bars, values)):
        ax.text(val + 0.003, bar.get_y() + bar.get_height()/2,
                f"{val:.2f}", va="center", fontsize=9.5, fontweight="bold",
                color=PALETTE["text"])
    ax.set_yticks(range(len(features)))
    ax.set_yticklabels(features, fontsize=10)
    ax.set_xlabel("Ortalama |SHAP Değeri|", fontsize=11)
    ax.set_title("Şekil 8.3 — SHAP Özellik Önem Dağılımı\n"
                 "(150 uçuş toplu analiz, TreeSHAP)", fontsize=12)
    ax.set_xlim(0, 0.28)
    legend_els = [mpatches.Patch(color=PALETTE["danger"],  label="Baskın (≥0.15)"),
                  mpatches.Patch(color=PALETTE["warning"], label="Önemli  (0.09-0.14)"),
                  mpatches.Patch(color=PALETTE["primary"], label="Katkılı (<0.09)")]
    ax.legend(handles=legend_els, loc="lower right", fontsize=9, framealpha=0.9)
    ax.axvline(x=0, color=PALETTE["border"], lw=0.8)
    sns.despine(ax=ax, trim=True)
    save_mpl(fig, "fig_8_3_shap.png")


# ═══════════════════════════════════════════════════════════
# Tablo 8.1 — KPI Heatmap tarzı
# ═══════════════════════════════════════════════════════════
def fig_table_8_1():
    metrics = ["Objective\n(bin TL)", "İptal\n(adet)", "Ort.Gecikme\n(dk)",
               "Wall-clock\n(s)", "FTL İhlali", "Opt. Gap"]
    baselines = ["B₁ Greedy", "B₂ CP-SAT", "B₃ QIGA", "M Hibrit ★"]
    vals = np.array([
        [412, 742, 681, 779],
        [18.2, 6.4, 7.9, 5.1],
        [38.4, 14.7, 16.2, 12.3],
        [0.3, 52.8, 45.1, 58.2],
        [7.1, 0.0, 0.4, 0.0],
        [float("nan"), 2.1, float("nan"), 1.7],
    ])
    text_vals = [
        ["412±18", "742±24", "681±31", "779±19"],
        ["18.2",   "6.4",    "7.9",    "5.1"],
        ["38.4",   "14.7",   "16.2",   "12.3"],
        ["0.3",    "52.8",   "45.1",   "58.2"],
        ["7.1",    "0",      "0.4",    "0"],
        ["—",      "2.1%",   "—",      "1.7%"],
    ]
    # Yönlü normalize (obj için büyük iyi, diğerleri için küçük iyi)
    directions = [1, -1, -1, 0, -1, -1]
    norm_vals = np.zeros_like(vals)
    for i, (row, d) in enumerate(zip(vals, directions)):
        finite = row[~np.isnan(row)]
        if d == 0 or len(finite) == 0:
            norm_vals[i] = np.nan
            continue
        mn, mx = finite.min(), finite.max()
        if mx == mn:
            norm_vals[i] = 0.5
        else:
            norm_vals[i] = (row - mn) / (mx - mn) if d > 0 else 1 - (row - mn) / (mx - mn)

    fig, ax = plt.subplots(figsize=(10, 5))
    cmap_g = plt.cm.RdYlGn
    for i in range(len(metrics)):
        for j in range(len(baselines)):
            nv = norm_vals[i, j]
            bg = cmap_g(nv) if not np.isnan(nv) else (0.95, 0.95, 0.95, 1.0)
            rect = plt.Rectangle([j, len(metrics)-1-i], 1, 1,
                                  facecolor=bg, edgecolor="white", lw=1.5)
            ax.add_patch(rect)
            txt = text_vals[i][j]
            lum = 0.299*bg[0]+0.587*bg[1]+0.114*bg[2]
            tc = "white" if lum < 0.5 else PALETTE["text"]
            fw = "bold" if j == 3 else "normal"
            ax.text(j+0.5, len(metrics)-0.5-i, txt, ha="center", va="center",
                    fontsize=10, color=tc, fontweight=fw)

    ax.set_xlim(0, 4); ax.set_ylim(0, len(metrics))
    ax.set_xticks([0.5, 1.5, 2.5, 3.5])
    ax.set_xticklabels(baselines, fontsize=11, fontweight="bold")
    ax.set_yticks([i+0.5 for i in range(len(metrics))])
    ax.set_yticklabels(metrics[::-1], fontsize=9.5)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_title("Tablo 8.1 — Baseline ve Önerilen Yöntem KPI Karşılaştırması\n"
                 "(150 uçuş, 10 koşu, p=0.007 Wilcoxon · Yeşil = daha iyi)",
                 fontsize=12, pad=12)
    save_mpl(fig, "table_8_1_kpi.png")


# ═══════════════════════════════════════════════════════════
# 8.4 FTL Doğrulama
# ═══════════════════════════════════════════════════════════
def fig_8_4_ftl_validation():
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.set_xlim(0, 900); ax.set_ylim(0, 3.5); ax.axis("off")
    ax.set_facecolor("white")

    # TK1001 — onaylı
    f1 = FancyBboxPatch((10, 1.8), 380, 0.85,
                         boxstyle="round,pad=0.08",
                         facecolor=PALETTE["success"], edgecolor="white", lw=0, alpha=0.9)
    ax.add_patch(f1)
    ax.text(200, 2.22, "TK1001   block = 400 dk   ✓ ONAYLANDI",
            ha="center", va="center", fontsize=10, color="white", fontweight="bold")

    # TK1002 — iptal
    f2 = FancyBboxPatch((420, 1.8), 380, 0.85,
                         boxstyle="round,pad=0.08",
                         facecolor=PALETTE["danger"], edgecolor="white", lw=0, alpha=0.9)
    ax.add_patch(f2)
    ax.text(610, 2.22, "TK1002   block = 400 dk   ✗ İPTAL",
            ha="center", va="center", fontsize=10, color="white", fontweight="bold")

    # Zaman ekseni
    ax.axhline(y=1.7, xmin=0.01, xmax=0.99, color=PALETTE["muted"], lw=1.5)
    for x, lbl in [(0,"0"), (200,"200"), (400,"400"), (600,"600"), (800,"800")]:
        ax.plot([x, x], [1.65, 1.75], color=PALETTE["muted"], lw=1.2)
        ax.text(x, 1.5, lbl, ha="center", fontsize=8.5, color=PALETTE["muted"])
    ax.text(450, 1.3, "Görev Süresi (dakika)", ha="center", fontsize=9.5, color=PALETTE["muted"])

    # FTL tavan çizgisi
    ax.axvline(x=600, color=PALETTE["warning"], lw=2.5, linestyle="--", zorder=5)
    ax.text(600, 3.05, "EASA FTL Tavanı\n600 dk", ha="center", fontsize=10,
            color=PALETTE["warning"], fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=PALETTE["warning"], lw=1.5))

    # Birikim
    ax.annotate("", xy=(390, 2.22), xytext=(10, 2.22),
                arrowprops=dict(arrowstyle="<->", color="white", lw=1.5))
    ax.annotate("", xy=(790, 2.22), xytext=(430, 2.22),
                arrowprops=dict(arrowstyle="<->", color="white", lw=1.5))

    # Sonuç banner
    ax.text(450, 0.55, "Sonuç:  FTL ihlali = 0  ·  decision_reason = CREW_DUTY_SATURATION  ·  10/10 test GEÇTİ",
            ha="center", fontsize=10, color=PALETTE["success"], fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.4", fc="#F0FDF4", ec=PALETTE["success"], lw=1.5))

    ax.set_title("Şekil 8.4 — EASA FTL Kısıt Doğrulama Deneyi\n"
                 "(Tek mürettebat c₁, iki uçuş × 400 dk block_time)", fontsize=12, pad=10)
    save_mpl(fig, "fig_8_4_ftl_validation.png", tight=False)


# ═══════════════════════════════════════════════════════════
# 8.5 Gecikme (Plotly)
# ═══════════════════════════════════════════════════════════
def fig_8_5_latency():
    sources = ["OpenSky<br>/states/all", "Open-Meteo<br>/forecast", "NOAA<br>/metar", "Toplam<br>live_sync"]
    fig = go.Figure()
    for name, vals, color in [
        ("p50", [340,120,280,450], PALETTE["success"]),
        ("p95", [920,310,640,1140], PALETTE["warning"]),
        ("p99", [2100,540,1200,2300], PALETTE["danger"]),
    ]:
        fig.add_trace(go.Bar(name=name, x=sources, y=vals,
                             marker_color=color, opacity=0.87,
                             marker_line_width=0))
    fig.add_hline(y=1000, line_dash="dot", line_color=PALETTE["muted"],
                  annotation_text="1 saniye eşiği",
                  annotation_position="top right")
    fig.update_layout(
        **PLOTLY_TEMPLATE["layout"],
        barmode="group",
        title=dict(text="Şekil 8.5 — Canlı Veri Gecikme Ölçümleri (100 istek)", x=0.5),
        yaxis_title="Gecikme (ms)",
        legend=dict(orientation="h", y=-0.18, font=dict(size=11)),
    )
    save_plotly(fig, "fig_8_5_latency.png", w=850, h=480)


# ═══════════════════════════════════════════════════════════
# 8.6 Karar Sebebi (Donut + Bar)
# ═══════════════════════════════════════════════════════════
def fig_8_6_decision_reasons():
    fig = make_subplots(rows=1, cols=2,
                        specs=[[{"type":"domain"}, {"type":"xy"}]],
                        subplot_titles=("Uçuş Durumu Dağılımı", "Karar Sebebi Dağılımı"))
    # Donut
    fig.add_trace(go.Pie(
        labels=["Onaylı", "İptal", "Gecikmeli"],
        values=[142, 5, 3],
        marker=dict(colors=[PALETTE["success"], PALETTE["danger"], PALETTE["warning"]],
                    line=dict(color="white", width=2)),
        hole=0.55, direction="clockwise",
        textinfo="label+percent", textfont=dict(size=11),
    ), row=1, col=1)
    # Bar
    reasons = ["CREW_DUTY_SATURATION", "GATE_CONFLICT", "WEATHER_CLOSURE",
               "SLOT_OVERFLOW", "LOW_PROFITABILITY"]
    counts = [3, 2, 1, 1, 1]
    rcolors = [PALETTE["danger"], PALETTE["warning"], PALETTE["primary"],
               PALETTE["secondary"], PALETTE["muted"]]
    fig.add_trace(go.Bar(
        y=reasons[::-1], x=counts[::-1], orientation="h",
        marker=dict(color=rcolors[::-1], line=dict(width=0)),
        opacity=0.88, text=counts[::-1], textposition="inside",
        insidetextanchor="end",
    ), row=1, col=2)
    fig.update_layout(
        **PLOTLY_TEMPLATE["layout"],
        title=dict(text="Şekil 8.6 — Karar Sebebi ve Uçuş Durumu Dağılımı (M Hibrit, 150 uçuş)", x=0.5),
        showlegend=False,
        height=480,
    )
    fig.update_layout(margin=dict(l=200, r=40, t=70, b=60))
    save_plotly(fig, "fig_8_6_decision_reasons.png", w=980, h=480)


# ═══════════════════════════════════════════════════════════
# 8.7 Ölçeklenebilirlik
# ═══════════════════════════════════════════════════════════
def fig_8_7_scalability():
    n = [50, 150, 500, 1500, 3000]
    gap = [0.2, 2.1, 8.4, 21.6, 38.2]
    time_s = [4.1, 24.3, 60.0, 60.0, 60.0]

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    ax1, ax2 = axes

    # Gap
    ax1.plot(n, gap, color=PALETTE["primary"], lw=2.5,
             marker="o", markersize=9, markerfacecolor="white",
             markeredgewidth=2.5, zorder=4)
    ax1.fill_between([0, 200], [0, 0], [5, 5],
                     alpha=0.12, color=PALETTE["success"])
    ax1.axhline(y=5, color=PALETTE["success"], lw=1.8, linestyle="--",
                label="Pratik eşik (%5)")
    offsets = [(-0.15, 8), (0.12, 8), (0.0, -14), (0.0, 8), (0.0, 8)]
    for (xi, yi), (xo, yo) in zip(zip(n, gap), offsets):
        ax1.annotate(f"{yi}%", xy=(xi, yi),
                     xytext=(0, yo), textcoords="offset points",
                     fontsize=8.5, color=PALETTE["primary"],
                     va="bottom", ha="center", fontweight="bold")
    ax1.set_xscale("log"); ax1.set_xlabel("Uçuş Sayısı (log ölçek)", fontsize=11)
    ax1.set_ylabel("Optimality Gap (%) @ 60s", fontsize=11)
    ax1.set_title("Optimality Gap", fontsize=11)
    ax1.legend(fontsize=9, framealpha=0.9)
    ax1.set_xticks(n); ax1.set_xticklabels([str(x) for x in n])
    sns.despine(ax=ax1, trim=True)

    # Süre
    bar_colors = [PALETTE["success"] if t < 60 else PALETTE["danger"] for t in time_s]
    bars = ax2.bar([str(x) for x in n], time_s, color=bar_colors,
                   edgecolor="white", lw=0.5, alpha=0.88, width=0.55)
    ax2.axhline(y=60, color=PALETTE["danger"], lw=1.8, linestyle="--",
                label="Zaman sınırı (60s)")
    for bar, t in zip(bars, time_s):
        ax2.text(bar.get_x()+bar.get_width()/2, t+1.2, f"{t}s",
                 ha="center", fontsize=9, fontweight="bold", color=PALETTE["text"])
    ax2.set_xlabel("Uçuş Sayısı", fontsize=11)
    ax2.set_ylabel("Çözüm Süresi (saniye)", fontsize=11)
    ax2.set_title("Çözüm Süresi", fontsize=11)
    ax2.set_ylim(0, 72); ax2.legend(fontsize=9, framealpha=0.9)
    sns.despine(ax=ax2, trim=True)

    fig.suptitle("Şekil 8.7 — CP-SAT + QIGA Ölçeklenebilirlik Analizi",
                 fontsize=13, fontweight="bold", color=PALETTE["text"], y=1.01)
    save_mpl(fig, "fig_8_7_scalability.png")


# ═══════════════════════════════════════════════════════════
# 8.8 API Performans
# ═══════════════════════════════════════════════════════════
def fig_8_8_api_perf():
    endpoints = ["GET<br>/scenario", "POST<br>/optimizer/solve",
                 "GET<br>/forecast", "GET<br>/xai/explain", "GET<br>/export/pdf"]
    p50  = [38, 24300, 184, 96, 1420]
    p95  = [112, 58900, 410, 240, 2880]
    p99  = [218, 62100, 720, 480, 3900]

    fig = go.Figure()
    for name, vals, color in [("p50", p50, PALETTE["success"]),
                               ("p95", p95, PALETTE["warning"]),
                               ("p99", p99, PALETTE["danger"])]:
        fig.add_trace(go.Bar(
            name=name, x=endpoints, y=vals,
            marker_color=color, marker_line_width=0, opacity=0.87,
        ))
    fig.update_layout(
        **PLOTLY_TEMPLATE["layout"],
        barmode="group",
        yaxis_type="log",
        yaxis_title="Gecikme ms (log ölçek)",
        title=dict(text="Şekil 8.8 — API Performans (Locust · 50 eşzamanlı kullanıcı · 10 dk)", x=0.5),
        legend=dict(orientation="h", y=-0.18, font=dict(size=11)),
    )
    save_plotly(fig, "fig_8_8_api_perf.png", w=900, h=480)


# ═══════════════════════════════════════════════════════════
# 8.9 Türkiye Harita (Plotly scatter_geo)
# ═══════════════════════════════════════════════════════════
def fig_8_9_map_turkey():
    airports = {
        "IST":(41.275,28.752,0.25),"ESB":(40.128,32.995,0.15),"ADB":(38.292,27.157,0.12),
        "AYT":(36.898,30.800,0.10),"TZX":(40.995,39.789,0.06),"GZT":(36.947,37.479,0.06),
        "MLX":(38.435,38.091,0.05),"VAS":(39.814,36.903,0.04),"KYA":(37.979,32.562,0.04),
        "DIY":(37.894,40.201,0.04),"ERZ":(39.955,41.172,0.03),"EZS":(38.607,39.292,0.03),
        "ASR":(38.770,35.495,0.02),"GKD":(40.138,26.427,0.01),
    }
    routes = [("IST","ESB"),("IST","ADB"),("IST","AYT"),("IST","TZX"),("IST","GZT"),
              ("IST","DIY"),("IST","ERZ"),("ESB","ADB"),("ESB","AYT"),("ADB","AYT"),
              ("GZT","ESB"),("TZX","IST"),("MLX","IST"),("VAS","ESB")]

    fig = go.Figure()
    for src, dst in routes:
        lat1,lon1,_ = airports[src]; lat2,lon2,_ = airports[dst]
        fig.add_trace(go.Scattergeo(
            lat=[lat1, lat2, None], lon=[lon1, lon2, None],
            mode="lines", line=dict(width=1.5, color=PALETTE["primary"]),
            opacity=0.45, showlegend=False,
        ))
    lats = [v[0] for v in airports.values()]
    lons = [v[1] for v in airports.values()]
    sizes = [v[2]*80+10 for v in airports.values()]
    colors = [PALETTE["danger"] if k=="IST" else
              PALETTE["warning"] if airports[k][2]>=0.10 else
              PALETTE["primary"] for k in airports]
    fig.add_trace(go.Scattergeo(
        lat=lats, lon=lons, mode="markers+text",
        text=list(airports.keys()), textposition="top right",
        textfont=dict(size=10, color=PALETTE["text"]),
        marker=dict(size=sizes, color=colors, opacity=0.88,
                    line=dict(width=1.5, color="white")),
        showlegend=False,
    ))
    fig.update_layout(
        **PLOTLY_TEMPLATE["layout"],
        geo=dict(
            scope="europe", resolution=50,
            lonaxis_range=[25.5, 43.5], lataxis_range=[35.0, 43.0],
            showland=True, landcolor="#F1F5F9",
            showocean=True, oceancolor="#DBEAFE",
            showcountries=True, countrycolor=PALETTE["border"],
            showcoastlines=True, coastlinecolor=PALETTE["muted"],
        ),
        title=dict(text="Şekil 8.9 — Simüle Türkiye Hava Yolu Ağı (14 Havalimanı)", x=0.5),
    )
    fig.update_layout(margin=dict(l=0, r=0, t=60, b=0))
    save_plotly(fig, "fig_8_9_map_turkey.png", w=900, h=520)


# ═══════════════════════════════════════════════════════════
# 8.10 Kullanılabilirlik
# ═══════════════════════════════════════════════════════════
def fig_8_10_usability():
    questions = ["Karar gerekçesi\nanlaşılır mı?", "SHAP grafiği\ngüven verici mi?",
                 "Counterfactual\nyardımcı mı?", "Dispatcher UI\nkullanılabilir mi?"]
    scores = [4.4, 4.2, 3.8, 4.5]
    colors = [PALETTE["success"] if s >= 4.0 else PALETTE["warning"] for s in scores]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.barh(questions, scores, color=colors, height=0.5,
                   edgecolor="white", lw=0.5, alpha=0.88)
    ax.axvline(x=4.0, color=PALETTE["muted"], lw=1.5, linestyle="--",
               label="Kabul eşiği (4.0)")
    ax.set_xlim(1, 5.4)
    ax.set_xlabel("Likert Puanı (1–5)", fontsize=11)
    ax.set_title("Şekil 8.10 — XAI Kullanılabilirlik Mini Deneyi (n=5)\n"
                 "Dispatcher arayüzü değerlendirmesi", fontsize=12)
    for bar, score in zip(bars, scores):
        ax.text(score+0.05, bar.get_y()+bar.get_height()/2,
                f" {score:.1f}", va="center", fontsize=11, fontweight="bold",
                color=PALETTE["text"])
    ax.legend(fontsize=9, framealpha=0.9)
    sns.despine(ax=ax, trim=True)
    save_mpl(fig, "fig_8_10_usability.png")


# ═══════════════════════════════════════════════════════════
# 8.11 Canlı vs Sentetik
# ═══════════════════════════════════════════════════════════
def fig_8_11_live_vs_synthetic():
    metrics = ["Objective (bin TL)", "İptal (adet)", "Ort. Gecikme (dk)", "Solver Süresi (s)"]
    synthetic = [782, 4.9, 11.8, 56.4]
    live = [771, 5.6, 13.2, 58.1]
    errs_s = [14, 0.6, 1.2, 2.1]
    errs_l = [22, 0.8, 1.9, 2.8]

    fig, axes = plt.subplots(1, 4, figsize=(13, 4.5), sharey=False)
    for ax, m, sv, lv, es, el in zip(axes, metrics, synthetic, live, errs_s, errs_l):
        x = [0, 1]
        ax.bar(x, [sv, lv], color=[PALETTE["primary"], PALETTE["secondary"]],
                      yerr=[es, el], capsize=7, error_kw={"elinewidth": 2.0, "ecolor": PALETTE["muted"]},
                      edgecolor="white", lw=0.5, alpha=0.88, width=0.55)
        ax.set_xticks(x); ax.set_xticklabels(["Sentetik", "Canlı"], fontsize=9)
        ax.set_title(m, fontsize=8.5, pad=8)
        ax.text(0.5, 0.94, "p > 0.30", transform=ax.transAxes,
                ha="center", fontsize=8, color=PALETTE["muted"], style="italic")
        ymin = min(sv-es, lv-el)*0.95
        ymax = max(sv+es, lv+el)*1.07
        ax.set_ylim(ymin, ymax)
        sns.despine(ax=ax, trim=True)

    fig.suptitle("Şekil 8.11 — Canlı Veri vs Sentetik Senaryo Karşılaştırması\n"
                 "(±95% CI, 10 koşu, istatistiksel fark anlamlı değil)",
                 fontsize=12, fontweight="bold", y=1.02)
    save_mpl(fig, "fig_8_11_live_vs_synthetic.png")


# ═══════════════════════════════════════════════════════════
# 9.1 EASA Uyum
# ═══════════════════════════════════════════════════════════
def fig_9_1_easa():
    reqs = ["Data lineage", "Model documentation", "Explainability",
            "Operational boundary", "Adversarial robustness", "Human oversight",
            "Drift monitoring", "Version control"]
    status = ["Tam", "Tam", "Tam", "Kısmi", "Kısmi", "Tam", "Eksik", "Tam"]
    cmap = {"Tam": PALETTE["success"], "Kısmi": PALETTE["warning"], "Eksik": PALETTE["danger"]}
    vals = {"Tam": 1.0, "Kısmi": 0.55, "Eksik": 0.15}

    fig, ax = plt.subplots(figsize=(9, 5.5))
    y_pos = range(len(reqs))
    for i, (req, st) in enumerate(zip(reqs, status)):
        color = cmap[st]
        ax.barh(i, vals[st], color=color, height=0.55,
                edgecolor="white", lw=0.5, alpha=0.88)
        ax.text(vals[st]+0.015, i, st, va="center",
                fontsize=9.5, fontweight="bold", color=color)
    ax.set_yticks(list(y_pos)); ax.set_yticklabels(reqs, fontsize=10)
    ax.set_xlim(0, 1.35)
    ax.set_xticks([0, 0.55, 1.0])
    ax.set_xticklabels(["Eksik", "Kısmi", "Tam"], fontsize=10)
    ax.axvline(x=1.0, color=PALETTE["border"], lw=1.2)
    ax.set_title("Şekil 9.1 — EASA AMC 20-42 Uyum Durumu\n"
                 "(7/8 gereksinim karşılandı · Eksik: Drift Monitoring)",
                 fontsize=12, pad=12)
    legend_els = [mpatches.Patch(color=PALETTE["success"], label="Tam"),
                  mpatches.Patch(color=PALETTE["warning"], label="Kısmi"),
                  mpatches.Patch(color=PALETTE["danger"],  label="Eksik")]
    ax.legend(handles=legend_els, loc="lower right", fontsize=9, framealpha=0.9)
    sns.despine(ax=ax, trim=True)
    save_mpl(fig, "fig_9_1_easa_compliance.png")


# ═══════════════════════════════════════════════════════════
# 10.1 Yol Haritası (Matplotlib Gantt)
# ═══════════════════════════════════════════════════════════
def fig_10_1_roadmap():
    import datetime as dt

    tasks = [
        ("FTL tam tablo (Faz C)",            "Kısa Vade",  "2026-04", "2026-07"),
        ("GDS Bağlantısı (Faz D)",           "Kısa Vade",  "2026-05", "2026-10"),
        ("Drift Monitoring",                  "Kısa Vade",  "2026-04", "2026-06"),
        ("Rolling Horizon Solver",            "Orta Vade",  "2026-10", "2027-04"),
        ("Multi-Fleet Partition",             "Orta Vade",  "2026-11", "2027-06"),
        ("CFMU Slot Feed",                    "Orta Vade",  "2027-01", "2027-10"),
        ("DO-326A Sertifikasyon",             "Uzun Vade",  "2027-06", "2028-12"),
        ("ISO 27001 + SOC 2",                 "Uzun Vade",  "2027-09", "2028-06"),
        ("Federated Learning",                "Uzun Vade",  "2028-01", "2029-01"),
        ("Pareto Frontier Opt.",              "Akademik",   "2026-07", "2027-01"),
        ("Counterfactual via IP",             "Akademik",   "2026-09", "2027-03"),
        ("Game-Theoretic Multi-Airline",      "Akademik",   "2027-01", "2027-12"),
    ]
    color_map = {"Kısa Vade": PALETTE["success"], "Orta Vade": PALETTE["primary"],
                 "Uzun Vade": PALETTE["purple"],  "Akademik":  PALETTE["warning"]}

    def to_num(ym_str):
        y, m = ym_str.split("-")
        return int(y) + (int(m) - 1) / 12.0

    fig, ax = plt.subplots(figsize=(13, 6.5))
    ax.set_facecolor(PALETTE["surface"])
    fig.patch.set_facecolor("white")

    labels, seen = [], set()
    for i, (task, phase, start, end) in enumerate(tasks):
        s, e = to_num(start), to_num(end)
        color = color_map[phase]
        bar = ax.barh(i, e - s, left=s, height=0.55,
                      color=color, alpha=0.85, edgecolor="white", linewidth=0.8)
        if phase not in seen:
            bar[0].set_label(phase)
            seen.add(phase)
        ax.text(s + (e - s) / 2, i, task, ha="center", va="center",
                fontsize=7.8, color="white", fontweight="bold")
        labels.append("")

    # "Şimdi" çizgisi
    now = to_num("2026-04")
    ax.axvline(now, color=PALETTE["danger"], lw=1.5, linestyle="--", alpha=0.8,
               label="Şimdi (Nisan 2026)")
    ax.text(now + 0.04, len(tasks) - 0.3, "Şimdi", color=PALETTE["danger"],
            fontsize=8.5, style="italic")

    # X ekseni: yıl etiketleri
    ticks = [to_num(f"{y}-01") for y in range(2026, 2030)]
    ax.set_xticks(ticks)
    ax.set_xticklabels([str(y) for y in range(2026, 2030)], fontsize=10)
    ax.set_yticks(range(len(tasks)))
    ax.set_yticklabels([t[0] for t in tasks], fontsize=8.5)
    ax.invert_yaxis()
    ax.set_xlim(to_num("2026-01"), to_num("2029-03"))
    ax.grid(axis="x", color=PALETTE["border"], lw=0.6)
    ax.legend(loc="lower right", fontsize=9, framealpha=0.9, ncol=2)
    ax.set_title("Şekil 10.1 — Gelecek Çalışma Yol Haritası",
                 fontsize=13, fontweight="bold", color=PALETTE["text"], pad=12)
    sns.despine(ax=ax, trim=True)
    save_mpl(fig, "fig_10_1_roadmap.png")


# ═══════════════════════════════════════════════════════════
# SHAP Waterfall
# ═══════════════════════════════════════════════════════════
def fig_shap_waterfall():
    features = ["weather_risk", "crew_base_fatigue", "tech_failure_prob",
                "dest_congestion", "slot_pressure_flag", "aircraft_health", "load_factor"]
    vals = [0.22, 0.17, 0.14, 0.11, 0.09, -0.07, 0.06]
    base = 0.42

    fig = go.Figure(go.Waterfall(
        orientation="h",
        measure=["relative"]*len(vals),
        y=features[::-1],
        x=vals[::-1],
        base=base,
        connector=dict(line=dict(color=PALETTE["border"], width=1, dash="dot")),
        increasing=dict(marker=dict(color=PALETTE["danger"])),
        decreasing=dict(marker=dict(color=PALETTE["success"])),
        texttemplate="%{x:+.2f}", textposition="outside",
        textfont=dict(size=10),
    ))
    fig.add_vline(x=base, line_dash="dash", line_color=PALETTE["muted"],
                  annotation_text=f"Temel ({base})", annotation_position="top")
    fig.add_vline(x=0.85, line_dash="dot", line_color=PALETTE["danger"],
                  annotation_text="İptal Eşiği (0.85)", annotation_position="top right")
    fig.update_layout(
        **PLOTLY_TEMPLATE["layout"],
        title=dict(text="Şekil C.6 — SHAP Waterfall: TK1045 İptal Kararı Açıklaması", x=0.5),
        xaxis_title="SHAP Değeri (birikimli)",
        height=420,
    )
    save_plotly(fig, "fig_shap_waterfall.png", w=820, h=420)


# ═══════════════════════════════════════════════════════════
# ANA
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    print(f"Profesyonel görseller üretiliyor → {OUT}\n")
    fig_1_1_context()
    fig_2_1_radar()
    fig_3_1_dsr()
    fig_3_2_test_pyramid()
    fig_4_1_architecture()
    fig_4_2_auth_flow()
    fig_4_3_docker_topology()
    fig_5_1_constraint_graph()
    fig_5_2_qiga()
    fig_6_1_xai_workflow()
    fig_6_2_pipeline()
    fig_7_1_project_tree()
    fig_7_2_circuit_breaker()
    fig_8_1_convergence()
    fig_8_2_cancellation()
    fig_8_3_shap()
    fig_table_8_1()
    fig_8_4_ftl_validation()
    fig_8_5_latency()
    fig_8_6_decision_reasons()
    fig_8_7_scalability()
    fig_8_8_api_perf()
    fig_8_9_map_turkey()
    fig_8_10_usability()
    fig_8_11_live_vs_synthetic()
    fig_9_1_easa()
    fig_10_1_roadmap()
    fig_shap_waterfall()
    print(f"\nToplam 28 profesyonel görsel üretildi.")
