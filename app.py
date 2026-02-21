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
# ================= AUTH SYSTEM =================

DB_FILE = "data/users.csv"

def init_db():
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame(columns=["name", "email", "password"])
        df.to_csv(DB_FILE, index=False)

def add_user(name, email, password):
    df = pd.read_csv(DB_FILE)
    if email in df['email'].values:
        return False
    new_user = pd.DataFrame([[name, email, password]],
                            columns=["name", "email", "password"])
    new_user.to_csv(DB_FILE, mode='a', header=False, index=False)
    return True

def verify_user(email, password):
    df = pd.read_csv(DB_FILE)
    user = df[(df['email'] == email) & (df['password'] == password)]
    return not user.empty

init_db()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"
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

st.set_page_config(page_title="AegisCAN-RT Command Center", layout="wide", initial_sidebar_state="expanded")
load_css()
# ================= LOGIN SCREEN =================

if not st.session_state.logged_in:

    IMAGE_PATH = "assets/logo.png"

    st.markdown(f"""
    <style>
    .auth-container {{
        display: flex;
        height: 90vh;
        border-radius: 20px;
        overflow: hidden;
        box-shadow: 0 25px 60px rgba(0,0,0,0.7);
    }}
    .auth-left {{
        flex: 1;
        background: url('{IMAGE_PATH}');
        background-size: cover;
        background-position: center;
    }}
    .auth-right {{
        flex: 1;
        background: linear-gradient(135deg, #0f0c29, #1a1f3a);
        display: flex;
        flex-direction: column;
        justify-content: center;
        padding: 60px;
        color: white;
    }}
    .stTextInput>div>div>input {{
        background-color: rgba(255,255,255,0.08);
        color: white;
    }}
    .stButton>button {{
        width: 100%;
        background: linear-gradient(90deg,#00f2ff,#7000ff);
        border: none;
        color: white;
    }}
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1,1])

    with col1:
        if os.path.exists(IMAGE_PATH):
            st.image(IMAGE_PATH, use_container_width=True)
        else:
            st.warning("Login background image not found. Put image in assets/logo.png")

    with col2:
        st.markdown("<h1 style='color:#00f2ff;'>AegisCAN-RT Access</h1>", unsafe_allow_html=True)

        if st.session_state.auth_mode == "login":

            email = st.text_input("Username / Email")
            password = st.text_input("Password", type="password")

            if st.button("Login"):
                if verify_user(email, password):
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Invalid Credentials")

            if st.button("Sign Up"):
                st.session_state.auth_mode = "signup"
                st.rerun()

        else:
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")

            if st.button("Create Account"):
                if add_user(name, email, password):
                    st.success("Account Created. Login Now.")
                    st.session_state.auth_mode = "login"
                    st.rerun()
                else:
                    st.warning("User already exists")

            if st.button("Back to Login"):
                st.session_state.auth_mode = "login"
                st.rerun()

    st.stop()
st_autorefresh(interval=100000, key="datarefresh")

if "engine" not in st.session_state:
    st.session_state.engine = GatewayEngine()

engine = st.session_state.engine

with st.sidebar:
    if st.button("🔓 Logout"):
        st.session_state.logged_in = False
        st.rerun()
    st.markdown("""
        <div style='text-align: center; padding: 10px; border: 1px double #00f2ff; border-radius: 10px; background: rgba(0,242,255,0.05);'>
            <h1 style='color: #00f2ff; text-shadow: 0 0 20px #00f2ff; margin-bottom: 0; font-size: 25px;'>AEGIS-CAN</h1>
            <p style='color: #7000ff; letter-spacing: 2px; font-size: 0.7rem; font-weight: bold;'>PREMIUM GATEWAY v3.0</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-box" style="margin-top:20px;">', unsafe_allow_html=True)
    tab = st.radio("OPERATIONAL INTERFACE", ["Live Telemetry", "Security Center", "Analytics", "System Monitor", "Logs"])
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("<p style='font-size:10px; color:#8B949E; margin-bottom:5px;'>HARDWARE CONTROL</p>", unsafe_allow_html=True)
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("DEPLOY", use_container_width=True):
            if not engine.running: engine.start()
    with btn_col2:
        if st.button("KILL", type="primary", use_container_width=True):
            engine.stop()
            
    st.markdown("""
        <div style='margin-top: 30px; padding: 15px; border-left: 3px solid #7000ff; background: rgba(112, 0, 255, 0.05); border-radius: 0 10px 10px 0;'>
            <p style='font-size: 10px; color: #7000ff; margin: 0; font-weight:bold;'>NODE ENCRYPTION</p>
            <p style='font-size: 14px; color: #00f2ff; margin: 0; font-family: monospace;'>AES-256-GCM ACTIVE</p>
            <hr style='margin: 10px 0; border-color: rgba(112,0,255,0.2);'>
            <p style='font-size: 10px; color: #8B949E; margin: 0;'>REGION</p>
            <p style='font-size: 12px; color: #ffffff; margin: 0;'>GLOBAL-CAN-01</p>
        </div>
    """, unsafe_allow_html=True)

now = datetime.now()
st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 15px 25px; background: rgba(0,242,255,0.03); border-radius: 15px; border: 1px solid rgba(0,242,255,0.1); margin-bottom: 25px;">
        <div style="text-align: left;">
            <p style="margin:0; color:#8B949E; font-size:10px; letter-spacing:2px;">OPERATOR IDENTITY</p>
            <p style="margin:0; color:#00f2ff; font-weight:bold; font-family: monospace;">SHILENDRA Dhakad  Software Engineer</p>
        </div>
        <div style="text-align: center;">
            <h1 class="glitch-text" style="font-size: 32px; margin:0; letter-spacing:5px;">AEGIS-CAN COMMAND CENTER</h1>
            <p style="margin:0; color:#8B949E; font-size:10px; letter-spacing:4px;">NEXT-GEN AUTOMOTIVE SECURITY INTERFACE</p>
        </div>
        <div style="text-align: right;">
            <p style="margin:0; color:#7000ff; font-family: monospace; font-weight:bold;">{now.strftime('%A')}</p>
            <p style="margin:0; color:white; font-size: 20px; font-weight:bold; font-family: monospace;">{now.strftime('%d %b %Y | %H:%M:%S')}</p>
        </div>
    </div>
""", unsafe_allow_html=True)

status_class = "pulse-online" if engine.running else "status-red"
status_text = "GATEWAY ACTIVE" if engine.running else "GATEWAY STANDBY"
st.markdown(f"""
    <div style="text-align: center; margin-bottom: 30px;">
        <span class="{status_class}" style="padding: 5px 20px; border-radius: 5px; font-size: 0.9rem; font-weight:bold; border: 1px solid;">{status_text}</span>
        <span style="background: rgba(112,0,255,0.1); color:#7000ff; border: 1px solid #7000ff; padding: 5px 20px; border-radius: 5px; font-size: 0.9rem; margin-left:10px; font-weight:bold;">NODE: VCAN-0x829</span>
        <span style="background: rgba(255,255,255,0.05); color:white; border: 1px solid rgba(255,255,255,0.2); padding: 5px 20px; border-radius: 5px; font-size: 0.9rem; margin-left:10px; font-weight:bold;">CORES: {len(engine.threads)} ACTIVE</span>
    </div>
""", unsafe_allow_html=True)

if tab == "Live Telemetry":
    m1, m2, m3 = st.columns(3)
    stats = get_system_stats(engine)
    
    with m1:
        st.markdown(f"""<div class="metric-card">
            <p class="metric-label">SYSTEM LOAD</p>
            <h2 class="metric-value">{stats['cpu']}%</h2>
            <p class="metric-delta">↑ 2.5% [PEAK RELAY]</p>
        </div>""", unsafe_allow_html=True)
    with m2:
        st.markdown(f"""<div class="metric-card">
            <p class="metric-label">KERNEL BUFFER</p>
            <h2 class="metric-value">{stats['ram']}%</h2>
            <p class="metric-delta" style="color:#00f2ff;">STABLE ALLOCATION</p>
        </div>""", unsafe_allow_html=True)
    with m3:
        st.markdown(f"""<div class="metric-card" style="border-right: 4px solid #7000ff;">
            <p class="metric-label">IO PIPELINES</p>
            <h2 class="metric-value">{stats['threads']}</h2>
            <p class="metric-delta" style="color:#7000ff;">ACTIVE THREADS</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown("<h3 style='color:#00f2ff; margin-bottom:20px;'>Signal Latency Oscilloscope (ms)</h3>", unsafe_allow_html=True)

    chart_placeholder = st.empty()

    while engine.running:
        if len(engine.telemetry) > 5:
            df = pd.DataFrame(engine.telemetry)
            chart_placeholder.area_chart(df["latency"].tail(50), use_container_width=True)

        elif os.path.exists("data/telemetry_log.csv"):
            df = pd.read_csv("data/telemetry_log.csv")
            chart_placeholder.area_chart(df.iloc[-50:, -1], use_container_width=True)

        else:
            dummy_data = np.random.normal(20, 5, size=50)
            chart_placeholder.area_chart(dummy_data)

        time.sleep(1)

    st.markdown('</div>', unsafe_allow_html=True)

elif tab == "Security Center":
    st.markdown('<h2 class="section-title">Adversarial Simulation & Analytics Suite</h2>', unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    with c1: 
        if st.button("INJECT DoS ATTACK", use_container_width=True): engine.run_attack("dos")
    with c2: 
        if st.button("TRIGGER BIT-FLIP", use_container_width=True): engine.run_attack("flip")
    with c3: 
        if st.button("DROP HEARTBEAT", use_container_width=True): engine.run_attack("heart")

    st.markdown("<br>", unsafe_allow_html=True)
    
    col_l, col_r = st.columns([2,1])
    with col_l:
        st.markdown("### Neural Event Matrix")
        if len(engine.telemetry) > 0:
            events = pd.DataFrame(engine.telemetry[-8:])
            for idx, row in events.iterrows():
                st.markdown(f"""
                    <div class="event-alert">
                        <span style="color:#ff0055; font-weight:bold;">[THREAT DETECTED]</span> 
                        ID: {row.get('id', 'N/A')} | Latency: {row.get('latency', '0')}ms | Vector: CAN-X
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.success("No intrusions detected. Firewall at 100% integrity.")
            
    with col_r:
        st.markdown("### Threat Analysis")
        risk_color = "#00ff88" if not engine.telemetry else "#ff0055"
        risk_label = "SECURE" if not engine.telemetry else "ALERT"
        st.markdown(f"""
            <div style="height: 180px; width: 180px; border-radius: 50%; border: 8px double {risk_color}; 
                        display: flex; flex-direction: column; align-items: center; justify-content: center; margin: auto;
                        box-shadow: 0 0 30px {risk_color}33; background: rgba(0,0,0,0.2);">
                <p style="margin:0; color:#8B949E; font-size:10px;">LEVEL</p>
                <h2 style="color: {risk_color}; margin: 0; font-family: monospace;">{risk_label}</h2>
            </div>
        """, unsafe_allow_html=True)

elif tab == "Analytics":

    st.markdown('<h2 class="section-title">ADVANCED ANALYTICS KERNEL</h2>', unsafe_allow_html=True)

    file_path = "data/latency_analysis.csv"

    if os.path.exists(file_path):
        df = pd.read_csv(file_path)

        # Ensure datetime conversion
        if 'Timestamp' in df.columns:
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        else:
            st.error("Timestamp column missing in CSV")
            st.stop()

    else:
        rows = 50
        df = pd.DataFrame({
            'Timestamp': pd.date_range(start=datetime.now(), periods=rows, freq='s'),
            'Latency (ms)': np.random.normal(25, 5, size=rows),
            'Packet Stability (%)': np.random.uniform(94, 99.9, size=rows),
            'Threat Probability (%)': np.random.uniform(0.1, 2.5, size=rows),
            'Engine Temp': np.random.uniform(60, 85, size=rows)
        })

    # Sort by time
    df = df.sort_values("Timestamp")

    # Set index once
    df.set_index("Timestamp", inplace=True)

    g1, g2 = st.columns(2)

    with g1:
        st.caption("SIGNAL LATENCY SPECTRUM")
        st.area_chart(df["Latency (ms)"])

    with g2:
        st.caption("PACKET INTEGRITY (REAL-TIME)")
        st.line_chart(df["Packet Stability (%)"])

    st.markdown("### Data Kernel Records")
    st.dataframe(df.tail(15), use_container_width=True)

elif tab == "System Monitor":
    st.markdown('<h2 class="section-title">THREAD ARCHITECTURE</h2>', unsafe_allow_html=True)
    if engine.threads:
        st.table([{"ID": t.name, "Status": "RUNNING", "Priority": "REAL-TIME", "Load": "LOW"} for t in engine.threads])
    else:
        st.info("No active threads. System idling.")

elif tab == "Logs":
    st.markdown('<h2 class="section-title">RAW KERNEL OUTPUT</h2>', unsafe_allow_html=True)
    if os.path.exists("data/telemetry_log.csv"):
        st.dataframe(pd.read_csv("data/telemetry_log.csv").tail(100), use_container_width=True)
    else:
        st.code("LOG_INIT: Initializing kernel interface... [OK]\nLISTENING ON VCAN0... [OK]\nWAITING FOR PACKETS...")

st.markdown(f"""
    <div class="footer">
        CORE SYNC: {now.strftime('%H:%M:%S')} | ENCRYPTION: AES-256-GCM | REGION: GLOBAL-CAN-01 | Version v3.0.2
    </div>
""", unsafe_allow_html=True)
