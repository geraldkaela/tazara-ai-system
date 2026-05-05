import streamlit as st
from auth import login, logout
from utils.session import is_logged_in, get_role

st.set_page_config(
    page_title="TAZARA RL System",
    layout="wide"
)

# ---------------- LOGIN GATE ----------------
if not is_logged_in():
    login()
    st.stop()

role = get_role()

# ---------------- SIDEBAR ----------------
st.sidebar.title("🚆 TAZARA RL System")
st.sidebar.markdown(f"**Role:** {role}")

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "KPI Data", "Settings"]
)

st.sidebar.button("🚪 Logout", on_click=logout)

# ---------------- PAGE ROUTING ----------------
if page == "Dashboard":
    import pages.dashboard as dashboard
    dashboard.render()

elif page == "KPI Data":
    import pages.kpis as kpis
    kpis.render()

elif page == "Settings":
    if role != "Admin":
        st.error("⛔ Access denied. Admins only.")
        st.stop()
    import pages.settings as settings
    settings.render()
