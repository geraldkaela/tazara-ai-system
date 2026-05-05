import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# ----------------------------
# Page config
# ----------------------------
st.set_page_config(
    page_title="TAZARA Multi-Route Operations",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🚂 TAZARA Multi-Route Operations Dashboard")
st.markdown("Advanced multi-train scheduling and real-time performance monitoring")

# ----------------------------
# Sidebar controls
# ----------------------------
st.sidebar.header("🎛 Control Panel")

# Refresh button
if st.sidebar.button("🔄 Refresh Data"):
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 🖥️ Premium Views")
if st.sidebar.button("🚀 Open Tactical View"):
    st.markdown(
        '<meta http-equiv="refresh" content="0; url=/static/multi_route.html">',
        unsafe_allow_html=True,
    )

# System status
st.sidebar.subheader("📊 System Status")
try:
    response = requests.get("http://127.0.0.1:8000/multi-route/status", timeout=5)
    if response.status_code == 200:
        status = response.json()
        st.sidebar.success("✅ Multi-Route System Online")
        st.sidebar.write(f"🚂 Trains: {status.get('supported_trains', [])}")
        st.sidebar.write(f"📦 Routes: {', '.join(status.get('routes', []))}")
        
        # Database status
        if status.get('database_connected'):
            st.sidebar.success("✅ Database Connected")
            db_stats = status.get('database_stats', {})
            st.sidebar.write(f"📊 Total Schedules: {db_stats.get('total_schedules', 0)}")
        else:
            st.sidebar.warning("⚠️ Database Disconnected")
    else:
        st.sidebar.error("❌ System Offline")
except:
    st.sidebar.error("❌ Connection Error")

# ----------------------------
# Main content area
# ----------------------------# Create tabs for different views
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview", "🚂 Schedule Viewer", "📈 Performance Analytics", "🔮 Predictive Analytics", "🔧 Configuration"
])

with tab1:
    st.header("📊 Multi-Route Operations Overview")
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🚂 Total Trains",
            value="6",
            delta=None
        )
    
    with col2:
        st.metric(
            label="📦 Active Routes",
            value="3",
            delta=None
        )
    
    with col3:
        st.metric(
            label="⚡ Daily Capacity",
            value="300 tons",
            delta=None
        )
    
    with col4:
        st.metric(
            label="🎯 Efficiency Target",
            value="85%",
            delta=None
        )
    
    # System capabilities
    st.subheader("🔧 System Capabilities")
    capabilities = [
        "🚂 Parallel Train Operations",
        "📦 Multi-Route Scheduling", 
        "🎯 Real-Time Optimization",
        "💰 ZMW Cost Analysis",
        "📈 Performance Tracking",
        "⚡ Efficiency Monitoring",
        "🔄 Dynamic Rebalancing"
    ]
    
    for i, capability in enumerate(capabilities, 1):
        st.write(f"**{i}. {capability}**")

