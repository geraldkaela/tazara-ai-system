# TAZARA AI SYSTEM - SCHEDULE CREATION WORKFLOW ANALYSIS

**Analysis Date:** April 19, 2026  
**Focus:** Complete schedule creation process from input to database  

---

## SCHEDULE CREATION WORKFLOW

### 1. USER INPUT STAGE

#### **1.1 Request Reception**
```python
# API Endpoint: POST /multi-route/schedule
class MultiRouteRequest(BaseModel):
    num_trains: int = 6
    max_days: int = 14
    cargo_requirements: Dict[str, float]
    use_deep_rl: bool = True
    metadata: Dict = {}  # Priority system data
```

#### **1.2 Input Processing**
- **Train Count:** 1-12 trains supported
- **Duration:** 1-14 days scheduling horizon
- **Cargo Requirements:** Route-specific cargo amounts
- **Metadata:** Contains priority system information
- **RL Mode:** Deep RL vs traditional Q-learning

---

### 2. PRIORITY SYSTEM INTEGRATION

#### **2.1 Priority Detection**
```python
# Automatic priority detection from metadata
if request.metadata and request.metadata.get('based_on_orders'):
    priority_integrator = PriorityOrderIntegrator()
    priority_scorer = PriorityScorer()
    
    # Analyzes order IDs for priority factors
    # Calculates priority scores (0-100)
    # Adjusts cargo requirements based on priority
```

#### **2.2 Priority Enhancement**
- **Emergency Orders:** 92.5/100 priority score
- **Urgent Orders:** 72.5/100 priority score  
- **Standard Orders:** 42.5/100 priority score
- **Cargo Boost:** 10% efficiency boost for high priority

#### **2.3 Enhanced Cargo Requirements**
```python
# Original cargo requirements
cargo_requirements = {
    "DAR_KAPIRI": 1500,
    "DAR_MBEYA": 800,
    "KAPIRI_NDOLA": 600
}

# Priority-enhanced requirements
if priority_score > 80:
    for route in cargo_requirements:
        cargo_requirements[route] *= 1.10  # 10% boost
```

---

### 3. ENVIRONMENT INITIALIZATION

#### **3.1 Multi-Route Environment Setup**
```python
# Create TAZARA railway environment
env = MultiRouteTazaraEnv(
    num_trains=request.num_trains,
    max_days=request.max_days,
    cargo_requirements=enhanced_cargo_requirements
)

# Environment components:
# - 6 TAZARA routes (DAR_KAPIRI, DAR_MBEYA, etc.)
# - Train fleet management
# - Cargo tracking per route
# - State space representation
# - Action space (6 routes + idle)
```

#### **3.2 State Space Definition**
```python
# 30-dimensional state vector
state_components = [
    # Cargo per route (6 dimensions)
    # Train positions (6 dimensions) 
    # Train states (6 dimensions)
    # Day progress (1 dimension)
    # Efficiency metrics (6 dimensions)
    # Cost factors (5 dimensions)
]
```

#### **3.3 Action Space Definition**
```python
# 13 possible actions per train
actions = [
    0,  # IDLE
    1,  # DAR_KAPIRI
    2,  # DAR_MBEYA
    3,  # KAPIRI_NDOLA
    4,  # DAR_KIDATU
    5,  # KIDATU_MAKAMBAKO
    6,  # MAKAMBAKO_MBEYA
    7,  # MBEYA_KASAMA
    8,  # KASAMA_MPIKA
    9,  # MPIKA_SERENJE
    10, # SERENJE_KAPIRI
    11, # KIDATU_TRANS_SHIPMENT
    12, # KAPIRI_DISTRIBUTION
]
```

---

### 4. AI AGENT LOADING

#### **4.1 Smart Agent Selection**
```python
def load_smart_agent(num_trains, cargo_requirements):
    total_cargo = sum(cargo_requirements.values())
    
    # Select appropriate agent based on scenario
    if total_cargo > 3000:
        model_path = "multi_route_agent_large_cargo.pkl"
    elif num_trains > 8:
        model_path = "multi_route_agent_12_trains.pkl"
    else:
        model_path = "multi_route_agent_tazara_network.pkl"
    
    # Load trained Q-learning agent
    agent = MultiRouteAgent(
        state_bins=(10,) * 30,
        action_size=13
    )
    agent.load(model_path)
    agent.exploration_rate = 0.0  # Production mode
    return agent
```

#### **4.2 Agent Capabilities**
- **Algorithm:** Q-learning with experience replay
- **Training:** Pre-trained on 15 different scenarios
- **State Representation:** 30-dimensional feature vector
- **Decision Making:** Epsilon-greedy with epsilon=0 (no exploration)

---

### 5. SCHEDULING SIMULATION

