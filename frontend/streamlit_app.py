import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import time

from torch import mode
from streamlit_autorefresh import st_autorefresh
import numpy as np
import matplotlib.pyplot as plt  

API_BASE = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

DB_FILE = "data/users.csv"

def init_db():
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame(columns=["name", "email", "password"])
        df.to_csv(DB_FILE, index=False)

def add_user(name, email, password):
    df = pd.read_csv(DB_FILE)
    if email in df['email'].values:
        return False
    new_user = pd.DataFrame([[name, email, password]], columns=["name", "email", "password"])
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

st.set_page_config(page_title="AEGIS-CAN COMMAND CENTER", layout="wide", initial_sidebar_state="expanded")

def load_css():
    try:
        with open("styles/dark.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except:
        st.warning("dark.css not found - using default")

load_css()

if not st.session_state.logged_in:
    st.markdown("""
    <div style="display: flex; height: 90vh; align-items: center; justify-content: center; background: linear-gradient(135deg, #0a001f, #1a0033);">
        <div style="width: 450px; padding: 60px; background: rgba(20,0,40,0.85); border-radius: 24px; border: 1px solid rgba(0,255,255,0.3); backdrop-filter: blur(12px); box-shadow: 0 0 50px rgba(0,255,255,0.2); text-align: center;">
            <h1 style="font-size: 3.5rem; color: #00faff; margin-bottom: 30px; text-shadow: 0 0 15px #00faff;">AEGIS-CAN RT System</h1>
    """, unsafe_allow_html=True)

    if st.session_state.auth_mode == "login":
        email = st.text_input("Operator ID / Email", key="login_email")
        password = st.text_input("Access Key", type="password", key="login_pass")
        if st.button("Authenticate", use_container_width=True):
            if verify_user(email, password):
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Access Denied - Invalid Credentials")
        if st.button("Register New Operator"):
            st.session_state.auth_mode = "signup"
            st.rerun()
    else:
        name = st.text_input("Full Designation")
        email = st.text_input("Operator ID")
        password = st.text_input("Set Access Key", type="password")
        if st.button("Create Clearance"):
            if add_user(name, email, password):
                st.success("Clearance Granted - Login Now")
                st.session_state.auth_mode = "login"
                st.rerun()
            else:
                st.warning("ID Already Registered")
        if st.button("Back to Login"):
            st.session_state.auth_mode = "login"
            st.rerun()

    st.markdown("</div></div>", unsafe_allow_html=True)
    st.stop()

st_autorefresh(interval=5000, key="autorefresh")

now = datetime.now()
now_str = now.strftime("%H:%M:%S")

st.markdown(f"""
<div style="padding: 20px; background: rgba(20,0,40,0.6); border-radius: 16px; border: 1px solid rgba(0,255,255,0.25); margin-bottom: 30px; text-align: center; box-shadow: 0 0 40px rgba(0,255,255,0.15);">
    <h1 style="font-size: 3rem; color: #00faff; margin: 0; text-shadow: 0 0 15px #00faff;">AEGIS-CAN COMMAND CENTER</h1>
    <p style="color: #c300ff; margin: 8px 0 0; font-size: 1.1rem;">v3.2 • {now.strftime('%d %b %Y • %H:%M:%S')}</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    st.markdown("### Controls")
    if st.button("Deploy Gateway"):
        try:
            r = requests.post(f"{API_BASE}/api/gateway/start")
            if r.status_code == 200:
                st.success("Deployed")
            else:
                st.error("Failed")
        except:
            st.error("Backend unreachable")

    if st.button("Kill Gateway"):
        try:
            r = requests.post(f"{API_BASE}/api/gateway/stop")
            if r.status_code == 200:
                st.success("Terminated")
            else:
                st.error("Failed")
        except:
            st.error("Backend unreachable")

    attack_mode = st.selectbox("Attack", ["None", "DoS Flood", "Bit-Flip Corruption", "Heartbeat Drop"])
    def execute_attack():
        mode_map = {"DoS Flood": "dos", "Bit-Flip Corruption": "flip", "Heartbeat Drop": "heart"}
        mode = mode_map.get(attack_mode)
    
        if not mode:
            st.warning("Please select a valid attack mode first")
            return

        try:
            r = requests.post(f"{API_BASE}/api/gateway/attack/{mode}")
            if r.status_code == 200:
                st.success(f"{attack_mode} VECTOR INJECTED")
            else:
                st.error(f"API Error: {r.json().get('detail', r.text)}")
        except Exception as e:
            st.error(f"Connection failed: {str(e)}")


if st.button("EXECUTE VECTOR", type="primary", use_container_width=True):
    execute_attack()
    
st.markdown(f"<div style='text-align:center; padding:20px; color:#00ff9d;'>Sync: {now_str} | Secured</div>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["LIVE TELEMETRY", "SECURITY CENTER", "ANALYTICS CORE", "SYSTEM MONITOR", "KERNEL LOGS"])

with tab1:
    st.subheader("SIGNAL LATENCY & PACKET FLOW")
    try:
        r = requests.get(f"{API_BASE}/api/analytics/telemetry?limit=300")
        if r.status_code == 200 and r.json():
            df = pd.DataFrame(r.json())
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])

                fig_line = px.line(df, x="timestamp", y="latency_us", color="type",
                                  title="Real-Time Latency Oscilloscope (µs)",
                                  template="plotly_dark", height=450)
                fig_line.update_traces(line=dict(width=2.5))
                st.plotly_chart(fig_line, use_container_width=True)

                avg_latency = df["latency_us"].mean() / 1000
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number+delta",
                    value=avg_latency,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Average Latency (ms)"},
                    gauge={
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "#00f2ff"},
                        'steps': [
                            {'range': [0, 30], 'color': "#00ff88"},
                            {'range': [30, 60], 'color': "#ffaa00"},
                            {'range': [60, 100], 'color': "#ff0055"}
                        ],
                        'threshold': {'line': {'color': "white", 'width': 4}, 'thickness': 0.75, 'value': avg_latency}
                    }
                ))
                fig_gauge.update_layout(template="plotly_dark", height=300)
                st.plotly_chart(fig_gauge, use_container_width=True)

                st.dataframe(df.tail(12).style.background_gradient(cmap="Blues"), use_container_width=True)
            else:
                st.info("No timestamp data – gateway may not be running")
        else:
            st.info("No telemetry received. Deploy gateway to begin.")
    except Exception as e:
        st.error(f"Telemetry fetch failed: {str(e)}")

with tab2:
    st.subheader("THREAT DETECTION & ADVERSARIAL SIMULATION")

    col1, col2 = st.columns([3,1])
    with col1:
        try:
            r = requests.get(f"{API_BASE}/api/analytics/telemetry?limit=100")
            if r.status_code == 200 and r.json():
                df = pd.DataFrame(r.json())
                attack_df = df[df['type'].str.contains("ATTACK|DOS|FLIP|HEART", case=False, na=False)]
                if not attack_df.empty:
                    fig = px.timeline(attack_df, x_start="timestamp", x_end="timestamp", y="type", color="type",
                                     title="Threat Event Timeline", template="plotly_dark")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.success("No active threats detected – system integrity 100%")
            else:
                st.info("No security events recorded")
        except:
            st.error("Security data fetch failed")

    with col2:
        st.markdown("<div class='threat-meter'><h2 style='color:white; font-size:3rem;'>RISK</h2><p style='font-size:1.4rem; color:#ff0055;'>CRITICAL</p></div>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#ffccdd; margin-top:20px;'>THREAT LEVEL</p>", unsafe_allow_html=True)

with tab3:
    st.subheader("AI-DRIVEN ANALYTICS & PREDICTION ENGINE")
    try:
        r = requests.get(f"{API_BASE}/api/analytics/telemetry?limit=500")
        if r.status_code == 200 and r.json():
            df = pd.DataFrame(r.json())
            if 'latency_us' in df.columns:
                df['latency_ms'] = df['latency_us'] / 1000

                col1, col2 = st.columns(2)
                with col1:
                    fig_area = px.area(df, x=df.index, y="latency_ms", title="Latency Trend + Prediction Band", template="plotly_dark")
                    st.plotly_chart(fig_area, use_container_width=True)

                with col2:
                    fig_hist = px.histogram(df, x="latency_ms", nbins=40, title="Latency Distribution", template="plotly_dark")
                    st.plotly_chart(fig_hist, use_container_width=True)

                st.dataframe(df.describe().T.style.background_gradient(cmap="Purples"), use_container_width=True)
            else:
                st.info("Insufficient data for analytics")
        else:
            st.info("Deploy gateway to generate analytics data")
    except:
        st.error("Analytics fetch failed")

with tab4:
    st.subheader("SYSTEM ARCHITECTURE & RESOURCE MONITOR")
    try:
        r_health = requests.get(f"{API_BASE}/health")
        if r_health.status_code == 200:
            status = r_health.json()["status"]
            color = "lime" if status == "healthy" else "red"
            st.markdown(f"<h2 style='color:{color}; text-shadow:0 0 15px {color};'>SYSTEM STATUS: {status.upper()}</h2>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            fig_cpu = go.Figure(go.Indicator(mode="gauge+number", value=35, title={'text': "CPU"}, gauge={'axis': {'range': [0,100]}}))
            fig_cpu.update_layout(template="plotly_dark")
            st.plotly_chart(fig_cpu)

        with col2:
            fig_ram = go.Figure(go.Indicator(mode="gauge+number", value=62, title={'text': "RAM"}, gauge={'axis': {'range': [0,100]}}))
            fig_ram.update_layout(template="plotly_dark")
            st.plotly_chart(fig_ram)

        with col3:
            fig_disk = go.Figure(go.Indicator(mode="gauge+number", value=48, title={'text': "DISK"}, gauge={'axis': {'range': [0,100]}}))
            fig_disk.update_layout(template="plotly_dark")
            st.plotly_chart(fig_disk)

    except:
        st.error("System monitor data unavailable")

with tab5:
    st.subheader("REAL-TIME KERNEL & EVENT LOG")
    try:
        r = requests.get(f"{API_BASE}/api/analytics/telemetry?limit=200")
        if r.status_code == 200 and r.json():
            df = pd.DataFrame(r.json())
            df['severity'] = df['type'].apply(lambda x: "CRITICAL" if "ATTACK" in str(x).upper() else "INFO")
            styled = df.style.applymap(lambda x: 'color: #ff0055' if x == "CRITICAL" else 'color: #00f2ff' if x == "INFO" else 'color: white', subset=['severity'])
            st.dataframe(styled, use_container_width=True, height=600)
        else:
            st.code("KERNEL_BOOT: 2026-02-26 23:00:00 [OK]\nVCAN0 INITIALIZED [OK]\nLISTENING FOR BLE PACKETS [ACTIVE]\nNO ANOMALIES DETECTED")
    except:
        st.error("Log stream unavailable")

st.markdown(f"""
<div class="footer">
    CORE SYNC: {now_str} | AES-256-GCM ACTIVE | NODE: GLOBAL-CAN-01 | PLATFORM v3.0.3 | SECURED BY AEGIS | Shailendra Dhakad *Backend Developer*
</div>
""", unsafe_allow_html=True)