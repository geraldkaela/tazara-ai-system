"""
Dynamic Real-Time Optimization Engine for TAZARA Multi-Route System
Phase 1: Continuous schedule optimization with labor cost minimization
"""

import asyncio
import time
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Callable
import numpy as np
import logging
from dataclasses import dataclass
from enum import Enum

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reinforcement_rl.enhanced_cost_model import LaborCostCalculator, IdleTimeOptimizer
from reinforcement_rl.multi_route_env import MultiRouteTazaraEnv
from reinforcement_rl.multi_route_agent import MultiRouteAgent
from disruption_handler.cascade_analyzer import CascadeAnalyzer
from disruption_handler.conflict_resolver import ConflictResolver

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizationTrigger(Enum):
    """Types of optimization triggers"""
    SCHEDULE_CREATED = "schedule_created"
    LABOR_COST_CHANGE = "labor_cost_change"
    DISRUPTION_DETECTED = "disruption_detected"
    PERIODIC_REOPTIMIZATION = "periodic_reoptimization"
    EFFICIENCY_THRESHOLD = "efficiency_threshold"

@dataclass
class OptimizationEvent:
    """Represents an optimization event"""
    event_type: OptimizationTrigger
    timestamp: datetime
    schedule_id: str
    trigger_data: Dict
    priority: int = 1  # 1=low, 2=medium, 3=high

@dataclass
class OptimizationResult:
    """Result of optimization process"""
    success: bool
    schedule_id: str
    old_cost_zmw: float
    new_cost_zmw: float
    cost_savings_zmw: float
    efficiency_improvement: float
    processing_time_ms: float
    optimization_details: Dict
    error_message: Optional[str] = None

