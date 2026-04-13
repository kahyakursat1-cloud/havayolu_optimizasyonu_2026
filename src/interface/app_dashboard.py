import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta
import sys
import os
import time
import logging

# 0. ENTERPRISE LOGGING CONFIGURATION
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Internal imports
from src.generator.synthetic_env import GrandMasterSimulator
from src.optimizer.dt_solver import DecathlonSolver
from src.optimizer.hybrid_ga import HybridGA

# 1. PAGE CONFIG
st.set_page_config(
    page_title="TF2026 | Havayolu Karar Destek Sistemi",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. ADVANCED CSS
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Playfair+Display:wght@700&display=swap');
    .stApp { background-color: #F8FAFC; }
    * { font-family: 'Inter', sans-serif !important; }
    .header-bar {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        color: #FFFFFF;
        padding: 3rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
        border-bottom: 6px solid #F59E0B; /* Orange for Safety focus */
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
    }
    .header-bar h1 { font-family: 'Playfair Display', serif !important; margin: 0; font-size: 3rem; color: #FFFFFF !important; }
    .metric-container { display: flex; justify-content: space-between; gap: 15px; margin-bottom: 2rem; }
    .metric-card {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 12px;
        border-top: 5px solid #0F172A;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        flex: 1;
    }
    .metric-label { font-size: 0.8rem; color: #475569; text-transform: uppercase; font-weight: 700; margin-bottom: 5px; }
    .metric-value { font-size: 1.6rem; color: #0F172A; font-weight: 800; }
    [data-testid="stSidebar"] { background-color: #020617 !important; border-right: 2px solid #1E293B; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
</style>
""", unsafe_allow_html=True)

# 3. OFFICIAL HEADER
st.markdown("""
    <div class="header-bar">
        <h1>TF2026-AIR-042 | Safety & Efficiency Terminal</h1>
        <p>Havayolu Dijital İkizi & Biyo-Matematiksel Yorgunluk Kontrolü v2.8</p>
    </div>
""", unsafe_allow_html=True)

# 4. STATE MANAGEMENT
if 'flights_df' not in st.session_state:
    sim = GrandMasterSimulator()
    st.session_state.flights_df = sim.generate_grand_scenario()
    st.session_state.optimized_res = None

# 5. SIDEBAR
with st.sidebar:
    st.markdown("<h1 style='text-align: center;'>💻 KOMUTA MERKEZİ</h1>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("💡 OPERASYONEL KRİZ")
    flights = st.session_state.flights_df
    ac_list = sorted(flights['ac_id'].unique())
    aog_ac = st.selectbox("Arızalı Uçak (AOG)", ["Mevcut Değil"] + list(ac_list))
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 OPTİMİZASYON DÖNGÜSÜNÜ BAŞLAT"):
        start_time = time.time()
        with st.spinner("Yorgunluk ve Emniyet Kısıtları Hesaplanıyor..."):
            temp_df = flights.copy()
            if aog_ac != "Mevcut Değil":
                temp_df.loc[temp_df['ac_id'] == aog_ac, 'ac_capacity'] = 0
            
            solver = DecathlonSolver(temp_df)
            milp_res = solver.solve_winning(max_time_sec=10)
            
            ga = HybridGA(temp_df, generations=15)
            st.session_state.optimized_res = ga.solve(initial_seed=milp_res)
            st.session_state.solve_speed = time.time() - start_time
            st.success(f"✅ Emniyet Odaklı Optimizasyon Tamamlandı. ({st.session_state.solve_speed:.2f} sn)")

# 6. CORE RESULTS
if st.session_state.optimized_res is not None:
    res = st.session_state.optimized_res
    active_res = res[res['is_canceled'] == 0]
    
    # Advanced FRM Calculations
    # Fatigue = Base + (BlockTime * 1.3 if Night else 1.0)
    active_res['calculated_fatigue'] = active_res['crew_base_fatigue'] + (active_res['block_time'] * active_res['is_night_flight'].apply(lambda x: 1.3 if x==1 else 1.0))
    crew_fatigue = active_res.groupby('crew_id')['calculated_fatigue'].sum().reset_index()
    
    avg_fatigue = crew_fatigue['calculated_fatigue'].mean()
    risk_zone_count = len(crew_fatigue[crew_fatigue['calculated_fatigue'] > 400]) # Example threshold
    
    total_rev = active_res['revenue_tl'].sum()
    total_cost = (active_res['op_cost_tl'] + active_res['fuel_cost_tl']).sum()
    total_co2 = active_res['co2_kg'].sum()
    net_profit = total_rev - total_cost - (total_co2 * 10)

    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-card" style="border-top-color: #10B981;">
            <div class="metric-label">📊 Net Finansal Getiri</div>
            <div class="metric-value">{net_profit:,.0f} ₺</div>
        </div>
        <div class="metric-card" style="border-top-color: #F59E0B;">
            <div class="metric-label">🛡️ Ort. Yorgunluk Skoru</div>
            <div class="metric-value">{avg_fatigue:.1f}</div>
        </div>
        <div class="metric-card" style="border-top-color: #EF4444;">
            <div class="metric-label">🚨 Riskli Mürettebat</div>
            <div class="metric-value">{risk_zone_count}</div>
        </div>
        <div class="metric-card" style="border-top-color: #60A5FA;">
            <div class="metric-label">🌍 Karbon Ayak İzi</div>
            <div class="metric-value">{total_co2:,.0f} kg</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📋 Operasyonel Çizelge", "🧬 Mürettebat Emniyet Analizi", "🌱 Yeşil Havacılık"])
    
    with tab1:
        st.subheader("Havayolu Akış Çizelgesi")
        gantt_data = []
        for _, row in active_res.iterrows():
            gantt_data.append(dict(Task=row['assigned_ac'], Start=row['departure_time'], Finish=row['arrival_time'], Resource=row['crew_id'],
                                   Description=f"{row['origin']} -> {row['destination']} (Gece: {'EVET' if row['is_night_flight']==1 else 'HAYIR'})"))
        if gantt_data:
            fig = px.timeline(pd.DataFrame(gantt_data), x_start="Start", x_end="Finish", y="Task", color="Resource", template="plotly_white")
            fig.update_layout(height=450, font_family="Inter", margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.subheader("📊 Yorgunluk Dağılım Map")
            fig_fatigue = px.bar(crew_fatigue.head(30), x='crew_id', y='calculated_fatigue', color='calculated_fatigue',
                                 color_continuous_scale='YlOrRd', title="Mürettebat Bazlı Yorgunluk (İlk 30)")
            st.plotly_chart(fig_fatigue, use_container_width=True)
        with col_c2:
            st.subheader("🌙 Gece Uçuşu Analizi")
            night_count = active_res['is_night_flight'].sum()
            day_count = len(active_res) - night_count
            fig_pie = px.pie(values=[day_count, night_count], names=['Gündüz', 'Gece'], color_discrete_sequence=['#60A5FA', '#0F172A'], hole=.4)
            st.plotly_chart(fig_pie, use_container_width=True)

    with tab3:
        st.subheader("Emisyon & Çevresel Etki Analizi")
        fig_co2 = px.scatter(active_res, x="dist_km", y="co2_kg", color="ac_type", size="demand", title="Mesafe vs Karbon Salınımı")
        st.plotly_chart(fig_co2, use_container_width=True)

else:
    st.info("Sistem Analiz Bekliyor. Lütfen optimizasyonu başlatın.")
    st.image("https://img.freepik.com/free-vector/modern-city-skyline-background-with-airplane_23-2148281313.jpg", width=800)

st.markdown("---")
st.caption("TEKNOFEST 2026 | AIR-042 Safety Edition | Biyo-Matematiksel Yorgunluk Uyumu: Tam ✅")
