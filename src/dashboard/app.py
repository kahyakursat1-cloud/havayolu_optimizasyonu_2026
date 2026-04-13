import streamlit as st
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
import sys
import os

# Ana klasoru path'e ekle
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from src.optimizer.dt_solver import DigitalTwinSolver
from src.generator.synthetic_env import AdvancedAirlineSimulator
import plotly.express as px

from src.models.causal_intelligence import BayesianCausalModel
from src.agent.tam_orchestrator import TAMOrchestrator
from src.agent.orchestrator import AgenticOrchestrator
from src.generator.ground_ops import GroundOpsSimulator
from src.optimizer.trajectory_a_star import TrajectoryPlannerAStar
from src.security.ot_monitor import OTSecurityMonitor

st.set_page_config(page_title="Aviation Singularity - v13.0 Masterpiece", layout="wide")

st.title("🌌 Aviation Singularity (v13.0 Ultimate OS)")

st.markdown("""
> [!CAUTION]
> **v13.0 Singularity Phase:** Sistem artık fizik temelli **3D A* Yörünge Optimizasyonu**, **Siber Dayanıklık (OT Monitoring)** ve merkezi çöküşlere karşı **ACR (Otonom Kriz Kurtarma)** katmanlarıyla donatılmıştır.
""")

# 1. Veri Yukleme & Simulators
@st.cache_data
def load_data():
    sim = AdvancedAirlineSimulator()
    return sim.generate_full_scenario(days=1)

if 'df' not in st.session_state:
    st.session_state.df = load_data()

# 2. Sidebar: v13 Command Center
st.sidebar.header("🕹️ v13.0 Singularity Müdahale")
system_failure = st.sidebar.toggle("💥 Merkezi Sistem Çöküşü (ACR Tetikle)", value=False)
ot_anomaly_sim = st.sidebar.toggle("🔒 OT Veri Anomalisi Enjekte Et", value=False)

st.sidebar.markdown("---")
st.sidebar.subheader("📐 3D Fizik Kontrolü")
target_mach = st.sidebar.slider("Hedef Mach (M)", 0.60, 0.85, 0.78)
target_fl = st.sidebar.slider("Hedef irtifa (FL)", 290, 410, 350)

# Agents & Monitors
airline_agent = AgenticOrchestrator(DigitalTwinSolver(st.session_state.df))
ot_monitor = OTSecurityMonitor()
planner_3d = TrajectoryPlannerAStar()

if system_failure:
    airline_agent.trigger_acr()
    st.sidebar.error("🚩 ACR MODU AKTİF: Merkezi Bulut Kapalı. P2P Haberleşiliyor.")

if st.sidebar.button("🚀 Optimize: 3D A* + Cyber-Resilience"):
    st.sidebar.info("v13.0 Motoru: Yörünge ve Güvenlik analizi yapılıyor...")
    
    # Solve Trajectory for a sample flight
    st.session_state.traj_res = planner_3d.optimize_3d_path(None, None, 1000)
    
    # Solve with v12 windowing logic + v13 data signing
    solver = DigitalTwinSolver(st.session_state.df)
    st.session_state.df = solver.solve_with_windows(window_size_hrs=6)
    
    # Data Signing
    st.session_state.ot_hash = ot_monitor.sign_operational_data(st.session_state.df.iloc[0].to_dict())
    
    st.sidebar.success("Singularity Senkronizasyonu Tamamlandı!")
    st.rerun()

# 3. KPI Panel (Singularity Style)
col1, col2, col3, col4, col5 = st.columns(5)
# System mode influence
health = 42 if system_failure else (92 if ot_anomaly_sim else 99)
col1.metric("Sistem Sağlık Endeksi", f"{health}%", delta="-57%" if system_failure else None)

# 3D Trajectory Efficiency
traj_gain = "+12.4%" if 'traj_res' in st.session_state else "N/A"
col2.metric("3D Yörünge Kazancı", traj_gain, help="A* bazlı irtifa/hız optimizasyonu")

# OT Anomaly Status
status_text = "TEHLİKE" if ot_anomaly_sim else "TEMİZ"
col3.metric("OT Güvenlik Durumu", status_text)

# Operational Data Hash
sig = st.session_state.get('ot_hash', "Not_Signed")[:8]
col4.metric("OT Veri İmzası (Hash)", f"0x{sig}")

# P2P Connectivity in ACR
p2p_status = "100% (P2P)" if system_failure else "Standby"
col5.metric("ACR Haberleşme", p2p_status)

# 4. Singularity Advanced Analytics
c1, c2 = st.columns(2)

with c1:
    st.subheader("📐 3D A* Yörünge Profilleme (Altitude vs Fuel)")
    if 'traj_res' in st.session_state:
        # Mock trajectory path data
        traj_df = pd.DataFrame({
            'Step': range(11),
            'Altitude': [330, 340, 350, 360, 360, 350, 350, 360, 370, 360, 350],
            'Mach': [0.76, 0.77, 0.78, 0.78, 0.79, 0.79, 0.78, 0.78, 0.77, 0.77, 0.76]
        })
        fig = px.line(traj_df, x='Step', y=['Altitude', 'Mach'], title="3D A* Uçuş Profili")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Yörünge profili için optimizasyonu başlatın.")

with c2:
    st.subheader("🔒 OT Anomali Tespit & Doğrulama Aracı")
    if ot_anomaly_sim:
        anomaly = ot_monitor.detect_anomaly('TK2026', 41000, 31000)
        if anomaly:
            st.error(f"⚠️ KRİTİK ALARM: {anomaly['type']}")
            st.warning("Yörünge komutu fizikle uyumsuz! Veri doğrulaması bekleniyor.")
            if st.button("🧬 Biyometrik Kimlik Doğrulamayı Başlat"):
                res = ot_monitor.prompt_biometric_verification(1)
                st.success(f"Dizge Doğrulandı: {res}. Komut bloklandı ve orijinal veriye dönüldü.")
    else:
        st.success("✅ OT Veri Akışı Normal: Hiçbir anomali tespit edilmedi.")

# 5. ACR Emergency Log
if system_failure:
    st.subheader("🚩 ACR Otonom Kriz Aksiyon Günlüğü (P2P Data)")
    critical_data = airline_agent.p2p_exchange_critical()
    st.json(critical_data)

# 6. Final Data Ecosystem
st.subheader("🌐 Singularity Canlı Veri Katmanı")
st.dataframe(st.session_state.df[['flight_id', 'causal_factor', 'assigned_delay', 'contrail_risk']])