class DynamicOptimizer:
    """Real-time dynamic optimization engine"""
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.labor_calculator = LaborCostCalculator()
        self.idle_optimizer = IdleTimeOptimizer()
        self.optimization_queue = asyncio.Queue()
        self.is_running = False
        self.optimization_callbacks = []
        self.cascade_analyzer = CascadeAnalyzer()
        self.conflict_resolver = ConflictResolver()
        
        # Optimization parameters
        self.max_processing_time_ms = 5000  # 5 seconds max
        self.min_cost_savings_threshold = 10.0  # ZMW - lowered for testing
        self.efficiency_threshold = 80.0  # percentage
        
        # Performance tracking
        self.optimization_history = []
        self.last_optimization_time = None
        self.optimization_count = 0
        
    def register_callback(self, callback: Callable[[OptimizationResult], None]):
        """Register callback for optimization results"""
        self.optimization_callbacks.append(callback)
    
    async def trigger_optimization(self, event: OptimizationEvent):
        """Trigger optimization for an event"""
        await self.optimization_queue.put(event)
        logger.info(f"Optimization triggered: {event.event_type.value} for schedule {event.schedule_id}")
    
    async def start_optimization_loop(self):
        """Start the continuous optimization loop"""
        self.is_running = True
        logger.info("Dynamic optimization loop started")
        
        while self.is_running:
            try:
                # Wait for optimization event with timeout
                event = await asyncio.wait_for(
                    self.optimization_queue.get(), 
                    timeout=60.0  # Check for periodic optimization every minute
                )
                
                # Process optimization event
                result = await self.process_optimization_event(event)
                
                # Notify callbacks
                for callback in self.optimization_callbacks:
                    try:
                        await callback(result)
                    except Exception as e:
                        logger.error(f"Error in optimization callback: {e}")
                
            except asyncio.TimeoutError:
                # Periodic optimization check
                await self.periodic_optimization_check()
            except Exception as e:
                logger.error(f"Error in optimization loop: {e}")
    
    async def process_optimization_event(self, event: OptimizationEvent) -> OptimizationResult:
        """Process a single optimization event"""
        start_time = time.time()
        
        try:
            logger.info(f"Processing optimization: {event.event_type.value} for {event.schedule_id}")
            
            # Get current schedule
            current_schedule = await self.get_schedule_data(event.schedule_id)
            if not current_schedule:
                return OptimizationResult(
                    success=False,
                    schedule_id=event.schedule_id,
                    old_cost_zmw=0,
                    new_cost_zmw=0,
                    cost_savings_zmw=0,
                    efficiency_improvement=0,
                    processing_time_ms=0,
                    optimization_details={},
                    error_message="Schedule not found"
                )
            
            # Calculate current costs
            old_cost = await self.calculate_schedule_cost(current_schedule)
            
            # Apply optimization based on event type
            if event.event_type == OptimizationTrigger.SCHEDULE_CREATED:
                optimized_schedule = await self.optimize_new_schedule(current_schedule)
            elif event.event_type == OptimizationTrigger.LABOR_COST_CHANGE:
                optimized_schedule = await self.optimize_for_labor_costs(current_schedule, event.trigger_data)
            elif event.event_type == OptimizationTrigger.DISRUPTION_DETECTED:
                optimized_schedule = await self.optimize_for_disruption(current_schedule, event.trigger_data)
            elif event.event_type == OptimizationTrigger.EFFICIENCY_THRESHOLD:
                optimized_schedule = await self.optimize_for_efficiency(current_schedule)
            else:
                optimized_schedule = await self.general_optimization(current_schedule)
            
            # Calculate new costs
            new_cost = await self.calculate_schedule_cost(optimized_schedule)
            
            # Calculate improvements
            cost_savings = old_cost - new_cost
            efficiency_improvement = await self.calculate_efficiency_improvement(current_schedule, optimized_schedule)
            
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Validate optimization meets thresholds
            if cost_savings >= self.min_cost_savings_threshold or efficiency_improvement >= 5.0:
                # Apply optimized schedule
                await self.apply_optimized_schedule(optimized_schedule)
                
                result = OptimizationResult(
                    success=True,
                    schedule_id=event.schedule_id,
                    old_cost_zmw=old_cost,
                    new_cost_zmw=new_cost,
                    cost_savings_zmw=cost_savings,
                    efficiency_improvement=efficiency_improvement,
                    processing_time_ms=processing_time_ms,
                    optimization_details={
                        "event_type": event.event_type.value,
                        "trigger_data": event.trigger_data,
                        "optimization_applied": True
                    }
                )
            else:
                # Optimization doesn't meet threshold, keep original
                result = OptimizationResult(
                    success=False,
                    schedule_id=event.schedule_id,
                    old_cost_zmw=old_cost,
                    new_cost_zmw=old_cost,
                    cost_savings_zmw=0,
                    efficiency_improvement=0,
                    processing_time_ms=processing_time_ms,
                    optimization_details={
                        "event_type": event.event_type.value,
                        "reason": "Insufficient cost savings or efficiency improvement",
                        "min_savings_required": self.min_cost_savings_threshold,
                        "actual_savings": cost_savings
                    }
                )
            
            # Log optimization event
            await self.log_optimization_event(event, result)
            
            # Update performance tracking
            self.optimization_history.append(result)
            self.optimization_count += 1
            self.last_optimization_time = datetime.now()
            
            return result
            
        except Exception as e:
            processing_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Error processing optimization: {e}")
            
            return OptimizationResult(
                success=False,
                schedule_id=event.schedule_id,
                old_cost_zmw=0,
                new_cost_zmw=0,
                cost_savings_zmw=0,
                efficiency_improvement=0,
                processing_time_ms=processing_time_ms,
                optimization_details={},
                error_message=str(e)
            )
    
    async def optimize_new_schedule(self, schedule: Dict) -> Dict:
        """Optimize newly created schedule for labor efficiency"""
        # Extract driver assignments
        driver_assignments = schedule.get("train_assignments", [])
        
        # Optimize driver assignments to minimize idle time
        optimized_assignments = await self.optimize_driver_assignments(driver_assignments)
        
        # Optimize shift assignments
        optimized_shifts = await self.optimize_shift_assignments(optimized_assignments)
        
        # Update schedule with optimizations
        optimized_schedule = schedule.copy()
        optimized_schedule["train_assignments"] = optimized_shifts
        optimized_schedule["optimization_applied"] = True
        optimized_schedule["optimization_timestamp"] = datetime.now().isoformat()
        
        return optimized_schedule
    
    async def optimize_for_labor_costs(self, schedule: Dict, cost_changes: Dict) -> Dict:
        """Optimize schedule based on labor cost changes"""
        # Update labor cost parameters
        new_wage_rates = cost_changes.get("wage_changes", {})
        new_skill_premiums = cost_changes.get("skill_premiums", {})
        
        # Re-optimize with new cost parameters
        optimized_schedule = await self.general_optimization(schedule)
        
        # Add cost change metadata
        optimized_schedule["labor_cost_changes"] = cost_changes
        optimized_schedule["cost_optimization_applied"] = True
        
        return optimized_schedule
    
    async def optimize_for_disruption(self, schedule: Dict, disruption_data: Dict) -> Dict:
        """Optimize schedule for disruption handling"""
        disruption_type = disruption_data.get("type", "unknown")
        affected_trains = disruption_data.get("affected_trains", [])
        
        # Phase 3: Robust Disruption Handling
        # 1. Analyze Cascade Effect
        disrupted_train_id = disruption_data.get("train_id", 0)
        delay_days = disruption_data.get("delay_days", 1)
        start_day = disruption_data.get("day", 1)
        
        cascade_impact = self.cascade_analyzer.analyze_delay_propagation(
            schedule.get("train_assignments", []),
            disrupted_train_id,
            delay_days,
            start_day
        )
        
        # 2. Resolve Conflicts
        current_state = np.zeros(20) # Placeholder for actual state extraction
        resolution = self.conflict_resolver.resolve_conflicts(
            current_state,
            cascade_impact,
            schedule.get("train_assignments", [])
        )
        
        # 3. Apply recovery heuristics if no specialized handler exists
        if disruption_type == "driver_unavailable":
            optimized_schedule = await self.handle_driver_unavailability(schedule, disruption_data)
        elif disruption_type == "route_blocked":
            optimized_schedule = await self.handle_route_blockage(schedule, disruption_data)
        elif disruption_type == "equipment_failure":
            optimized_schedule = await self.handle_equipment_failure(schedule, disruption_data)
        else:
            optimized_schedule = await self.general_optimization(schedule)
        
        optimized_schedule["disruption_handled"] = True
        optimized_schedule["cascade_impact"] = cascade_impact
        optimized_schedule["resolution_plan"] = resolution
        optimized_schedule["disruption_data"] = disruption_data
        
        return optimized_schedule
    
    async def optimize_for_efficiency(self, schedule: Dict) -> Dict:
        """Optimize schedule for efficiency improvements"""
        # Focus on reducing overtime and improving utilization
        driver_assignments = schedule.get("train_assignments", [])
        
        # Rebalance workloads
        rebalanced_assignments = await self.rebalance_workloads(driver_assignments)
        
        # Optimize skill utilization
        skill_optimized = await self.optimize_skill_utilization(rebalanced_assignments)
        
        optimized_schedule = schedule.copy()
        optimized_schedule["train_assignments"] = skill_optimized
        optimized_schedule["efficiency_optimization_applied"] = True
        
        return optimized_schedule
    
    async def general_optimization(self, schedule: Dict) -> Dict:
        """General optimization algorithm"""
        optimized_schedule = schedule.copy()
        
        # Apply multiple optimization strategies
        optimized_assignments = schedule.get("train_assignments", [])
        
        # 1. Minimize overtime
        optimized_assignments = await self.minimize_overtime(optimized_assignments)
        
        # 2. Optimize skill utilization
        optimized_assignments = await self.optimize_skill_utilization(optimized_assignments)
        
        # 3. Balance workloads
        optimized_assignments = await self.rebalance_workloads(optimized_assignments)
        
        optimized_schedule["train_assignments"] = optimized_assignments
        optimized_schedule["general_optimization_applied"] = True
        
        return optimized_schedule
    
    async def optimize_driver_assignments(self, assignments: List[Dict]) -> List[Dict]:
        """Optimize driver assignments to minimize costs"""
        # Sort assignments by cost impact
        optimized = assignments.copy()
        
        # Apply idle time optimization
        for assignment in optimized:
            driver_id = assignment.get("driver_id", "")
            hours = assignment.get("hours_worked", 8.0)
            
            # Check if we can reduce hours or optimize shift
            if hours > 10.0:  # High overtime indicator
                # Try to redistribute work
                assignment["optimization_note"] = "Consider redistributing to reduce overtime"
        
        return optimized
    
    async def optimize_shift_assignments(self, assignments: List[Dict]) -> List[Dict]:
        """Optimize shift assignments for cost efficiency"""
        optimized = assignments.copy()
        
        for assignment in optimized:
            current_shift = assignment.get("shift_type", "day")
            
            # Suggest shift optimization
            if current_shift == "night":
                assignment["shift_optimization"] = "Consider moving to day shift to reduce premiums"
            elif current_shift == "evening":
                assignment["shift_optimization"] = "Consider moving to day shift for minor savings"
        
        return optimized
    
    async def minimize_overtime(self, assignments: List[Dict]) -> List[Dict]:
        """Minimize overtime in assignments"""
        optimized = assignments.copy()
        
        # Calculate total hours per driver
        driver_hours = {}
        for assignment in optimized:
            driver_id = assignment.get("driver_id", "")
            hours = assignment.get("hours_worked", 8.0)
            driver_hours[driver_id] = driver_hours.get(driver_id, 0) + hours
        
        # Identify drivers with high overtime
        for driver_id, total_hours in driver_hours.items():
            if total_hours > 10.0:
                # Find assignments for this driver
                for assignment in optimized:
                    if assignment.get("driver_id") == driver_id:
                        assignment["overtime_optimization"] = f"High overtime ({total_hours:.1f}h total) - consider redistribution"
        
        return optimized
    
    async def optimize_skill_utilization(self, assignments: List[Dict]) -> List[Dict]:
        """Optimize skill utilization"""
        optimized = assignments.copy()
        
        for assignment in optimized:
            skill_level = assignment.get("skill_level", "beginner")
            task_complexity = assignment.get("task_complexity", "low")
            
            # Check skill-task match
            if skill_level == "expert" and task_complexity == "low":
                assignment["skill_optimization"] = "Overqualified - consider junior driver"
            elif skill_level == "beginner" and task_complexity == "high":
                assignment["skill_optimization"] = "Underqualified - consider senior driver"
        
        return optimized
    
    async def rebalance_workloads(self, assignments: List[Dict]) -> List[Dict]:
        """Rebalance workloads across drivers"""
        optimized = assignments.copy()
        
        # Calculate workload distribution
        workloads = []
        for assignment in optimized:
            workloads.append(assignment.get("hours_worked", 8.0))
        
        avg_workload = np.mean(workloads) if workloads else 8.0
        std_workload = np.std(workloads) if workloads else 0.0
        
        # Flag imbalanced assignments
        for i, assignment in enumerate(optimized):
            workload = assignment.get("hours_worked", 8.0)
            if abs(workload - avg_workload) > std_workload:
                assignment["workload_optimization"] = f"Workload imbalance ({workload:.1f}h vs avg {avg_workload:.1f}h)"
        
        return optimized
    
    async def handle_driver_unavailability(self, schedule: Dict, disruption_data: Dict) -> Dict:
        """Handle driver unavailability disruption"""
        unavailable_driver = disruption_data.get("driver_id")
        assignments = schedule.get("train_assignments", [])
        
        # Find affected assignments
        optimized_assignments = []
        for assignment in assignments:
            if assignment.get("driver_id") != unavailable_driver:
                optimized_assignments.append(assignment)
            else:
                # Find replacement driver
                replacement = await self.find_replacement_driver(assignment)
                if replacement:
                    assignment["driver_id"] = replacement["driver_id"]
                    assignment["skill_level"] = replacement["skill_level"]
                    assignment["replacement_reason"] = f"Driver {unavailable_driver} unavailable"
                    optimized_assignments.append(assignment)
        
        optimized_schedule = schedule.copy()
        optimized_schedule["train_assignments"] = optimized_assignments
        return optimized_schedule
    
    async def handle_route_blockage(self, schedule: Dict, disruption_data: Dict) -> Dict:
        """Handle route blockage disruption"""
        blocked_route = disruption_data.get("route_name")
        assignments = schedule.get("train_assignments", [])
        
        # Re-route affected trains
        optimized_assignments = []
        for assignment in assignments:
            if assignment.get("route_name") != blocked_route:
                optimized_assignments.append(assignment)
            else:
                # Find alternative route
                alternative_route = await self.find_alternative_route(blocked_route)
                if alternative_route:
                    assignment["route_name"] = alternative_route
                    assignment["route_change_reason"] = f"Route {blocked_route} blocked"
                    optimized_assignments.append(assignment)
        
        optimized_schedule = schedule.copy()
        optimized_schedule["train_assignments"] = optimized_assignments
        return optimized_schedule
    
    async def handle_equipment_failure(self, schedule: Dict, disruption_data: Dict) -> Dict:
        """Handle equipment failure disruption"""
        failed_train = disruption_data.get("train_id")
        assignments = schedule.get("train_assignments", [])
        
        # Reassign work from failed train
        optimized_assignments = []
        for assignment in assignments:
            if assignment.get("train_id") != failed_train:
                optimized_assignments.append(assignment)
            else:
                # Redistribute to other trains
                redistribution = await self.redistribute_train_work(assignment)
                optimized_assignments.extend(redistribution)
        
        optimized_schedule = schedule.copy()
        optimized_schedule["train_assignments"] = optimized_assignments
        return optimized_schedule
    
    async def find_replacement_driver(self, assignment: Dict) -> Optional[Dict]:
        """Find replacement driver for assignment"""
        # Simple implementation - in real system, query database
        available_drivers = [
            {"driver_id": "driver_backup_001", "skill_level": "intermediate"},
            {"driver_id": "driver_backup_002", "skill_level": "advanced"}
        ]
        
        required_skill = assignment.get("skill_level", "beginner")
        
        for driver in available_drivers:
            if driver["skill_level"] == required_skill or driver["skill_level"] == "advanced":
                return driver
        
        return available_drivers[0] if available_drivers else None
    
    async def find_alternative_route(self, blocked_route: str) -> Optional[str]:
        """Find alternative route for blocked route"""
        route_alternatives = {
            "DAR_KAPIRI": "DAR_MBEYA",
            "DAR_MBEYA": "KAPIRI_NDOLA",
            "KAPIRI_NDOLA": "DAR_KAPIRI"
        }
        return route_alternatives.get(blocked_route)
    
    async def redistribute_train_work(self, failed_assignment: Dict) -> List[Dict]:
        """Redistribute work from failed train"""
        # Simple implementation - split work among available trains
        work_split = failed_assignment.get("hours_worked", 8.0) / 2
        
        return [
            {
                "train_id": failed_assignment.get("train_id", 0) + 100,
                "driver_id": f"driver_replacement_1",
                "hours_worked": work_split,
                "work_redistribution": True
            },
            {
                "train_id": failed_assignment.get("train_id", 0) + 101,
                "driver_id": f"driver_replacement_2",
                "hours_worked": work_split,
                "work_redistribution": True
            }
        ]
    
    async def periodic_optimization_check(self):
        """Perform periodic optimization check"""
        if self.last_optimization_time:
            time_since_last = datetime.now() - self.last_optimization_time
            if time_since_last > timedelta(minutes=30):  # Check every 30 minutes
                # Find schedules that need optimization
                schedules_needing_optimization = await self.find_schedules_needing_optimization()
                
                for schedule_id in schedules_needing_optimization:
                    event = OptimizationEvent(
                        event_type=OptimizationTrigger.PERIODIC_REOPTIMIZATION,
                        timestamp=datetime.now(),
                        schedule_id=schedule_id,
                        trigger_data={"reason": "periodic_check"},
                        priority=1
                    )
                    await self.trigger_optimization(event)
    
    async def find_schedules_needing_optimization(self) -> List[str]:
        """Find schedules that need optimization"""
        # Simple implementation - in real system, query database
        return ["test_schedule_001"]  # Placeholder
    
    async def get_schedule_data(self, schedule_id: str) -> Optional[Dict]:
        """Get schedule data from database"""
        # Simple implementation - in real system, query database
        return {
            "schedule_id": schedule_id,
            "train_assignments": [
                {"train_id": 1, "driver_id": "driver_001", "hours_worked": 10.5, "skill_level": "advanced"},
                {"train_id": 2, "driver_id": "driver_002", "hours_worked": 8.0, "skill_level": "intermediate"},
                {"train_id": 3, "driver_id": "driver_003", "hours_worked": 12.0, "skill_level": "beginner"}
            ]
        }
    
    async def calculate_schedule_cost(self, schedule: Dict) -> float:
        """Calculate total schedule cost"""
        assignments = schedule.get("train_assignments", [])
        total_cost = 0.0
        
        for assignment in assignments:
            # Simple cost calculation
            hours = assignment.get("hours_worked", 8.0)
            skill_level = assignment.get("skill_level", "beginner")
            
            # Base rate + skill premium
            base_rate = 50.0  # ZMW per hour
            skill_premium = {"beginner": 0, "intermediate": 0.2, "advanced": 0.4}.get(skill_level, 0)
            
            cost = hours * base_rate * (1 + skill_premium)
            total_cost += cost
        
        return total_cost
    
    async def calculate_efficiency_improvement(self, old_schedule: Dict, new_schedule: Dict) -> float:
        """Calculate efficiency improvement percentage"""
        old_cost = await self.calculate_schedule_cost(old_schedule)
        new_cost = await self.calculate_schedule_cost(new_schedule)
        
        if old_cost > 0:
            return ((old_cost - new_cost) / old_cost) * 100
        return 0.0
    
    async def apply_optimized_schedule(self, schedule: Dict):
        """Apply optimized schedule to database"""
        # Simple implementation - in real system, update database
        logger.info(f"Applied optimized schedule: {schedule.get('schedule_id')}")
    
    async def log_optimization_event(self, event: OptimizationEvent, result: OptimizationResult):
        """Log optimization event to database"""
        # Simple implementation - in real system, log to database
        logger.info(f"Logged optimization: {event.event_type.value} - Success: {result.success}")
    
    def get_optimization_statistics(self) -> Dict:
        """Get optimization performance statistics"""
        if not self.optimization_history:
            return {}
        
        successful_optimizations = [r for r in self.optimization_history if r.success]
        total_savings = sum(r.cost_savings_zmw for r in successful_optimizations)
        avg_processing_time = np.mean([r.processing_time_ms for r in self.optimization_history])
        
        return {
            "total_optimizations": len(self.optimization_history),
            "successful_optimizations": len(successful_optimizations),
            "success_rate": len(successful_optimizations) / len(self.optimization_history) * 100,
            "total_cost_savings_zmw": total_savings,
            "average_processing_time_ms": avg_processing_time,
            "last_optimization": self.last_optimization_time.isoformat() if self.last_optimization_time else None
        }
    
    def stop_optimization_loop(self):
        """Stop the optimization loop"""
        self.is_running = False
        logger.info("Dynamic optimization loop stopped")

