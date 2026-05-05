# PRIORITY-BASED AUTO SCHEDULING DESIGN

**Purpose:** Design for automatic scheduling of high-priority orders  
**Date:** April 19, 2026  

---

## CURRENT SYSTEM ANALYSIS

### **Current Priority System**
```python
# Current implementation in /multi-route/schedule
if request.metadata and request.metadata.get('based_on_orders'):
    # Manual trigger only
    priority_integrator = PriorityOrderIntegrator()
    priority_scorer = PriorityScorer()
    # Enhances existing manual cargo requirements
```

### **Current Limitations**
- **Manual Trigger:** Only works when user manually creates schedule
- **No Auto-Detection:** No system to automatically detect and schedule high-priority orders
- **No Priority Queue:** Orders wait for manual scheduling regardless of priority
- **No Real-time Processing:** Priority analysis happens on-demand, not continuously

---

## PROPOSED PRIORITY AUTO-SCHEDULING SYSTEM

### **1. ARCHITECTURE OVERVIEW**

```
ORDER DATABASE
    |
    v
PRIORITY MONITOR (Continuous)
    |
    v
PRIORITY QUEUE (High-Priority Orders)
    |
    v
AUTO-SCHEDULER (AI Agent)
    |
    v
SCHEDULE EXECUTION
    |
    v
NOTIFICATION SYSTEM
```

### **2. CORE COMPONENTS**

#### **2.1 Priority Monitor Service**
```python
class PriorityMonitor:
    """Continuously monitors orders for high-priority items"""
    
    def __init__(self):
        self.check_interval = 300  # 5 minutes
        self.priority_threshold = 75.0  # Score threshold
    
    async def monitor_orders(self):
        """Background task to monitor orders"""
        while True:
            high_priority_orders = await self.check_high_priority_orders()
            if high_priority_orders:
                await self.add_to_priority_queue(high_priority_orders)
            await asyncio.sleep(self.check_interval)
    
    async def check_high_priority_orders(self):
        """Check for unscheduled high-priority orders"""
        query = """
        SELECT * FROM customer_orders 
        WHERE status = 'pending' 
        AND priority_score >= %s
        ORDER BY priority_score DESC, created_at ASC
        """
        # Returns orders above threshold
```

#### **2.2 Priority Queue Manager**
```python
class PriorityQueue:
    """Manages high-priority order queue"""
    
    def __init__(self):
        self.queue = []
        self.max_queue_size = 50
    
    async def add_orders(self, orders):
        """Add high-priority orders to queue"""
        for order in orders:
            if len(self.queue) < self.max_queue_size:
                self.queue.append({
                    'order_id': order['id'],
                    'priority_score': order['priority_score'],
                    'cargo_requirements': self.parse_cargo_from_order(order),
                    'deadline': order['delivery_deadline'],
                    'created_at': order['created_at']
                })
                # Sort by priority score and deadline
                self.queue.sort(key=lambda x: (-x['priority_score'], x['deadline']))
    
    async def get_next_batch(self, max_trains=12):
        """Get next batch of orders for scheduling"""
        if not self.queue:
            return None
        
        # Select orders that can be handled with available trains
        batch = []
        total_cargo = 0
        
        for order in self.queue[:]:
            if len(batch) >= max_trains:
                break
            
            # Check if we can handle this order
            order_cargo = sum(order['cargo_requirements'].values())
            if total_cargo + order_cargo <= 12000:  # Max capacity per batch
                batch.append(order)
                total_cargo += order_cargo
                self.queue.remove(order)
        
        return batch if batch else None
```

#### **2.3 Auto-Scheduler Service**
```python
class AutoScheduler:
    """Automatically schedules high-priority orders"""
    
    def __init__(self):
        self.priority_queue = PriorityQueue()
        self.available_trains = 12
        self.scheduling_interval = 600  # 10 minutes
    
    async def auto_schedule_loop(self):
        """Main auto-scheduling loop"""
        while True:
            try:
                # Get next batch of high-priority orders
                order_batch = await self.priority_queue.get_next_batch(self.available_trains)
                
                if order_batch:
                    # Create schedule for this batch
                    schedule = await self.create_priority_schedule(order_batch)
                    
                    # Execute schedule
                    await self.execute_schedule(schedule)
                    
                    # Notify stakeholders
                    await self.send_priority_notifications(schedule)
                
                await asyncio.sleep(self.scheduling_interval)
                
            except Exception as e:
                logger.error(f"Auto-scheduling error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def create_priority_schedule(self, order_batch):
        """Create schedule for priority order batch"""
        # Aggregate cargo requirements from batch
        aggregated_cargo = self.aggregate_cargo_requirements(order_batch)
        
        # Create schedule request with priority metadata
        schedule_request = MultiRouteRequest(
            num_trains=min(self.available_trains, len(order_batch)),
            max_days=self.calculate_deadline_days(order_batch),
            cargo_requirements=aggregated_cargo,
            use_deep_rl=True,
            metadata={
                'auto_scheduled': True,
                'priority_batch': [order['order_id'] for order in order_batch],
                'priority_scores': [order['priority_score'] for order in order_batch],
                'based_on_orders': True
            }
        )
        
        # Use existing scheduling endpoint
        return await create_multi_route_schedule(schedule_request)
```

