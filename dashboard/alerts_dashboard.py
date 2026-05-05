import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# ----------------------------
# Page config
# ----------------------------
st.set_page_config(
    page_title="TAZARA Alerts Dashboard",
    layout="wide"
)

st.title("🚨 TAZARA Alerts & Operations Dashboard")
st.markdown("Real-time alerts and daily operations monitoring")

# ----------------------------
# Sidebar controls
# ----------------------------
st.sidebar.header("⚙️ Controls")

# Refresh button
if st.sidebar.button("🔄 Refresh Data"):
    # Clear cache and refresh
    st.cache_data.clear()
    st.rerun()

# Connection test
if st.sidebar.button("🔗 Test Connection"):
    try:
        response = requests.get("http://127.0.0.1:8000/health/", timeout=3)
        if response.status_code == 200:
            st.sidebar.success("✅ API Connected")
        else:
            st.sidebar.error(f"❌ API Error: {response.status_code}")
    except Exception as e:
        st.sidebar.error(f"❌ Connection Failed: {str(e)}")

# Generate sample alerts
if st.sidebar.button("📊 Generate Sample Alerts"):
    try:
        response = requests.post("http://127.0.0.1:8000/alerts/generate-sample")
        if response.status_code == 200:
            st.sidebar.success("Sample alerts generated!")
            st.rerun()
        else:
            st.sidebar.error("Failed to generate alerts")
    except:
        st.sidebar.error("Cannot connect to API server")

# ----------------------------
# Fetch alerts data
# ----------------------------
@st.cache_data(ttl=5)  # Cache for 5 seconds
def load_alerts():
    try:
        url = "http://127.0.0.1:8000/alerts/"
        st.sidebar.write(f"🔗 Trying: {url}")
        response = requests.get(url, timeout=5)
        st.sidebar.write(f"📊 Status: {response.status_code}")
        if response.status_code == 200:
            st.sidebar.success("✅ Connected to API!")
            return response.json()
        else:
            st.sidebar.error(f"❌ API Error: {response.status_code}")
            st.sidebar.write(f"📝 Response: {response.text}")
            return []
    except Exception as e:
        st.sidebar.error(f"❌ Connection Failed: {str(e)}")
        return []

