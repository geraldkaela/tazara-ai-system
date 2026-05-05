"""Analytics and performance trends API routes.

Endpoints for dashboard analytics and performance monitoring.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


class PerformanceMetric(BaseModel):
    """Single performance metric data point."""
    date: str
    on_time_percentage: float
    avg_delay_minutes: float
    total_cargo_tons: float
    fuel_efficiency: float
    cost_per_ton_km: float


class PerformanceTrendsResponse(BaseModel):
    """Performance trends over time."""
    period_days: int
    start_date: str
    end_date: str
    metrics: List[PerformanceMetric]
    summary: Dict[str, Any]
    trends: Dict[str, str]  # improving, stable, declining


class RoutePerformance(BaseModel):
    """Performance summary for a route."""
    route: str
    on_time_rate: float
    avg_delay: float
    total_trips: int
    cargo_volume: float
    efficiency_score: float


class SystemOverview(BaseModel):
    """System-wide performance overview."""
    active_routes: int
    active_trains: int
    on_time_performance: float
    daily_cargo_volume: float
    system_efficiency: float


def generate_mock_metrics(days: int) -> List[Dict]:
    """Generate mock performance metrics for the last N days."""
    import random
    
    metrics = []
    end_date = datetime.utcnow()
    
    for i in range(days):
        date = end_date - timedelta(days=i)
        
        # Generate realistic-looking data with some variation
        base_on_time = 85.0
        base_delay = 12.0
        base_cargo = 450.0
        base_fuel = 2.8
        base_cost = 0.45
        
        # Add some randomness and trend
        trend_factor = i * 0.1  # Slight improvement over time
        randomness = random.uniform(-5, 5)
        
        metrics.append({
            "date": date.strftime("%Y-%m-%d"),
            "on_time_percentage": round(min(100, base_on_time + trend_factor + randomness), 1),
            "avg_delay_minutes": round(max(0, base_delay - trend_factor/2 + randomness/2), 1),
            "total_cargo_tons": round(base_cargo + random.uniform(-50, 50), 1),
            "fuel_efficiency": round(base_fuel + random.uniform(-0.3, 0.3), 2),
            "cost_per_ton_km": round(max(0.3, base_cost - trend_factor/100 + random.uniform(-0.05, 0.05)), 3)
        })
    
    # Reverse to get chronological order
    metrics.reverse()
    return metrics


def calculate_trends(metrics: List[Dict]) -> Dict[str, str]:
    """Calculate trends from metrics."""
    if len(metrics) < 2:
        return {k: "stable" for k in ["on_time_percentage", "avg_delay_minutes", "fuel_efficiency"]}
    
    # Split in half and compare
    mid = len(metrics) // 2
    first_half = metrics[:mid]
    second_half = metrics[mid:]
    
    trends = {}
    
    for key in ["on_time_percentage", "fuel_efficiency"]:
        first_avg = sum(m[key] for m in first_half) / len(first_half)
        second_avg = sum(m[key] for m in second_half) / len(second_half)
        
        diff = second_avg - first_avg
        if abs(diff) < 1.0:
            trends[key] = "stable"
        elif diff > 0:
            trends[key] = "improving"
        else:
            trends[key] = "declining"
    
    # For delay, lower is better
    for key in ["avg_delay_minutes"]:
        first_avg = sum(m[key] for m in first_half) / len(first_half)
        second_avg = sum(m[key] for m in second_half) / len(second_half)
        
        diff = first_avg - second_avg  # Reversed because lower is better
        if abs(diff) < 1.0:
            trends[key] = "stable"
        elif diff > 0:
            trends[key] = "improving"
        else:
            trends[key] = "declining"
    
    return trends


def generate_summary(metrics: List[Dict]) -> Dict[str, Any]:
    """Generate summary statistics from metrics."""
    if not metrics:
        return {}
    
    on_time_values = [m["on_time_percentage"] for m in metrics]
    delay_values = [m["avg_delay_minutes"] for m in metrics]
    cargo_values = [m["total_cargo_tons"] for m in metrics]
    
    return {
        "avg_on_time_performance": round(sum(on_time_values) / len(on_time_values), 1),
        "best_day": max(metrics, key=lambda x: x["on_time_percentage"])["date"],
        "worst_day": min(metrics, key=lambda x: x["on_time_percentage"])["date"],
        "avg_daily_delay": round(sum(delay_values) / len(delay_values), 1),
        "total_cargo_volume": round(sum(cargo_values), 1),
        "peak_cargo_day": max(metrics, key=lambda x: x["total_cargo_tons"])["date"]
    }


@router.get("/performance-trends", response_model=PerformanceTrendsResponse)
def get_performance_trends(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze")
) -> PerformanceTrendsResponse:
    """
    Get performance trends for the last N days.
    
    **Example:**
    ```
    GET /api/analytics/performance-trends?days=30
    ```
    """
    try:
        # Generate metrics
        metrics_data = generate_mock_metrics(days)
        
        # Convert to response model
        metrics = [PerformanceMetric(**m) for m in metrics_data]
        
        # Calculate trends
        trends = calculate_trends(metrics_data)
        
        # Generate summary
        summary = generate_summary(metrics_data)
        
        # Date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        return PerformanceTrendsResponse(
            period_days=days,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            metrics=metrics,
            summary=summary,
            trends=trends
        )
        
    except Exception as e:
        logger.error(f"Performance trends query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")


@router.get("/routes", response_model=List[RoutePerformance])
def get_route_performance():
    """Get performance summary for all routes."""
    routes = [
        RoutePerformance(
            route="DAR_KAPIRI",
            on_time_rate=87.5,
            avg_delay=8.2,
            total_trips=156,
            cargo_volume=45230.5,
            efficiency_score=82.3
        ),
        RoutePerformance(
            route="DAR_MBeya", 
            on_time_rate=84.2,
            avg_delay=12.5,
            total_trips=98,
            cargo_volume=28450.0,
            efficiency_score=78.5
        ),
        RoutePerformance(
            route="KAPIRI_MBeya",
            on_time_rate=89.1,
            avg_delay=6.8,
            total_trips=72,
            cargo_volume=18520.3,
            efficiency_score=85.7
        )
    ]
    return routes


@router.get("/overview", response_model=SystemOverview)
def get_system_overview():
    """Get system-wide performance overview."""
    return SystemOverview(
        active_routes=3,
        active_trains=8,
        on_time_performance=86.7,
        daily_cargo_volume=1250.5,
        system_efficiency=82.1
    )


@router.get("/status")
def analytics_status():
    """Check analytics service status."""
    return {
        "service": "operational",
        "version": "1.0",
        "data_sources": [
            "train_operations",
            "cargo_tracking",
            "schedule_performance"
        ],
        "last_updated": datetime.utcnow().isoformat()
    }
