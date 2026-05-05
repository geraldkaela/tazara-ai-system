# TAZARA AI DASHBOARD - FEATURES & GRAPHS ANALYSIS REPORT

**Focus:** How Dashboard Components Work  
**Target File:** `dashboard/static/multi_route.html`  
**Generated:** April 8, 2026  

---

## GRAPHS & VISUALIZATIONS

### 1. CARGO DELIVERY TREND

#### **How It Works**
```
Database Query (/multi-route/performance/trends)
    |
    v
Last 30 Days of Schedule Data
    |
    v
Chart.js Line Chart Visualization
```

#### **Data Source**
- **API Endpoint:** `GET /multi-route/performance/trends`
- **Database Query:**
```sql
SELECT 
    DATE(timestamp) as date,
    SUM((performance_metrics->>'total_cargo_delivered')::float) as cargo_delivered,
    AVG(num_trains) as trains_used
FROM multi_route_schedules 
WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(timestamp)
ORDER BY date
```

#### **What It Shows**
- **X-Axis:** Last 30 days (date range)
- **Y-Axis:** Cargo delivered in tons
- **Data Points:** Daily cargo totals from your actual schedules
- **Trend Line:** Shows delivery patterns over time

#### **Integration Flow**
1. **Page Load:** JavaScript calls `loadPerformanceCharts()`
2. **API Call:** Fetches data from `/multi-route/performance/trends`
3. **Data Processing:** Formats dates and cargo values
4. **Chart Rendering:** Creates line chart with Chart.js
5. **Real-time Updates:** Refreshes when user creates new schedules

#### **Key Features**
- **Real Data:** Uses your 100+ actual schedules
- **Time Range:** Rolling 30-day window
- **Interactive:** Hover tooltips show exact values
- **Responsive:** Adapts to screen size

---

### 2. PROFIT TREND (ZMW)

#### **How It Works**
```
Database Query (/multi-route/performance/trends)
    |
    v
Financial Data from Schedules
    |
    v
Chart.js Line Chart (ZMW Currency)
```

#### **Data Source**
- **Same API:** `GET /multi-route/performance/trends`
- **Database Field:** `performance_metrics->>'total_profit'`
- **Query Logic:** Similar to cargo trend but with profit data

#### **What It Shows**
- **X-Axis:** Last 30 days
- **Y-Axis:** Profit in Zambian Kwacha (ZMW)
- **Data Points:** Daily profit totals
- **Trend Analysis:** Financial performance over time

#### **Integration Flow**
1. **Parallel Loading:** Loaded with cargo trend (same API call)
2. **Currency Formatting:** ZMW symbol and thousands separators
3. **Chart Styling:** Green color scheme for positive metrics
4. **Value Display:** Formatted as ZMW 2,500,000

#### **Key Features**
- **Financial Metrics:** Real profit from actual operations
- **Currency Formatting:** Proper ZMW display
- **Trend Analysis:** Identifies profitable periods
- **Performance Tracking:** Compares daily profitability

---

### 3. ROUTE EFFICIENCY COMPARISON

#### **How It Works**
```
Database Query (/multi-route/performance/routes)
    |
    v
Route-Specific Performance Data
    |
    v
Chart.js Bar Chart (Multiple Metrics)
```

#### **Data Source**
- **API Endpoint:** `GET /multi-route/performance/routes`
- **Database Query:**
```sql
SELECT 
    cargo_requirements,
    performance_metrics
FROM multi_route_schedules
WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'
```

#### **Data Processing**
```python
# For each route:
avg_efficiency = sum(efficiency_samples) / len(efficiency_samples)
avg_cargo = total_cargo / num_schedules
# Where efficiency = cargo_per_train (tons/train)
```

#### **What It Shows**
- **X-Axis:** Route names (DAR_KAPIRI, DAR_MBEYA, etc.)
- **Y-Axis:** Dual metrics
  - **Green Bars:** Average efficiency (tons per train)
  - **Blue Bars:** Average cargo (tons per schedule)
- **Data:** Real performance from your actual schedules

#### **Integration Flow**
1. **Route Analysis:** Calculates per-route performance metrics
2. **Data Aggregation:** Combines multiple schedules per route
3. **Chart Creation:** Dual-dataset bar chart
4. **Label Updates:** Shows "Avg Efficiency (tons/train)" not percentage

#### **Key Features**
- **Route Comparison:** Side-by-side performance analysis
- **Dual Metrics:** Efficiency and cargo volume
- **Real Data:** Based on your 100+ schedules
- **Performance Insights:** Identifies best/worst performing routes

---

