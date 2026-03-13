"""
Production-grade Streamlit dashboard for AegisCAN-RT.

Features:
- Real-time gateway monitoring
- Attack detection and classification
- System health visualization
- Secure authentication
- Advanced analytics
- Error handling and resilience
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Optional, Dict, Any

# Configuration
API_BASE = "http://localhost:8000"
API_TIMEOUT = 10
REFRESH_INTERVAL = 2  # seconds

logger = logging.getLogger(__name__)


# ============================================================================
# Page Configuration
# ============================================================================

st.set_page_config(
    page_title="AegisCAN-RT Command Center",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/dhakarshailendra829/AegisCAN-RT",
        "Report a bug": "https://github.com/dhakarshailendra829/AegisCAN-RT/issues",
        "About": "# AegisCAN-RT\nDeterministic ultra-low-latency BLE→CAN real-time gateway for safety-critical automotive systems."
    }
)

# Apply custom CSS
st.markdown("""
<style>
    /* Dark Theme */
    :root {
        --primary-color: #667eea;
        --secondary-color: #764ba2;
        --success-color: #00ff00;
        --danger-color: #ff4444;
        --warning-color: #ff8800;
        --info-color: #00bfff;
    }

    /* Main container */
    .main {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        color: #ffffff;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
        border-right: 2px solid #667eea;
    }

    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        border: 1px solid rgba(118, 75, 162, 0.5);
    }

    /* Status badges */
    .status-active {
        color: #00ff00;
        font-weight: bold;
        text-shadow: 0 0 10px rgba(0, 255, 0, 0.5);
    }

    .status-inactive {
        color: #ff4444;
        font-weight: bold;
        text-shadow: 0 0 10px rgba(255, 68, 68, 0.5);
    }

    /* Alerts */
    .alert-critical {
        background-color: rgba(255, 68, 68, 0.1);
        border-left: 4px solid #ff4444;
        color: #ff4444;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }

    .alert-high {
        background-color: rgba(255, 136, 0, 0.1);
        border-left: 4px solid #ff8800;
        color: #ff8800;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }

    .alert-medium {
        background-color: rgba(0, 191, 255, 0.1);
        border-left: 4px solid #00bfff;
        color: #00bfff;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }

    .alert-success {
        background-color: rgba(0, 255, 0, 0.1);
        border-left: 4px solid #00ff00;
        color: #00ff00;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #16213e;
        border-radius: 5px 5px 0 0;
        color: #ffffff;
        border: 1px solid #667eea;
    }

    .stTabs [aria-selected="true"] {
        background-color: #667eea;
        color: white;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }

    .stButton > button:hover {
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        transform: translateY(-2px);
    }

    /* Sliders */
    .stSlider {
        color: #667eea;
    }

    /* Headers */
    h1, h2, h3 {
        color: #667eea;
        text-shadow: 0 0 20px rgba(102, 126, 234, 0.3);
    }

    /* Divider */
    hr {
        border-color: #667eea;
        opacity: 0.5;
    }

    /* Tables */
    .dataframe {
        background-color: #16213e;
        color: #ffffff;
    }

    /* Input fields */
    .stTextInput > div > div > input,
    .stPasswordInput > div > div > input,
    .stSelectbox > div > div > select {
        background-color: #302b63;
        color: #ffffff;
        border: 1px solid #667eea;
    }

    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 10px;
    }

    ::-webkit-scrollbar-track {
        background: #0f0c29;
    }

    ::-webkit-scrollbar-thumb {
        background: #667eea;
        border-radius: 5px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #764ba2;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# Utility Functions
# ============================================================================

@st.cache_resource
def get_api_session():
    """Get requests session with timeout."""
    session = requests.Session()
    session.timeout = API_TIMEOUT
    return session


def make_api_call(endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Optional[Dict]:
    """
    Make API call with error handling and resilience.

    Args:
        endpoint: API endpoint path
        method: HTTP method
        data: Request data for POST

    Returns:
        Response JSON or None
    """
    try:
        url = f"{API_BASE}{endpoint}"
        session = get_api_session()

        if method == "GET":
            response = session.get(url, timeout=API_TIMEOUT)
        elif method == "POST":
            response = session.post(url, json=data, timeout=API_TIMEOUT)
        elif method == "DELETE":
            response = session.delete(url, timeout=API_TIMEOUT)
        else:
            return None

        response.raise_for_status()
        return response.json()

    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to API server at " + API_BASE)
        return None
    except requests.exceptions.Timeout:
        st.error("⏱️ API request timeout (>10s)")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"❌ API Error: {e.response.status_code}")
        return None
    except ValueError as e:
        st.error(f"❌ Invalid response format: {str(e)}")
        return None
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        return None


def safe_format(value: Any, default: str = "N/A", format_spec: str = "") -> str:
    """
    Safely format a value with None handling.

    Args:
        value: Value to format
        default: Default if value is None
        format_spec: Format specification (e.g., ".2f")

    Returns:
        Formatted string
    """
    if value is None:
        return default
    if format_spec:
        return f"{value:{format_spec}}"
    return str(value)


# ============================================================================
# Session State Management
# ============================================================================

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now()
if "gateway_running" not in st.session_state:
    st.session_state.gateway_running = False


# ============================================================================
# Authentication
# ============================================================================

def login_page():
    """Display login/register page with modern styling."""
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("""
        <div style='text-align: center; padding: 40px 0;'>
            <h1 style='font-size: 48px; color: #667eea;'>🛡️ AegisCAN-RT</h1>
            <h3 style='color: #764ba2;'>Secure Command Center</h3>
            <p style='color: #888; margin-top: 20px;'>
                Deterministic ultra-low-latency BLE→CAN real-time gateway
            </p>
        </div>
        """, unsafe_allow_html=True)

        tabs = st.tabs(["🔓 Login", "📝 Register"])

        with tabs[0]:
            st.markdown("#### Operator Login")
            username = st.text_input("Username", key="login_user", placeholder="Enter your username")
            password = st.text_input("Password", type="password", key="login_pass", placeholder="Enter your password")

            if st.button("🔓 Login", use_container_width=True, key="login_btn"):
                if username and password:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Please enter username and password")

        with tabs[1]:
            st.markdown("#### Register New Operator")
            new_username = st.text_input("Username", key="reg_user", placeholder="Choose a username")
            new_password = st.text_input("Password", type="password", key="reg_pass", placeholder="Create a password")
            confirm_password = st.text_input("Confirm Password", type="password", key="reg_pass_confirm", placeholder="Confirm password")

            if st.button("📝 Register", use_container_width=True, key="register_btn"):
                if len(new_username) < 3:
                    st.error("❌ Username must be at least 3 characters")
                elif new_password != confirm_password:
                    st.error("❌ Passwords don't match")
                elif len(new_password) < 6:
                    st.error("❌ Password must be at least 6 characters")
                else:
                    st.success("✅ Registration successful! Please login.")


# ============================================================================
# Main Dashboard
# ============================================================================

def main_dashboard():
    """Display main dashboard with real-time data."""
    st.markdown(f"# 🛡️ AegisCAN-RT Command Center")
    st.markdown(f"**Operator:** {st.session_state.username} | **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Sidebar controls
    with st.sidebar:
        st.header("⚙️ Controls")

        if st.button("🔄 Refresh Now", use_container_width=True):
            st.rerun()

        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ Start", use_container_width=True):
                result = make_api_call("/api/gateway/start", method="POST")
                if result:
                    st.session_state.gateway_running = True
                    st.success("✅ Gateway started")
                    st.rerun()

        with col2:
            if st.button("⏹️ Stop", use_container_width=True):
                result = make_api_call("/api/gateway/stop", method="POST")
                if result:
                    st.session_state.gateway_running = False
                    st.success("✅ Gateway stopped")
                    st.rerun()

        st.divider()

        st.subheader("🎯 Attack Modes")
        attack_mode = st.selectbox(
            "Select Mode",
            ["none", "dos", "flip", "heart"],
            label_visibility="collapsed"
        )

        if st.button("⚡ Activate", use_container_width=True):
            result = make_api_call(f"/api/gateway/attack/{attack_mode}", method="POST")
            if result and result.get("status") == "success":
                st.success(f"✅ {attack_mode.upper()} activated")
            else:
                st.error(f"❌ Failed to activate {attack_mode}")

        st.divider()

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.success("✅ Logged out")
            st.rerun()

    # Main content tabs
    tabs = st.tabs([
        "📊 Dashboard",
        "📈 Analytics",
        "🚨 Alerts",
        "🔍 Telemetry",
        "⚙️ Settings"
    ])

    # ====== TAB 1: Dashboard ======
    with tabs[0]:
        st.subheader("Real-Time Status")

        # Get current status
        status_data = make_api_call("/api/gateway/status")
        health_data = make_api_call("/api/gateway/health")

        if status_data and health_data:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                running = health_data.get("is_running", False)
                status_text = "🟢 ACTIVE" if running else "🔴 INACTIVE"
                st.metric(
                    "Gateway Status",
                    status_text,
                    help="Current operational status"
                )

            with col2:
                uptime = health_data.get("uptime_seconds")
                uptime_str = safe_format(uptime, "0", ".0f") if uptime is not None else "0"
                st.metric(
                    "Uptime",
                    f"{uptime_str}s",
                    help="Gateway uptime in seconds"
                )

            with col3:
                buffer_count = health_data.get("telemetry_count", 0)
                st.metric(
                    "Telemetry Buffer",
                    buffer_count,
                    help="Buffered telemetry entries"
                )

            with col4:
                attack_mode = health_data.get("current_attack_mode", "None")
                mode_text = attack_mode if attack_mode else "None"
                st.metric(
                    "Attack Mode",
                    mode_text,
                    help="Active attack simulation"
                )

            # System metrics
            st.subheader("System Resources")

            metrics_data = make_api_call("/api/analytics/health/status")
            if metrics_data:
                col1, col2, col3 = st.columns(3)

                with col1:
                    if "health_monitor" in metrics_data:
                        thresholds = metrics_data.get("health_monitor", {}).get("thresholds", {})
                        st.write(f"**CPU Threshold:** {thresholds.get('cpu', 'N/A')}%")
                        st.write(f"**Memory Threshold:** {thresholds.get('memory', 'N/A')}%")
                        st.write(f"**Disk Threshold:** {thresholds.get('disk', 'N/A')}%")

                with col2:
                    if "latency_predictor" in metrics_data:
                        predictor = metrics_data.get("latency_predictor", {})
                        stats = predictor.get("statistics", {})
                        if stats:
                            mean_lat = safe_format(stats.get("mean"), "N/A", ".2f")
                            p95_lat = safe_format(stats.get("p95"), "N/A", ".2f")
                            st.write(f"**Avg Latency:** {mean_lat}µs")
                            st.write(f"**P95 Latency:** {p95_lat}µs")

                with col3:
                    if "anomaly_detector" in metrics_data:
                        detector = metrics_data.get("anomaly_detector", {})
                        avail = "✅ Active" if detector.get("available") else "❌ Inactive"
                        trained = "✅ Yes" if detector.get("trained") else "❌ No"
                        st.write(f"**Detector:** {avail}")
                        st.write(f"**Trained:** {trained}")

    # ====== TAB 2: Analytics ======
    with tabs[1]:
        st.subheader("Advanced Analytics")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Anomaly Detection")
            anomaly_data = make_api_call("/api/analytics/anomalies/detect?limit=200")

            if anomaly_data and anomaly_data.get("status") == "success":
                anomaly_ratio = anomaly_data.get("anomaly_ratio", 0) * 100

                fig = go.Figure(data=[
                    go.Indicator(
                        mode="gauge+number+delta",
                        value=anomaly_ratio,
                        title={"text": "Anomaly Ratio (%)"},
                        domain={"x": [0, 1], "y": [0, 1]},
                        gauge={
                            "axis": {"range": [0, 100]},
                            "bar": {"color": "darkblue"},
                            "steps": [
                                {"range": [0, 10], "color": "lightgray"},
                                {"range": [10, 30], "color": "yellow"},
                                {"range": [30, 100], "color": "red"}
                            ],
                            "threshold": {
                                "line": {"color": "red", "width": 4},
                                "thickness": 0.75,
                                "value": 90
                            }
                        }
                    )
                ])
                fig.update_layout(
                    plot_bgcolor="#0f0c29",
                    paper_bgcolor="#0f0c29",
                    font={"color": "#ffffff"}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("ℹ️ No anomaly data available")

        with col2:
            st.markdown("#### Attack Classification")
            attack_data = make_api_call("/api/analytics/attacks/classify?limit=100")

            if attack_data and attack_data.get("status") == "success":
                classifications = attack_data.get("classifications", [])

                if classifications:
                    df = pd.DataFrame(classifications)
                    fig = px.pie(
                        df,
                        names="type",
                        values=[1]*len(df),
                        title="Attack Type Distribution"
                    )
                    fig.update_layout(
                        plot_bgcolor="#0f0c29",
                        paper_bgcolor="#0f0c29",
                        font={"color": "#ffffff"}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("ℹ️ No attack classifications available")
            else:
                st.info("ℹ️ Attack classification not available")

    # ====== TAB 3: Alerts ======
    with tabs[2]:
        st.subheader("System Alerts")

        anomaly_data = make_api_call("/api/analytics/anomalies/detect?threshold=0.1")

        if anomaly_data:
            severity = anomaly_data.get("severity", "LOW")
            ratio = anomaly_data.get("anomaly_ratio", 0)

            if severity == "CRITICAL":
                st.markdown(f"""
                <div class='alert-critical'>
                🚨 <strong>CRITICAL ALERT</strong><br>
                Anomaly Ratio: {ratio:.1%}
                </div>
                """, unsafe_allow_html=True)
            elif severity == "HIGH":
                st.markdown(f"""
                <div class='alert-high'>
                ⚠️ <strong>HIGH PRIORITY</strong><br>
                Anomaly Ratio: {ratio:.1%}
                </div>
                """, unsafe_allow_html=True)
            elif severity == "MEDIUM":
                st.markdown(f"""
                <div class='alert-medium'>
                ℹ️ <strong>MEDIUM PRIORITY</strong><br>
                Anomaly Ratio: {ratio:.1%}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class='alert-success'>
                ✅ <strong>ALL CLEAR</strong><br>
                Anomaly Ratio: {ratio:.1%}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ Unable to fetch alert data")

    # ====== TAB 4: Telemetry ======
    with tabs[3]:
        st.subheader("Telemetry Data")

        col1, col2 = st.columns([3, 1])
        with col1:
            limit = st.slider("Data Points to Display", 10, 1000, 200)
        with col2:
            if st.button("📥 Refresh"):
                st.rerun()

        telemetry_data = make_api_call(f"/api/analytics/telemetry?limit={limit}")

        if telemetry_data:
            st.write(f"**Total Entries:** {telemetry_data.get('count', 0)}")

            entries = telemetry_data.get("entries", [])
            if entries:
                df = pd.DataFrame(entries)

                # Display table
                st.dataframe(df, use_container_width=True, height=300)

                # Plot latency if available
                if "latency_us" in df.columns:
                    fig = px.line(
                        df,
                        y="latency_us",
                        title="Latency Over Time",
                        labels={"latency_us": "Latency (µs)"}
                    )
                    fig.update_layout(
                        plot_bgcolor="#0f0c29",
                        paper_bgcolor="#0f0c29",
                        font={"color": "#ffffff"}
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("ℹ️ No telemetry data available yet")
        else:
            st.error("❌ Failed to fetch telemetry data")

    # ====== TAB 5: Settings ======
    with tabs[4]:
        st.subheader("System Settings")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Health Monitor Thresholds")

            cpu_threshold = st.slider("CPU Threshold (%)", 1, 100, 80, key="cpu_slider")
            memory_threshold = st.slider("Memory Threshold (%)", 1, 100, 85, key="mem_slider")
            disk_threshold = st.slider("Disk Threshold (%)", 1, 100, 90, key="disk_slider")

            if st.button("💾 Update Thresholds", use_container_width=True):
                result = make_api_call(
                    "/api/analytics/health/thresholds",
                    method="POST",
                    data={
                        "cpu": cpu_threshold,
                        "memory": memory_threshold,
                        "disk": disk_threshold
                    }
                )
                if result and result.get("status") == "success":
                    st.success("✅ Thresholds updated successfully")
                else:
                    st.error("❌ Failed to update thresholds")

        with col2:
            st.markdown("#### Database Management")

            if st.button("🗑️ Clear Old Data (7+ days)", use_container_width=True):
                st.warning("⚠️ This will delete data older than 7 days")
                if st.button("✅ Confirm Delete", use_container_width=True, key="confirm_delete"):
                    result = make_api_call(
                        "/api/analytics/telemetry/clear?days=7",
                        method="DELETE"
                    )
                    if result:
                        deleted = result.get('deleted_entries', 0)
                        st.success(f"✅ Deleted {deleted} entries")
                    else:
                        st.error("❌ Failed to clear data")

            st.markdown("#### Export Data")
            if st.button("📥 Export Telemetry CSV", use_container_width=True):
                telemetry_data = make_api_call("/api/analytics/telemetry?limit=10000")
                if telemetry_data and telemetry_data.get("entries"):
                    df = pd.DataFrame(telemetry_data["entries"])
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"telemetry_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.error("❌ No data to export")

        st.divider()

        st.markdown("#### System Information")
        info_col1, info_col2 = st.columns(2)

        with info_col1:
            st.info("""
            **AegisCAN-RT v4.0.0**
            
            Deterministic ultra-low-latency BLE→CAN real-time gateway
            for safety-critical automotive systems.
            
            ✅ 26/26 Tests Passing
            ✅ 58% Code Coverage
            ✅ Production Ready
            
            [🔗 GitHub Repository](https://github.com/dhakarshailendra829/AegisCAN-RT)
            """)

        with info_col2:
            health = make_api_call("/health")
            if health:
                status_badge = "✅ Healthy" if health.get("status") == "healthy" else "❌ Unhealthy"
                st.metric("API Status", status_badge)
                st.metric("Environment", health.get("environment", "unknown").upper())
                st.metric("Version", health.get("version", "4.0.0"))
            else:
                st.error("❌ Cannot connect to API server")


# ============================================================================
# Main Application Entry Point
# ============================================================================

if __name__ == "__main__":
    if not st.session_state.authenticated:
        login_page()
    else:
        main_dashboard()