# Test the dynamic optimizer
if __name__ == "__main__":
    async def test_dynamic_optimizer():
        optimizer = DynamicOptimizer()
        
        # Create test event
        event = OptimizationEvent(
            event_type=OptimizationTrigger.SCHEDULE_CREATED,
            timestamp=datetime.now(),
            schedule_id="test_schedule_001",
            trigger_data={"test": True},
            priority=2
        )
        
        # Process optimization
        result = await optimizer.process_optimization_event(event)
        
        print("🚆 Dynamic Optimization Test")
        print("=" * 50)
        print(f"Schedule ID: {result.schedule_id}")
        print(f"Success: {result.success}")
        print(f"Old Cost: ZMW {result.old_cost_zmw:.2f}")
        print(f"New Cost: ZMW {result.new_cost_zmw:.2f}")
        print(f"Cost Savings: ZMW {result.cost_savings_zmw:.2f}")
        print(f"Efficiency Improvement: {result.efficiency_improvement:.2f}%")
        print(f"Processing Time: {result.processing_time_ms:.2f}ms")
        
        if result.error_message:
            print(f"Error: {result.error_message}")
        
        # Get statistics
        stats = optimizer.get_optimization_statistics()
        print(f"\nOptimization Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    
    # Run test
    asyncio.run(test_dynamic_optimizer())
