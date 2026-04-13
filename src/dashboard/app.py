import streamlit as st
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
import sys
import os

# Ana klasoru path'e ekle
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from src.optimizer.dt_solver import DigitalTwinSolver
import plotly.express as px

st.set_page_config(page_title="Havayolu Dijital İkizi - v7.0 Heavy Duty", layout="wide")

st.title("✈️ Havayolu Karar Destek Sistemi (Digital Twin v7.0)")

st.markdown("""
> [!IMPORTANT]
> **v7.0 Heavy Duty:** Sistem artık EASA uyumlu mürettebat mesai limitsiz, bakım rotalamalı ve SAF (Sürdürülebilir Yakıt) destekli optimizasyon yapmaktadır.
""")

# 1. Veri Yukleme
@st.cache_data
def load_data():
    sim = AdvancedAirlineSimulator()
    return sim.generate_full_scenario(days=1)

if 'df' not in st.session_state:
    st.session_state.df = load_data()

# 2. Sidebar Kontrolleri
st.sidebar.header("🕹️ What-If & Regülasyon Yönetimi")
slot_delay = st.sidebar.slider("Havalimanı Slot Gecikmesi (dk)", 0, 120, 0)
easa_mode = st.sidebar.checkbox("EASA Part-ORO.FTL Kısıtlarını Zorunlu Kıl", value=True)

# Simulasyon: Gecikme etkisini uygula
current_df = st.session_state.df.copy()
current_df['delay_risk'] += (slot_delay / 120.0)

if st.sidebar.button("🚀 Winning-Level Re-Optimize! (MILP)"):
    st.sidebar.warning("DigitalTwinSolver (MILP) Çalişiyor... EASA + Maintenance + SAF Entegre Ediliyor.")
    solver = DigitalTwinSolver(current_df)
    # Solve with winning level constraints
    st.session_state.df = solver.solve_winning(max_time_sec=10)
    st.sidebar.success("Optimizasyon Tamamlandi (🥇 Derece Seviyesi)!")
    st.rerun()

# 3. KPI Panel
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Toplam Uçuş", len(current_df))
col2.metric("Ortalama Gecikme Riski", f"{current_df['delay_risk'].mean():.2f}")
col3.metric("Toplam Yolcu", f"{current_df['passenger_count'].sum():,}")

# Green Metrics
avg_saf = current_df['saf_usage'].mean() if 'saf_usage' in current_df.columns else 0.0
total_co2 = current_df['co2_kg'].sum() / 1000.0 # Tons
col4.metric("Ort. SAF Kullanımı", f"%{avg_saf:.1f}")
col5.metric("Toplam CO2 (Ton)", f"{total_co2:.1f}")

# 4. Maintenance & Crew Monitoring
c1, c2 = st.columns(2)

with c1:
    st.subheader("🔧 Uçak Bakım Durumu (Remaining FH)")
    ac_status = current_df.groupby('aircraft_id')['ac_remaining_fh'].min().reset_index()
    fig_ac = px.bar(ac_status, x='aircraft_id', y='ac_remaining_fh', 
                    color='ac_remaining_fh', color_continuous_scale='RdYlGn',
                    labels={'ac_remaining_fh': 'Kalan Uçuş Saati'})
    fig_ac.add_hline(y=10, line_dash="dash", line_color="red", annotation_text="Bakım Eşiği (10h)")
    st.plotly_chart(fig_ac, use_container_width=True)

with c2:
    st.subheader("👨‍✈️ Mürettebat Yorgunluk Analizi (EASA Standards)")
    crew_fatigue = current_df.groupby('crew_id')['crew_base_fatigue'].max().reset_index()
    # Mock some fatigue accumulation if not solved yet
    fig_crew = px.histogram(crew_fatigue, x='crew_base_fatigue', nbins=20, 
                            title="Yorgunluk Dağılımı", color_discrete_sequence=['#FFA500'])
    st.plotly_chart(fig_crew, use_container_width=True)

# 5. Network & Schedule
st.subheader("🌐 Operasyonel Bağlantı Ağı ve Çizelge")
G = nx.from_pandas_edgelist(current_df, 'origin', 'destination', create_using=nx.DiGraph())
pos = nx.spring_layout(G)
edge_x, edge_y = [], []
for edge in G.edges():
    x0, y0 = pos[edge[0]]; x1, y1 = pos[edge[1]]
    edge_x.extend([x0, x1, None]); edge_y.extend([y0, y1, None])
edge_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(width=0.5, color='#888'), hoverinfo='none', mode='lines')
node_x, node_y = [], []
for node in G.nodes():
    x, y = pos[node]; node_x.append(x); node_y.append(y)
node_trace = go.Scatter(x=node_x, y=node_y, mode='markers+text', text=list(G.nodes()), textposition="top center", 
                        marker=dict(size=20, color='SkyBlue', line_width=2))
fig_net = go.Figure(data=[edge_trace, node_trace], layout=go.Layout(showlegend=False, margin=dict(b=0,l=0,r=0,t=0),
                                                               xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                                               yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))
st.plotly_chart(fig_net, use_container_width=True)

st.dataframe(current_df[['flight_id', 'origin', 'destination', 'departure_time', 'aircraft_id', 'saf_usage', 'delay_risk']].sort_values('departure_time'))
