import streamlit as st

def is_logged_in():
    return st.session_state.get("authenticated", False)

def require_login():
    if not is_logged_in():
        st.warning("Please log in to access the system.")
        st.stop()

def get_role():
    return st.session_state.get("role", "Guest")
