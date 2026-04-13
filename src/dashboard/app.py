import streamlit as st
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
import sys
import os

# Ana klasoru path'e ekle
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from src.generator.synthetic_env import AdvancedAirlineSimulator
from src.optimizer.hybrid_ga import HybridGA

st.set_page_config(page_title="Havayolu Dijital İkizi - DSS", layout="wide")

st.title("✈️ Havayolu Karar Destek Sistemi (Digital Twin)")

st.markdown("""
> [!NOTE]
> Bu platform, havayolu operasyonlarının dijital ikizini kullanarak **What-if** senaryoları üzerinde anlık re-optimizasyon yapar.
""")

# 1. Veri Yukleme
@st.cache_data
def load_data():
    sim = AdvancedAirlineSimulator()
    return sim.generate_full_scenario(days=1)

if 'df' not in st.session_state:
    st.session_state.df = load_data()

# 2. Sidebar Kontrolleri
st.sidebar.header("🕹️ What-If Senaryo Yönetimi")
slot_delay = st.sidebar.slider("Havalimanı Slot Gecikmesi (dk)", 0, 120, 0)
risk_threshold = st.sidebar.slider("Kabul Edilebilir Risk Eşiği", 0.0, 1.0, 0.5)

# Simulasyon: Gecikme etkisini uygula
current_df = st.session_state.df.copy()
current_df['delay_risk'] += (slot_delay / 120.0)

if st.sidebar.button("🔥 Sistemi Yeniden Optimize Et"):
    st.sidebar.warning("Hybrid GA Çalişiyor... (MILP + Custom Operators)")
    ga = HybridGA(current_df)
    st.session_state.df = ga.solve()
    st.sidebar.success("Optimizasyon Tamamlandi!")
    st.rerun()

# 3. KPI Panel
col1, col2, col3, col4 = st.columns(4)
col1.metric("Toplam Uçuş", len(current_df))
col2.metric("Ortalama Gecikme Riski", f"{current_df['delay_risk'].mean():.2f}")
col3.metric("Toplam Yolcu Kapasitesi", f"{current_df['passenger_count'].sum():,}")
col4.metric("Aktif Uçak Sayısı", current_df['aircraft_id'].nunique())

# 4. Network Graph (Plotly)
st.subheader("🌐 Havayolu Bağlantı Ağı (Network Topology)")
G = nx.from_pandas_edgelist(current_df, 'origin', 'destination', create_using=nx.DiGraph())
pos = nx.spring_layout(G)

edge_x = []
edge_y = []
for edge in G.edges():
    x0, y0 = pos[edge[0]]
    x1, y1 = pos[edge[1]]
    edge_x.extend([x0, x1, None])
    edge_y.extend([y0, y1, None])

edge_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(width=0.5, color='#888'), hoverinfo='none', mode='lines')

node_x = []
node_y = []
for node in G.nodes():
    x, y = pos[node]
    node_x.append(x)
    node_y.append(y)

node_trace = go.Scatter(x=node_x, y=node_y, mode='markers+text', text=list(G.nodes()), textposition="top center", 
                        marker=dict(size=20, color='SkyBlue', line_width=2))

fig = go.Figure(data=[edge_trace, node_trace], layout=go.Layout(showlegend=False, hovermode='closest', 
                                                              margin=dict(b=0,l=0,r=0,t=0),
                                                              xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                                              yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))
st.plotly_chart(fig, use_container_width=True)

# 5. Ucus Listesi
st.subheader("📋 Güncel Uçuş Çizelgesi ve Risk Analizi")
st.dataframe(current_df[['flight_id', 'origin', 'destination', 'departure_time', 'aircraft_id', 'delay_risk']].sort_values('delay_risk', ascending=False))
