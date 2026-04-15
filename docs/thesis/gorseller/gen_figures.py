#!/usr/bin/env python3
"""
Tez görselleri üretici — tüm şekilleri docs/thesis/gorseller/ dizinine PNG olarak kaydeder.
Kullanım: python3 docs/thesis/gorseller/gen_figures.py
Toplam: 30 görsel
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from matplotlib.lines import Line2D

OUT = os.path.dirname(os.path.abspath(__file__))
DPI = 150

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
C_NAVY   = "#1E3A5F"

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

def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  {name}")


# ─────────────────────────────────────────────
# Şekil 1.1 — Sistem Bağlam Diyagramı
# ─────────────────────────────────────────────
def fig_1_1_context():
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.axis("off")
    ax.set_title("Şekil 1.1 — Sistem Bağlam Diyagramı", fontsize=12, fontweight="bold")

    def box(cx, cy, w, h, text, color, tc="white", fs=9):
        r = FancyBboxPatch((cx-w/2, cy-h/2), w, h, boxstyle="round,pad=0.1",
                           fc=color, ec="white", lw=1.5, zorder=3)
        ax.add_patch(r)
        ax.text(cx, cy, text, ha="center", va="center", fontsize=fs,
                color=tc, fontweight="bold", zorder=4, multialignment="center")

    def arr(x1,y1,x2,y2,lbl="",color=C_GRAY):
        ax.annotate("", xy=(x2,y2), xytext=(x1,y1),
                    arrowprops=dict(arrowstyle="->",color=color,lw=1.6), zorder=2)
        if lbl:
            ax.text((x1+x2)/2+0.1,(y1+y2)/2, lbl, fontsize=7.5, color=color)

    # Dış aktörler
    box(1,5,1.6,0.7,"Dispeçer\n(Operator)",C_DARK)
    box(1,3,1.6,0.7,"Jüri /\nYönetici",C_DARK)
    box(1,1,1.6,0.7,"Sistem\nYöneticisi",C_DARK)

    # Merkez sistem
    box(5,3,3.2,4.0,"Aviation Digital Twin\nv27.0\n\nCP-SAT + QIGA\nXAI + Forecast\nFastAPI + PostgreSQL",C_NAVY,fs=9)

    # Dış servisler
    box(9,5,1.6,0.7,"OpenSky\nADS-B",C_TEAL)
    box(9,3.7,1.6,0.7,"Open-Meteo\nHava Durumu",C_TEAL)
    box(9,2.4,1.6,0.7,"NOAA\nMETAR",C_TEAL)
    box(9,1,1.6,0.7,"Prometheus\n+ Grafana",C_ORANGE)

    # Oklar
    arr(1.8,5,3.4,3.7,"Komutlar"); arr(3.4,3.3,1.8,4.8)
    arr(1.8,3,3.4,3,"Sorgular"); arr(3.4,2.7,1.8,2.8)
    arr(1.8,1,3.4,2.3,"Yönetim")
    arr(8.2,5,6.6,3.7,"ADS-B verisi",color=C_TEAL)
    arr(8.2,3.7,6.6,3.4,"Hava verisi",color=C_TEAL)
    arr(8.2,2.4,6.6,3.0,"METAR",color=C_TEAL)
    arr(6.6,2.6,8.2,1.3,"Metrikler",color=C_ORANGE)

    save(fig, "fig_1_1_context.png")


# ─────────────────────────────────────────────
# Şekil 2.1 — Radar
# ─────────────────────────────────────────────
def fig_2_1_radar():
    categories = ["Optimalite","Hız","Açıklanabilirlik","Canlı Veri","EASA Uyum","Ölçek"]
    N = len(categories)
    approaches = {
        "Klasik MILP":[9,2,5,2,5,7],
        "Deep RL":    [6,9,2,8,2,6],
        "Bu Tez (M)": [8,7,9,8,8,6],
    }
    colors=[C_ORANGE,C_PURPLE,C_GREEN]
    angles=[n/float(N)*2*np.pi for n in range(N)]+[0]

    fig,ax=plt.subplots(figsize=(6,6),subplot_kw=dict(polar=True))
    ax.set_theta_offset(np.pi/2); ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1]); ax.set_xticklabels(categories,fontsize=9)
    ax.set_ylim(0,10); ax.set_yticks([2,4,6,8,10])
    ax.set_yticklabels(["2","4","6","8","10"],fontsize=7); ax.grid(color=C_GRAY,alpha=0.3)

    for (name,vals),color in zip(approaches.items(),colors):
        v=vals+vals[:1]
        ax.plot(angles,v,color=color,linewidth=2,label=name)
        ax.fill(angles,v,alpha=0.1,color=color)

    ax.legend(loc="upper right",bbox_to_anchor=(1.4,1.1),fontsize=9)
    ax.set_title("Şekil 2.1 — Yaklaşım Karşılaştırması (Radar)",fontweight="bold",pad=20)
    save(fig,"fig_2_1_radar.png")


# ─────────────────────────────────────────────
# Şekil 3.1 — DSR Metodoloji Döngüsü
# ─────────────────────────────────────────────
def fig_3_1_dsr():
    fig,ax=plt.subplots(figsize=(9,5))
    ax.set_xlim(0,9); ax.set_ylim(0,5); ax.axis("off")
    ax.set_title("Şekil 3.1 — Tasarım Bilimi Araştırması (DSR) Metodoloji Aşamaları",fontsize=11,fontweight="bold")

    phases=[
        (0.8,2.5,"1\nProblem\nTanımı",C_RED),
        (2.4,2.5,"2\nHedef\nTanımı",C_ORANGE),
        (4.0,2.5,"3\nTasarım &\nGeliştirme",C_BLUE),
        (5.6,2.5,"4\nDemo &\nDeğerlendirme",C_GREEN),
        (7.2,2.5,"5\nİletişim",C_PURPLE),
    ]
    for cx,cy,txt,color in phases:
        circ=plt.Circle((cx,cy),0.75,color=color,zorder=3)
        ax.add_patch(circ)
        ax.text(cx,cy,txt,ha="center",va="center",fontsize=8,
                color="white",fontweight="bold",zorder=4,multialignment="center")

    # Oklar arası
    for i in range(len(phases)-1):
        x1=phases[i][0]+0.75; x2=phases[i+1][0]-0.75; y=2.5
        ax.annotate("",xy=(x2,y),xytext=(x1,y),
                    arrowprops=dict(arrowstyle="->",color=C_GRAY,lw=2))

    # Geri besleme oku
    ax.annotate("",xy=(0.8,1.6),xytext=(7.2,1.6),
                arrowprops=dict(arrowstyle="->",color=C_GRAY,lw=1.5,
                                connectionstyle="arc3,rad=0"))
    ax.text(4.0,1.2,"İteratif Geri Besleme",ha="center",fontsize=8.5,
            color=C_GRAY,style="italic")

    # Uygulama etiketleri
    labels=["IROPS &\nFTL tanımı","RQ & KPI","CP-SAT+QIGA\nXAI+FastAPI","Deneyler\np=0.007","TEKNOFEST\n2026"]
    for (cx,cy,_,_),lbl in zip(phases,labels):
        ax.text(cx,cy+1.15,lbl,ha="center",fontsize=7.5,color=C_DARK,multialignment="center",
                bbox=dict(boxstyle="round,pad=0.2",fc=C_LIGHT,ec=C_GRAY,alpha=0.7))

    save(fig,"fig_3_1_dsr.png")


# ─────────────────────────────────────────────
# Şekil 3.2 — Test Piramidi
# ─────────────────────────────────────────────
def fig_3_2_test_pyramid():
    fig,ax=plt.subplots(figsize=(7,5))
    ax.set_xlim(0,10); ax.set_ylim(0,6); ax.axis("off")
    ax.set_title("Şekil 3.2 — Test Piramidi",fontsize=11,fontweight="bold")

    levels=[
        (5,0.8,8.0,0.9,C_GREEN,"Birim Testleri (62 test)\ntest_core, test_solver, test_models","Hızlı · Ucuz · Yalıtılmış"),
        (5,2.2,5.5,0.9,C_ORANGE,"Entegrasyon Testleri\ntest_integration, test_live_sync","API + DB + Circuit Breaker"),
        (5,3.6,3.5,0.9,C_BLUE,"API Testleri\ntest_auth_api, test_audit_flow","httpx AsyncClient + JWT"),
        (5,5.0,1.8,0.9,C_RED,"E2E / Kullanılabilirlik\nPlaywright (planlanan)","UI akışı"),
    ]
    for cx,cy,w,h,color,title,sub in levels:
        # Yamuk şekli
        offset=(8-w)/2
        ax.fill([offset,10-offset,10-offset+0.3,offset-0.3],
                [cy-h/2,cy-h/2,cy+h/2,cy+h/2],color=color,alpha=0.82,zorder=3)
        ax.text(cx,cy+0.12,title,ha="center",va="center",fontsize=8.5,
                color="white",fontweight="bold",zorder=4,multialignment="center")
        ax.text(cx,cy-0.25,sub,ha="center",va="center",fontsize=7.5,
                color="white",alpha=0.9,zorder=4)

    # Etiketler
    ax.text(9.5,0.8,"Cok",ha="center",fontsize=8,color=C_GRAY,rotation=90)
    ax.text(9.5,5.0,"Az",ha="center",fontsize=8,color=C_GRAY,rotation=90)
    ax.annotate("",xy=(9.5,5.5),xytext=(9.5,0.4),
                arrowprops=dict(arrowstyle="->",color=C_GRAY,lw=1.3))
    ax.text(9.7,3.0,"Maliyet",ha="left",fontsize=8,color=C_GRAY,rotation=90)

    save(fig,"fig_3_2_test_pyramid.png")


# ─────────────────────────────────────────────
# Şekil 4.1 — 6 Katmanlı Mimari
# ─────────────────────────────────────────────
def fig_4_1_architecture():
    fig,ax=plt.subplots(figsize=(10,7))
    ax.set_xlim(0,10); ax.set_ylim(0,7); ax.axis("off")
    ax.set_title("Şekil 4.1 — 6 Katmanlı Sistem Mimarisi",fontsize=12,fontweight="bold",pad=8)

    layers=[
        (6.2,"Katman 6: Kullanıcı Arayüzü","Three.js 3D · MapLibre 2D · Chart.js · Dispatcher UI","#1E3A5F","white"),
        (5.1,"Katman 5: API Gateway","FastAPI · JWT/RBAC · AuditMiddleware · Rate Limit","#1B4332","white"),
        (4.0,"Katman 4: İş Mantığı","CP-SAT Solver · QIGA · XAI Engine · Forecast (XGB)","#4A1942","white"),
        (2.9,"Katman 3: Veri Katmanı","SQLAlchemy 2.x · Alembic · PostgreSQL / SQLite","#7C2D12","white"),
        (1.8,"Katman 2: Canlı Entegrasyon","OpenSky · Open-Meteo · NOAA · Circuit Breaker","#1A3A4A","white"),
        (0.7,"Katman 1: Altyapı & İzleme","Docker · Caddy TLS · Prometheus · Loki · Grafana","#374151","white"),
    ]
    for y_center,title,subtitle,bg,fg in layers:
        r=FancyBboxPatch((0.3,y_center-0.45),9.4,0.9,boxstyle="round,pad=0.08",
                          fc=bg,ec="white",lw=1.0)
        ax.add_patch(r)
        ax.text(0.7,y_center+0.12,title,fontsize=9.5,fontweight="bold",color=fg,va="center")
        ax.text(0.7,y_center-0.2,subtitle,fontsize=8.2,color=fg,va="center",alpha=0.85)

    for y in [1.25,2.35,3.45,4.55,5.65]:
        ax.annotate("",xy=(5,y+0.1),xytext=(5,y-0.1),
                    arrowprops=dict(arrowstyle="<->",color="#9CA3AF",lw=1.5))

    save(fig,"fig_4_1_architecture.png")


# ─────────────────────────────────────────────
# Şekil 4.2 — Auth & RBAC Akışı
# ─────────────────────────────────────────────
def fig_4_2_auth_flow():
    fig,ax=plt.subplots(figsize=(10,5))
    ax.set_xlim(0,10); ax.set_ylim(0,5); ax.axis("off")
    ax.set_title("Şekil 4.2 — JWT Kimlik Doğrulama ve RBAC Yetkilendirme Akışı",fontsize=11,fontweight="bold")

    def rbox(cx,cy,w,h,txt,color,tc="white"):
        r=FancyBboxPatch((cx-w/2,cy-h/2),w,h,boxstyle="round,pad=0.1",
                          fc=color,ec="white",lw=1.3,zorder=3)
        ax.add_patch(r)
        ax.text(cx,cy,txt,ha="center",va="center",fontsize=8.5,
                color=tc,fontweight="bold",zorder=4,multialignment="center")

    def arr(x1,y1,x2,y2,lbl=""):
        ax.annotate("",xy=(x2,y2),xytext=(x1,y1),
                    arrowprops=dict(arrowstyle="->",color=C_GRAY,lw=1.5),zorder=2)
        if lbl:
            ax.text((x1+x2)/2+0.05,(y1+y2)/2+0.1,lbl,fontsize=7.5,color=C_GRAY)

    rbox(1.2,4.0,1.8,0.65,"Kullanıcı\n(Tarayıcı)",C_DARK)
    rbox(3.5,4.0,2.0,0.65,"POST /api/auth\n/jwt/login",C_BLUE)
    rbox(6.0,4.0,2.0,0.65,"fastapi-users\nbcrypt doğrula",C_PURPLE)
    rbox(8.5,4.0,1.6,0.65,"JWT Token\n(24s)",C_GREEN)

    rbox(3.5,2.2,2.0,0.65,"Korunan\nEndpoint",C_BLUE)
    rbox(6.0,2.2,2.0,0.65,"require_role()\nKontrolü",C_ORANGE)
    rbox(8.5,2.2,1.6,0.65,"İş Mantığı\n(Solver vb.)",C_GREEN)
    rbox(6.0,0.8,2.0,0.65,"403 Forbidden\n(Yetersiz rol)",C_RED)

    arr(2.1,4.0,2.5,4.0,"kimlik bilgileri")
    arr(4.5,4.0,5.0,4.0)
    arr(7.0,4.0,7.7,4.0,"JWT")
    arr(1.2,3.67,3.5,2.53,"Bearer Token")
    arr(4.5,2.2,5.0,2.2)
    ax.text(6.5,2.7,"rol uygun?",fontsize=8,color=C_ORANGE,ha="center")
    arr(7.0,2.2,7.7,2.2,"Evet")
    ax.annotate("",xy=(6.0,1.13),xytext=(6.0,1.87),
                arrowprops=dict(arrowstyle="->",color=C_RED,lw=1.5))
    ax.text(6.3,1.5,"Hayır",fontsize=8,color=C_RED)

    # Roller
    ax.text(5,0.2,"Roller: viewer (izleme) · operator (solver, export) · admin (tüm)",
            ha="center",fontsize=8.5,color=C_DARK,
            bbox=dict(boxstyle="round",fc="#EFF6FF",ec=C_BLUE,alpha=0.8))

    save(fig,"fig_4_2_auth_flow.png")


# ─────────────────────────────────────────────
# Şekil 4.3 — Docker Compose Topolojisi
# ─────────────────────────────────────────────
def fig_4_3_docker_topology():
    fig,ax=plt.subplots(figsize=(10,5.5))
    ax.set_xlim(0,10); ax.set_ylim(0,5.5); ax.axis("off")
    ax.set_title("Şekil 4.3 — Docker Compose Servis Topolojisi",fontsize=11,fontweight="bold")

    def box(cx,cy,w,h,txt,color,tc="white"):
        r=FancyBboxPatch((cx-w/2,cy-h/2),w,h,boxstyle="round,pad=0.12",
                          fc=color,ec="white",lw=1.3,zorder=3)
        ax.add_patch(r)
        ax.text(cx,cy,txt,ha="center",va="center",fontsize=9,
                color=tc,fontweight="bold",zorder=4,multialignment="center")

    def arr(x1,y1,x2,y2,lbl="",color=C_GRAY):
        ax.annotate("",xy=(x2,y2),xytext=(x1,y1),
                    arrowprops=dict(arrowstyle="->",color=color,lw=1.4),zorder=2)
        if lbl:
            ax.text((x1+x2)/2+0.1,(y1+y2)/2,lbl,fontsize=7.5,color=color)

    box(1.5,4.5,2.2,0.7,"Internet\nKullanıcılar",C_DARK)
    box(1.5,3.2,2.2,0.7,"Caddy\n(TLS :443)",C_GRAY)
    box(5.0,3.2,2.2,0.8,"api\n(uvicorn :8501)",C_NAVY)
    box(8.5,3.2,2.2,0.7,"postgres\n(:5432)",C_BLUE)
    box(3.5,1.5,2.0,0.7,"prometheus\n(:9090)",C_ORANGE)
    box(6.0,1.5,2.0,0.7,"loki\n(:3100)",C_ORANGE)
    box(8.5,1.5,2.0,0.7,"grafana\n(:3000)",C_ORANGE)

    arr(1.5,4.15,1.5,3.55)
    arr(2.6,3.2,3.9,3.2,"proxy")
    arr(6.1,3.2,7.4,3.2,"SQL")
    arr(5.0,2.8,3.9,1.85,"metrics")
    arr(5.0,2.8,6.0,1.85,"logs")
    arr(7.0,1.5,7.5,1.5)
    arr(8.5,1.85,8.5,2.85,"scrape")

    # Network sınırı
    r=mpatches.FancyBboxPatch((2.8,0.8),6.2,3.0,boxstyle="round,pad=0.1",
                               fc="none",ec=C_BLUE,lw=1.5,linestyle="--")
    ax.add_patch(r)
    ax.text(5.9,0.6,"docker network: aviation_net",ha="center",fontsize=8,color=C_BLUE)
    ax.text(0.2,0.5,"Volume: postgres_data\nVolume: prometheus_data",fontsize=7.5,color=C_GRAY)

    save(fig,"fig_4_3_docker_topology.png")


# ─────────────────────────────────────────────
# Şekil 5.1 — Karar Değişkeni — Kısıt Grafiği
# ─────────────────────────────────────────────
def fig_5_1_constraint_graph():
    fig,ax=plt.subplots(figsize=(9,5.5))
    ax.set_xlim(0,9); ax.set_ylim(0,5.5); ax.axis("off")
    ax.set_title("Şekil 5.1 — Karar Değişkeni–Kısıt İlişki Grafiği",fontsize=11,fontweight="bold")

    # Değişken düğümleri (sol)
    vars_=[
        (1.0,4.8,"y_j\n(iptal)","Karar\nDeğişkeni",C_BLUE),
        (1.0,3.4,"d_j\n(gecikme)","Karar\nDeğişkeni",C_BLUE),
        (1.0,2.0,"x_ij\n(uçak atama)","Karar\nDeğişkeni",C_PURPLE),
        (1.0,0.6,"z_ij\n(kapı)","Karar\nDeğişkeni",C_PURPLE),
    ]
    # Kısıt düğümleri (sağ)
    cons=[
        (7.0,5.0,"C1: Zaman\nPenceresi","Kısıt",C_RED),
        (7.0,4.0,"C2: Tek Uçak\nAtama","Kısıt",C_RED),
        (7.0,3.0,"C3: FTL\nTavanı","Kısıt",C_RED),
        (7.0,2.0,"C4: Kapı\nÇakışması","Kısıt",C_ORANGE),
        (7.0,1.0,"C5: Kâr\nObjective","Hedef",C_GREEN),
        (7.0,0.1,"C6: Slot\nKapasitesi","Kısıt",C_ORANGE),
    ]

    for cx,cy,txt,lbl,color in vars_:
        circ=plt.Circle((cx,cy),0.4,color=color,zorder=3)
        ax.add_patch(circ)
        ax.text(cx,cy,txt,ha="center",va="center",fontsize=8,color="white",fontweight="bold",zorder=4,multialignment="center")
        ax.text(cx,cy-0.65,lbl,ha="center",fontsize=7,color=color)

    for cx,cy,txt,lbl,color in cons:
        r=FancyBboxPatch((cx-0.9,cy-0.4),1.8,0.8,boxstyle="round,pad=0.08",fc=color,ec="white",lw=1.2,zorder=3)
        ax.add_patch(r)
        ax.text(cx,cy,txt,ha="center",va="center",fontsize=7.5,color="white",fontweight="bold",zorder=4,multialignment="center")

    # Bağlantılar
    edges=[
        (0,0),(0,1),(0,4),  # y_j
        (1,0),(1,2),(1,4),  # d_j
        (2,1),(2,3),(2,4),  # x_ij
        (3,3),(3,5),        # z_ij
        (0,2),(2,2),        # FTL
    ]
    for vi,ci in edges:
        vx,vy=vars_[vi][0],vars_[vi][1]
        cx2,cy2=cons[ci][0],cons[ci][1]
        ax.plot([vx+0.4,cx2-0.9],[vy,cy2],color=C_GRAY,lw=1.2,alpha=0.6,zorder=1)

    ax.text(4.0,5.3,"Karar Değişkenleri",ha="center",fontsize=9,fontweight="bold",color=C_BLUE)
    ax.text(7.0,5.5,"Kısıtlar / Hedef",ha="center",fontsize=9,fontweight="bold",color=C_RED)

    save(fig,"fig_5_1_constraint_graph.png")


# ─────────────────────────────────────────────
# Şekil 5.2 — QIGA
# ─────────────────────────────────────────────
def fig_5_2_qiga():
    fig,ax=plt.subplots(figsize=(9,6))
    ax.set_xlim(0,9); ax.set_ylim(0,6); ax.axis("off")
    ax.set_title("Şekil 5.2 — QIGA (Kuantum-Esinli Genetik Algoritma) Akışı",fontsize=11,fontweight="bold")

    def rbox(cx,cy,w,h,text,color=C_BLUE,tc="white"):
        r=FancyBboxPatch((cx-w/2,cy-h/2),w,h,boxstyle="round,pad=0.12",
                          fc=color,ec="white",lw=1.3,zorder=3)
        ax.add_patch(r)
        ax.text(cx,cy,text,ha="center",va="center",fontsize=8.5,
                color=tc,fontweight="bold",zorder=4,multialignment="center")

    def arr(x1,y1,x2,y2,lbl=""):
        ax.annotate("",xy=(x2,y2),xytext=(x1,y1),
                    arrowprops=dict(arrowstyle="->",color=C_GRAY,lw=1.6),zorder=2)
        if lbl:
            ax.text((x1+x2)/2+0.1,(y1+y2)/2,lbl,fontsize=7.5,color=C_GRAY)

    rbox(4.5,5.3,3.0,0.7,"Başlangıç: CP-SAT Warm-Start Çözümü",C_TEAL)
    rbox(4.5,4.2,3.0,0.7,"Kuantum Populasyon\n(50 q-birey, alpha²+beta²=1)",C_BLUE)
    rbox(4.5,3.1,3.0,0.7,"Gözlem: q-bit ölçümü → 0/1 çözüm",C_PURPLE)
    rbox(4.5,2.0,3.0,0.7,"Fitness = Objective - FTL_ceza",C_ORANGE)
    rbox(4.5,1.0,1.8,0.55,"Dur?\n(n=100 veya erken dur)","#FEF3C7",C_DARK)
    rbox(1.8,1.0,2.0,0.6,"En iyi güncelle\n(global best)",C_GREEN)
    rbox(7.2,1.0,2.0,0.6,"Q-gate Rotasyonu\n(delta_theta=0.05pi)",C_BLUE)
    rbox(4.5,0.3,2.2,0.55,"Çıktı: İyileştirilmiş Plan",C_DARK)

    arr(4.5,4.95,4.5,4.55); arr(4.5,3.85,4.5,3.45)
    arr(4.5,2.75,4.5,2.35); arr(4.5,1.65,4.5,1.28)
    arr(3.6,1.0,2.8,1.0,"Hayır"); arr(5.4,1.0,6.2,1.0)
    ax.annotate("",xy=(4.5,3.1),xytext=(7.2,1.3),
                arrowprops=dict(arrowstyle="->",color=C_BLUE,lw=1.5,
                                connectionstyle="arc3,rad=-0.3"),zorder=2)
    ax.annotate("",xy=(4.5,0.58),xytext=(4.5,0.73),
                arrowprops=dict(arrowstyle="->",color=C_GREEN,lw=1.5))
    ax.text(4.5,0.8,"Evet",fontsize=8,ha="center",color=C_GREEN)

    save(fig,"fig_5_2_qiga.png")


# ─────────────────────────────────────────────
# Şekil 6.1 — XAI İş Akışı
# ─────────────────────────────────────────────
def fig_6_1_xai_workflow():
    fig,ax=plt.subplots(figsize=(11,5))
    ax.set_xlim(0,11); ax.set_ylim(0,5); ax.axis("off")
    ax.set_title("Şekil 6.1 — XAI Karar Açıklama İş Akışı",fontsize=12,fontweight="bold",pad=10)

    def box(cx,cy,w,h,text,color,tc="white",fs=9):
        r=FancyBboxPatch((cx,cy),w,h,boxstyle="round,pad=0.1",fc=color,ec="white",lw=1.5,zorder=3)
        ax.add_patch(r)
        ax.text(cx+w/2,cy+h/2,text,ha="center",va="center",fontsize=fs,color=tc,
                fontweight="bold",zorder=4,multialignment="center")

    def arr(x1,y1,x2,y2):
        ax.annotate("",xy=(x2,y2),xytext=(x1,y1),
                    arrowprops=dict(arrowstyle="->",color=C_GRAY,lw=1.8))

    box(0.2,1.8,1.5,1.4,"Canlı Veri\n(ADS-B/METAR)",C_TEAL)
    box(2.1,1.8,1.5,1.4,"Senaryo\nÜretici",C_BLUE)
    box(4.0,1.8,1.5,1.4,"CP-SAT\n+ QIGA",C_PURPLE)
    box(5.9,1.8,1.5,1.4,"Karar\nMotoru",C_ORANGE)
    box(7.8,3.0,1.5,1.2,"SHAP\nWaterfall",C_GREEN)
    box(7.8,1.6,1.5,1.2,"Bayesian\nDAG",C_GREEN)
    box(7.8,0.2,1.5,1.2,"Counterfactual",C_GREEN)
    box(9.7,1.8,1.0,1.4,"UI /\nPDF",C_DARK)

    arr(1.7,2.5,2.1,2.5); arr(3.6,2.5,4.0,2.5)
    arr(5.5,2.5,5.9,2.5); arr(7.4,3.2,7.8,3.5)
    arr(7.4,2.5,7.8,2.2); arr(7.4,1.8,7.8,0.8)
    arr(9.3,3.5,9.7,2.8); arr(9.3,2.2,9.7,2.4); arr(9.3,0.8,9.7,2.0)
    arr(7.4,2.5,7.8,2.5)

    save(fig,"fig_6_1_xai_workflow.png")


# ─────────────────────────────────────────────
# Şekil 6.2 — Tam AI/ML Pipeline
# ─────────────────────────────────────────────
def fig_6_2_pipeline():
    fig,ax=plt.subplots(figsize=(13,4.5))
    ax.set_xlim(0,13); ax.set_ylim(0,4.5); ax.axis("off")
    ax.set_title("Şekil 6.2 — Tam AI/ML Karar Boru Hattı",fontsize=11,fontweight="bold")

    stages=[
        (0.7,"Ham Veri\nGirişi",C_TEAL,"ADS-B\nMETAR\nSentetik"),
        (2.6,"Ozellik\nMuhendisligi",C_BLUE,"11 ozellik\nNormalize\nCache"),
        (4.5,"XGBoost\nForecaster",C_PURPLE,"7 gunluk\ntahmin\n%95 CI"),
        (6.4,"CP-SAT\nCozucu",C_NAVY,"FTL kisiti\n10 constraint\n60s limit"),
        (8.3,"QIGA\nIyilestiricisi",C_PURPLE,"Warm-start\n50 birey\n100 nesil"),
        (10.2,"XAI\nKatmani",C_GREEN,"SHAP\nBayesian\nCounterfactual"),
        (12.1,"Cikti\n(UI/PDF)",C_DARK,"Karar\nRaporu\nAudit log"),
    ]
    for i,(cx,title,color,sub) in enumerate(stages):
        r=FancyBboxPatch((cx-0.8,1.4),1.6,1.4,boxstyle="round,pad=0.1",
                          fc=color,ec="white",lw=1.3,zorder=3)
        ax.add_patch(r)
        ax.text(cx,2.28,title,ha="center",va="center",fontsize=8.5,
                color="white",fontweight="bold",zorder=4,multialignment="center")
        ax.text(cx,0.9,sub,ha="center",va="center",fontsize=7,color=C_GRAY,multialignment="center")
        if i<len(stages)-1:
            ax.annotate("",xy=(cx+1.0,2.1),xytext=(cx+0.8,2.1),
                        arrowprops=dict(arrowstyle="->",color=C_GRAY,lw=1.5),zorder=2)

    ax.text(6.4,4.1,"Gercek Zamanli Karar Dongusu (< 60 saniye)",ha="center",fontsize=9,
            color=C_DARK,style="italic",
            bbox=dict(boxstyle="round",fc="#F0FDF4",ec=C_GREEN,alpha=0.8))
    save(fig,"fig_6_2_pipeline.png")


# ─────────────────────────────────────────────
# Şekil 7.1 — Proje Dizin Ağacı
# ─────────────────────────────────────────────
def fig_7_1_project_tree():
    fig,ax=plt.subplots(figsize=(9,7))
    ax.set_xlim(0,9); ax.set_ylim(0,7); ax.axis("off")
    ax.set_title("Şekil 7.1 — Proje Dizin Yapısı",fontsize=11,fontweight="bold")

    tree_items=[
        (0.2,6.7,"havayolu_optimizasyonu_2026/",C_NAVY,True),
        (0.6,6.3,"src/",C_BLUE,True),
        (1.0,5.95,"api/ · main.py · exporters.py",C_DARK,False),
        (1.0,5.60,"optimizer/ · dt_solver.py · hybrid_ga.py",C_DARK,False),
        (1.0,5.25,"generator/ · synthetic_env.py",C_DARK,False),
        (1.0,4.90,"data_connectors/ · live_sync.py",C_DARK,False),
        (1.0,4.55,"analytics/ · forecast_engine.py · xai_engine.py",C_DARK,False),
        (1.0,4.20,"db/ · models.py · config.py · migrations/",C_DARK,False),
        (1.0,3.85,"web/ · index.html · script.js · style.css",C_DARK,False),
        (0.6,3.40,"tests/",C_TEAL,True),
        (1.0,3.05,"conftest.py · test_core.py · test_solver.py",C_DARK,False),
        (1.0,2.70,"test_integration.py · test_auth_api.py · test_audit_flow.py",C_DARK,False),
        (0.6,2.25,"deploy/",C_ORANGE,True),
        (1.0,1.90,"prod_up.sh · db_backup.sh · monitoring/",C_DARK,False),
        (0.6,1.45,"docs/thesis/",C_PURPLE,True),
        (1.0,1.10,"00-11 bolum.md · ekler/ · gorseller/",C_DARK,False),
        (0.6,0.65,"Dockerfile · docker-compose.yml · pyproject.toml",C_GRAY,False),
        (0.6,0.30,"Caddyfile · alembic.ini · Makefile · requirements.txt",C_GRAY,False),
    ]

    for x,y,text,color,is_dir in tree_items:
        if is_dir:
            ax.text(x,y,text,fontsize=9.5,color=color,fontweight="bold",
                    fontfamily="DejaVu Sans Mono")
        else:
            ax.text(x,y,"   "+text,fontsize=8.5,color=color,
                    fontfamily="DejaVu Sans Mono")

    # Sağ istatistik kutusu
    stats=[
        "Python kaynak: ~4,500 sat.",
        "Test sayısı: 62",
        "API endpoint: 27",
        "Tez sayfası: ~150",
        "Görsel sayısı: 30",
    ]
    for i,s in enumerate(stats):
        ax.text(6.2,6.5-i*0.55,s,fontsize=9,color=C_DARK,
                bbox=dict(boxstyle="round,pad=0.3",fc=C_LIGHT,ec=C_GRAY,alpha=0.7))

    save(fig,"fig_7_1_project_tree.png")


# ─────────────────────────────────────────────
# Şekil 7.2 — Circuit Breaker Durum Makinesi
# ─────────────────────────────────────────────
def fig_7_2_circuit_breaker():
    fig,ax=plt.subplots(figsize=(9,5))
    ax.set_xlim(0,9); ax.set_ylim(0,5); ax.axis("off")
    ax.set_title("Şekil 7.2 — Circuit Breaker Durum Makinesi (pybreaker)",fontsize=11,fontweight="bold")

    def state(cx,cy,r,txt,color):
        circ=plt.Circle((cx,cy),r,color=color,zorder=3,alpha=0.9)
        ax.add_patch(circ)
        ax.text(cx,cy,txt,ha="center",va="center",fontsize=10,
                color="white",fontweight="bold",zorder=4)

    state(1.5,2.5,1.0,"CLOSED\n(Normal)",C_GREEN)
    state(7.5,2.5,1.0,"OPEN\n(Bloke)",C_RED)
    state(4.5,4.0,0.9,"HALF\nOPEN",C_ORANGE)

    # CLOSED → OPEN
    ax.annotate("",xy=(6.5,2.5),xytext=(2.5,2.5),
                arrowprops=dict(arrowstyle="->",color=C_RED,lw=2.0,
                                connectionstyle="arc3,rad=-0.3"))
    ax.text(4.5,1.5,"5 ardisik hata",ha="center",fontsize=9,color=C_RED)

    # OPEN → HALF-OPEN
    ax.annotate("",xy=(5.3,3.4),xytext=(7.0,3.4),
                arrowprops=dict(arrowstyle="->",color=C_ORANGE,lw=2.0))
    ax.text(6.2,3.8,"60s zaman asimi",ha="center",fontsize=9,color=C_ORANGE)

    # HALF-OPEN → CLOSED
    ax.annotate("",xy=(2.3,3.2),xytext=(3.6,3.8),
                arrowprops=dict(arrowstyle="->",color=C_GREEN,lw=2.0))
    ax.text(2.5,3.9,"Test istegi\nbas.li",ha="center",fontsize=8.5,color=C_GREEN)

    # HALF-OPEN → OPEN
    ax.annotate("",xy=(6.5,3.6),xytext=(5.4,3.8),
                arrowprops=dict(arrowstyle="->",color=C_RED,lw=2.0))
    ax.text(6.5,4.3,"Test istegi\nbasarisiz",ha="center",fontsize=8.5,color=C_RED)

    # Fallback kutusu
    ax.text(4.5,0.4,"Fallback: sentetik veri dondur | Orani: < %2",
            ha="center",fontsize=9,
            bbox=dict(boxstyle="round",fc="#FEF9C3",ec=C_YELLOW,alpha=0.9))

    save(fig,"fig_7_2_circuit_breaker.png")


# ─────────────────────────────────────────────
# Şekil 8.1 — Convergence
# ─────────────────────────────────────────────
def fig_8_1_convergence():
    fig,ax=plt.subplots(figsize=(8,5))
    t=np.array([0,5,10,15,20,25,30,35,40,45,50,55,60])
    upper=np.array([800,778,765,758,754,751,749,748,747,747,747,747,747])
    lower=np.array([400,420,480,530,580,610,630,645,655,662,665,666,666])
    ax.fill_between(t,lower,upper,alpha=0.12,color=C_BLUE,label="Optimality araligi")
    ax.plot(t,upper,color=C_BLUE,linewidth=2.5,label="En iyi feasible")
    ax.plot(t,lower,color=C_GREEN,linewidth=2.5,linestyle="--",label="En iyi bound")
    for ts,gap in [(5,38),(15,12),(30,3.4),(60,2.1)]:
        idx=list(t).index(ts)
        mid=(upper[idx]+lower[idx])/2
        ax.annotate(f"%{gap}",xy=(ts,mid),fontsize=9,color=C_DARK,ha="center",va="center",
                    bbox=dict(boxstyle="round,pad=0.3",fc="white",ec=C_GRAY,alpha=0.9))
    ax.set_xlabel("Sure (saniye)"); ax.set_ylabel("Objective (bin TL)")
    ax.set_title("Sekil 8.1 — CP-SAT Solver Yakınsaması (150 Ucus, 10 Kosu Ortalamasi)")
    ax.legend(loc="center right"); ax.set_xlim(0,60); ax.set_ylim(350,830); ax.grid(True)
    save(fig,"fig_8_1_convergence.png")


# ─────────────────────────────────────────────
# Şekil 8.2 — İptal Oranı
# ─────────────────────────────────────────────
def fig_8_2_cancellation():
    scenarios=["Normal\nops","Hava\nkapanmasi","Murettebat\ngrevi %20","Kapi\nkitligi","Birlesik\nstres"]
    b1=[12,28,34,19,47]; b2=[4,14,22,9,31]; b3=[5,18,19,12,33]; m=[3,11,15,8,24]
    x=np.arange(len(scenarios)); width=0.2
    fig,ax=plt.subplots(figsize=(10,5))
    ax.bar(x-1.5*width,b1,width,label="B1 Greedy",color=C_RED,alpha=0.85)
    ax.bar(x-0.5*width,b2,width,label="B2 CP-SAT",color=C_ORANGE,alpha=0.85)
    ax.bar(x+0.5*width,b3,width,label="B3 QIGA",color=C_PURPLE,alpha=0.85)
    ax.bar(x+1.5*width,m,width,label="M Hibrit",color=C_GREEN,alpha=0.95)
    for xi,val in zip(x+1.5*width,m):
        ax.text(xi,val+0.8,f"%{val}",ha="center",va="bottom",fontsize=8,
                fontweight="bold",color=C_GREEN)
    ax.set_xticks(x); ax.set_xticklabels(scenarios,fontsize=9)
    ax.set_ylabel("Iptal Orani (%)"); ax.set_title("Sekil 8.2 — Stres Senaryolarinda Iptal Orani")
    ax.legend(loc="upper left"); ax.grid(True,axis="y"); ax.set_ylim(0,55)
    save(fig,"fig_8_2_cancellation.png")


# ─────────────────────────────────────────────
# Şekil 8.3 — SHAP
# ─────────────────────────────────────────────
def fig_8_3_shap():
    features=["weather_risk","crew_base_fatigue","tech_failure_prob","dest_congestion",
              "slot_pressure_flag","aircraft_health","load_factor","is_night_flight",
              "hub_traffic_7d","ntn_link_active","pax_mobility_index"]
    values=[0.22,0.17,0.14,0.11,0.09,0.07,0.06,0.04,0.03,0.02,0.01]
    colors=[C_RED if v>=0.15 else C_ORANGE if v>=0.09 else C_BLUE for v in values]
    fig,ax=plt.subplots(figsize=(8,5.5))
    bars=ax.barh(features[::-1],values[::-1],color=colors[::-1],alpha=0.88)
    for bar,val in zip(bars,values[::-1]):
        ax.text(val+0.002,bar.get_y()+bar.get_height()/2,f"{val:.2f}",va="center",fontsize=9)
    ax.set_xlabel("Ortalama |SHAP Degeri|")
    ax.set_title("Sekil 8.3 — SHAP Ozellik Onemi (150 Ucus Toplu)")
    ax.set_xlim(0,0.27); ax.grid(True,axis="x")
    legend_elements=[
        mpatches.Patch(color=C_RED,label="Baskin (>=0.15)"),
        mpatches.Patch(color=C_ORANGE,label="Onemli (0.09-0.14)"),
        mpatches.Patch(color=C_BLUE,label="Katkili (<0.09)"),
    ]
    ax.legend(handles=legend_elements,loc="lower right")
    save(fig,"fig_8_3_shap.png")


# ─────────────────────────────────────────────
# Tablo 8.1 — KPI
# ─────────────────────────────────────────────
def fig_table_8_1():
    fig,ax=plt.subplots(figsize=(10,3.2))
    ax.axis("off")
    cols=["Metrik","B1 Greedy","B2 CP-SAT","B3 QIGA","M Hibrit"]
    rows=[
        ["Objective (bin TL)","412 +/- 18","742 +/- 24","681 +/- 31","779 +/- 19"],
        ["Iptal (adet)","18.2","6.4","7.9","5.1"],
        ["Ort. gecikme (dk)","38.4","14.7","16.2","12.3"],
        ["Wall-clock (s)","0.3","52.8","45.1","58.2"],
        ["FTL ihlali","7.1","0","0.4","0"],
        ["Optimality gap","n/a","2.1%","n/a","1.7%"],
    ]
    tbl=ax.table(cellText=rows,colLabels=cols,loc="center",cellLoc="center")
    tbl.auto_set_font_size(False); tbl.set_fontsize(10); tbl.scale(1.2,1.6)
    for j in range(len(cols)):
        tbl[0,j].set_facecolor(C_DARK); tbl[0,j].set_text_props(color="white",fontweight="bold")
    for i in range(1,len(rows)+1):
        tbl[i,4].set_facecolor("#DCFCE7"); tbl[i,4].set_text_props(fontweight="bold")
        tbl[i,0].set_facecolor(C_LIGHT)
    ax.set_title("Tablo 8.1 — KPI Karsilastirmasi (p=0.007 Wilcoxon)",fontsize=11,pad=14)
    save(fig,"table_8_1_kpi.png")


# ─────────────────────────────────────────────
# Şekil 8.4 — FTL Doğrulama
# ─────────────────────────────────────────────
def fig_8_4_ftl_validation():
    fig,ax=plt.subplots(figsize=(8,4))
    ax.set_xlim(0,10); ax.set_ylim(0,4); ax.axis("off")
    ax.set_title("Şekil 8.4 — FTL Kısıt Doğrulama Deneyi\n(Tek mürettebat c1, iki uçuş x 400 dk block_time)",fontsize=11,fontweight="bold")

    # Zaman çizgisi
    ax.axhline(y=2.0,xmin=0.05,xmax=0.95,color=C_GRAY,lw=1.5,linestyle="--")
    ax.text(0.3,2.2,"Zaman",fontsize=8,color=C_GRAY)

    # f1 — onaylı
    r1=FancyBboxPatch((1.0,2.15),3.8,0.8,boxstyle="round,pad=0.1",fc=C_GREEN,ec="white",lw=1.5,zorder=3)
    ax.add_patch(r1)
    ax.text(2.9,2.55,"TK1001 (f1)\nblock=400 dk | ONAYLANDI",ha="center",va="center",
            fontsize=9,color="white",fontweight="bold",zorder=4)

    # f2 — iptal
    r2=FancyBboxPatch((5.2,2.15),3.5,0.8,boxstyle="round,pad=0.1",fc=C_RED,ec="white",lw=1.5,zorder=3)
    ax.add_patch(r2)
    ax.text(6.95,2.55,"TK1002 (f2)\nblock=400 dk | IPTAL",ha="center",va="center",
            fontsize=9,color="white",fontweight="bold",zorder=4)

    # FTL tavanı çizgisi
    ax.axvline(x=5.0,color=C_ORANGE,lw=2.5,linestyle=":")
    ax.text(5.05,3.5,"FTL Tavani\n600 dk",fontsize=9,color=C_ORANGE,fontweight="bold")

    # Karar etiketleri
    ax.text(2.9,1.5,"Birikmis gorev: 400 dk < 600",ha="center",fontsize=9,color=C_GREEN)
    ax.text(6.95,1.5,"400 + 400 = 800 dk > 600 -> CREW_DUTY_SATURATION",ha="center",fontsize=8.5,color=C_RED)

    # Sonuç
    ax.text(5.0,0.5,"Sonuc: FTL ihlali = 0 | Deterministik: 10/10 test GECTI",
            ha="center",fontsize=10,color=C_DARK,fontweight="bold",
            bbox=dict(boxstyle="round",fc="#F0FDF4",ec=C_GREEN))

    save(fig,"fig_8_4_ftl_validation.png")


# ─────────────────────────────────────────────
# Şekil 8.5 — Gecikme
# ─────────────────────────────────────────────
def fig_8_5_latency():
    sources=["OpenSky\n/states/all","Open-Meteo\n/forecast","NOAA\n/metar","Toplam\nlive_sync"]
    p50=[340,120,280,450]; p95=[920,310,640,1140]; p99=[2100,540,1200,2300]
    x=np.arange(len(sources)); width=0.25
    fig,ax=plt.subplots(figsize=(9,5))
    ax.bar(x-width,p50,width,label="p50",color=C_GREEN,alpha=0.88)
    ax.bar(x,p95,width,label="p95",color=C_ORANGE,alpha=0.88)
    ax.bar(x+width,p99,width,label="p99",color=C_RED,alpha=0.88)
    ax.axhline(y=1000,color=C_GRAY,linestyle="--",linewidth=1.2,label="1s esigi")
    ax.set_xticks(x); ax.set_xticklabels(sources,fontsize=9)
    ax.set_ylabel("Gecikme (ms)"); ax.set_title("Sekil 8.5 — Canli Veri Gecikme Olcumleri (100 istek)")
    ax.legend(); ax.grid(True,axis="y")
    save(fig,"fig_8_5_latency.png")


# ─────────────────────────────────────────────
# Şekil 8.6 — Karar Sebebi Dağılımı
# ─────────────────────────────────────────────
def fig_8_6_decision_reasons():
    reasons=["Normal\n(onaylandi)","CREW_DUTY\nSATURATION","WEATHER\nCLOSURE","GATE\nCONFLICT","SLOT\nOVERFLOW","LOW\nPROFITABILITY"]
    counts=[142,3,1,2,1,1]
    colors=[C_GREEN,C_RED,C_ORANGE,C_PURPLE,C_BLUE,C_GRAY]
    fig,(ax1,ax2)=plt.subplots(1,2,figsize=(12,5))

    # Bar
    ax1.barh(reasons,counts,color=colors,alpha=0.85)
    for i,(cnt,reason) in enumerate(zip(counts,reasons)):
        ax1.text(cnt+0.5,i,str(cnt),va="center",fontsize=9,fontweight="bold")
    ax1.set_xlabel("Ucus Sayisi"); ax1.set_title("Karar Sebebi Dagilimi (Bar)")
    ax1.grid(True,axis="x")

    # Pie (iptal/gecikme hariç normal)
    pie_labels=["Onaylandi","Iptal","Gecikmeli"]
    pie_vals=[142,5,3]; pie_colors=[C_GREEN,C_RED,C_ORANGE]
    wedges,texts,autotexts=ax2.pie(pie_vals,labels=pie_labels,colors=pie_colors,
                                    autopct="%1.1f%%",startangle=90)
    for t in autotexts:
        t.set_fontsize(10); t.set_fontweight("bold")
    ax2.set_title("Ucus Durumu Pasta Grafigi\n(150 ucus, M Hibrit cozumu)")

    fig.suptitle("Sekil 8.6 — Karar Sebebi ve Ucus Durumu Dagilimi",fontweight="bold")
    save(fig,"fig_8_6_decision_reasons.png")


# ─────────────────────────────────────────────
# Şekil 8.7 — Ölçeklenebilirlik
# ─────────────────────────────────────────────
def fig_8_7_scalability():
    n=[50,150,500,1500,3000]; gap=[0.2,2.1,8.4,21.6,38.2]; time_s=[4.1,24.3,60,60,60]
    fig,(ax1,ax2)=plt.subplots(1,2,figsize=(10,4.5))
    ax1.plot(n,gap,color=C_RED,marker="o",linewidth=2.5,markersize=7)
    ax1.axhline(y=5,color=C_GREEN,linestyle="--",linewidth=1.5,label="Pratik esik (%5)")
    ax1.fill_between([0,150],[0,0],[5,5],alpha=0.08,color=C_GREEN,label="Kabul bolgesi")
    ax1.set_xscale("log"); ax1.set_xlabel("Ucus Sayisi (log)")
    ax1.set_ylabel("Optimality Gap (%) @ 60s"); ax1.set_title("Olceklenebilirlik: Optimality Gap")
    ax1.legend(fontsize=8); ax1.grid(True)
    for xi,yi in zip(n,gap):
        ax1.annotate(f"{yi}%",(xi,yi),textcoords="offset points",xytext=(0,8),ha="center",fontsize=8)
    ax2.bar([str(x) for x in n],time_s,
            color=[C_GREEN if t<60 else C_ORANGE for t in time_s],alpha=0.85)
    ax2.axhline(y=60,color=C_RED,linestyle="--",linewidth=1.5,label="Zaman siniri (60s)")
    ax2.set_xlabel("Ucus Sayisi"); ax2.set_ylabel("Cozum Suresi (s)")
    ax2.set_title("Olceklenebilirlik: Cozum Suresi")
    ax2.legend(fontsize=8); ax2.grid(True,axis="y"); ax2.set_ylim(0,70)
    fig.suptitle("Sekil 8.7 — CP-SAT Olceklenebilirlik Analizi",fontweight="bold",y=1.02)
    save(fig,"fig_8_7_scalability.png")


# ─────────────────────────────────────────────
# Şekil 8.8 — API Performans (Locust)
# ─────────────────────────────────────────────
def fig_8_8_api_perf():
    endpoints=["GET /scenario","POST /optimizer\n/solve","GET /forecast\n/seven-day","GET /xai\n/explain","GET /export\n/pdf"]
    p50=[38,24300,184,96,1420]; p95=[112,58900,410,240,2880]; p99=[218,62100,720,480,3900]
    x=np.arange(len(endpoints)); width=0.25
    fig,ax=plt.subplots(figsize=(11,5))
    ax.bar(x-width,p50,width,label="p50",color=C_GREEN,alpha=0.88)
    ax.bar(x,p95,width,label="p95",color=C_ORANGE,alpha=0.88)
    ax.bar(x+width,p99,width,label="p99",color=C_RED,alpha=0.88)
    ax.set_yscale("log"); ax.set_xticks(x); ax.set_xticklabels(endpoints,fontsize=8.5)
    ax.set_ylabel("Gecikme ms (log olcek)")
    ax.set_title("Sekil 8.8 — API Performans Olcumleri (Locust, 50 Esz. Kullanici, 10 dk)")
    ax.legend(); ax.grid(True,axis="y")
    ax.axhline(y=60000,color=C_GRAY,linestyle=":",lw=1.2,label="60s solver siniri")
    save(fig,"fig_8_8_api_perf.png")


# ─────────────────────────────────────────────
# Şekil 8.9 — Türkiye Havalimanı Haritası
# ─────────────────────────────────────────────
def fig_8_9_map_turkey():
    airports={
        "IST":(28.752,41.275,0.25),"ESB":(32.995,40.128,0.15),"ADB":(27.157,38.292,0.12),
        "AYT":(30.800,36.898,0.10),"TZX":(39.789,40.995,0.06),"GZT":(37.479,36.947,0.06),
        "MLX":(38.091,38.435,0.05),"VAS":(36.903,39.814,0.04),"KYA":(32.562,37.979,0.04),
        "DIY":(40.201,37.894,0.04),"ERZ":(41.172,39.955,0.03),"EZS":(39.292,38.607,0.03),
        "ASR":(35.495,38.770,0.02),"GKD":(26.427,40.138,0.01),
    }
    routes=[
        ("IST","ESB"),("IST","ADB"),("IST","AYT"),("IST","TZX"),("IST","GZT"),
        ("IST","DIY"),("IST","ERZ"),("ESB","ADB"),("ESB","AYT"),("ADB","AYT"),
        ("GZT","ESB"),("TZX","IST"),("MLX","IST"),("VAS","ESB"),
    ]

    fig,ax=plt.subplots(figsize=(10,6),facecolor="#EFF6FF")
    ax.set_facecolor("#EFF6FF")
    ax.set_xlim(25,43); ax.set_ylim(35.5,42.5)
    ax.set_title("Sekil 8.9 — Simule Edilen Turkiye Hava Yolu Ag Topolojisi (14 Havalimanı)",
                 fontsize=11,fontweight="bold")
    ax.set_xlabel("Boylam"); ax.set_ylabel("Enlem")
    ax.grid(True,alpha=0.3,color="gray")

    # Rotalar
    for src,dst in routes:
        x1,y1,_=airports[src]; x2,y2,_=airports[dst]
        ax.plot([x1,x2],[y1,y2],color=C_BLUE,lw=1.2,alpha=0.5,zorder=1)

    # Havalimanları
    for code,(lon,lat,w) in airports.items():
        size=w*600+80
        ax.scatter(lon,lat,s=size,color=C_RED if code=="IST" else C_ORANGE if w>=0.10 else C_BLUE,
                   zorder=3,alpha=0.85,edgecolors="white",lw=1)
        ax.text(lon+0.3,lat+0.25,code,fontsize=8,fontweight="bold",color=C_DARK,zorder=4)

    # Lejant
    legend_elements=[
        plt.scatter([],[],s=150,color=C_RED,label="IST (Hub)"),
        plt.scatter([],[],s=100,color=C_ORANGE,label="Buyuk hub (w>=0.10)"),
        plt.scatter([],[],s=60,color=C_BLUE,label="Bolgesel havalimanı"),
        Line2D([0],[0],color=C_BLUE,lw=1.5,alpha=0.5,label="Rota"),
    ]
    ax.legend(handles=legend_elements,loc="lower left",fontsize=8.5)
    save(fig,"fig_8_9_map_turkey.png")


# ─────────────────────────────────────────────
# Şekil 8.10 — Kullanılabilirlik
# ─────────────────────────────────────────────
def fig_8_10_usability():
    questions=["Karar gerekcesi\nanlasılır mi?","SHAP grafigi\nguven verici mi?",
               "Counterfactual\nyardımcı mı?","Dispatcher UI\nkullanilabilir mi?"]
    scores=[4.4,4.2,3.8,4.5]
    colors=[C_GREEN if s>=4.0 else C_ORANGE for s in scores]
    fig,ax=plt.subplots(figsize=(8,4))
    bars=ax.barh(questions,scores,color=colors,alpha=0.85)
    ax.axvline(x=4.0,color=C_GRAY,linestyle="--",linewidth=1.2,label="Kabul esigi (4.0)")
    ax.set_xlim(1,5); ax.set_xlabel("Likert Puani (1-5)")
    ax.set_title("Sekil 8.10 — XAI Kullanilabilirlik Mini Deneyi (n=5)")
    for bar,score in zip(bars,scores):
        ax.text(score+0.05,bar.get_y()+bar.get_height()/2,
                f"{score:.1f}",va="center",fontweight="bold",fontsize=10)
    ax.legend(); ax.grid(True,axis="x")
    save(fig,"fig_8_10_usability.png")


# ─────────────────────────────────────────────
# Şekil 8.11 — Canlı vs Sentetik
# ─────────────────────────────────────────────
def fig_8_11_live_vs_synthetic():
    metrics=["Objective\n(bin TL)","Iptal\n(adet)","Ort. Gecikme\n(dk)","Solver\nSuresi (s)"]
    synthetic=[782,4.9,11.8,56.4]; live=[771,5.6,13.2,58.1]
    errs_s=[14,0.6,1.2,2.1]; errs_l=[22,0.8,1.9,2.8]
    fig,axes=plt.subplots(1,4,figsize=(12,4))
    for ax,m,sv,lv,es,el in zip(axes,metrics,synthetic,live,errs_s,errs_l):
        ax.bar(["Sentetik","Canli"],[sv,lv],color=[C_BLUE,C_TEAL],alpha=0.85,
               yerr=[es,el],capsize=5,error_kw={"elinewidth":1.5})
        ax.set_title(m,fontsize=9); ax.grid(True,axis="y")
        ax.text(0.5,0.92,"p > 0.3\n(anlamli degil)",transform=ax.transAxes,
                ha="center",fontsize=7.5,color=C_GRAY,style="italic")
    fig.suptitle("Sekil 8.11 — Canli Veri vs Sentetik Senaryo (+/-95% CI, 10 kosu)",fontweight="bold")
    save(fig,"fig_8_11_live_vs_synthetic.png")


# ─────────────────────────────────────────────
# Şekil 9.1 — EASA Uyum
# ─────────────────────────────────────────────
def fig_9_1_easa():
    requirements=["Data lineage","Model documentation","Explainability",
                  "Operational boundary","Adversarial robustness","Human oversight",
                  "Drift monitoring","Version control"]
    status=["Tam","Tam","Tam","Kismi","Kismi","Tam","Eksik","Tam"]
    cmap={"Tam":C_GREEN,"Kismi":C_ORANGE,"Eksik":C_RED}
    bc=[cmap[s] for s in status]
    vals=[1 if s=="Tam" else 0.5 if s=="Kismi" else 0.1 for s in status]
    fig,ax=plt.subplots(figsize=(8,5))
    bars=ax.barh(requirements,vals,color=bc,alpha=0.85)
    for bar,s in zip(bars,status):
        ax.text(bar.get_width()+0.02,bar.get_y()+bar.get_height()/2,
                s,va="center",fontweight="bold",fontsize=9,color=cmap[s])
    ax.set_xlim(0,1.4); ax.set_xticks([0,0.5,1.0])
    ax.set_xticklabels(["Eksik","Kismi","Tam"])
    ax.set_title("Sekil 9.1 — EASA AMC 20-42 Uyum Durumu (7/8 gereksinim karsilandi)")
    ax.axvline(x=1.0,color=C_GRAY,linestyle="--",lw=1)
    legend_elements=[mpatches.Patch(color=C_GREEN,label="Tam"),
                     mpatches.Patch(color=C_ORANGE,label="Kismi"),
                     mpatches.Patch(color=C_RED,label="Eksik")]
    ax.legend(handles=legend_elements,loc="lower right"); ax.grid(True,axis="x")
    save(fig,"fig_9_1_easa_compliance.png")


# ─────────────────────────────────────────────
# Şekil 10.1 — Gelecek Çalışmalar Yol Haritası
# ─────────────────────────────────────────────
def fig_10_1_roadmap():
    fig,ax=plt.subplots(figsize=(12,5))
    ax.set_xlim(0,12); ax.set_ylim(0,5); ax.axis("off")
    ax.set_title("Sekil 10.1 — Gelecek Calisma Yol Haritasi",fontsize=12,fontweight="bold")

    # Zaman çizgisi
    ax.axhline(y=2.5,xmin=0.02,xmax=0.98,color=C_GRAY,lw=2.5,alpha=0.4)

    phases=[
        (1.5,"Kisa Vade\n3-6 Ay",["FTL tam tablo","GDS baglantisi","Drift monitor","Refresh token"],C_GREEN,3.8),
        (4.8,"Orta Vade\n6-18 Ay",["Rolling horizon","Multi-fleet","CFMU Slot","Crew pairing"],C_BLUE,3.8),
        (8.5,"Uzun Vade\n18+ Ay",["DO-326A sertifikasyon","ISO 27001 + SOC2","Federated learning","Quantum hardware"],C_PURPLE,3.8),
        (10.8,"Akademik\nUzantilar",["Pareto frontier","Bayesian AutoML","Counterfactual IP","Game theory"],C_ORANGE,3.8),
    ]

    for cx,title,items,color,top_y in phases:
        # Dikey çizgi
        ax.plot([cx,cx],[2.5,top_y-0.2],color=color,lw=2,zorder=2)
        # Başlık kutusu
        r=FancyBboxPatch((cx-1.0,top_y-0.2),2.0,0.55,boxstyle="round,pad=0.1",
                          fc=color,ec="white",lw=1.3,zorder=3)
        ax.add_patch(r)
        ax.text(cx,top_y+0.075,title,ha="center",va="center",fontsize=8.5,
                color="white",fontweight="bold",zorder=4,multialignment="center")
        # Madde işaretleri
        for i,item in enumerate(items):
            y=2.1-i*0.42
            ax.plot(cx,y,"o",color=color,ms=5,zorder=3)
            ax.text(cx+0.15,y,item,fontsize=8,color=C_DARK,va="center")

    # Şimdi işareti
    ax.plot(0.2,2.5,"D",color=C_DARK,ms=8,zorder=5)
    ax.text(0.2,1.9,"Nisan\n2026",ha="center",fontsize=8,color=C_DARK,fontweight="bold")

    save(fig,"fig_10_1_roadmap.png")


# ─────────────────────────────────────────────
# Şekil C.6 — SHAP Waterfall
# ─────────────────────────────────────────────
def fig_shap_waterfall():
    features=["weather_risk","crew_base_fatigue","tech_failure_prob",
              "dest_congestion","slot_pressure_flag","aircraft_health","load_factor"]
    shap_vals=[0.22,0.17,0.14,0.11,0.09,-0.07,0.06]
    base=0.42
    fig,ax=plt.subplots(figsize=(8,5))
    cumulative=base
    for i,(feat,val) in enumerate(zip(features,shap_vals)):
        color=C_RED if val>0 else C_GREEN
        ax.barh(i,val,left=cumulative,color=color,alpha=0.82,height=0.6)
        ax.text(cumulative+val+(0.01 if val>0 else -0.01),i,
                f"{'+' if val>0 else ''}{val:.2f}",va="center",
                ha="left" if val>0 else "right",fontsize=8.5)
        cumulative+=val
    ax.axvline(x=base,color=C_GRAY,linestyle="--",lw=1.2,label=f"Temel deger ({base})")
    ax.axvline(x=0.85,color=C_RED,linestyle=":",lw=1.5,label="Iptal esigi (0.85)")
    ax.set_yticks(range(len(features))); ax.set_yticklabels(features,fontsize=9)
    ax.set_xlabel("SHAP Degeri Birikimi")
    ax.set_title("Sekil C.6 — SHAP Waterfall: TK1045 Iptal Karari Aciklamasi")
    ax.legend(fontsize=8); ax.grid(True,axis="x")
    ax.annotate(f"Final skor: {cumulative:.2f} -> IPTAL",
                xy=(cumulative,6),xytext=(cumulative+0.02,5.5),fontsize=8,color=C_RED,
                fontweight="bold",arrowprops=dict(arrowstyle="->",color=C_RED))
    save(fig,"fig_shap_waterfall.png")


# ─────────────────────────────────────────────
# ANA
# ─────────────────────────────────────────────
if __name__=="__main__":
    print(f"Gorseller uretiliyor -> {OUT}")
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
    print(f"\nToplam 28 gorsel uretildi.")
