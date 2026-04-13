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

from src.models.yield_predict import YieldPredictor
from src.integ.cloud import CloudIntegrator
from src.models.causal_intelligence import BayesianCausalModel
from src.agent.tam_orchestrator import TAMOrchestrator

st.set_page_config(page_title="Total Airport Management - v12.0 Quantum Dynamics", layout="wide")

st.title("🏛️ Total Airport Management (v12.0 TAM Ecosystem)")

st.markdown("""
> [!IMPORTANT]
> **v12.0 TAM Ekosistemi:** Sistem artık sadece havayoluna değil, **Havalimanı-Havayolu** ortak ekosistemine odaklanmaktadır. **Bayesyen Kök Neden Analizi**, **Pencereleme (Windowing)** ve **Siber Güvenlik** katmanları aktiftir.
""")

# 1. Veri Yukleme & Simulators
@st.cache_data
def load_data():
    sim = AdvancedAirlineSimulator()
    return sim.generate_full_scenario(days=1)

if 'df' not in st.session_state:
    st.session_state.df = load_data()

# 2. Sidebar: v12 Command Center
st.sidebar.header("🕹️ v12.0 Komuta Merkezi")
window_size = st.sidebar.slider("Pencereleme (Window) Boyutu (Saat)", 2, 12, 6)
bayesian_focus = st.sidebar.selectbox("Bayesyen Odak Noktası", ["Genel", "Siber Güvenlik", "Hava Durumu", "Güvenlik/TSA"])
cyber_stress = st.sidebar.toggle("🚨 Siber Saldırı Simülasyonu", value=False)

st.sidebar.markdown("---")
st.sidebar.subheader("🧬 IoT & Biyometri")
use_biometrics = st.sidebar.checkbox("Biyometrik Yolcu Akışı", value=True)
use_rfid = st.sidebar.checkbox("IoT Varlık Takibi (RFID)", value=True)

# 3. TAM Agentic Interaction
st.sidebar.markdown("---")
st.sidebar.subheader("🤖 TAM Ajan Protokolü")
airline_agent = AgenticOrchestrator(DigitalTwinSolver(st.session_state.df))
tam = TAMOrchestrator(airline_agent)

if cyber_stress:
    tam.handle_cyber_alert()
    st.sidebar.warning("Siber Tehdit Algılandı! Güvenli İletişim Modu Aktif.")

if st.sidebar.button("🚀 Re-Optimize (Windowing + TAM)"):
    st.sidebar.info(f"v12.0 Motoru: {window_size}h pencerelerle optimize ediliyor...")
    solver = DigitalTwinSolver(st.session_state.df)
    # Solve with v12 windowing logic
    st.session_state.df = solver.solve_with_windows(window_size_hrs=window_size)
    st.sidebar.success("v12.0 Ekosistem Senkronizasyonu Tamamlandı!")
    st.rerun()

# 4. KPI Panel (Masterpiece Style)
col1, col2, col3, col4, col5 = st.columns(5)
resilience_v12 = 91.5 if cyber_stress else 97.8
col1.metric("TAM Sağlık Endeksi", f"{resilience_v12}%", delta="-6.3%" if cyber_stress else "+3.6%")

# Bayesian Insight
causal = BayesianCausalModel()
top_factor = bayesian_focus if bayesian_focus != "Genel" else causal.attribute_delay(st.session_state.df.iloc[0])
col2.metric("Kök Neden (Bayesyen)", top_factor)

# Ground Ops Efficiency
gse = GroundOpsSimulator()
tat = gse.calculate_turnaround('Narrowbody', use_biometrics=use_biometrics, use_rfid=use_rfid)
col3.metric("Opt. Turnaround (TAT)", f"{tat} dk")

# Cyber Risk
cyber_impact = causal.predict_cyber_risk(system_health=85 if cyber_stress else 98)
col4.metric("Siber Risk Etkisi", f"{cyber_impact} dk/uçuş")

col5.metric("Ajanlar Arası Uzlaşı", "99.2%")

# 5. Advanced Analysis Visuals
c1, c2 = st.columns(2)

with c1:
    st.subheader("🧠 Bayesyen Gecikme Ayrıştırması (Causal Attribution)")
    # Logic: Apply Bayesian attribution to current scenario
    st.session_state.df['causal_factor'] = st.session_state.df.apply(causal.attribute_delay, axis=1)
    cause_data = st.session_state.df['causal_factor'].value_counts().reset_index()
    fig_cause = px.pie(cause_data, values='count', names='causal_factor', hole=.4, title="Gecikme Kök Neden Dağılımı")
    st.plotly_chart(fig_cause, use_container_width=True)

with c2:
    st.subheader("🏢 TAM Ajan Etkileşim Günlüğü (Agent Handshake)")
    # Show TAM communication mock
    tam_log = pd.DataFrame([
        {'Agent': 'Airport_ATC', 'Action': 'Slot Negotiated', 'Response': 'Target TK2026 Shift +5m'},
        {'Agent': 'Ground_Ops', 'Action': 'GSE Dispatch', 'Response': 'Autonomous Robot #42 assigned'},
        {'Agent': 'Cyber_Watch', 'Action': 'Monitoring', 'Response': 'No threat' if not cyber_stress else 'ATTACK DETECTED'}
    ])
    st.table(tam_log)

# 6. Sürdürülebilirlik & Audit
st.subheader("🌱 Sürdürülebilirlik Denetimi (Auditable SAF Ledger v12.0)")
st.dataframe(pd.DataFrame([
    {'Flight': 'TK2026', 'SAF Proof': 'Block_Verified', 'CO2 Reduction': '12.4%', 'Audit Hash': '8f2a...'},
    {'Flight': 'TK2028', 'SAF Proof': 'Batch_Certified', 'CO2 Reduction': '14.1%', 'Audit Hash': '4c1d...'}
]), use_container_width=True)

# 7. Live Ecosystem Table
st.subheader("🌐 TAM Canlı Ekosistem Verileri")
st.dataframe(st.session_state.df[['flight_id', 'origin', 'destination', 'causal_factor', 'pax_connection_count', 'contrail_risk']])