#### **5.1 Daily Optimization Loop**
```python
for day in range(request.max_days):
    # Get current state
    state = env.get_state()
    
    # AI agent selects actions for all trains
    actions = agent.select_action(state)
    
    # Force work actions for first 3 days
    if day < 3:
        actions = force_work_actions(env, request.num_trains)
    
    # Execute actions in environment
    next_state, reward, done, truncated, info = env.step(actions)
    
    # Record daily assignment
    day_assignment = {
        "day": day + 1,
        "actions": list(actions),
        "reward": reward,
        "cargo_delivered": sum(env.cargo_delivered.values()),
        "state": next_state.tolist()
    }
    day_assignments_list.append(day_assignment)
```

#### **5.2 Forced Work Actions (Days 1-3)**
```python
# Prevent excessive idling in early days
def force_work_actions(env, num_trains):
    cargo_routes = [(i, route) for i, route in enumerate(env.route_names) 
                   if env.current_cargo.get(route, 0) > 0]
    
    if cargo_routes:
        # Distribute trains across cargo routes
        trains_per_route = num_trains // len(cargo_routes)
        remaining = num_trains % len(cargo_routes)
        
        actions = []
        for route_idx, route_name in cargo_routes:
            trains_for_this_route = trains_per_route + (1 if cargo_routes.index((route_idx, route_name)) < remaining else 0)
            actions.extend([route_idx + 1] * trains_for_this_route)
        
        # Fill remaining with idle
        while len(actions) < num_trains:
            actions.append(0)
        
        return actions[:num_trains]
```

#### **5.3 Environment Step Execution**
```python
def step(self, actions):
    # Process train actions
    for train_idx, action in enumerate(actions):
        if action == 0:  # IDLE
            train_states[train_idx] = "IDLE"
        else:
            # Assign train to route
            route_name = route_names[action - 1]
            train_states[train_idx] = "EN_ROUTE"
            
            # Update cargo delivered
            cargo_delivered = min(
                train_capacity[train_idx],
                current_cargo[route_name]
            )
            total_cargo_delivered[route_name] += cargo_delivered
            current_cargo[route_name] -= cargo_delivered
    
    # Calculate reward using advanced cost model
    reward = calculate_total_reward(
        cargo_delivered, train_assignments, 
        delays, fuel_consumption, maintenance_costs
    )
    
    return next_state, reward, done, truncated, info
```

---

### 6. SCHEDULE GENERATION

#### **6.1 Daily Assignment Creation**
```python
# Generate detailed daily assignments
for day_num, day_data in enumerate(day_assignments_list):
    daily_assignments.append({
        "day": day_num + 1,
        "train_assignments": [
            {
                "train_id": f"T-{train_idx + 1}",
                "route": "IDLE" if action == 0 else route_names[action - 1],
                "rationale": generate_rationale(action, route_names),
                "driver_id": f"D{((day_num * request.num_trains + train_idx) % 10) + 1:02d}",
                "skill_level": 4,
                "fuel_consumed": calculate_fuel_consumption(action, train_specs),
                "distance_travelled": calculate_distance(action, route_distances),
                "cargo_delivered": calculate_cargo_delivered(action, train_specs)
            }
            for train_idx, action in enumerate(day_data["actions"])
        ]
    })
```

#### **6.2 Rationale Generation**
```python
def generate_rationale(action, route_names):
    if action == 0:
        return "Strategically idling to prevent station congestion and wait for higher-priority cargo accumulation at Port."
    else:
        return f"Selected {route_names[action - 1]} route based on optimized turnaround time and current locomotive fuel economy."
```

---

### 7. PERFORMANCE CALCULATION

#### **7.1 Final Metrics Calculation**
```python
# Calculate comprehensive performance metrics
total_cargo_delivered = sum(env.cargo_delivered.values())
total_profit = sum(day_assignment["reward"] for day_assignment in day_assignments_list)

# Generate cost breakdown
cost_breakdown = get_improved_cost_breakdown(
    total_cargo_delivered,
    request.num_trains,
    request.max_days,
    idle_days=0
)

# Calculate efficiency metrics
efficiency_analysis = {
    'cargo_per_train': total_cargo_delivered / request.num_trains,
    'profit_per_train': total_profit / request.num_trains,
    'delivery_rate': calculate_delivery_rate(total_cargo_delivered, enhanced_cargo_requirements),
    'efficiency': calculate_realistic_efficiency(total_cargo_delivered, request.num_trains, request.max_days)
}
```

#### **7.2 Cost Breakdown Components**
```python
cost_breakdown = {
    'total_revenue': total_cargo_delivered * revenue_per_ton,
    'fuel_costs': total_fuel_consumed * fuel_price_per_liter,
    'crew_costs': total_crew_days * daily_crew_cost,
    'maintenance_costs': total_distance * maintenance_cost_per_km,
    'fixed_costs': request.num_trains * request.max_days * daily_fixed_cost,
    'total_profit': total_profit,
    'profit_margin': (total_profit / total_revenue) * 100
}
```

---

### 8. DATABASE STORAGE

