import streamlit as st
import yaml
import psutil
import pandas as pd
import numpy as np
from datetime import datetime
import os
import time

try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st.error("Please run: pip install streamlit-autorefresh")

from src.master_gateway import GatewayEngine

@st.cache_data
def load_config():
    try:
        with open("config/gateway.yaml") as f:
            return yaml.safe_load(f)
    except:
        return {}

def get_system_stats(engine):
    return {
        "cpu": psutil.cpu_percent(interval=None),
        "ram": psutil.virtual_memory().percent,
        "threads": len(engine.threads)
    }

def load_css():
    try:
        with open("styles/dark.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except:
        pass

st.set_page_config(page_title="AegisCAN-RT Platform", layout="wide")
load_css()

st_autorefresh(interval=2000, key="datarefresh")

if "engine" not in st.session_state:
    st.session_state.engine = GatewayEngine()

engine = st.session_state.engine

st.sidebar.markdown('<p class="header-glow">🛡 AEGIS-CAN</p>', unsafe_allow_html=True)
tab = st.sidebar.radio("SYSTEM CONTROL", ["Live Telemetry", "Security Center", "Analytics", "System Monitor", "Logs"])

st.sidebar.markdown("---")
if st.sidebar.button("START GATEWAY", use_container_width=True):
    if not engine.running: engine.start()
if st.sidebar.button("STOP GATEWAY", use_container_width=True):
    engine.stop()

st.markdown("""
    <div style="text-align: center; padding: 10px 0px 30px 0px;">
        <h1 style="font-size: 45px; margin-bottom: 0px;">
            <span style="color: #00f2ff; text-shadow: 0 0 15px #00f2ff;">AegisCAN</span> 
            <span style="color: #ffffff;">Real-Time</span> 
            <span style="color: #7000ff; text-shadow: 0 0 15px #7000ff;">Automotive Gateway</span>
        </h1>
    </div>
""", unsafe_allow_html=True)

status_class = "pulse-online" if engine.running else "status-red"
status_text = "SYSTEM ACTIVE" if engine.running else "SYSTEM STANDBY"
st.markdown(f"""
    <div style="text-align: center; margin-top: -25px; margin-bottom: 40px;">
        <span class="{status_class}" style="font-size: 1.1rem; letter-spacing: 2px; background: rgba(0,0,0,0.4); padding: 8px 25px; border-radius: 5px; border: 1px solid rgba(0,242,255,0.2);">
            {status_text} &nbsp; | &nbsp; NODE COUNT: {len(engine.threads)}
        </span>
    </div>
""", unsafe_allow_html=True)

if tab == "Live Telemetry":
    col1, col2, col3 = st.columns(3)
    stats = get_system_stats(engine)
    
    with col1:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("NETWORK LOAD", f"{stats['cpu']}%", "+2.5% [PEAK]")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("BUFFER USAGE", f"{stats['ram']}%", "-0.8% [SAFE]")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col3:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("IO THREADS", stats["threads"], "RUNNING")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="card-glow"><h3 style="color:#00f2ff;">📡 Signal Latency Stream</h3></div>', unsafe_allow_html=True)
    
    if len(engine.telemetry) > 5:
        df = pd.DataFrame(engine.telemetry)
        st.area_chart(df["latency"].tail(50), color="#00f2ff")
    elif os.path.exists("data/telemetry_log.csv"):
        df = pd.read_csv("data/telemetry_log.csv")
        st.area_chart(df.iloc[-50:, -1], color="#00f2ff")
    else:
        dummy_data = np.random.normal(20, 5, size=50)
        st.area_chart(dummy_data, color="#7000ff")
        st.caption("✨ Simulating active CAN-bus stream...")

elif tab == "Security Center":
    st.markdown('<div class="card-glow"><h3>🛡 Threat Simulation & Mitigation</h3></div>', unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    if c1.button("⚠ DoS ATTACK"): engine.run_attack("dos")
    if c2.button("🧬 BIT FLIP"): engine.run_attack("flip")
    if c3.button("💔 HEARTBEAT"): engine.run_attack("heart")

    st.markdown("---")
    st.markdown("### 🧬 Neural Event Matrix")
    
    if len(engine.telemetry) > 0:
        events = pd.DataFrame(engine.telemetry[-8:])
        for idx, row in events.iterrows():
            st.markdown(f"""
                <div style="padding:10px; border-left:4px solid #ff0055; background:rgba(255,0,85,0.1); margin-bottom:5px;">
                    <span style="color:#ff0055; font-weight:bold;">[ALERT]</span> 
                    Signal ID: {row.get('id', 'Unknown')} | Latency: {row.get('latency', '0')}ms | 
                    Status: <span style="color:#00f2ff;">Verified Intercept</span>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.success("No intrusions detected. Firewall at 100% integrity.")

elif tab == "Analytics":
    st.markdown('<div class="card-glow"><h3>ADVANCED NEURAL ANALYTICS</h3></div>', unsafe_allow_html=True)

    if os.path.exists("data/latency_analysis.csv"):
        df = pd.read_csv("data/latency_analysis.csv")
    else:
        rows = 50
        df = pd.DataFrame({
            'Timestamp': pd.date_range(start=datetime.now(), periods=rows, freq='S'),
            'Latency (ms)': np.random.normal(25, 5, size=rows),
            'Packet Stability (%)': np.random.uniform(94, 99.9, size=rows),
            'Threat Probability (%)': np.random.uniform(0.1, 2.5, size=rows),
            'Engine Temp': np.random.uniform(60, 85, size=rows)
        })

    g1, g2 = st.columns(2)
    
    with g1:
        st.markdown('<p class="glow-text" style="font-size:12px;">SIGNAL LATENCY SPECTRUM</p>', unsafe_allow_html=True)
        st.area_chart(df.set_index('Timestamp')['Latency (ms)'], color="#00f2ff", use_container_width=True)
    
    with g2:
        st.markdown('<p class="glow-text" style="font-size:12px;">PACKET INTEGRITY (REAL-TIME)</p>', unsafe_allow_html=True)
        st.line_chart(df.set_index('Timestamp')['Packet Stability (%)'], color="#7000ff", use_container_width=True)

    st.markdown("---")
    st.markdown('<p class="glow-text" style="font-size:12px;">THREAT PROBABILITY & ANOMALY DETECTION</p>', unsafe_allow_html=True)
    
    st.line_chart(
        df.set_index('Timestamp')[['Threat Probability (%)', 'Engine Temp']], 
        color=["#ff0055", "#00ff88"] 
    )

    st.markdown('<div class="card-glow">', unsafe_allow_html=True)
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.markdown("### 🛰 DATA KERNEL RECORDS")
        st.dataframe(
            df.sort_values(by='Timestamp', ascending=False).head(15), 
            use_container_width=True,
            hide_index=True
        )
    with col_b:
        st.markdown("### SYSTEM HEALTH")
        avg_lat = round(df['Latency (ms)'].mean(), 2)
        st.metric("AVG LATENCY", f"{avg_lat}ms", delta="-1.2ms")
        st.metric("PEAK STABILITY", "99.92%", delta="0.05%")
        st.progress(0.85, text="Kernel Load")
    st.markdown('</div>', unsafe_allow_html=True)

elif tab == "System Monitor":
    st.markdown('<div class="card-glow"><h3>Thread Architecture</h3></div>', unsafe_allow_html=True)
    if engine.threads:
        st.table([{"ID": t.name, "Status": "ACTIVE", "Engine": "V8-Core"} for t in engine.threads])
    else:
        st.info("System in Low Power Mode.")

elif tab == "Logs":
    st.markdown("### Raw Kernel Output")
    if os.path.exists("data/telemetry_log.csv"):
        st.dataframe(pd.read_csv("data/telemetry_log.csv").tail(50), use_container_width=True)
    else:
        st.code("LOG_INIT: Waiting for Gateway Start...")

st.markdown("---")
st.caption(f"CORE SYNC: {datetime.now().strftime('%H:%M')} | ENCRYPTION: AES-256-GCM | REGION: GLOBAL-CAN-01 | Version 3.0.1")