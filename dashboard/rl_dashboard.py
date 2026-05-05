import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ----------------------------
# Page config
# ----------------------------
st.set_page_config(
    page_title="TAZARA RL Dashboard",
    layout="wide"
)

st.title("🚆 TAZARA Reinforcement Learning Dashboard")
st.markdown("Performance evaluation and KPI analysis of the RL scheduling agent")

# ----------------------------
# Load KPI data
# ----------------------------
DATA_PATH = "metrics/rl_kpis_phase5.csv"

@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH)

df = load_data()

# ----------------------------
# Sidebar filters
# ----------------------------
st.sidebar.header("📊 Filters")

episode_range = st.sidebar.slider(
    "Select Episode Range",
    int(df["episode"].min()),
    int(df["episode"].max()),
    (int(df["episode"].min()), int(df["episode"].max()))
)

filtered_df = df[
    (df["episode"] >= episode_range[0]) &
    (df["episode"] <= episode_range[1])
]

# ----------------------------
# KPI Cards
# ----------------------------
st.subheader("📌 Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Avg Reward",
    f"{filtered_df['total_reward'].mean():.2f}"
)

col2.metric(
    "Avg Cargo Delivered",
    f"{filtered_df['cargo_delivered'].mean():.2f}"
)

col3.metric(
    "Avg Trains Used",
    f"{filtered_df['trains_used'].mean():.2f}"
)

col4.metric(
    "Avg Idle Penalty",
    f"{filtered_df['idle_penalty'].mean():.2f}"
)

# ----------------------------
# Reward per Episode
# ----------------------------
st.subheader("📈 Reward per Episode")

fig, ax = plt.subplots()
ax.plot(
    filtered_df["episode"],
    filtered_df["total_reward"],
    marker="o"
)
ax.set_xlabel("Episode")
ax.set_ylabel("Total Reward")
ax.grid(True)

st.pyplot(fig)

# ----------------------------
# Action Distribution
# ----------------------------
st.subheader("🎯 Action Distribution")

action_totals = {
    "Assign Train": filtered_df["assign_actions"].sum(),
    "Delay Train": filtered_df["delay_actions"].sum(),
    "Skip Route": filtered_df["skip_actions"].sum()
}

fig2, ax2 = plt.subplots()
ax2.bar(action_totals.keys(), action_totals.values())
ax2.set_ylabel("Count")

st.pyplot(fig2)

# ----------------------------
# Cargo vs Idle Penalty
# ----------------------------
st.subheader("📦 Cargo Delivered vs Idle Penalties")

fig3, ax3 = plt.subplots()
ax3.plot(filtered_df["episode"], filtered_df["cargo_delivered"], label="Cargo Delivered")
ax3.plot(filtered_df["episode"], filtered_df["idle_penalty"], label="Idle Penalty")
ax3.legend()
ax3.set_xlabel("Episode")
ax3.grid(True)

st.pyplot(fig3)

# ----------------------------
# Download CSV
# ----------------------------
st.subheader("⬇️ Download KPI Data")

csv = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download KPI CSV",
    data=csv,
    file_name="rl_kpis_filtered.csv",
    mime="text/csv"
)

st.success("Dashboard loaded successfully ✅")