#### **8.1 Schedule Persistence**
```python
# Save complete schedule to database
def save_schedule_to_database(schedule_data):
    conn = psycopg2.connect(database_connection_string)
    cursor = conn.cursor()
    
    insert_query = """
    INSERT INTO multi_route_schedules (
        schedule_id, num_trains, total_days, cargo_requirements,
        daily_actions, train_assignments, performance_metrics,
        cost_breakdown_zmw, efficiency_analysis
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    cursor.execute(insert_query, (
        schedule_data['schedule_id'],
        schedule_data['num_trains'],
        schedule_data['max_days'],
        json.dumps(schedule_data['cargo_requirements']),
        json.dumps(schedule_data['daily_actions']),
        json.dumps(schedule_data['daily_assignments']),
        json.dumps(schedule_data['performance_metrics']),
        json.dumps(schedule_data['cost_breakdown']),
        json.dumps(schedule_data['efficiency_analysis'])
    ))
    
    conn.commit()
    cursor.close()
    conn.close()
```

#### **8.2 Stored Data Structure**
```json
{
    "schedule_id": "multi_route_20260419_143022",
    "num_trains": 6,
    "max_days": 14,
    "cargo_requirements": {
        "DAR_KAPIRI": 1500,
        "DAR_MBEYA": 800,
        "KAPIRI_NDOLA": 600
    },
    "performance_metrics": {
        "total_cargo_delivered": 2900,
        "total_profit": 2500000,
        "efficiency": 45.8,
        "delivery_rate": 85.2
    },
    "cost_breakdown_zmw": {
        "total_revenue": 14500000,
        "fuel_costs": 2800000,
        "crew_costs": 1200000,
        "maintenance_costs": 800000,
        "total_profit": 9700000
    },
    "efficiency_analysis": {
        "cargo_per_train": 483.3,
        "profit_per_train": 1616666.7
    }
}
```

---

### 9. RESPONSE GENERATION

#### **9.1 API Response Structure**
```python
return ScheduleResponse(
    schedule_id=schedule_id,
    total_profit=total_profit,
    cargo_delivered=total_cargo_delivered,
    daily_assignments=daily_assignments,
    cost_breakdown=cost_breakdown,
    efficiency_analysis=schedule_data['efficiency_analysis']
)
```

#### **9.2 Priority System Feedback**
```python
# Include priority system status in response
if priority_system_active:
    response["priority_system"] = {
        "active": True,
        "orders_processed": len(priority_orders),
        "priority_score": avg_priority_score,
        "efficiency_boost": "10% for high-priority orders"
    }
```

---

## COMPLETE WORKFLOW SUMMARY

### **10. END-TO-END PROCESS**

```
USER INPUT
    |
    v
PRIORITY DETECTION & ENHANCEMENT
    |
    v
ENVIRONMENT INITIALIZATION
    |
    v
AI AGENT LOADING
    |
    v
DAILY OPTIMIZATION LOOP (14 days)
    |
    v
SCHEDULE GENERATION
    |
    v
PERFORMANCE CALCULATION
    |
    v
DATABASE STORAGE
    |
    v
API RESPONSE
```

### **11. KEY TECHNOLOGIES USED**

#### **Artificial Intelligence**
- **Reinforcement Learning:** Q-learning with experience replay
- **State Space:** 30-dimensional feature representation
- **Action Space:** 13 possible actions per train
- **Reward System:** Multi-objective optimization

#### **Optimization Algorithms**
- **Priority Enhancement:** Automatic detection and boosting
- **Cost Modeling:** Advanced cost-benefit analysis
- **Route Optimization:** Multi-train coordination
- **Resource Allocation:** Efficient train assignment

#### **Data Processing**
- **Real-time Simulation:** Day-by-day optimization
- **Performance Tracking:** Comprehensive metrics calculation
- **Database Integration:** PostgreSQL with JSON storage
- **API Integration:** FastAPI with structured responses

---

## CONCLUSION

### **12. SCHEDULE CREATION EXCELLENCE**

The TAZARA AI system demonstrates **sophisticated schedule creation** through:

1. **Intelligent Input Processing:** Priority system integration
2. **Advanced AI Optimization:** Reinforcement learning agents
3. **Real-time Simulation:** Day-by-day decision making
4. **Comprehensive Analysis:** Multi-objective optimization
5. **Persistent Storage:** Complete audit trail in database
6. **Detailed Reporting:** Performance metrics and cost breakdowns

### **13. OPERATIONAL BENEFITS**

- **Automated Optimization:** AI-driven vs manual scheduling
- **Priority Handling:** Enhanced service for high-value orders
- **Resource Efficiency:** Optimal train and route utilization
- **Cost Optimization:** Multi-factor cost minimization
- **Performance Tracking:** Real-time metrics and analytics
- **Scalability:** 1-12 trains across 6 routes

**The schedule creation workflow represents a complete, production-ready AI-powered railway scheduling system!** 🚂🤖✨