### **3. IMPLEMENTATION STRATEGY**

#### **3.1 Phase 1: Priority Queue System**
```python
# New API endpoints
@router.post("/priority/queue/add")
async def add_to_priority_queue(order_ids: List[str]):
    """Manually add orders to priority queue"""
    
@router.get("/priority/queue/status")
async def get_priority_queue_status():
    """Get current priority queue status"""
    
@router.delete("/priority/queue/clear")
async def clear_priority_queue():
    """Clear priority queue (admin only)"""
```

#### **3.2 Phase 2: Auto-Scheduler Integration**
```python
# Background service integration
class BackgroundScheduler:
    def __init__(self):
        self.priority_monitor = PriorityMonitor()
        self.auto_scheduler = AutoScheduler()
    
    async def start(self):
        """Start all background services"""
        await asyncio.gather(
            self.priority_monitor.monitor_orders(),
            self.auto_scheduler.auto_schedule_loop()
        )
```

#### **3.3 Phase 3: Real-time Monitoring**
```python
# WebSocket integration for real-time updates
@router.websocket("/ws/priority-updates")
async def priority_updates_websocket(websocket: WebSocket):
    """Real-time priority scheduling updates"""
```

---

## 4. PRIORITY SCORING ENHANCEMENT

### **4.1 Enhanced Priority Factors**
```python
class EnhancedPriorityScorer:
    """Advanced priority scoring for auto-scheduling"""
    
    def calculate_priority_score(self, order):
        """Calculate comprehensive priority score"""
        score = 0
        
        # Urgency factors (0-40 points)
        if 'emergency' in order['order_id'].lower():
            score += 40
        elif 'urgent' in order['order_id'].lower():
            score += 30
        elif 'priority' in order['order_id'].lower():
            score += 20
        
        # Customer tier factors (0-30 points)
        tier_scores = {'platinum': 30, 'gold': 20, 'silver': 10, 'bronze': 5}
        score += tier_scores.get(order['customer_tier'].lower(), 0)
        
        # Deadline urgency (0-20 points)
        days_until_deadline = (order['delivery_deadline'] - datetime.now()).days
        if days_until_deadline <= 1:
            score += 20
        elif days_until_deadline <= 3:
            score += 15
        elif days_until_deadline <= 7:
            score += 10
        elif days_until_deadline <= 14:
            score += 5
        
        # Cargo value (0-10 points)
        if order['cargo_value'] > 1000000:  # High value cargo
            score += 10
        elif order['cargo_value'] > 500000:
            score += 5
        
        return min(score, 100)  # Cap at 100
```

### **4.2 Dynamic Priority Adjustment**
```python
def adjust_priority_for_time(self, order):
    """Adjust priority based on waiting time"""
    hours_waiting = (datetime.now() - order['created_at']).total_seconds() / 3600
    
    # Increase priority for orders waiting too long
    if hours_waiting > 24:
        return min(order['priority_score'] + 10, 100)
    elif hours_waiting > 12:
        return min(order['priority_score'] + 5, 100)
    
    return order['priority_score']
```

---

## 5. SCHEDULING OPTIMIZATION

### **5.1 Priority-Aware AI Agent**
```python
class PriorityAwareAgent(MultiRouteAgent):
    """AI agent optimized for priority scheduling"""
    
    def select_priority_action(self, state, priority_orders):
        """Select actions considering priority orders"""
        # Weight actions towards priority routes
        priority_routes = self.extract_priority_routes(priority_orders)
        
        # Modify action selection to prioritize these routes
        base_actions = self.select_action(state)
        
        # Adjust actions for priority consideration
        adjusted_actions = []
        for action in base_actions:
            if action in priority_routes:
                # Boost priority route selection
                adjusted_actions.append(action)
            elif action == 0 and len(priority_routes) > 0:
                # Reduce idling when priority orders exist
                adjusted_actions.append(random.choice(priority_routes))
            else:
                adjusted_actions.append(action)
        
        return adjusted_actions
```

