"""
Multi-Variable Constraint Optimization for TAZARA Multi-Route System
Phase 1: Advanced optimization with time, cost, skills, location, and priority constraints
"""

import numpy as np
import sys
import os
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reinforcement_rl.enhanced_cost_model import LaborCostCalculator, calculate_labor_efficiency_metrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Constraint:
    """Represents a constraint in the optimization"""
    name: str
    type: str  # time, cost, skill, location, priority
    weight: float  # Importance weight (0-1)
    penalty: float  # Penalty for violation
    description: str

@dataclass
class OptimizationSolution:
    """Represents an optimization solution"""
    assignments: List[Dict]
    constraint_satisfaction: Dict[str, float]
    total_cost: float
    total_efficiency: float
    optimization_score: float
    violations: List[str]

class MultiVariableOptimizer:
    """Advanced multi-variable constraint optimization engine"""
    
    def __init__(self):
        self.labor_calculator = LaborCostCalculator()
        self.constraints = []
        self.optimization_history = []
        
    def add_constraint(self, constraint: Constraint):
        """Add a constraint to the optimization"""
        self.constraints.append(constraint)
        logger.info(f"Added constraint: {constraint.name} (weight: {constraint.weight})")
    
    def optimize_schedule(self, schedule_data: Dict) -> OptimizationSolution:
        """
        Optimize schedule with all constraints
        """
        try:
            logger.info(f"Starting multi-variable optimization for schedule {schedule_data.get('schedule_id')}")
            
            # Extract current assignments
            current_assignments = schedule_data.get("train_assignments", [])
            
            # Generate optimization candidates
            candidates = self._generate_optimization_candidates(current_assignments)
            
            # Evaluate each candidate
            best_solution = None
            best_score = -float('inf')
            
            for candidate in candidates:
                solution = self._evaluate_candidate(candidate, schedule_data)
                
                if solution.optimization_score > best_score:
                    best_score = solution.optimization_score
                    best_solution = solution
            
            if best_solution:
                logger.info(f"Best solution found with score: {best_score:.2f}")
                self.optimization_history.append(best_solution)
                return best_solution
            else:
                # Return current assignments as fallback
                return self._create_fallback_solution(current_assignments, schedule_data)
                
        except Exception as e:
            logger.error(f"Error in multi-variable optimization: {e}")
            return self._create_fallback_solution(schedule_data.get("train_assignments", []), schedule_data)
    
    def _generate_optimization_candidates(self, assignments: List[Dict]) -> List[List[Dict]]:
        """Generate optimization candidates"""
        candidates = []
        
        # Candidate 1: Current assignments
        candidates.append(assignments.copy())
        
        # Candidate 2: Overtime minimization
        overtime_minimized = self._minimize_overtime(assignments)
        candidates.append(overtime_minimized)
        
        # Candidate 3: Skill optimization
        skill_optimized = self._optimize_skills(assignments)
        candidates.append(skill_optimized)
        
        # Candidate 4: Cost optimization
        cost_optimized = self._optimize_costs(assignments)
        candidates.append(cost_optimized)
        
        # Candidate 5: Balanced approach
        balanced = self._balanced_optimization(assignments)
        candidates.append(balanced)
        
        # Candidate 6: Priority-based
        priority_optimized = self._optimize_by_priority(assignments)
        candidates.append(priority_optimized)
        
        return candidates
    
    def _evaluate_candidate(self, candidate: List[Dict], schedule_data: Dict) -> OptimizationSolution:
        """Evaluate a candidate solution against all constraints"""
        try:
            # Calculate basic metrics
            total_cost = self._calculate_total_cost(candidate)
            
            # Prepare cost data for efficiency metrics
            cost_breakdown_list = []
            for a in candidate:
                cost_result = self.labor_calculator.calculate_labor_cost(
                    driver_id=a.get("driver_id", "unknown"),
                    hours_worked=a.get("hours_worked", 8.0),
                    route_name=a.get("route_name"),
                    is_weekend=False
                )
                cost_breakdown_list.append(cost_result)
            
            efficiency_metrics = calculate_labor_efficiency_metrics(cost_breakdown_list)
            
            # Evaluate constraint satisfaction
            constraint_satisfaction = {}
            violations = []
            
            for constraint in self.constraints:
                satisfaction = self._evaluate_constraint(constraint, candidate, schedule_data)
                constraint_satisfaction[constraint.name] = satisfaction
                
                if satisfaction < 1.0:  # Constraint violated
                    violations.append(f"{constraint.name}: {constraint.description}")
            
            # Calculate overall optimization score
            optimization_score = self._calculate_optimization_score(
                total_cost, 
                efficiency_metrics.get("labor_cost_efficiency", 100),
                constraint_satisfaction,
                violations
            )
            
            return OptimizationSolution(
                assignments=candidate,
                constraint_satisfaction=constraint_satisfaction,
                total_cost=total_cost,
                total_efficiency=efficiency_metrics.get("labor_cost_efficiency", 100),
                optimization_score=optimization_score,
                violations=violations
            )
            
        except Exception as e:
            logger.error(f"Error evaluating candidate: {e}")
            return self._create_fallback_solution(candidate, schedule_data)
    
    def _evaluate_constraint(self, constraint: Constraint, candidate: List[Dict], schedule_data: Dict) -> float:
        """Evaluate a single constraint for a candidate"""
        try:
            if constraint.type == "time":
                return self._evaluate_time_constraint(constraint, candidate, schedule_data)
            elif constraint.type == "cost":
                return self._evaluate_cost_constraint(constraint, candidate, schedule_data)
            elif constraint.type == "skill":
                return self._evaluate_skill_constraint(constraint, candidate, schedule_data)
            elif constraint.type == "location":
                return self._evaluate_location_constraint(constraint, candidate, schedule_data)
            elif constraint.type == "priority":
                return self._evaluate_priority_constraint(constraint, candidate, schedule_data)
            else:
                return 1.0  # Unknown constraint, assume satisfied
                
        except Exception as e:
            logger.error(f"Error evaluating constraint {constraint.name}: {e}")
            return 0.0
    
    def _evaluate_time_constraint(self, constraint: Constraint, candidate: List[Dict], schedule_data: Dict) -> float:
        """Evaluate time constraint (delivery deadlines)"""
        total_hours = sum(a.get("hours_worked", 8.0) for a in candidate)
        max_hours = constraint.penalty  # Using penalty as max allowed hours
        
        if total_hours <= max_hours:
            return 1.0
        else:
            # Partial satisfaction based on excess
            excess = total_hours - max_hours
            return max(0.0, 1.0 - (excess / max_hours))
    
    def _evaluate_cost_constraint(self, constraint: Constraint, candidate: List[Dict], schedule_data: Dict) -> float:
        """Evaluate cost constraint (budget limits)"""
        total_cost = self._calculate_total_cost(candidate)
        max_cost = constraint.penalty  # Using penalty as max allowed cost
        
        if total_cost <= max_cost:
            return 1.0
        else:
            # Partial satisfaction based on excess
            excess = total_cost - max_cost
            return max(0.0, 1.0 - (excess / max_cost))
    
    def _evaluate_skill_constraint(self, constraint: Constraint, candidate: List[Dict], schedule_data: Dict) -> float:
        """Evaluate skill constraint (driver capabilities)"""
        required_skill = constraint.penalty  # Using penalty as required skill level
        skill_hierarchy = {"beginner": 1, "intermediate": 2, "advanced": 3}
        
        satisfied_assignments = 0
        for assignment in candidate:
            current_skill = assignment.get("skill_level", "beginner")
            if skill_hierarchy.get(current_skill, 0) >= skill_hierarchy.get(required_skill, 0):
                satisfied_assignments += 1
        
        return satisfied_assignments / len(candidate) if candidate else 1.0
    
    def _evaluate_location_constraint(self, constraint: Constraint, candidate: List[Dict], schedule_data: Dict) -> float:
        """Evaluate location constraint (geographic clustering)"""
        preferred_location = constraint.penalty  # Using penalty as preferred location
        
        satisfied_assignments = 0
        for assignment in candidate:
            current_location = assignment.get("location", "unknown")
            if current_location == preferred_location or current_location == "unknown":
                satisfied_assignments += 1
        
        return satisfied_assignments / len(candidate) if candidate else 1.0
    
    def _evaluate_priority_constraint(self, constraint: Constraint, candidate: List[Dict], schedule_data: Dict) -> float:
        """Evaluate priority constraint (cargo importance)"""
        required_priority = constraint.penalty  # Using penalty as required priority
        
        satisfied_assignments = 0
        for assignment in candidate:
            current_priority = assignment.get("priority", "normal")
            if self._priority_satisfies_requirement(current_priority, required_priority):
                satisfied_assignments += 1
        
        return satisfied_assignments / len(candidate) if candidate else 1.0
    
    def _priority_satisfies_requirement(self, current: str, required: str) -> bool:
        """Check if current priority satisfies requirement"""
        priority_hierarchy = {"low": 1, "normal": 2, "high": 3, "urgent": 4}
        return priority_hierarchy.get(current, 0) >= priority_hierarchy.get(required, 0)
    
    def _calculate_optimization_score(self, total_cost: float, efficiency: float, 
                                   constraint_satisfaction: Dict[str, float], 
                                   violations: List[str]) -> float:
        """Calculate overall optimization score"""
        try:
            # Base score
            score = 100.0
            
            # Cost component (lower is better)
            cost_penalty = min(30, total_cost / 100)  # Max 30 points penalty
            score -= cost_penalty
            
            # Efficiency component (higher is better)
            efficiency_bonus = min(20, (100 - efficiency) / 5)  # Max 20 points bonus
            score += efficiency_bonus
            
            # Constraint satisfaction component
            total_weight = sum(c.weight for c in self.constraints)
            if total_weight > 0:
                weighted_satisfaction = sum(
                    constraint_satisfaction.get(c.name, 0) * c.weight 
                    for c in self.constraints
                ) / total_weight
                constraint_bonus = weighted_satisfaction * 30  # Max 30 points
                score += constraint_bonus
            
            # Violation penalty
            violation_penalty = len(violations) * 10
            score -= violation_penalty
            
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating optimization score: {e}")
            return 0.0
    
    def _minimize_overtime(self, assignments: List[Dict]) -> List[Dict]:
        """Generate candidate with minimized overtime"""
        optimized = []
        
        for assignment in assignments:
            new_assignment = assignment.copy()
            hours = assignment.get("hours_worked", 8.0)
            
            # Reduce overtime to minimum
            if hours > 8.0:
                new_assignment["hours_worked"] = 8.0
                new_assignment["overtime_reduction"] = hours - 8.0
            else:
                new_assignment["overtime_reduction"] = 0.0
            
            optimized.append(new_assignment)
        
        return optimized
    
    def _optimize_skills(self, assignments: List[Dict]) -> List[Dict]:
        """Generate candidate with optimized skill utilization"""
        optimized = []
        
        # Sort by skill level (highest first)
        sorted_assignments = sorted(assignments, 
                               key=lambda x: {"advanced": 3, "intermediate": 2, "beginner": 1}.get(x.get("skill_level", "beginner"), 0),
                               reverse=True)
        
        for assignment in sorted_assignments:
            new_assignment = assignment.copy()
            new_assignment["skill_optimization_applied"] = True
            optimized.append(new_assignment)
        
        return optimized
    
    def _optimize_costs(self, assignments: List[Dict]) -> List[Dict]:
        """Generate candidate with optimized costs"""
        optimized = []
        
        for assignment in assignments:
            new_assignment = assignment.copy()
            
            # Optimize shift for lower cost
            current_shift = assignment.get("shift_type", "day")
            if current_shift in ["night", "evening"]:
                new_assignment["shift_type"] = "day"
                new_assignment["shift_optimization"] = f"Changed from {current_shift} to day shift"
            
            optimized.append(new_assignment)
        
        return optimized
    
    def _balanced_optimization(self, assignments: List[Dict]) -> List[Dict]:
        """Generate balanced optimization candidate"""
        optimized = []
        
        # Calculate average hours
        avg_hours = sum(a.get("hours_worked", 8.0) for a in assignments) / len(assignments) if assignments else 8.0
        
        for assignment in assignments:
            new_assignment = assignment.copy()
            hours = assignment.get("hours_worked", 8.0)
            
            # Balance towards average
            if abs(hours - avg_hours) > 2.0:
                new_assignment["hours_worked"] = avg_hours
                new_assignment["workload_balancing"] = f"Balanced from {hours} to {avg_hours:.1f}"
            
            optimized.append(new_assignment)
        
        return optimized
    
    def _optimize_by_priority(self, assignments: List[Dict]) -> List[Dict]:
        """Generate priority-based optimization candidate"""
        optimized = []
        
        # Sort by priority (highest first)
        priority_order = {"urgent": 4, "high": 3, "normal": 2, "low": 1}
        sorted_assignments = sorted(assignments,
                               key=lambda x: priority_order.get(x.get("priority", "normal"), 0),
                               reverse=True)
        
        for assignment in sorted_assignments:
            new_assignment = assignment.copy()
            new_assignment["priority_optimization_applied"] = True
            optimized.append(new_assignment)
        
        return optimized
    
    def _calculate_total_cost(self, assignments: List[Dict]) -> float:
        """Calculate total cost for assignments"""
        return sum(self._calculate_assignment_cost(a) for a in assignments)
    
    def _calculate_assignment_cost(self, assignment: Dict) -> float:
        """Calculate cost for single assignment"""
        try:
            hours = assignment.get("hours_worked", 8.0)
            skill_level = assignment.get("skill_level", "beginner")
            shift_type = assignment.get("shift_type", "day")
            
            # Use labor calculator
            cost_breakdown = self.labor_calculator.calculate_labor_cost(
                driver_id=assignment.get("driver_id", "unknown"),
                hours_worked=hours,
                route_name=assignment.get("route_name"),
                is_weekend=False
            )
            
            return cost_breakdown.get("total_labor_cost_zmw", 0.0)
            
        except Exception as e:
            logger.error(f"Error calculating assignment cost: {e}")
            return 0.0
    
    def _create_fallback_solution(self, assignments: List[Dict], schedule_data: Dict) -> OptimizationSolution:
        """Create fallback solution when optimization fails"""
        return OptimizationSolution(
            assignments=assignments,
            constraint_satisfaction={c.name: 0.5 for c in self.constraints},  # Partial satisfaction
            total_cost=self._calculate_total_cost(assignments),
            total_efficiency=50.0,  # Default efficiency
            optimization_score=25.0,  # Low score for fallback
            violations=["Optimization failed - using fallback"]
        )
    
    def get_optimization_summary(self) -> Dict:
        """Get summary of optimization history"""
        if not self.optimization_history:
            return {"message": "No optimization history available"}
        
        total_optimizations = len(self.optimization_history)
        successful_optimizations = len([s for s in self.optimization_history if s.optimization_score > 50])
        average_score = np.mean([s.optimization_score for s in self.optimization_history])
        
        return {
            "total_optimizations": total_optimizations,
            "successful_optimizations": successful_optimizations,
            "success_rate": successful_optimizations / total_optimizations * 100 if total_optimizations > 0 else 0,
            "average_score": average_score,
            "best_score": max(s.optimization_score for s in self.optimization_history),
            "constraints_used": [c.name for c in self.constraints]
        }

