import streamlit as st

def render():
    st.title("⚙️ System Settings")

    st.info("Admin-only configuration panel")

    episodes = st.number_input(
        "Evaluation Episodes",
        min_value=1,
        max_value=100,
        value=5
    )

    auto_refresh = st.toggle("Auto-refresh dashboard after evaluation")

    if st.button("💾 Save Settings"):
        st.success("Settings saved (session-based for now)")