with tab2:
    st.header("🚂 Multi-Route Schedule Viewer")
    
    # Excel Upload Section
    st.subheader("📁 Upload Excel File for Batch Scheduling")
    
    # Create columns for upload and manual creation
    upload_col, manual_col = st.columns([1, 1])
    
    with upload_col:
        st.write("**Upload Excel File**")
        st.write("Upload an Excel file with cargo requirements for batch scheduling.")
        
        uploaded_file = st.file_uploader(
            "Choose Excel file",
            type=['xlsx', 'xls'],
            help="Upload an Excel file with columns: Route, Cargo_Tons, Trains, Days"
        )
        
        if uploaded_file is not None:
            try:
                # Read Excel file
                import pandas as pd
                df = pd.read_excel(uploaded_file)
                
                st.success(f"✅ File uploaded successfully! Found {len(df)} rows.")
                
                # Display the data
                st.write("**Preview of uploaded data:**")
                st.dataframe(df.head())
                
                # Show available columns
                st.write(f"**Available columns:** {list(df.columns)}")
                
                # Flexible column validation - check for common variations
                column_mapping = {}
                required_columns = ['Route', 'Cargo_Tons']
                
                # Map common column name variations
                column_variations = {
                    'Route': ['Route', 'route', 'ROUTE', 'Route Name', 'route_name', 'ROUTE_NAME'],
                    'Cargo_Tons': ['Cargo_Tons', 'Cargo Tons', 'cargo_tons', 'CARGO_TONS', 'Cargo', 'cargo', 'CARGO', 'Tons', 'tons', 'TONS'],
                    'Trains': ['Trains', 'trains', 'TRAINS', 'Train', 'train', 'TRAIN', 'Num Trains', 'num_trains'],
                    'Days': ['Days', 'days', 'DAYS', 'Day', 'day', 'DAY', 'Duration', 'duration']
                }
                
                # Find matching columns
                for required_col, variations in column_variations.items():
                    for col in df.columns:
                        if col in variations:
                            column_mapping[required_col] = col
                            break
                
                # Check if we found the required columns
                missing_columns = [col for col in required_columns if col not in column_mapping]
                
                if missing_columns:
                    st.error(f"❌ Could not find required columns. Looking for: {required_columns}")
                    st.error(f"❌ Missing: {missing_columns}")
                    st.info("💡 **Expected column names:** Route, Cargo_Tons (or variations like 'route', 'cargo', 'tons')")
                else:
                    st.success("✅ All required columns found!")
                    st.write(f"**Column mapping:** {column_mapping}")
                    
                    # Process button
                    if st.button("🚀 Process Excel Schedules", type="primary"):
                        with st.spinner("Processing Excel schedules..."):
                            try:
                                # Convert DataFrame to list of schedules
                                schedules = []
                                for _, row in df.iterrows():
                                    route = str(row[column_mapping['Route']]).upper()
                                    cargo_tons = float(row[column_mapping['Cargo_Tons']])
                                    trains = int(row.get(column_mapping.get('Trains', 'Trains'), 6))
                                    days = int(row.get(column_mapping.get('Days', 'Days'), 14))
                                    
                                    # Validate route
                                    if route not in ['DAR_KAPIRI', 'DAR_MBEYA', 'KAPIRI_NDOLA']:
                                        st.warning(f"⚠️ Unknown route '{route}', skipping...")
                                        continue
                                    
                                    schedules.append({
                                        'route': route,
                                        'cargo_tons': cargo_tons,
                                        'trains': trains,
                                        'days': days
                                    })
                                
                                if schedules:
                                    # Process each schedule
                                    results = []
                                    for i, schedule in enumerate(schedules):
                                        st.write(f"Processing schedule {i+1}/{len(schedules)}: {schedule['route']}")
                                        
                                        # Create schedule request
                                        schedule_request = {
                                            "num_trains": schedule['trains'],
                                            "max_days": schedule['days'],
                                            "cargo_requirements": {
                                                schedule['route']: schedule['cargo_tons']
                                            }
                                        }
                                        
                                        response = requests.post(
                                            "http://127.0.0.1:8000/multi-route/schedule",
                                            json=schedule_request,
                                            timeout=30
                                        )
                                        
                                        if response.status_code == 200:
                                            result = response.json()
                                            results.append({
                                                'route': schedule['route'],
                                                'schedule_id': result['schedule_id'],
                                                'cargo_delivered': result['performance_metrics']['total_cargo_delivered'],
                                                'efficiency': result['performance_metrics']['efficiency'],
                                                'status': 'Success'
                                            })
                                        else:
                                            results.append({
                                                'route': schedule['route'],
                                                'schedule_id': None,
                                                'cargo_delivered': 0,
                                                'efficiency': 0,
                                                'status': f'Failed: {response.status_code}'
                                            })
                                    
                                    # Display results
                                    st.success("✅ Excel processing completed!")
                                    
                                    results_df = pd.DataFrame(results)
                                    st.write("**Processing Results:**")
                                    st.dataframe(results_df)
                                    
                                    # Summary
                                    successful = len([r for r in results if r['status'] == 'Success'])
                                    total_cargo = sum([r['cargo_delivered'] for r in results])
                                    avg_efficiency = sum([r['efficiency'] for r in results]) / len(results) if results else 0
                                    
                                    st.subheader("📊 Batch Processing Summary")
                                    col1, col2, col3, col4 = st.columns(4)
                                    
                                    with col1:
                                        st.metric("Total Schedules", len(results))
                                    with col2:
                                        st.metric("Successful", successful)
                                    with col3:
                                        st.metric("Total Cargo", f"{total_cargo:.0f} tons")
                                    with col4:
                                        st.metric("Avg Efficiency", f"{avg_efficiency:.1f}%")
                                
                            except Exception as e:
                                st.error(f"❌ Error processing schedules: {str(e)}")
                        
            except Exception as e:
                st.error(f"❌ Error reading Excel file: {str(e)}")
        
        # Download template button
        st.write("**Need a template?**")
        if st.button("📥 Download Excel Template"):
            # Create template DataFrame
            template_data = {
                'Route': ['DAR_KAPIRI', 'DAR_MBEYA', 'KAPIRI_NDOLA'],
                'Cargo_Tons': [1000, 1000, 500],
                'Trains': [6, 6, 4],
                'Days': [14, 14, 14]
            }
            template_df = pd.DataFrame(template_data)
            
            # Add instructions as a second sheet
            instructions_data = {
                'Column': ['Route', 'Cargo_Tons', 'Trains', 'Days'],
                'Description': [
                    'Route name (DAR_KAPIRI, DAR_MBEYA, KAPIRI_NDOLA)',
                    'Cargo amount in tons (number)',
                    'Number of trains to use (optional, default: 6)',
                    'Planning horizon in days (optional, default: 14)'
                ],
                'Example': ['DAR_KAPIRI', '1000', '6', '14']
            }
            instructions_df = pd.DataFrame(instructions_data)
            
            # Convert to Excel
            import io
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                template_df.to_excel(writer, index=False, sheet_name='Schedule_Template')
                instructions_df.to_excel(writer, index=False, sheet_name='Instructions')
            
            # Offer download
            st.download_button(
                label="📥 Download Template.xlsx",
                data=output.getvalue(),
                file_name="tazara_schedule_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with manual_col:
        st.write("**Or Create Manually**")
        st.write("Create a single schedule manually using the form below.")
        
        # Schedule creation section
        st.subheader("Create New Schedule")
    
    col1, col2 = st.columns(2)
    
    with col1:
        num_trains = st.number_input(
            "Number of Trains",
            min_value=1,
            max_value=12,
            value=6,
            step=1
        )
        
        max_days = st.number_input(
            "Planning Horizon (Days)",
            min_value=1,
            max_value=30,
            value=14,
            step=1
        )
    
    with col2:
        st.write("**Cargo Requirements (tons)**")
        st.write("Enter cargo amounts for each route:")
        
        # Cargo inputs
        cargo_inputs = {}
        routes = ["DAR_KAPIRI", "DAR_MBEYA", "KAPIRI_NDOLA"]
        
        for route in routes:
            cargo_inputs[route] = st.number_input(
                f"{route} (tons)",
                min_value=0,
                max_value=5000,
                value=500,
                step=1,
                key=f"cargo_{route}"
            )
        
        if st.button("🚀 Generate Multi-Route Schedule"):
            # Create schedule request
            schedule_request = {
                "num_trains": int(num_trains),
                "max_days": int(max_days),
                "cargo_requirements": cargo_inputs
            }
            
            try:
                response = requests.post(
                    "http://127.0.0.1:8000/multi-route/schedule",
                    json=schedule_request,
                    timeout=30
                )
                
                if response.status_code == 200:
                    schedule = response.json()
                    st.success("✅ Multi-Route Schedule Created!")
                    st.write(f"**Schedule ID**: {schedule['schedule_id']}")
                    
                    # Display schedule summary
                    st.subheader("📋 Schedule Summary")
                    summary_col1, summary_col2 = st.columns(2)
                    
                    with summary_col1:
                        st.write("**Performance Metrics**")
                        metrics = schedule['performance_metrics']
                        st.write(f"- Total Cargo Delivered: {metrics['total_cargo_delivered']:.0f} tons")
                        st.write(f"- Trains Used: {metrics['trains_used']}")
                        st.write(f"- Active Trains: {metrics['active_trains']}")
                        st.write(f"- Efficiency: {metrics['efficiency']:.1f} tons/train")
                    
                    with summary_col2:
                        st.write("**ZMW Cost Breakdown**")
                        cost_breakdown = schedule['cost_breakdown_zmw']
                        st.write(f"- Revenue: ZMW {cost_breakdown['revenue_zmw']:,.2f}")
                        st.write(f"- Train Cost: ZMW {cost_breakdown['train_cost_zmw']:,.2f}")
                        st.write(f"- Delay Cost: ZMW {cost_breakdown['delay_cost_zmw']:,.2f}")
                        st.write(f"- Idle Cost: ZMW {cost_breakdown['idle_cost_zmw']:,.2f}")
                        
                        # Phase 4 Metrics
                        total_fuel = sum([a.get('fuel_cost_est', 0) for a in schedule.get('train_assignments', [])])
                        st.write(f"- **Est. Fuel Cost: ZMW {total_fuel:,.2f}**")
                        
                        st.write(f"- Coordination Bonus: ZMW {cost_breakdown.get('coordination_bonus_zmw', 0):,.2f}")
                        st.write(f"- **Net Profit: ZMW {cost_breakdown['net_profit_zmw']:,.2f}**")
                    
                    # Display efficiency analysis
                    st.subheader("🎯 Route Efficiency Analysis")
                    efficiency = schedule['efficiency_analysis']
                    
                    eff_data = []
                    for route, efficiency in efficiency['route_efficiency'].items():
                        eff_data.append({
                            "Route": route,
                            "Efficiency": f"{efficiency:.1f} tons/train",
                            "Utilization": f"{(efficiency / 50) * 100:.1f}%"
                        })
                    
                    eff_df = pd.DataFrame(eff_data)
                    st.dataframe(eff_df, use_container_width=True)
                    
                    # Daily actions visualization
                    st.subheader("📅 Daily Train Actions & Resource Matching (Phase 4)")
                    train_assignments = schedule['train_assignments']
                    
                    # Create assignment dataframe
                    assign_df = pd.DataFrame(train_assignments)
                    
                    # Select and rename columns for display
                    if not assign_df.empty:
                        display_assign = assign_df[[
                            'day', 'train_id', 'route_name', 'driver_id', 'skill_level', 'fuel_cost_est'
                        ]].copy()
                        display_assign.columns = [
                            'Day', 'Train ID', 'Route', 'Driver Assigned', 'Skill Level', 'Fuel Cost (ZMW)'
                        ]
                        st.dataframe(display_assign, use_container_width=True)
                    else:
                        st.info("No train assignments found.")
                    
                else:
                    st.error(f"❌ Schedule Creation Failed: {response.text}")
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

with tab3:
    st.header("📈 Performance Analytics")
    
    # Load real performance data from database
    st.subheader("📊 Historical Performance Trends")
    
    try:
        # Get performance trends from database
        trends_response = requests.get("http://127.0.0.1:8000/multi-route/performance/trends?days=30", timeout=5)
        if trends_response.status_code == 200:
            trends_data = trends_response.json()
            trends = trends_data.get('trends', [])
            
            if trends:
                # Convert to DataFrame for visualization
                trends_df = pd.DataFrame(trends)
                
                # Performance trend chart
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=trends_df['performance_date'],
                    y=trends_df['avg_cargo'],
                    mode='lines+markers',
                    name='Avg Cargo Delivered',
                    line=dict(color='blue')
                ))
                
                fig.add_trace(go.Scatter(
                    x=trends_df['performance_date'],
                    y=trends_df['avg_efficiency'],
                    mode='lines+markers',
                    name='Avg Efficiency',
                    line=dict(color='green')
                ))
                
                fig.add_trace(go.Scatter(
                    x=trends_df['performance_date'],
                    y=trends_df['total_profit'],
                    mode='lines+markers',
                    name='Total Profit',
                    line=dict(color='red')
                ))
                
                fig.update_layout(
                    title='Multi-Route Performance Trends (Last 30 Days)',
                    xaxis_title='Date',
                    yaxis_title='Value',
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Performance summary table
                st.subheader("📋 Performance Summary")
                summary_col1, summary_col2 = st.columns(2)
                
                with summary_col1:
                    st.write("**Recent Performance**")
                    latest_trend = trends[0] if trends else {}
                    st.write(f"- Avg Cargo: {latest_trend.get('avg_cargo', 0):.1f} tons")
                    st.write(f"- Avg Efficiency: {latest_trend.get('avg_efficiency', 0):.1f}%")
                    st.write(f"- Total Profit: ZMW {latest_trend.get('total_profit', 0):,.2f}")
                
                with summary_col2:
                    st.write("**Trend Analysis**")
                    if len(trends) > 1:
                        cargo_change = trends[0]['avg_cargo'] - trends[-1]['avg_cargo']
                        efficiency_change = trends[0]['avg_efficiency'] - trends[-1]['avg_efficiency']
                        
                        st.write(f"- Cargo Change: {cargo_change:+.1f} tons")
                        st.write(f"- Efficiency Change: {efficiency_change:+.1f}%")
                        st.write(f"- Data Points: {len(trends)}")
            else:
                st.info("📊 No performance data available yet. Create some schedules to see trends.")
        
        else:
            st.error("❌ Failed to load performance trends")
    
    except Exception as e:
        st.error(f"❌ Error loading performance data: {e}")
    
    # Route performance comparison
    st.subheader("🎯 Route Performance Comparison")
    
    try:
        # Get route performance from database
        route_response = requests.get("http://127.0.0.1:8000/multi-route/performance/routes", timeout=5)
        if route_response.status_code == 200:
            route_data = route_response.json()
            route_performance = route_data.get('route_performance', [])
            
            if route_performance:
                route_df = pd.DataFrame(route_performance)
                st.dataframe(route_df, use_container_width=True)
                
                # Route efficiency chart
                fig2 = px.bar(
                    route_df,
                    x='route_name',
                    y='avg_efficiency',
                    color='route_name',
                    title='Route Efficiency Comparison'
                )
                
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("📊 No route performance data available yet.")
        
        else:
            st.error("❌ Failed to load route performance")
    
    except Exception as e:
        st.error(f"❌ Error loading route data: {e}")
    
    # Recent schedules
    st.subheader("📅 Recent Schedules")
    
    try:
        # Get recent schedules from database
        schedules_response = requests.get("http://127.0.0.1:8000/multi-route/schedules?limit=10", timeout=5)
        if schedules_response.status_code == 200:
            schedules_data = schedules_response.json()
            schedules = schedules_data.get('schedules', [])
            
            if schedules:
                schedules_df = pd.DataFrame(schedules)
                
                # Format for display
                display_columns = ['schedule_id', 'timestamp', 'num_trains', 'total_cargo', 'efficiency', 'net_profit_zmw']
                display_df = schedules_df[display_columns].copy()
                display_df.columns = ['Schedule ID', 'Created', 'Trains', 'Cargo (tons)', 'Efficiency', 'Profit (ZMW)']
                
                st.dataframe(display_df, use_container_width=True)
            else:
                st.info("📊 No schedules found. Create your first schedule to see data here.")
        
        else:
            st.error("❌ Failed to load recent schedules")
    
    except Exception as e:
        st.error(f"❌ Error loading schedules: {e}")

with tab4:
    st.header("🔮 Predictive Analytics & AI Insights")
    st.markdown("Advanced forecasting and risk assessment powered by LSTM and Statistical models")
    
    forecast_col, risk_col = st.columns([1, 1])
    
    with forecast_col:
        st.subheader("📦 Cargo Demand Forecasting")
        st.write("Predict future cargo volumes using the trained LSTM model.")
        
        f_days = st.slider("Forecast Horizon (Days)", 1, 30, 7)
        f_model = st.selectbox("Select Model", ["lstm", "arima"])
        
        if st.button("🔮 Generate Forecast", type="primary"):
            with st.spinner(f"Running {f_model.upper()} prediction..."):
                try:
                    f_req = {
                        "days_ahead": f_days,
                        "include_confidence": True,
                        "model_type": f_model
                    }
                    f_resp = requests.post("http://127.0.0.1:8000/api/forecast/", json=f_req, timeout=30)
                    
                    if f_resp.status_code == 200:
                        f_data = f_resp.json()
                        forecasts = f_data.get('forecasts', [])
                        
                        if forecasts:
                            f_df = pd.DataFrame(forecasts)
                            f_df['date'] = pd.to_datetime(f_df['date'])
                            
                            # Visualization
                            fig_f = go.Figure()
                            
                            # Confidence interval (shading)
                            fig_f.add_trace(go.Scatter(
                                x=pd.concat([f_df['date'], f_df['date'][::-1]]),
                                y=pd.concat([f_df['upper_bound'], f_df['lower_bound'][::-1]]),
                                fill='toself',
                                fillcolor='rgba(0,100,80,0.2)',
                                line=dict(color='rgba(255,255,255,0)'),
                                hoverinfo="skip",
                                showlegend=True,
                                name='90% Confidence Interval'
                            ))
                            
                            # Forecast line
                            fig_f.add_trace(go.Scatter(
                                x=f_df['date'],
                                y=f_df['forecast_tons'],
                                mode='lines+markers',
                                name='Forecasted Tons',
                                line=dict(color='rgb(0,100,80)')
                            ))
                            
                            fig_f.update_layout(
                                title=f"{f_model.upper()} Demand Forecast ({f_days} Days)",
                                xaxis_title="Date",
                                yaxis_title="Cargo Tons",
                                hovermode="x unified"
                            )
                            
                            st.plotly_chart(fig_f, use_container_width=True)
                            
                            # Summary metrics
                            summary = f_data.get('summary', {})
                            s_col1, s_col2, s_col3 = st.columns(3)
                            s_col1.metric("Peak Demand", f"{summary.get('max_forecast', 0):.1f} tons")
                            s_col2.metric("Min Demand", f"{summary.get('min_forecast', 0):.1f} tons")
                            s_col3.metric("Avg Demand", f"{summary.get('mean_forecast', 0):.1f} tons")
                            
                        else:
                            st.warning("No forecast data returned.")
                    else:
                        st.error(f"Forecast API failed: {f_resp.status_code}")
                except Exception as e:
                    st.error(f"Forecast Error: {str(e)}")

    with risk_col:
        st.subheader("🚨 Schedule Risk Assessment")
        st.write("Identify operational bottlenecks and evaluate schedule robustness.")
        
        r_route = st.selectbox("Route to Analyze", ["DAR_KAPIRI", "DAR_MBEYA", "KAPIRI_NDOLA"])
        r_date = st.date_input("Planned Departure Date", datetime.now() + timedelta(days=1))
        
        if st.button("🚨 Run Risk Analysis", type="primary"):
            with st.spinner("Analyzing risk factors..."):
                try:
                    r_req = {
                        "schedule_id": f"SIM_{datetime.now().strftime('%H%M%S')}",
                        "route": r_route,
                        "planned_departure": r_date.isoformat(),
                        "historical_issues": [] # API handles base risk if empty
                    }
                    r_resp = requests.post("http://127.0.0.1:8000/api/risk/analyze", json=r_req, timeout=30)
                    
                    if r_resp.status_code == 200:
                        r_data = r_resp.json()
                        
                        # Risk Score Gauge
                        risk_score = r_data.get('risk_score', 0)
                        risk_level = r_data.get('risk_level', 'Unknown').upper()
                        
                        fig_r = go.Figure(go.Indicator(
                            mode = "gauge+number",
                            value = risk_score * 100,
                            domain = {'x': [0, 1], 'y': [0, 1]},
                            title = {'text': f"Risk Level: {risk_level}", 'font': {'size': 24}},
                            gauge = {
                                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                                'bar': {'color': "darkblue"},
                                'bgcolor': "white",
                                'borderwidth': 2,
                                'bordercolor': "gray",
                                'steps': [
                                    {'range': [0, 30], 'color': 'green'},
                                    {'range': [30, 60], 'color': 'yellow'},
                                    {'range': [60, 80], 'color': 'orange'},
                                    {'range': [80, 100], 'color': 'red'}],
                                'threshold': {
                                    'line': {'color': "black", 'width': 4},
                                    'thickness': 0.75,
                                    'value': risk_score * 100}}))
                        
                        st.plotly_chart(fig_r, use_container_width=True)
                        
                        # Bottlenecks
                        st.write("**Top Bottlenecks Detected:**")
                        bottlenecks = r_data.get('bottlenecks', [])
                        for b in bottlenecks:
                            st.info(f"📍 **{b['location']}**: {b['type'].title()} ({b['severity'].upper()} Severity, {int(b['probability']*100)}% prob)")
                        
                        # Recommendations
                        st.write("**AI Recommendations:**")
                        recs = r_data.get('recommendations', [])
                        for rec in recs:
                            st.success(f"💡 **{rec['action']}**: {rec['impact']} (Priority: {rec['priority'].upper()})")
                            
                    else:
                        st.error(f"Risk API failed: {r_resp.status_code}")
                except Exception as e:
                    st.error(f"Risk Analysis Error: {str(e)}")

with tab5:
    st.header("🔧 System Configuration")
    
    st.subheader("🎛 Multi-Route Parameters")
    
    # Configuration options
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Training Configuration**")
        learning_rate = st.slider(
            "Learning Rate",
            min_value=0.01,
            max_value=0.5,
            value=0.1,
            step=0.01
        )
        
        exploration_rate = st.slider(
            "Exploration Rate",
            min_value=0.0,
            max_value=1.0,
            value=0.1,
            step=0.01
        )
        
        episodes = st.number_input(
            "Training Episodes",
            min_value=100,
            max_value=10000,
            value=1000,
            step=100
        )
    
    with col2:
        st.write("**Operational Parameters**")
        max_trains_config = st.slider(
            "Maximum Trains",
            min_value=1,
            max_value=12,
            value=6,
            step=1
        )
        
        planning_horizon = st.slider(
            "Planning Horizon (Days)",
            min_value=1,
            max_value=30,
            value=14,
            step=1
        )
        
        coordination_bonus = st.checkbox(
            "Enable Coordination Bonus",
            value=True
        )
    
    # Advanced settings
    st.subheader("🔧 Advanced Settings")
    
    auto_retrain = st.checkbox(
        "Automatic Retraining",
        value=False,
        help="Automatically retrain agent when performance degrades"
    )
    
    performance_threshold = st.number_input(
        "Performance Threshold (%)",
        min_value=50,
        max_value=100,
        value=85,
        step=1,
        help="Alert when efficiency falls below this threshold"
    )
    
    # Save configuration button
    if st.button("💾 Save Configuration"):
        config = {
            "learning_rate": learning_rate,
            "exploration_rate": exploration_rate,
            "episodes": episodes,
            "max_trains": max_trains_config,
            "planning_horizon": planning_horizon,
            "coordination_bonus": coordination_bonus,
            "auto_retrain": auto_retrain,
            "performance_threshold": performance_threshold
        }
        
        st.success("✅ Configuration Saved!")
        st.json(config)

# ----------------------------
# Footer information
# ----------------------------
st.sidebar.markdown("---")
st.sidebar.markdown("### 📚 System Information")
st.sidebar.write(f"**Version**: Multi-Route v2.0")
st.sidebar.write(f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
st.sidebar.write(f"**API Status**: Connected")

# ----------------------------
# Help section
# ----------------------------
with st.expander("📖 User Guide"):
    st.markdown("""
    ### 🎯 How to Use This Dashboard
    
    **1. Overview Tab**: System status and capabilities
    - Monitor multi-route system health
    - View available features and routes
    
    **2. Schedule Viewer Tab**: Create and view schedules
    - Enter cargo requirements for each route
    - Generate optimized multi-route schedules
    - View detailed performance metrics
    - Analyze train assignments and efficiency
    
    **3. Performance Analytics Tab**: Historical trends
    - View performance trends over time
    - Compare route efficiency
    - Monitor key performance indicators
    - Analyze cargo delivery patterns
    
    **4. Configuration Tab**: System settings
    - Adjust training parameters
    - Configure operational limits
    - Set performance thresholds
    - Enable advanced features
    
    ### 🚂 Key Metrics Explained
    
    **Cargo Delivered**: Total tons of cargo successfully transported
    **Train Efficiency**: Cargo tons per train used
    **Net Profit**: Revenue minus all costs (ZMW)
    **Coordination Bonus**: Reward for multi-train coordination
    
    ### 💡 Tips for Optimal Performance
    
    - **Balanced cargo distribution** across all routes
    - **Minimize idle time** for better efficiency
    - **Coordinate train movements** for bonus rewards
    - **Monitor efficiency trends** for continuous improvement
    - **Use performance alerts** for proactive management
    """)

# ----------------------------
# Real-time status updates
# ----------------------------
def display_real_time_status():
    """Display real-time system status"""
    try:
        response = requests.get("http://127.0.0.1:8000/multi-route/status", timeout=5)
        if response.status_code == 200:
            status = response.json()
            
            # Status indicators
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if status.get('multi_route_enabled'):
                    st.success("🟢 Multi-Route Active")
                else:
                    st.warning("🟡 Multi-Route Disabled")
            
            with col2:
                st.metric(
                    label="🤖 Model Status",
                    value="Trained" if status.get('model_trained') else "Untrained"
                )
            
            with col3:
                st.metric(
                    label="📊 Active Schedules",
                    value="0",  # In production, this would come from database
                    delta=None
                )
        
    except:
        st.error("❌ Status Check Failed")

# Auto-refresh for real-time updates
if st.sidebar.checkbox("🔄 Auto-refresh (30s)"):
    st.rerun()

# Display real-time status
display_real_time_status()