### 4. ADVANCED DEMAND FORECASTING

#### **How It Works**
```
Database Data (Last 30 Days)
    |
    v
LSTM Neural Network Model
    |
    v
Future Predictions + Confidence Intervals
    |
    v
Chart.js Line Chart with Shaded Areas
```

#### **Data Source**
- **API Endpoint:** `POST /api/forecast/`
- **Database Query:**
```sql
SELECT 
    DATE(timestamp) as date,
    SUM((performance_metrics->>'total_cargo_delivered')::float) as cargo_tons
FROM multi_route_schedules
WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(timestamp)
ORDER BY date DESC
```

#### **ML Model Processing**
```python
# LSTM Model (models/lstm_model.keras - 131KB)
model = load_model('models/lstm_model.keras')
scaler = load_scaler()  # Feature preprocessing
forecast_values = make_lstm_forecast(model, scaler, last_value, days_ahead)
```

#### **What It Shows**
- **X-Axis:** Future dates (April 7-13, 2026 - next 7 days)
- **Y-Axis:** Predicted cargo demand in tons
- **Main Line:** LSTM forecast (12,000+ tons daily)
- **Shaded Area:** Confidence intervals (±15% bounds)
- **Model Selection:** LSTM or ARIMA (dropdown)

#### **Integration Flow**
1. **Data Collection:** Extracts last 30 days from database
2. **Model Loading:** Loads trained LSTM model and scaler
3. **Forecast Generation:** Predicts next N days
4. **Confidence Calculation:** Adds ±15% confidence bounds
5. **Chart Rendering:** Line chart with confidence shading
6. **Model Switching:** User can select LSTM vs ARIMA

#### **Key Features**
- **AI-Powered:** Neural network predictions
- **Current Dates:** Fixed to show April 2026 (not old January dates)
- **Confidence Intervals:** Shows prediction uncertainty
- **Model Options:** LSTM (neural) vs ARIMA (statistical)
- **Real Data Base:** Uses your actual operational data

---

## USER INTERACTION FEATURES

### 5. CREATE CUSTOMER ORDER

#### **How It Works**
```
User Form Input
    |
    v
JavaScript Validation
    |
    v
API Call (POST /multi-route/orders)
    |
    v
Database Storage
    |
    v
Order List Update
```

#### **Form Fields**
- **Order ID:** Unique identifier
- **Customer Name:** Client identification
- **Cargo Type:** Type of goods
- **Cargo Weight:** Weight in tons
- **Route:** Transportation route
- **Urgency Level:** Emergency/Urgent/Normal
- **Customer Tier:** Platinum/Gold/Silver
- **Delivery Deadline:** Date requirement

#### **Integration Flow**
1. **Form Submission:** JavaScript collects form data
2. **Validation:** Checks required fields and data types
3. **API Call:** Sends POST to `/multi-route/orders`
4. **Database Storage:** Order saved to database
5. **UI Update:** Order appears in Customer Orders list
6. **Priority Detection:** Automatically tags for priority processing

#### **Key Features**
- **Priority Detection:** Urgency + Tier = Priority Score
- **Real-time Updates:** Immediate list refresh
- **Validation:** Prevents invalid submissions
- **Priority Tags:** Visual indicators for high-priority orders

---

### 6. CUSTOMER ORDERS (List Display)

#### **How It Works**
```
Database Query (/multi-route/orders)
    |
    v
Order Data Retrieval
    |
    v
Dynamic Table Generation
    |
    v
Priority Badge Display
```

#### **Data Source**
- **API Endpoint:** `GET /multi-route/orders`
- **Database Table:** Orders stored with priority metadata
- **Display Logic:** Shows all orders with priority indicators

#### **What It Shows**
- **Order ID:** Unique identifier
- **Customer Name:** Client information
- **Cargo Details:** Type and weight
- **Route Information:** Transportation route
- **Priority Badges:** 
  - Red: Emergency orders
  - Orange: Urgent orders
  - Blue: Standard orders
- **Actions:** Delete and schedule creation options

#### **Integration Flow**
1. **Page Load:** Fetches all orders from database
2. **Table Generation:** Creates dynamic HTML table
3. **Priority Styling:** Applies color-coded badges
4. **Action Buttons:** Delete and schedule creation
5. **Real-time Updates:** Refreshes when orders added/removed

#### **Key Features**
- **Priority Visualization:** Color-coded urgency levels
- **Order Management:** Add, delete, and schedule orders
- **Bulk Operations:** Select multiple orders for scheduling
- **Real-time Sync:** Immediate updates across all views

---

### 7. CREATE SCHEDULE

