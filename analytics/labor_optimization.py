"""
Labor Optimization Analytics for TAZARA Multi-Route System
Phase 1: Advanced labor cost analysis and optimization recommendations
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reinforcement_rl.enhanced_cost_model import (
    LaborCostCalculator, 
    IdleTimeOptimizer,
    calculate_labor_efficiency_metrics
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LaborOptimizationAnalyzer:
    """Advanced labor optimization analytics and recommendations"""
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.cost_calculator = LaborCostCalculator()
        self.idle_optimizer = IdleTimeOptimizer()
        
    def analyze_labor_efficiency(self, schedule_data: Dict) -> Dict:
        """
        Analyze labor efficiency for a given schedule
        """
        try:
            # Extract driver assignments from schedule
            driver_assignments = self._extract_driver_assignments(schedule_data)
            
            if not driver_assignments:
                return {"error": "No driver assignments found in schedule"}
            
            # Calculate labor costs
            team_cost_analysis = self.cost_calculator.calculate_team_labor_cost(
                driver_assignments, 
                schedule_data.get("route_name", "DAR_KAPIRI")
            )
            
            # Calculate efficiency metrics
            efficiency_metrics = calculate_labor_efficiency_metrics(
                team_cost_analysis["team_costs"]
            )
            
            # Generate optimization recommendations
            recommendations = self._generate_optimization_recommendations(
                team_cost_analysis, efficiency_metrics
            )
            
            # Calculate potential savings
            potential_savings = self._calculate_potential_savings(
                team_cost_analysis, recommendations
            )
            
            return {
                "schedule_id": schedule_data.get("schedule_id"),
                "analysis_timestamp": datetime.now().isoformat(),
                "driver_assignments": driver_assignments,
                "team_cost_analysis": team_cost_analysis,
                "efficiency_metrics": efficiency_metrics,
                "optimization_recommendations": recommendations,
                "potential_savings": potential_savings,
                "overall_efficiency_score": self._calculate_efficiency_score(efficiency_metrics)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing labor efficiency: {e}")
            return {"error": str(e)}
    
    def _extract_driver_assignments(self, schedule_data: Dict) -> List[Dict]:
        """Extract driver assignments from schedule data"""
        assignments = []
        
        # Extract from train assignments
        train_assignments = schedule_data.get("train_assignments", [])
        for train in train_assignments:
            driver_id = train.get("driver_id", f"driver_{train.get('train_id', 'unknown')}")
            hours_worked = train.get("hours_worked", 8.0)  # Default to 8 hours
            
            assignments.append({
                "driver_id": driver_id,
                "hours_worked": hours_worked,
                "is_weekend": self._is_weekend_shift(schedule_data.get("start_date")),
                "skill_level": train.get("skill_level", "beginner"),
                "shift_type": train.get("shift_type", "day")
            })
        
        return assignments
    
    def _is_weekend_shift(self, date_str: str) -> bool:
        """Check if shift is on weekend"""
        try:
            if date_str:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                return date_obj.weekday() >= 5  # Saturday = 5, Sunday = 6
        except:
            pass
        return False
    
    def _generate_optimization_recommendations(self, 
                                          team_cost_analysis: Dict, 
                                          efficiency_metrics: Dict) -> List[Dict]:
        """Generate specific optimization recommendations"""
        recommendations = []
        
        # Overtime optimization
        overtime_percentage = efficiency_metrics.get("overtime_percentage", 0)
        if overtime_percentage > 20:
            recommendations.append({
                "type": "overtime_reduction",
                "priority": "high",
                "description": f"High overtime usage ({overtime_percentage:.1f}%) - consider adding more drivers or redistributing workload",
                "potential_savings_percent": min(30, overtime_percentage - 20),
                "implementation_effort": "medium"
            })
        
        # Skill level optimization
        cost_distribution = efficiency_metrics.get("cost_distribution", {})
        premium_overtime_cost = cost_distribution.get("premium_overtime_cost", 0)
        if premium_overtime_cost > 0:
            recommendations.append({
                "type": "premium_overtime_elimination",
                "priority": "high",
                "description": f"Premium overtime costs ZMW {premium_overtime_cost:.2f} - redistribute work to avoid >12 hour shifts",
                "potential_savings_percent": 25,
                "implementation_effort": "low"
            })
        
        # Utilization optimization
        avg_utilization = team_cost_analysis.get("average_utilization", 0)
        if avg_utilization < 80:
            recommendations.append({
                "type": "utilization_improvement",
                "priority": "medium",
                "description": f"Low average utilization ({avg_utilization:.1f}%) - optimize task assignments",
                "potential_savings_percent": 15,
                "implementation_effort": "medium"
            })
        
        # Shift optimization
        recommendations.append({
            "type": "shift_optimization",
            "priority": "medium",
            "description": "Consider shift rebalancing to reduce night shift premiums",
            "potential_savings_percent": 10,
            "implementation_effort": "low"
        })
        
        # Skill development
        recommendations.append({
            "type": "skill_development",
            "priority": "low",
            "description": "Invest in driver training to reduce skill premium costs",
            "potential_savings_percent": 20,
            "implementation_effort": "high"
        })
        
        return recommendations
    
    def _calculate_potential_savings(self, 
                                  team_cost_analysis: Dict, 
                                  recommendations: List[Dict]) -> Dict:
        """Calculate potential savings from recommendations"""
        total_cost = team_cost_analysis.get("total_team_cost_zmw", 0)
        total_potential_savings = 0
        
        for rec in recommendations:
            savings_percent = rec.get("potential_savings_percent", 0)
            potential_savings = total_cost * (savings_percent / 100)
            rec["potential_savings_zmw"] = potential_savings
            total_potential_savings += potential_savings
        
        return {
            "total_potential_savings_zmw": total_potential_savings,
            "savings_percentage": (total_potential_savings / total_cost * 100) if total_cost > 0 else 0,
            "recommendation_breakdown": recommendations
        }
    
    def _calculate_efficiency_score(self, efficiency_metrics: Dict) -> float:
        """Calculate overall efficiency score (0-100)"""
        score = 100.0
        
        # Penalty for high overtime
        overtime_percentage = efficiency_metrics.get("overtime_percentage", 0)
        if overtime_percentage > 15:
            score -= min(30, (overtime_percentage - 15) * 2)
        
        # Penalty for high cost per hour
        avg_cost_per_hour = efficiency_metrics.get("average_cost_per_hour", 0)
        if avg_cost_per_hour > 100:  # ZMW threshold
            score -= min(20, (avg_cost_per_hour - 100) * 0.2)
        
        # Bonus for low overtime
        if overtime_percentage < 10:
            score += 10
        
        return max(0, min(100, score))
    
    def compare_labor_strategies(self, 
                              current_schedule: Dict, 
                              alternative_strategies: List[Dict]) -> Dict:
        """
        Compare current labor strategy with alternatives
        """
        current_analysis = self.analyze_labor_efficiency(current_schedule)
        
        strategy_comparisons = []
        for strategy in alternative_strategies:
            strategy_analysis = self.analyze_labor_efficiency(strategy)
            strategy_comparisons.append({
                "strategy_name": strategy.get("name", "Alternative"),
                "analysis": strategy_analysis,
                "cost_difference": strategy_analysis.get("efficiency_metrics", {}).get("total_labor_cost_zmw", 0) - 
                                current_analysis.get("efficiency_metrics", {}).get("total_labor_cost_zmw", 0),
                "efficiency_improvement": strategy_analysis.get("overall_efficiency_score", 0) - 
                                        current_analysis.get("overall_efficiency_score", 0)
            })
        
        # Sort by cost savings
        strategy_comparisons.sort(key=lambda x: x["cost_difference"])
        
        return {
            "current_strategy": current_analysis,
            "alternative_strategies": strategy_comparisons,
            "best_alternative": strategy_comparisons[0] if strategy_comparisons else None,
            "recommendation": self._generate_strategy_recommendation(current_analysis, strategy_comparisons)
        }
    
    def _generate_strategy_recommendation(self, 
                                      current_analysis: Dict, 
                                      alternatives: List[Dict]) -> Dict:
        """Generate strategy recommendation based on comparison"""
        if not alternatives:
            return {"recommendation": "No alternatives available", "confidence": 0}
        
        best_alternative = alternatives[0]
        current_score = current_analysis.get("overall_efficiency_score", 0)
        best_score = best_alternative.get("analysis", {}).get("overall_efficiency_score", 0)
        cost_savings = -best_alternative.get("cost_difference", 0)  # Negative means savings
        
        if best_score > current_score + 10 and cost_savings > 1000:
            return {
                "recommendation": f"Adopt {best_alternative['strategy_name']} strategy",
                "confidence": "high",
                "reasoning": f"Improves efficiency by {best_score - current_score:.1f} points and saves ZMW {cost_savings:.2f}"
            }
        elif best_score > current_score + 5:
            return {
                "recommendation": f"Consider {best_alternative['strategy_name']} strategy",
                "confidence": "medium",
                "reasoning": f"Improves efficiency by {best_score - current_score:.1f} points"
            }
        else:
            return {
                "recommendation": "Maintain current strategy",
                "confidence": "high",
                "reasoning": "Current strategy is already optimal"
            }
    
    def generate_labor_report(self, 
                           schedule_data: Dict, 
                           include_recommendations: bool = True) -> Dict:
        """
        Generate comprehensive labor optimization report
        """
        analysis = self.analyze_labor_efficiency(schedule_data)
        
        if "error" in analysis:
            return analysis
        
        report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "schedule_id": analysis.get("schedule_id"),
                "report_type": "labor_optimization"
            },
            "executive_summary": {
                "total_labor_cost_zmw": analysis.get("efficiency_metrics", {}).get("total_labor_cost_zmw", 0),
                "efficiency_score": analysis.get("overall_efficiency_score", 0),
                "overtime_percentage": analysis.get("efficiency_metrics", {}).get("overtime_percentage", 0),
                "potential_savings_zmw": analysis.get("potential_savings", {}).get("total_potential_savings_zmw", 0)
            },
            "detailed_analysis": analysis,
            "recommendations": analysis.get("optimization_recommendations", []) if include_recommendations else [],
            "action_items": self._generate_action_items(analysis) if include_recommendations else []
        }
        
        return report
    
    def _generate_action_items(self, analysis: Dict) -> List[Dict]:
        """Generate specific action items from analysis"""
        action_items = []
        
        recommendations = analysis.get("optimization_recommendations", [])
        for rec in recommendations:
            if rec.get("priority") == "high":
                action_items.append({
                    "action": rec.get("description"),
                    "priority": "high",
                    "timeline": "1-2 weeks",
                    "responsible": "Operations Manager",
                    "kpi": f"Reduce costs by ZMW {rec.get('potential_savings_zmw', 0):.2f}"
                })
        
        return action_items

# Test the labor optimization analyzer
if __name__ == "__main__":
    # Create sample schedule data
    sample_schedule = {
        "schedule_id": "test_schedule_001",
        "route_name": "DAR_KAPIRI",
        "start_date": "2026-02-10",
        "train_assignments": [
            {
                "train_id": 1,
                "driver_id": "driver_001",
                "hours_worked": 10.5,
                "skill_level": "advanced",
                "shift_type": "day"
            },
            {
                "train_id": 2,
                "driver_id": "driver_002",
                "hours_worked": 8.0,
                "skill_level": "intermediate",
                "shift_type": "night"
            },
            {
                "train_id": 3,
                "driver_id": "driver_003",
                "hours_worked": 12.0,
                "skill_level": "beginner",
                "shift_type": "evening"
            }
        ]
    }
    
    # Initialize analyzer
    analyzer = LaborOptimizationAnalyzer()
    
    # Generate comprehensive report
    report = analyzer.generate_labor_report(sample_schedule)
    
    print("🚆 Labor Optimization Report")
    print("=" * 50)
    
    # Executive summary
    summary = report["executive_summary"]
    print(f"Schedule ID: {report['report_metadata']['schedule_id']}")
    print(f"Total Labor Cost: ZMW {summary['total_labor_cost_zmw']:.2f}")
    print(f"Efficiency Score: {summary['efficiency_score']:.1f}/100")
    print(f"Overtime Percentage: {summary['overtime_percentage']:.1f}%")
    print(f"Potential Savings: ZMW {summary['potential_savings_zmw']:.2f}")
    print()
    
    # Recommendations
    print("Optimization Recommendations:")
    for i, rec in enumerate(report["recommendations"], 1):
        print(f"{i}. [{rec['priority'].upper()}] {rec['description']}")
        print(f"   Potential Savings: {rec['potential_savings_percent']:.0f}% (ZMW {rec['potential_savings_zmw']:.2f})")
        print(f"   Implementation Effort: {rec['implementation_effort']}")
        print()
    
    # Action items
    if report["action_items"]:
        print("High Priority Action Items:")
        for item in report["action_items"]:
            print(f"• {item['action']}")
            print(f"  Timeline: {item['timeline']} | KPI: {item['kpi']}")
            print()
