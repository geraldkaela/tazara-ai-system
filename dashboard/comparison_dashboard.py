import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO

# ----------------------------
# Page config
# ----------------------------
st.set_page_config(
    page_title="TAZARA Comparison Dashboard",
    layout="wide"
)

st.title("🔄 TAZARA Baseline vs RL Comparison")
st.markdown("Compare traditional scheduling with Reinforcement Learning performance")

# ----------------------------
# File upload
# ----------------------------
st.sidebar.header("📁 Upload Schedule File")
uploaded_file = st.sidebar.file_uploader(
    "Choose Excel file",
    type=['xlsx'],
    help="Upload schedule file with route, cargo, and priority columns"
)

if uploaded_file is not None:
    # Send file to comparison API
    files = {"file": (uploaded_file.name, uploaded_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    
    try:
        response = requests.post(
            "http://127.0.0.1:8000/compare/",
            files=files
        )
        
        if response.status_code == 200:
            data = response.json()
            comparison = data["comparison"]
            
            # ----------------------------
            # Overview Metrics
            # ----------------------------
            st.subheader("📊 Performance Overview")
            
            baseline_metrics = comparison["baseline"]["metrics"]
            rl_metrics = comparison["rl"]["metrics"]
            analysis = comparison["analysis"]
            
            # Financial comparison
            col1, col2, col3, col4 = st.columns(4)
            
            col1.metric(
                "Baseline Net Profit",
                f"ZMW {baseline_metrics['cost_breakdown_zmw']['net_profit_zmw']:,.2f}",
                delta=None
            )
            
            col2.metric(
                "RL Net Profit",
                f"ZMW {rl_metrics['cost_breakdown_zmw']['net_profit_zmw']:,.2f}",
                delta=f"ZMW {analysis['profit_improvement_zmw']:,.2f}",
                delta_color="normal" if analysis['profit_improvement_zmw'] >= 0 else "inverse"
            )
            
            col3.metric(
                "Baseline Cargo Delivered",
                f"{baseline_metrics['total_cargo_delivered']:,.0f} tons"
            )
            
            col4.metric(
                "RL Cargo Delivered",
                f"{rl_metrics['total_cargo_delivered']:,.0f} tons",
                delta=f"{analysis['cargo_efficiency_improvement']:,.0f} tons",
                delta_color="normal" if analysis['cargo_efficiency_improvement'] >= 0 else "inverse"
            )
            
            # ----------------------------
            # Cost Breakdown Comparison
            # ----------------------------
            st.subheader("💰 ZMW Cost Breakdown Comparison")
            
            # Create comparison dataframe
            cost_data = {
                "Metric": ["Revenue", "Train Cost", "Delay Cost", "Idle Cost", "Net Profit"],
                "Baseline (ZMW)": [
                    baseline_metrics['cost_breakdown_zmw']['revenue_zmw'],
                    baseline_metrics['cost_breakdown_zmw']['train_cost_zmw'],
                    baseline_metrics['cost_breakdown_zmw']['delay_cost_zmw'],
                    baseline_metrics['cost_breakdown_zmw']['idle_cost_zmw'],
                    baseline_metrics['cost_breakdown_zmw']['net_profit_zmw']
                ],
                "RL (ZMW)": [
                    rl_metrics['cost_breakdown_zmw']['revenue_zmw'],
                    rl_metrics['cost_breakdown_zmw']['train_cost_zmw'],
                    rl_metrics['cost_breakdown_zmw']['delay_cost_zmw'],
                    rl_metrics['cost_breakdown_zmw']['idle_cost_zmw'],
                    rl_metrics['cost_breakdown_zmw']['net_profit_zmw']
                ]
            }
            
            cost_df = pd.DataFrame(cost_data)
            st.dataframe(cost_df, use_container_width=True)
            
            # ----------------------------
            # Visualizations
            # ----------------------------
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Cost Comparison Chart")
                fig, ax = plt.subplots(figsize=(10, 6))
                
                x = range(len(cost_df["Metric"]))
                width = 0.35
                
                ax.bar([i - width/2 for i in x], cost_df["Baseline (ZMW)"], width, 
                       label='Baseline', alpha=0.8, color='lightcoral')
                ax.bar([i + width/2 for i in x], cost_df["RL (ZMW)"], width,
                       label='RL', alpha=0.8, color='lightblue')
                
                ax.set_xlabel('Metrics')
                ax.set_ylabel('ZMW')
                ax.set_title('Baseline vs RL Cost Comparison')
                ax.set_xticks(x)
                ax.set_xticklabels(cost_df["Metric"], rotation=45)
                ax.legend()
                ax.grid(True, alpha=0.3)
                
                st.pyplot(fig)
            
            with col2:
                st.subheader("📈 Improvement Analysis")
                improvement_data = {
                    "Improvement Type": [
                        "Profit Improvement",
                        "Revenue Improvement", 
                        "Cost Reduction",
                        "Cargo Efficiency"
                    ],
                    "ZMW/Tons": [
                        analysis['profit_improvement_zmw'],
                        analysis['revenue_improvement_zmw'],
                        analysis['cost_reduction_zmw'],
                        analysis['cargo_efficiency_improvement']
                    ],
                    "Unit": ["ZMW", "ZMW", "ZMW", "Tons"]
                }
                
                improvement_df = pd.DataFrame(improvement_data)
                
                fig, ax = plt.subplots(figsize=(10, 6))
                colors = ['green' if x >= 0 else 'red' for x in improvement_df["ZMW/Tons"]]
                
                bars = ax.bar(improvement_df["Improvement Type"], improvement_df["ZMW/Tons"], color=colors, alpha=0.7)
                ax.set_ylabel('Value')
                ax.set_title('RL vs Baseline Improvements')
                ax.tick_params(axis='x', rotation=45)
                ax.grid(True, alpha=0.3)
                ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
                
                # Add value labels on bars
                for bar, value in zip(bars, improvement_df["ZMW/Tons"]):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{value:,.0f}', ha='center', va='bottom' if height >= 0 else 'top')
                
                st.pyplot(fig)
            
            # ----------------------------
            # Schedule Comparison
            # ----------------------------
            st.subheader("📋 Schedule Comparison")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Baseline Schedule:**")
                baseline_schedule = comparison["baseline"]["schedule"]
                for i, action in enumerate(baseline_schedule, 1):
                    st.write(f"Day {i}: {action}")
            
            with col2:
                st.write("**RL Schedule:**")
                rl_schedule = comparison["rl"]["schedule"]
                for i, action in enumerate(rl_schedule, 1):
                    st.write(f"Day {i}: {action}")
            
            # ----------------------------
            # Summary
            # ----------------------------
            st.subheader("🎯 Executive Summary")
            
            if analysis['profit_improvement_zmw'] > 0:
                st.success(f"✅ RL outperforms baseline by ZMW {analysis['profit_improvement_zmw']:,.2f}")
            else:
                st.warning(f"⚠️ Baseline outperforms RL by ZMW {abs(analysis['profit_improvement_zmw']):,.2f}")
            
            if analysis['cargo_efficiency_improvement'] > 0:
                st.success(f"✅ RL delivers {analysis['cargo_efficiency_improvement']:,.0f} more tons of cargo")
            else:
                st.warning(f"⚠️ Baseline delivers {abs(analysis['cargo_efficiency_improvement']):,.0f} more tons of cargo")
                
        else:
            st.error(f"❌ Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to API server. Make sure the server is running on http://127.0.0.1:8000")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

else:
    st.info("👆 Upload a schedule file to compare Baseline vs RL performance")
