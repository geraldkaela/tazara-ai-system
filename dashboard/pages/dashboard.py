import streamlit as st
import pandas as pd
import altair as alt

def render():
    st.title("📊 RL Daily Operations Dashboard")
    try:
        df = pd.read_csv("metrics/rl_daily_report.csv")
    except FileNotFoundError:
        st.warning("Metrics CSV not found. Run evaluation first.")
        return

    # Filters
    min_day = int(df["day"].min())
    max_day = int(df["day"].max())
    day_range = st.slider("Select Day Range", min_value=min_day, max_value=max_day,
                          value=(min_day, max_day))
    df = df[(df["day"] >= day_range[0]) & (df["day"] <= day_range[1])]

    # KPIs
    st.subheader("📌 Key Performance Indicators")
    st.metric("Avg Reward (Cost Savings)", f"{df['total_reward'].mean():.2f}")
    st.metric("Avg Cargo Delivered (tons)", f"{df['cargo_delivered'].mean():.2f}")
    st.metric("Avg Trains Used", f"{df['trains_used'].mean():.1f}")
    st.metric("Avg Idle Penalty (cost)", f"{df['idle_penalty'].mean():.2f}")

    # Reward per day
    st.subheader("📈 Reward per Day")
    reward_chart = alt.Chart(df).mark_line(point=True).encode(
        x="day",
        y="total_reward"
    )
    st.altair_chart(reward_chart, use_container_width=True)

    # Action distribution
    st.subheader("🎯 Action Distribution")
    action_df = df[["assign_count", "delay_count", "skip_count"]].sum().reset_index()
    action_df.columns = ["action", "count"]
    action_chart = alt.Chart(action_df).mark_bar().encode(
        x="action",
        y="count"
    )
    st.altair_chart(action_chart, use_container_width=True)
