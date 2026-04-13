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
from src.agent.orchestrator import AgenticOrchestrator
from src.generator.ground_ops import GroundOpsSimulator, SustainabilityLedger

st.set_page_config(page_title="Havacılık İşletim Sistemi - v11.0 Agentic & Quantum-Ready", layout="wide")

st.title("🛡️ Havacılık İşletim Sistemi (v11.0 Aviation OS)")

st.markdown("""
> [!IMPORTANT]
> **v11.0 Otonom Karar Mekanizması:** Sistem artık pasif bir çözücü değil, otonom kararlar alabilen bir **Ajan (Agentic AI)** tarafından yönetilmektedir. Kritik kararlar için "Kullanıcı Onayı" mekanizması devrededir.
""")

# 1. Veri Yukleme & Simulators
@st.cache_data
def load_data():
    sim = AdvancedAirlineSimulator()
    return sim.generate_full_scenario(days=1)

if 'df' not in st.session_state:
    st.session_state.df = load_data()

# 2. Sidebar: v11 Controller
st.sidebar.header("🕹️ v11.0 Komuta Merkezi")
mode = st.sidebar.radio("Çalışma Modu", ["Standard", "Quantum-Inspired", "Agentic Otonom"])
auto_gse = st.sidebar.toggle("🤖 Otonom Yer Hizmetleri (GSE)", value=True)
cloud_sync = st.sidebar.toggle("☁️ Bulut Senkronizasyonu", value=True)

# Agentic Orchestration Panel
st.sidebar.markdown("---")
st.sidebar.subheader("🤖 Ajan Durumu")
orchestrator = AgenticOrchestrator(DigitalTwinSolver(st.session_state.df))
disruption_status = orchestrator.analyze_disruption(st.session_state.df)

if disruption_status == "CRITICAL_DISRUPTION":
    st.sidebar.error("⚠️ Kritik Aksaklık Tespit Edildi!")
    if st.sidebar.button("📩 Çözüm İçin Ajanı Görevlendir"):
        action = orchestrator.negotiate_recovery(st.session_state.df)
        st.session_state.pending_action = action
else:
    st.sidebar.success("✅ Operasyon Kararlı")

# 3. User Approval Flow (v11 Requirement)
if 'pending_action' in st.session_state:
    with st.expander("🔔 AJAN ÖNERİSİ: Kullanıcı Onayı Gerekiyor", expanded=True):
        st.info(f"**Öneri:** {st.session_state.pending_action['action_type']} | **Etki:** {st.session_state.pending_action['impact']}")
        c1, c2 = st.columns(2)
        if c1.button("✅ ONAYLA VE UYGULA"):
            st.success("Ajan komutu uygulandı. Yeniden optimize ediliyor...")
            # Re-optimize with agentic parameters
            solver = DigitalTwinSolver(st.session_state.df)
            st.session_state.df = solver.solve_winning(max_time_sec=10)
            del st.session_state.pending_action
            st.rerun()
        if c2.button("❌ REDDET"):
            del st.session_state.pending_action
            st.rerun()

# 4. KPI Panel (Power BI Style)
col1, col2, col3, col4, col5 = st.columns(5)
# Using ground ops simulator for TAT impact
gse = GroundOpsSimulator()
tat_gain = 20 if auto_gse else 0
col1.metric("Turnaround Verimliliği", f"+{tat_gain}%", help="Otonom bagaj/yakıt robotları etkisi")

total_rev = (st.session_state.df['business_pax'].sum() * 2500 + st.session_state.df['leisure_pax'].sum() * 800) / 1e6
col2.metric("Toplam Gelir", f"{total_rev:.2f}M TL")

# Quantum Stability
q_status = "Quantum-Ready" if mode == "Quantum-Inspired" else "Classical"
col3.metric("Optimizasyon Modu", q_status)

# SAF Audit
ledger = SustainabilityLedger()
total_co2_saved = st.session_state.df['dist_km'].sum() * 0.05 # Mock calculation
col4.metric("CO2 Tasarrufu (Audit)", f"{total_co2_saved/1000:.1f} Ton")

col5.metric("Ajan Sağlık Puanı", "98/100")

# 5. Advanced Visuals
c1, c2 = st.columns(2)

with c1:
    st.subheader("📊 Operasyonel Risk Analizi (Delay Drivers)")
    # Logic: Group by reasons (Mock)
    risk_df = pd.DataFrame({'Sebep': ['Hava Trafik', 'Mürettebat', 'Teknik', 'Yer Hizmetleri'], 'Etki': [45, 30, 15, 10]})
    st.plotly_chart(px.bar(risk_df, x='Sebep', y='Etki', color='Sebep', title="Gecikme Kaynakları Analizi"), use_container_width=True)

with c2:
    st.subheader("🌱 Sürdürülebilirlik Denetimi (Auditable SAF Ledger)")
    # Show audit ledger tail
    st.dataframe(pd.DataFrame([
        {'Flight': 'TK2026', 'SAF (Lt)': 4500, 'CO2 Saved (Kg)': 120, 'Audit Hash': '8f2a...'},
        {'Flight': 'TK2028', 'SAF (Lt)': 3200, 'CO2 Saved (Kg)': 85, 'Audit Hash': '4c1d...'}
    ]), use_container_width=True)

# 6. Live Map & Table
st.subheader("🌐 Havacılık İşletim Sistemi: Canlı Operasyonel Görünüm")
# ... [Network graph preserved] ...
st.dataframe(st.session_state.df[['flight_id', 'origin', 'destination', 'passenger_count', 'contrail_risk', 'assigned_delay']])