#### **How It Works**
```
User Parameters + Selected Orders
    |
    v
Priority System Integration
    |
    v
Reinforcement Learning Optimization
    |
    v
Schedule Generation
    |
    v
Database Storage + Results Display
```

#### **Input Parameters**
- **Number of Trains:** 1-12 trains available
- **Maximum Days:** 1-14 day scheduling horizon
- **Cargo Requirements:** Route-specific cargo amounts
- **Order Selection:** Choose orders to include
- **Priority Data:** Auto-detected from selected orders

#### **Integration Flow**
1. **Parameter Collection:** Form data and selected orders
2. **Priority Detection:** Analyzes order metadata
3. **API Call:** POST to `/multi-route/schedule`
4. **Priority Enhancement:** Adjusts cargo based on priority
5. **RL Optimization:** Multi-route train assignment
6. **Schedule Generation:** Daily train assignments
7. **Database Storage:** Complete schedule saved
8. **Results Display:** Comprehensive schedule details

#### **Priority System Integration**
```python
# Auto-detection from order IDs
if 'Medical' in order_id or 'Emergency' in order_id:
    urgency = 'emergency'
    tier = 'platinum'
    priority_score = 92.5/100
    cargo_boost = 1.10  # 10% efficiency boost
```

#### **Results Display**
- **Schedule Overview:** Train assignments and routes
- **Performance Metrics:** Total profit, cargo delivered, efficiency
- **Priority Status:** Shows if priority system was active
- **Cost Breakdown:** Detailed ZMW cost analysis
- **Gantt Chart:** Visual schedule timeline
- **Risk Analysis:** Operational risk assessment

#### **Key Features**
- **Priority Enhancement:** Automatic priority detection and optimization
- **RL Optimization:** AI-powered multi-train coordination
- **Comprehensive Results:** Detailed performance analysis
- **Real-time Processing:** Sub-second schedule generation
- **Database Persistence:** Schedules saved for analytics

---

## INTEGRATION SUMMARY

### 8. HOW ALL FEATURES WORK TOGETHER

#### **Data Flow Integration**
```
Customer Orders
    |
    v
Create Schedule (with Priority Enhancement)
    |
    v
Database Storage
    |
    v
Analytics & Graphs (Real-time Updates)
```

#### **Priority System Integration**
- **Order Creation:** Priority tags applied automatically
- **Schedule Creation:** Priority factors enhance optimization
- **Results Display:** Priority status shown in results
- **Analytics:** Priority vs non-priority performance comparison

#### **Real-time Data Integration**
- **All Graphs:** Use database data from actual schedules
- **Immediate Updates:** New schedules appear in graphs instantly
- **Consistent Data:** All features use same data source
- **Performance Tracking:** Live metrics from operations

#### **User Experience Integration**
- **Seamless Workflow:** Order creation to scheduling to analytics
- **Priority Transparency:** Users see priority impact without complexity
- **Comprehensive Feedback:** Detailed results and performance metrics
- **Interactive Visualization:** Charts update with real data

### 9. TECHNICAL ARCHITECTURE

#### **Frontend Integration**
- **JavaScript:** Handles all user interactions and API calls
- **Chart.js:** Renders all visualizations
- **Real-time Updates:** 30-second polling for live data
- **Responsive Design:** Works on desktop and mobile

#### **Backend Integration**
- **FastAPI:** Handles all API endpoints
- **PostgreSQL:** Centralized data storage
- **ML Models:** Cached for performance
- **Priority System:** Integrated into scheduling logic

#### **Data Integration**
- **Single Source of Truth:** PostgreSQL database
- **Real Operational Data:** 100+ actual schedules
- **Consistent Metrics:** Same calculations across all features
- **Audit Trail:** Complete history of all operations

---

## CONCLUSION

### 10. SYSTEM COHESION

The TAZARA AI dashboard demonstrates **perfect integration** where:

1. **Customer Orders** feed the scheduling system with priority data
2. **Create Schedule** uses AI optimization with priority enhancement
3. **All Graphs** display real operational data from the same database
4. **Priority System** works transparently across all features
5. **Real-time Updates** keep all visualizations current

### 11. Key Integration Achievements

- **End-to-End Workflow:** From order creation to performance analytics
- **Priority Enhancement:** Automatic detection without user complexity
- **Real Data Visualization:** All charts use actual operational data
- **Seamless User Experience:** Enhanced capabilities without disruption
- **Comprehensive Analytics:** Multi-dimensional performance insights

The dashboard represents a **unified operational platform** where every component works together harmoniously to provide AI-enhanced railway scheduling and management capabilities.