@st.cache_data(ttl=5)  # Cache for 5 seconds
def load_alerts_summary():
    try:
        response = requests.get("http://127.0.0.1:8000/alerts/summary", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return {}
    except:
        return {}

@st.cache_data(ttl=5)  # Cache for 5 seconds
def load_daily_reports():
    try:
        response = requests.get("http://127.0.0.1:8000/alerts/daily-reports?days=7", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except:
        return []

alerts = load_alerts()
summary = load_alerts_summary()
daily_reports = load_daily_reports()

# ----------------------------
# Alert Summary Cards
# ----------------------------
st.subheader("🚨 Alert Summary")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "🔴 Critical",
    summary.get("critical_alerts", 0),
    delta=None,
    delta_color="inverse"
)

col2.metric(
    "🟡 Warning", 
    summary.get("warning_alerts", 0),
    delta=None,
    delta_color="inverse"
)

col3.metric(
    "🔵 Info",
    summary.get("info_alerts", 0),
    delta=None
)

col4.metric(
    "📋 Total Unacknowledged",
    summary.get("total_unacknowledged", 0),
    delta=None,
    delta_color="inverse"
)

# ----------------------------
# Active Alerts Table
# ----------------------------
st.subheader("📋 Active Alerts")

if alerts:
    # Filter for unacknowledged alerts
    active_alerts = [a for a in alerts if not a.get("acknowledged", False)]
    
    if active_alerts:
        # Create dataframe for display
        alert_df = pd.DataFrame(active_alerts)
        
        # Format timestamp
        alert_df['timestamp'] = pd.to_datetime(alert_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Color coding for severity
        def color_severity(severity):
            if severity == "critical":
                return "🔴"
            elif severity == "warning":
                return "🟡"
            else:
                return "🔵"
        
        alert_df['severity_icon'] = alert_df['severity'].apply(color_severity)
        
        # Reorder columns
        display_columns = ['severity_icon', 'timestamp', 'category', 'message', 'zmw_impact']
        alert_df = alert_df[display_columns]
        
        # Rename for display
        alert_df.columns = ['Severity', 'Time', 'Category', 'Message', 'ZMW Impact']
        
        st.dataframe(alert_df, use_container_width=True)
        
        # Acknowledge buttons
        st.subheader("✅ Acknowledge Alerts")
        
        for alert in active_alerts:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{alert['category'].title()}**: {alert['message']}")
            with col2:
                if st.button(f"Acknowledge", key=f"ack_{alert['id']}"):
                    try:
                        response = requests.put(f"http://127.0.0.1:8000/alerts/{alert['id']}/acknowledge")
                        if response.status_code == 200:
                            st.success(f"Alert {alert['id']} acknowledged!")
                            st.rerun()
                        else:
                            st.error("Failed to acknowledge")
                    except:
                        st.error("Cannot connect to API")
    else:
        st.success("✅ No active alerts!")
else:
    st.warning("⚠️ Cannot load alerts - make sure API server is running")

# ----------------------------
# Daily Operations Reports
# ----------------------------
st.subheader("📊 Daily Operations Reports")

if daily_reports:
    # Create dataframe
    reports_df = pd.DataFrame(daily_reports)
    
    if not reports_df.empty:
        # Format date
        reports_df['date'] = pd.to_datetime(reports_df['date']).dt.strftime('%Y-%m-%d')
        
        # Select columns for display
        display_cols = ['date', 'total_cargo_delivered', 'net_profit_zmw', 'efficiency_score']
        reports_df_display = reports_df[display_cols]
        reports_df_display.columns = ['Date', 'Cargo (tons)', 'Net Profit (ZMW)', 'Efficiency (%)']
        
        st.dataframe(reports_df_display, use_container_width=True)
        
        # Performance trend chart
        st.subheader("📈 Performance Trend")
        
        fig = go.Figure()
        
        # Add profit trend
        fig.add_trace(go.Scatter(
            x=reports_df['date'],
            y=reports_df['net_profit_zmw'],
            mode='lines+markers',
            name='Net Profit (ZMW)',
            line=dict(color='green'),
            yaxis='y1'
        ))
        
        # Add efficiency trend
        fig.add_trace(go.Scatter(
            x=reports_df['date'],
            y=reports_df['efficiency_score'],
            mode='lines+markers',
            name='Efficiency (%)',
            line=dict(color='blue'),
            yaxis='y2'
        ))
        
        # Create dual axis
        fig.update_layout(
            title='Daily Performance Trends',
            xaxis_title='Date',
            yaxis=dict(
                title='Net Profit (ZMW)',
                tickfont=dict(color='green')
            ),
            yaxis2=dict(
                title='Efficiency (%)',
                tickfont=dict(color='blue'),
                overlaying='y',
                side='right'
            ),
            legend=dict(x=0.01, y=0.99)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Recommendations section
        if not reports_df.empty:
            latest_report = reports_df.iloc[-1]
            if latest_report.get('recommendations'):
                st.subheader("💡 Latest Recommendations")
                for rec in latest_report['recommendations']:
                    st.write(f"• {rec}")
else:
    st.info("📋 No daily reports available")

# ----------------------------
# System Status
# ----------------------------
st.subheader("🖥️ System Status")

col1, col2 = st.columns(2)

with col1:
    st.write("**API Server Status**")
    try:
        response = requests.get("http://127.0.0.1:8000/health/", timeout=5)
        if response.status_code == 200:
            st.success("🟢 Online")
        else:
            st.error("🔴 Error")
    except:
        st.error("🔴 Offline")

with col2:
    st.write("**Last 24h Activity**")
    last_24h = summary.get("last_24h_alerts", 0)
    if last_24h > 0:
        st.warning(f"⚠️ {last_24h} alerts in last 24 hours")
    else:
        st.success("✅ No recent alerts")