# Test multi-variable optimizer
if __name__ == "__main__":
    # Create optimizer
    optimizer = MultiVariableOptimizer()
    
    # Add constraints
    optimizer.add_constraint(Constraint(
        name="time_limit",
        type="time",
        weight=0.3,
        penalty=40.0,  # Max 40 hours total
        description="Total hours should not exceed 40 hours"
    ))
    
    optimizer.add_constraint(Constraint(
        name="cost_budget",
        type="cost",
        weight=0.4,
        penalty=5000.0,  # Max ZMW 5000 total cost
        description="Total cost should not exceed ZMW 5000"
    ))
    
    optimizer.add_constraint(Constraint(
        name="skill_requirement",
        type="skill",
        weight=0.2,
        penalty="intermediate",  # At least intermediate skill
        description="All assignments should have at least intermediate skill level"
    ))
    
    optimizer.add_constraint(Constraint(
        name="location_preference",
        type="location",
        weight=0.1,
        penalty="central",  # Prefer central location
        description="Prefer central depot locations"
    ))
    
    # Test schedule
    test_schedule = {
        "schedule_id": "multi_var_test_001",
        "train_assignments": [
            {
                "train_id": 1,
                "driver_id": "driver_001",
                "hours_worked": 12.0,  # High overtime
                "skill_level": "beginner",  # Low skill
                "shift_type": "night",  # Expensive shift
                "location": "remote",  # Non-preferred location
                "priority": "low"  # Low priority
            },
            {
                "train_id": 2,
                "driver_id": "driver_002",
                "hours_worked": 6.0,  # Underutilized
                "skill_level": "advanced",  # High skill
                "shift_type": "day",  # Optimal shift
                "location": "central",  # Preferred location
                "priority": "high"  # High priority
            },
            {
                "train_id": 3,
                "driver_id": "driver_003",
                "hours_worked": 10.0,
                "skill_level": "intermediate",
                "shift_type": "evening",
                "location": "central",
                "priority": "normal"
            }
        ]
    }
    
    # Run optimization
    solution = optimizer.optimize_schedule(test_schedule)
    
    print("🚆 Multi-Variable Constraint Optimization Test")
    print("=" * 60)
    print(f"Schedule ID: {test_schedule['schedule_id']}")
    print(f"Optimization Score: {solution.optimization_score:.2f}/100")
    print(f"Total Cost: ZMW {solution.total_cost:.2f}")
    print(f"Total Efficiency: {solution.total_efficiency:.1f}%")
    print(f"Constraint Violations: {len(solution.violations)}")
    
    if solution.violations:
        print("\nViolations:")
        for violation in solution.violations:
            print(f"  - {violation}")
    
    print("\nConstraint Satisfaction:")
    for constraint_name, satisfaction in solution.constraint_satisfaction.items():
        print(f"  {constraint_name}: {satisfaction:.2f}")
    
    print("\nOptimization Summary:")
    summary = optimizer.get_optimization_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
