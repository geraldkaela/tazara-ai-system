import yaml
import streamlit as st

def load_users():
    with open("dashboard/users.yaml", "r") as f:
        return yaml.safe_load(f)

def login():
    st.title("🔐 TAZARA System Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        users = load_users()

        for user in users.values():
            if user["username"] == username and user["password"] == password:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.role = user["role"]
                st.success(f"Welcome {username} ({user['role']})")
                st.rerun()

        st.error("Invalid username or password")

def logout():
    for key in ["authenticated", "username", "role"]:
        st.session_state.pop(key, None)
    st.rerun()
