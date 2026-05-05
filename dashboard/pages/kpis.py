import streamlit as st
import pandas as pd

def render():
    st.title("📁 KPI Data")

    df = pd.read_csv("metrics/rl_kpis_phase5.csv")

    st.dataframe(df)

    st.download_button(
        label="⬇️ Download KPI CSV",
        data=df.to_csv(index=False),
        file_name="rl_kpis_phase5.csv",
        mime="text/csv"
    )