### **5.2 Deadline-Constrained Scheduling**
```python
def calculate_optimal_schedule_days(self, order_batch):
    """Calculate optimal days based on deadlines"""
    min_deadline = min(order['deadline'] for order in order_batch)
    max_deadline = max(order['deadline'] for order in order_batch)
    
    # Schedule to meet earliest deadline with buffer
    days_needed = max(3, (min_deadline - datetime.now()).days - 1)
    
    return min(days_needed, 14)  # Cap at 14 days
```

---

## 6. NOTIFICATION SYSTEM

### **6.1 Priority Notifications**
```python
class PriorityNotificationService:
    """Handles notifications for priority scheduling"""
    
    async def notify_priority_scheduled(self, schedule):
        """Notify when priority orders are scheduled"""
        notification = {
            'type': 'priority_scheduled',
            'schedule_id': schedule['schedule_id'],
            'orders': schedule['metadata']['priority_batch'],
            'priority_scores': schedule['metadata']['priority_scores'],
            'scheduled_at': datetime.now().isoformat(),
            'estimated_completion': self.calculate_completion_time(schedule)
        }
        
        # Send to dashboard, email, SMS
        await self.send_notification(notification)
    
    async def notify_missed_deadline(self, order):
        """Notify when priority order might miss deadline"""
        notification = {
            'type': 'deadline_risk',
            'order_id': order['order_id'],
            'priority_score': order['priority_score'],
            'deadline': order['deadline'],
            'risk_level': 'high'
        }
        
        await self.send_urgent_notification(notification)
```

---

## 7. IMPLEMENTATION BENEFITS

### **7.1 Operational Benefits**
- **Immediate Response:** High-priority orders scheduled automatically
- **Deadline Compliance:** Better meeting of delivery deadlines
- **Resource Optimization:** Efficient use of available trains
- **Customer Satisfaction:** Improved service for priority customers

### **7.2 System Benefits**
- **Reduced Manual Work:** No need for manual priority scheduling
- **Real-time Processing:** Continuous monitoring and scheduling
- **Scalability:** Handles increasing order volumes
- **Intelligence:** AI-powered optimization for priority orders

---

## 8. IMPLEMENTATION PLAN

### **Phase 1: Foundation (Week 1)**
1. Create priority queue database table
2. Implement priority monitor service
3. Add priority scoring enhancements
4. Create basic auto-scheduler

### **Phase 2: Integration (Week 2)**
1. Integrate with existing scheduling API
2. Implement background services
3. Add notification system
4. Create monitoring dashboard

### **Phase 3: Optimization (Week 3)**
1. Implement priority-aware AI agents
2. Add deadline-constrained scheduling
3. Optimize queue management
4. Add real-time WebSocket updates

### **Phase 4: Testing & Deployment (Week 4)**
1. Comprehensive testing
2. Performance optimization
3. User training
4. Production deployment

---

## 9. TECHNICAL CONSIDERATIONS

### **9.1 Performance**
- **Background Services:** Non-blocking async operations
- **Database Optimization:** Indexed queries for priority orders
- **Memory Management:** Efficient queue operations
- **Scalability:** Horizontal scaling support

### **9.2 Reliability**
- **Error Handling:** Robust error recovery
- **Monitoring:** Health checks and logging
- **Backup Systems:** Manual override capabilities
- **Data Integrity:** Transaction management

### **9.3 Security**
- **Access Control:** Role-based permissions
- **Audit Trail:** Complete scheduling history
- **Data Protection:** Secure order information
- **API Security:** Authentication and authorization

---

## CONCLUSION

This priority-based auto-scheduling system will transform your TAZARA AI system from a manual scheduling tool to an intelligent, automated system that:

1. **Automatically detects** high-priority orders
2. **Immediately schedules** them using optimized AI
3. **Continuously monitors** for new priority orders
4. **Notifies stakeholders** of scheduling actions
5. **Optimizes resources** for priority customer service

The system maintains your existing AI scheduling capabilities while adding intelligent automation for priority handling.
