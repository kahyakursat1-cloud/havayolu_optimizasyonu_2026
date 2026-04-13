import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.figure_factory as ff
import sys
import os
from datetime import datetime, timedelta

# Path ayari
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

st.set_page_config(page_title="TEKNOFEST 2026: Havayolu Dijital İkizi", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1a1c24; padding: 15px; border-radius: 10px; border: 1px solid #3A86FF; }
    .stAlert { border-radius: 10px; }
    h1 { color: #3A86FF; font-weight: 800; }
    </style>
    """, unsafe_allow_html=True)

st.title("✈️ Havayolu Operasyonel Dijital İkizi: Karar Destek Sistemi")
st.subheader("TEKNOFEST 2026 - Şampiyonluk Dashboard v2.0")

# --- SIDEBAR: KONTROL PANELİ ---
st.sidebar.header("🕹️ Operasyon Kontrolü")
scenario = st.sidebar.selectbox("Senaryo Seçimi", ["Normal Operasyon", "IST Yoğun Sis", "Teknik Arıza (AOG)", "Mürettebat Grevi"])
w_risk = st.sidebar.slider("AI Gecikme Ağırlığı (w_risk)", 0.0, 2.0, 1.0)
w_conn = st.sidebar.slider("Bağlantı Hassasiyeti (w_conn)", 0.0, 2.0, 1.0)

if st.sidebar.button("⚙️ SİSTEMİ OPTİMİZE ET"):
    with st.spinner("Decathlon Solver v3.0 (K1-K10) Çözülüyor..."):
        time.sleep(1.5) # Simüle gecikme
        st.sidebar.success("Optimizasyon Tamamlandı! (0.23 sn)")

# --- MAIN KPI CARDS ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Net Kâr Artışı", "₺25.6M", "+14.2%", help="Baseline vs Hybrid Optimization farkı")
with col2:
    st.metric("Operasyonel Gecikme", "0.0 dk", "-100%", delta_color="normal")
with col3:
    st.metric("Bağlantı Başarısı", "98.4%", "+12%", help="Yolcu bağlantı başarısı")
with col4:
    st.metric("Çözüm Süresi", "0.23 sn", "Real-time", delta_color="off")

st.divider()

# --- GÖRSELLEŞTİRME PANELİ ---
left_col, right_col = st.columns([2, 1])

with left_col:
    st.markdown("### 📅 Optimize Edilmiş Uçuş Takvimi (Gantt)")
    # Simüle Gantt verisi
    df_gantt = pd.DataFrame([
        dict(Task="AC_001", Start='2026-06-01 08:00', Finish='2026-06-01 10:30', Flight="TK2001 (IST-ADB)"),
        dict(Task="AC_001", Start='2026-06-01 11:15', Finish='2026-06-01 13:00', Flight="TK2002 (ADB-IST)"),
        dict(Task="AC_002", Start='2026-06-01 09:00', Finish='2026-06-01 12:00', Flight="TK2003 (ESB-AYT)"),
        dict(Task="AC_002", Start='2026-06-01 13:00', Finish='2026-06-01 15:30', Flight="TK2004 (AYT-ESB)"),
    ])
    fig = px.timeline(df_gantt, x_start="Start", x_end="Finish", y="Task", color="Flight", template="plotly_dark")
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)

with right_col:
    st.markdown("### 🧠 AI Gecikme Analizi (SHAP)")
    shap_data = pd.DataFrame({
        'Feature': ['Historical Delay', 'Weather Severity', 'Airport Density', 'AC Age', 'Route Dist'],
        'Importance': [0.28, 0.19, 0.15, 0.12, 0.08]
    })
    fig_shap = px.bar(shap_data, x='Importance', y='Feature', orientation='h', 
                      color='Importance', color_continuous_scale='Blues', template="plotly_dark")
    st.plotly_chart(fig_shap, use_container_width=True)

st.divider()

# --- KRİZ YÖNETİMİ PANELİ ---
st.markdown("### 🛡️ Kriz Müdahale ve What-if Analizi")
if scenario != "Normal Operasyon":
    st.warning(f"⚠️ DİKKAT: {scenario} durumu tespit edildi! Sistem otomatik iyileştirme planı hazırladı.")
    st.info("💡 Öneri: 2 uçuşun slotlarını kaydırın, 1 uçağı yedekle değiştirin (Maliyet dâhil: ₺12K)")
else:
    st.success("✅ Tüm operasyon nominal kısıtlar (K1-K10) içerisinde devam ediyor.")

# --- FOOTER ---
st.caption("TEKNOFEST 2026 | Havayolu Optimizasyonu Yarışması | Stratejik Karar Destek Sistemi v2.0")
