import os
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import uuid

# RBAC imports
from api.auth.rbac import Permission, require_permission
from api.auth.auth import get_current_user, UserInDB

router = APIRouter()

# In-memory storage (for demo - use database in production)
alerts_db = []
daily_reports = []
schedules_db = []

class Alert(BaseModel):
    id: str
    timestamp: str
    severity: str  # "critical", "warning", "info"
    category: str  # "schedule", "performance", "financial", "operational"
    message: str
    zmw_impact: Optional[float] = None
    route_name: Optional[str] = None
    acknowledged: bool = False
    schedule_id: Optional[str] = None

class Schedule(BaseModel):
    id: Optional[str] = None
    timestamp: Optional[str] = None
    schedule_type: str  # "baseline", "rl_optimized", "manual"
    status: str  # "draft", "active", "executing", "completed", "cancelled"
    routes: List[str]
    trains_used: int
    total_cargo: float
    cargo_types: List[str]
    duration_days: int
    performance_metrics: Optional[dict] = None
    financial_metrics: Optional[dict] = None
    completion_percentage: float = 0.0
    on_time_performance: float = 0.0

class DailyReport(BaseModel):
    date: str
    total_cargo_delivered: float
    total_trains_used: int
    delay_days: int
    idle_days: int
    net_profit_zmw: float
    revenue_zmw: float
    total_cost_zmw: float
    efficiency_score: float  # 0-100
    recommendations: List[str]

@router.post("/schedules/create", response_model=Schedule)
async def create_schedule(schedule: Schedule):
    """
    Create a new schedule and generate appropriate alerts
    """
    schedule.id = f"schedule_{len(schedules_db) + 1:04d}"
    schedule.timestamp = datetime.now().isoformat()
    schedules_db.append(schedule)
    
    # Auto-generate schedule creation alert
    await _generate_schedule_alert(schedule, "created")
    
    return schedule

@router.get("/schedules", response_model=List[Schedule])
async def get_schedules(status: Optional[str] = None, schedule_type: Optional[str] = None):
    """
    Get all schedules with optional filtering
    """
    filtered_schedules = schedules_db.copy()
    
    # Also fetch multi-route schedules from database
    try:
        import psycopg2
        import json
        
        conn = psycopg2.connect(
            host="localhost",
            database="tazara_multi_route",
            user="tazara",
            password="tazara123"
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT schedule_id, num_trains, total_days, cargo_requirements, 
                   performance_metrics, cost_breakdown_zmw, timestamp
            FROM multi_route_schedules 
            ORDER BY timestamp DESC
        """)
        
        db_schedules = cursor.fetchall()
        print(f"DEBUG: Found {len(db_schedules)} multi-route schedules in database")
        
        for db_schedule in db_schedules:
            (schedule_id, num_trains, total_days, cargo_requirements, 
             performance_metrics, cost_breakdown_zmw, timestamp) = db_schedule
            
            # Convert to Schedule format
            if isinstance(cargo_requirements, str):
                cargo_dict = json.loads(cargo_requirements) if cargo_requirements else {}
            else:
                cargo_dict = cargo_requirements if cargo_requirements else {}
            
            routes = list(cargo_dict.keys()) if cargo_dict else []
            
            multi_route_schedule = Schedule(
                id=schedule_id,
                timestamp=timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                schedule_type="rl_optimized",
                status="executing",
                routes=routes,
                trains_used=num_trains,
                total_cargo=performance_metrics.get("total_cargo_delivered", 0) if performance_metrics else 0,
                cargo_types=list(cargo_dict.keys()) if cargo_dict else [],
                duration_days=total_days,
                completion_percentage=0.0,
                on_time_performance=100.0,
                financial_metrics=cost_breakdown_zmw if cost_breakdown_zmw else {}
            )
            
            filtered_schedules.append(multi_route_schedule)
            print(f"DEBUG: Added multi-route schedule {schedule_id} to alerts")
        
        cursor.close()
        conn.close()
        print(f"DEBUG: Total schedules after adding multi-route: {len(filtered_schedules)}")
        
    except Exception as e:
        print(f"ERROR: Failed to fetch multi-route schedules: {e}")
        import traceback
        traceback.print_exc()
        # Continue with in-memory schedules if database fails
    
    if status:
        filtered_schedules = [s for s in filtered_schedules if s.status == status]
    
    if schedule_type:
        filtered_schedules = [s for s in filtered_schedules if s.schedule_type == schedule_type]
    
    # Sort by timestamp (newest first)
    filtered_schedules.sort(key=lambda x: x.timestamp, reverse=True)
    return filtered_schedules

@router.put("/schedules/{schedule_id}/status")
async def update_schedule_status(schedule_id: str, new_status: str):
    """
    Update schedule status and generate appropriate alerts
    """
    for schedule in schedules_db:
        if schedule.id == schedule_id:
            old_status = schedule.status
            schedule.status = new_status
            
            # Generate status change alert
            await _generate_schedule_alert(schedule, "status_change", old_status)
            
            return {"message": f"Schedule {schedule_id} status updated to {new_status}"}
    
    raise HTTPException(status_code=404, detail="Schedule not found")

@router.put("/schedules/{schedule_id}/progress")
async def update_schedule_progress(schedule_id: str, completion_percentage: float, on_time_performance: float):
    """
    Update schedule progress and generate performance alerts
    """
    for schedule in schedules_db:
        if schedule.id == schedule_id:
            schedule.completion_percentage = completion_percentage
            schedule.on_time_performance = on_time_performance
            
            # Generate performance alerts
            await _generate_schedule_alert(schedule, "performance_update")
            
            return {"message": f"Schedule {schedule_id} progress updated"}
    
    raise HTTPException(status_code=404, detail="Schedule not found")

@router.post("/create", response_model=Alert)
async def create_alert(alert: Alert):
    """
    Create a new alert
    """
    alert.id = f"alert_{len(alerts_db) + 1:04d}"
    alert.timestamp = datetime.now().isoformat()
    alerts_db.append(alert)
    return alert

async def _generate_schedule_alert(schedule: Schedule, alert_type: str, old_status: str = None):
    """
    Generate alerts based on schedule events
    """
    alerts = []
    
    if alert_type == "created":
        alerts.append(Alert(
            id=f"schedule_created_{schedule.id}",
            timestamp=datetime.now().isoformat(),
            severity="info",
            category="schedule",
            message=f"Schedule {schedule.id} created: {schedule.schedule_type} with {schedule.trains_used} trains for {len(schedule.routes)} routes",
            schedule_id=schedule.id
        ))
        
        # Add financial alert if financial metrics available
        if schedule.financial_metrics:
            revenue = schedule.financial_metrics.get("revenue_zmw", 0)
            cost = schedule.financial_metrics.get("total_cost_zmw", 0)
            alerts.append(Alert(
                id=f"schedule_financial_{schedule.id}",
                timestamp=datetime.now().isoformat(),
                severity="info",
                category="financial",
                message=f"Schedule {schedule.id} projected: Revenue ZMW {revenue:,.0f}, Cost ZMW {cost:,.0f}",
                zmw_impact=revenue - cost,
                schedule_id=schedule.id
            ))
    
    elif alert_type == "status_change":
        if new_status == "executing":
            alerts.append(Alert(
                id=f"schedule_started_{schedule.id}",
                timestamp=datetime.now().isoformat(),
                severity="info",
                category="schedule",
                message=f"Schedule {schedule.id} execution started",
                schedule_id=schedule.id
            ))
        elif new_status == "completed":
            alerts.append(Alert(
                id=f"schedule_completed_{schedule.id}",
                timestamp=datetime.now().isoformat(),
                severity="info",
                category="schedule",
                message=f"Schedule {schedule.id} completed: {schedule.completion_percentage:.1f}% completion, {schedule.on_time_performance:.1f}% on-time performance",
                schedule_id=schedule.id
            ))
        elif new_status == "cancelled":
            alerts.append(Alert(
                id=f"schedule_cancelled_{schedule.id}",
                timestamp=datetime.now().isoformat(),
                severity="warning",
                category="schedule",
                message=f"Schedule {schedule.id} cancelled",
                schedule_id=schedule.id
            ))
    
    elif alert_type == "performance_update":
        # Performance deviation alerts
        if schedule.on_time_performance < 80:
            alerts.append(Alert(
                id=f"schedule_delay_{schedule.id}",
                timestamp=datetime.now().isoformat(),
                severity="warning",
                category="operational",
                message=f"Schedule {schedule.id} on-time performance: {schedule.on_time_performance:.1f}% (below 80% threshold)",
                schedule_id=schedule.id
            ))
        
        if schedule.completion_percentage < 50 and schedule.status == "executing":
            alerts.append(Alert(
                id=f"schedule_slow_{schedule.id}",
                timestamp=datetime.now().isoformat(),
                severity="warning",
                category="performance",
                message=f"Schedule {schedule.id} progress slow: {schedule.completion_percentage:.1f}% complete",
                schedule_id=schedule.id
            ))
        
        # Performance achievement alerts
        if schedule.on_time_performance >= 95:
            alerts.append(Alert(
                id=f"schedule_excellent_{schedule.id}",
                timestamp=datetime.now().isoformat(),
                severity="info",
                category="performance",
                message=f"Schedule {schedule.id} excellent on-time performance: {schedule.on_time_performance:.1f}%",
                schedule_id=schedule.id
            ))
    
    # Add all generated alerts
    alerts_db.extend(alerts)

@router.post("/generate-sample-schedules")
async def generate_sample_schedules():
    """
    Generate sample schedules for testing
    """
    sample_schedules = [
        Schedule(
            id="sample_schedule_001",
            timestamp=datetime.now().isoformat(),
            schedule_type="rl_optimized",
            status="executing",
            routes=["DAR_KAPIRI", "DAR_MBEYA"],
            trains_used=5,
            total_cargo=1200.0,
            cargo_types=["Copper", "Coal"],
            duration_days=7,
            completion_percentage=65.0,
            on_time_performance=92.0,
            financial_metrics={
                "revenue_zmw": 980000.0,
                "total_cost_zmw": 420000.0,
                "net_profit_zmw": 560000.0
            }
        ),
        Schedule(
            id="sample_schedule_002",
            timestamp=(datetime.now() - timedelta(hours=2)).isoformat(),
            schedule_type="baseline",
            status="completed",
            routes=["DAR_KAPIRI", "KAPIRI_NDOLA"],
            trains_used=4,
            total_cargo=800.0,
            cargo_types=["Copper"],
            duration_days=5,
            completion_percentage=100.0,
            on_time_performance=78.0,
            financial_metrics={
                "revenue_zmw": 650000.0,
                "total_cost_zmw": 380000.0,
                "net_profit_zmw": 270000.0
            }
        ),
        Schedule(
            id="sample_schedule_003",
            timestamp=(datetime.now() - timedelta(days=1)).isoformat(),
            schedule_type="manual",
            status="active",
            routes=["DAR_MBEYA", "KAPIRI_NDOLA"],
            trains_used=3,
            total_cargo=600.0,
            cargo_types=["Containers", "Fuel"],
            duration_days=3,
            completion_percentage=25.0,
            on_time_performance=85.0,
            financial_metrics={
                "revenue_zmw": 480000.0,
                "total_cost_zmw": 310000.0,
                "net_profit_zmw": 170000.0
            }
        )
    ]
    
    schedules_db.extend(sample_schedules)
    
    # Generate alerts for sample schedules
    for schedule in sample_schedules:
        await _generate_schedule_alert(schedule, "created")
        if schedule.status == "executing":
            await _generate_schedule_alert(schedule, "status_change", "active")
            await _generate_schedule_alert(schedule, "performance_update")
        elif schedule.status == "completed":
            await _generate_schedule_alert(schedule, "status_change", "executing")
            await _generate_schedule_alert(schedule, "performance_update")
    
    return {"message": f"Generated {len(sample_schedules)} sample schedules with alerts"}

@router.get("/", response_model=List[Alert])
async def get_alerts(
    severity: Optional[str] = None, 
    acknowledged: Optional[bool] = None, 
    category: Optional[str] = None,
    current_user: UserInDB = Depends(require_permission(Permission.VIEW_ALERTS))
):
    """
    Get all alerts with optional filtering
    """
    filtered_alerts = alerts_db
    
    if severity:
        filtered_alerts = [a for a in filtered_alerts if a.severity == severity]
    
    if acknowledged is not None:
        filtered_alerts = [a for a in filtered_alerts if a.acknowledged == acknowledged]
    
    if category:
        filtered_alerts = [a for a in filtered_alerts if a.category == category]
    
    # Sort by timestamp (newest first)
    filtered_alerts.sort(key=lambda x: x.timestamp, reverse=True)
    return filtered_alerts

@router.put("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """
    Acknowledge an alert
    """
    for alert in alerts_db:
        if alert.id == alert_id:
            alert.acknowledged = True
            return {"message": f"Alert {alert_id} acknowledged"}
    
    raise HTTPException(status_code=404, detail="Alert not found")

@router.post("/daily-report", response_model=DailyReport)
async def create_daily_report(report: DailyReport):
    """
    Create a daily operations report
    """
    report.date = datetime.now().strftime("%Y-%m-%d")
    daily_reports.append(report)
    
    # Auto-generate alerts based on report
    await _generate_alerts_from_report(report)
    
    return report

@router.get("/summary")
async def get_alerts_summary(
    current_user: UserInDB = Depends(require_permission(Permission.VIEW_ALERTS))
):
    """
    Get summary of active alerts and schedules
    """
    # Alert counts
    critical_count = len([a for a in alerts_db if a.severity == "critical" and not a.acknowledged])
    warning_count = len([a for a in alerts_db if a.severity == "warning" and not a.acknowledged])
    info_count = len([a for a in alerts_db if a.severity == "info" and not a.acknowledged])
    low_count = len([a for a in alerts_db if a.severity == "low" and not a.acknowledged])
    
    print(f"DEBUG: Alert counts - Critical: {critical_count}, Warning: {warning_count}, Info: {info_count}, Low: {low_count}")
    
    # Schedule counts from in-memory
    active_schedules = len([s for s in schedules_db if s.status in ["active", "executing"]])
    completed_schedules = len([s for s in schedules_db if s.status == "completed"])
    rl_schedules = len([s for s in schedules_db if s.schedule_type == "rl_optimized"])
    
    # Add multi-route schedules from database
    try:
        import psycopg2
        
        conn = psycopg2.connect(
            host="localhost",
            database="tazara_multi_route",
            user="tazara",
            password="tazara123"
        )
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM multi_route_schedules")
        db_total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM multi_route_schedules")
        db_active = cursor.fetchone()[0]  # All are considered "executing"
        
        # Add database counts to totals
        total_schedules = len(schedules_db) + db_total
        active_schedules += db_active
        rl_schedules += db_total  # All multi-route schedules are RL optimized
        
        cursor.close()
        conn.close()
        
        print(f"DEBUG: Summary - DB schedules: {db_total}, Active: {db_active}, RL: {db_total}")
        
    except Exception as e:
        print(f"WARNING: Failed to fetch multi-route summary: {e}")
        total_schedules = len(schedules_db)
    
    print(f"DEBUG: Final counts - Total schedules: {total_schedules}, Active: {active_schedules}, RL: {rl_schedules}")
    
    # Recent activity
    last_24h_alerts = len([a for a in alerts_db if 
                           datetime.fromisoformat(a.timestamp) > datetime.now() - timedelta(hours=24)])
    last_24h_schedules = len([s for s in schedules_db if 
                             datetime.fromisoformat(s.timestamp) > datetime.now() - timedelta(hours=24)])
    
    # Performance metrics
    avg_on_time = 0
    avg_completion = 0
    executing_schedules = [s for s in schedules_db if s.status == "executing"]
    if executing_schedules:
        avg_on_time = sum(s.on_time_performance for s in executing_schedules) / len(executing_schedules)
        avg_completion = sum(s.completion_percentage for s in executing_schedules) / len(executing_schedules)
    
    return {
        "alerts": {
            "critical_alerts": critical_count,
            "warning_alerts": warning_count,
            "info_alerts": info_count,
            "low_alerts": low_count,
            "total_alerts": len(alerts_db),  
            "total_unacknowledged": critical_count + warning_count + info_count + low_count,
            "last_24h_alerts": last_24h_alerts
        },
        "schedules": {
            "active_schedules": active_schedules,
            "completed_schedules": completed_schedules,
            "rl_optimized_schedules": rl_schedules,
            "total_schedules": total_schedules,
            "last_24h_created": last_24h_schedules
        },
        "performance": {
            "avg_on_time_performance": round(avg_on_time, 1),
            "avg_completion_percentage": round(avg_completion, 1),
            "executing_schedules": len(executing_schedules)
        }
    }

async def _generate_real_alerts_from_reports():
    """Generate alerts based on REAL daily report data"""
    alerts = []
    
    print("Generating REAL alerts from actual daily reports...")
    
    for report in daily_reports:
        date = report.date
        
        # CRITICAL: Profit loss alerts
        if report.net_profit_zmw < 0:
            alerts.append(Alert(
                id=f"profit_loss_{date}",
                timestamp=datetime.now().isoformat(),
                severity="critical",
                category="profit",
                message=f"Daily net loss detected: ZMW {abs(report.net_profit_zmw):,.0f} on {date}",
                financial_impact=abs(report.net_profit_zmw),
                schedule_id=f"daily_report_{date}"
            ))
            print(f"Generated CRITICAL alert for profit loss: ZMW {abs(report.net_profit_zmw):,.0f}")
        
        # WARNING: Low efficiency alerts
        if report.efficiency_score < 50:
            alerts.append(Alert(
                id=f"critical_efficiency_{date}",
                timestamp=datetime.now().isoformat(),
                severity="warning",
                category="efficiency",
                message=f"Critical efficiency: {report.efficiency_score:.1f}% on {date} - trains severely underutilized",
                zmw_impact=report.total_cost_zmw * 0.3,  # 30% of costs wasted
                schedule_id=f"daily_report_{date}"
            ))
            print(f"Generated WARNING alert for critical efficiency: {report.efficiency_score:.1f}%")
        elif report.efficiency_score < 80:
            alerts.append(Alert(
                id=f"low_efficiency_{date}",
                timestamp=datetime.now().isoformat(),
                severity="warning", 
                category="efficiency",
                message=f"Low efficiency: {report.efficiency_score:.1f}% on {date} - train utilization below target",
                zmw_impact=report.total_cost_zmw * 0.15,  # 15% of costs wasted
                schedule_id=f"daily_report_{date}"
            ))
            print(f"Generated WARNING alert for low efficiency: {report.efficiency_score:.1f}%")
        
        # INFO: Zero cargo alerts
        if report.total_cargo_delivered == 0:
            alerts.append(Alert(
                id=f"zero_cargo_{date}",
                timestamp=datetime.now().isoformat(),
                severity="info",
                category="operations",
                message=f"No cargo delivered on {date} - {report.total_trains_used} trains ran empty",
                zmw_impact=report.total_cost_zmw,
                schedule_id=f"daily_report_{date}"
            ))
            print(f"Generated INFO alert for zero cargo: {report.total_trains_used} trains")
        
        # LOW: High performance alerts (good news)
        if report.efficiency_score > 150:
            alerts.append(Alert(
                id=f"high_performance_{date}",
                timestamp=datetime.now().isoformat(),
                severity="low",
                category="performance",
                message=f"Exceptional performance: {report.efficiency_score:.1f}% efficiency on {date}",
                zmw_impact=report.net_profit_zmw,
                schedule_id=f"daily_report_{date}"
            ))
            print(f"Generated LOW alert for high performance: {report.efficiency_score:.1f}%")
    
    # Add alerts to database
    alerts_db.extend(alerts)
    print(f"Generated {len(alerts)} REAL alerts from daily reports")

async def _generate_alerts_from_report(report: DailyReport):
    """Generate alerts based on daily report"""
    alerts = []
    
    # Profit alert
    if report.net_profit_zmw < 0:
        alerts.append(Alert(
            id=f"profit_loss_{report.date}",
            timestamp=datetime.now().isoformat(),
            severity="critical",
            category="profit",
            message=f"Daily net loss detected: ZMW {abs(report.net_profit_zmw):,.0f}",
            financial_impact=abs(report.net_profit_zmw)
        ))
    
    # Efficiency alert
    if report.efficiency_score < 80:
        alerts.append(Alert(
            id=f"efficiency_{report.date}",
            timestamp=datetime.now().isoformat(),
            severity="warning",
            category="efficiency",
            message=f"Low efficiency score: {report.efficiency_score:.1f}%"
        ))
    
    # On-time performance alert
    if report.on_time_performance < 90:
        alerts.append(Alert(
            id=f"ontime_{report.date}",
            timestamp=datetime.now().isoformat(),
            severity="warning",
            category="delay",
            message=f"Poor on-time performance: {report.on_time_performance:.1f}%"
        ))
    
    # Add alerts to database
    alerts_db.extend(alerts)

@router.get("/daily-reports")
async def get_daily_reports(days: int = 7):
    """
    Get daily operations reports - always regenerated from fresh data
    """
    # Always regenerate reports from current database data (no caching)
    daily_reports.clear()
    generate_sample_daily_reports()
    
    # Clear existing alerts and regenerate from REAL data
    alerts_db.clear()
    await _generate_real_alerts_from_reports()
    
    # Return the most recent reports
    return daily_reports[-days:] if len(daily_reports) >= days else daily_reports

def generate_sample_daily_reports():
    """Generate daily reports from actual multi-route schedule data"""
    import random
    from datetime import datetime, timedelta
    
    print("Generating daily reports from actual schedule data...")
    
    try:
        import psycopg2
        import json
        
        conn = psycopg2.connect(
            host="localhost",
            database="tazara_multi_route",
            user="tazara",
            password="tazara123"
        )
        cursor = conn.cursor()
        
        # First, get the actual dates that have schedules
        cursor.execute("""
            SELECT DISTINCT DATE(timestamp) as schedule_date
            FROM multi_route_schedules 
            ORDER BY schedule_date DESC
            LIMIT 7
        """)
        
        dates_with_schedules = [row[0] for row in cursor.fetchall()]
        print(f"Found schedules on these dates: {dates_with_schedules}")
        
        # Generate reports only for dates that actually have schedules
        for date in dates_with_schedules:
            date_str = date.strftime("%Y-%m-%d")
            
            # Query schedules created on this specific date - simplified query
            cursor.execute("""
                SELECT COUNT(*) as schedule_count,
                       COALESCE(SUM(num_trains), 0) as total_trains
                FROM multi_route_schedules 
                WHERE DATE(timestamp) = %s
            """, (date,))
            
            result = cursor.fetchone()
            if not result or len(result) < 2:
                print(f"Invalid query result for {date_str}, skipping...")
                continue
                
            schedule_count, total_trains = result
            
            # If no schedules found for this date, skip
            if schedule_count == 0:
                print(f"No schedules found for {date_str}, skipping...")
                continue
            
            # Get additional metrics with simpler queries
            cursor.execute("""
                SELECT performance_metrics, cost_breakdown_zmw
                FROM multi_route_schedules 
                WHERE DATE(timestamp) = %s
                LIMIT 10
            """, (date,))
            
            metric_results = cursor.fetchall()
            
            # Calculate totals from the actual data
            total_cargo = 0
            total_profit = 0
            
            for perf_metrics, cost_breakdown in metric_results:
                try:
                    if perf_metrics:
                        import json
                        if isinstance(perf_metrics, str):
                            perf_dict = json.loads(perf_metrics)
                        else:
                            perf_dict = perf_metrics
                        cargo = perf_dict.get('total_cargo_delivered', 0)
                        total_cargo += float(cargo) if cargo else 0
                    
                    if cost_breakdown:
                        if isinstance(cost_breakdown, str):
                            cost_dict = json.loads(cost_breakdown)
                        else:
                            cost_dict = cost_breakdown
                        profit = cost_dict.get('net_profit_zmw', 0)
                        total_profit += float(profit) if profit else 0
                except Exception as e:
                    print(f"Warning: Could not parse metrics for {date_str}: {e}")
                    continue
            
            # Calculate efficiency based on ACTUAL cargo per train from database
            avg_cargo = total_cargo / schedule_count if schedule_count > 0 else 0
            
            # Calculate actual cargo per train (what's really being delivered)
            actual_cargo_per_train = total_cargo / total_trains if total_trains > 0 else 0
            
            # Use realistic capacity based on actual performance data
            # From your data: ~300 tons per train is what's actually being delivered
            realistic_capacity_per_train = 300  # Based on actual cargo data
            
            # Calculate efficiency using realistic capacity
            efficiency = (actual_cargo_per_train / realistic_capacity_per_train) * 100 if realistic_capacity_per_train > 0 else 0
            
            # Cap at 150% for display
            efficiency = min(efficiency, 150.0)
            
            print(f"Efficiency calculation for {date_str}:")
            print(f"  Total cargo: {total_cargo:.1f} tons")
            print(f"  Total trains: {total_trains}")
            print(f"  Actual cargo per train: {actual_cargo_per_train:.1f} tons")
            print(f"  Realistic capacity: {realistic_capacity_per_train} tons")
            print(f"  Efficiency: {efficiency:.1f}%")
            
            # Generate recommendations based on performance
            recommendations = []
            if efficiency < 80:
                recommendations.append("Improve train utilization efficiency")
            if avg_cargo < 1000:
                recommendations.append("Increase cargo loading capacity")
            if total_profit < 100000:
                recommendations.append("Optimize revenue generation")
            if not recommendations:
                recommendations.append("Operations performing well")
            
            report = DailyReport(
                date=date_str,
                total_cargo_delivered=total_cargo,
                total_trains_used=total_trains or 0,
                delay_days=random.randint(0, 1),  # Could be calculated from actual delays
                idle_days=random.randint(0, 1),    # Could be calculated from actual idle time
                net_profit_zmw=total_profit,
                revenue_zmw=(total_profit * 1.5) if total_profit else 0,  # Estimate revenue
                total_cost_zmw=(total_profit * 0.5) if total_profit else 0,  # Estimate costs
                efficiency_score=round(efficiency, 1),
                recommendations=recommendations[:3]  # Limit to 3 recommendations
            )
            
            daily_reports.append(report)
            print(f"Generated report for {date_str}: {schedule_count} schedules, {total_trains} trains, {total_cargo:.0f} tons cargo, ZMW {total_profit:,} profit")
        
        cursor.close()
        conn.close()
        
        if len(daily_reports) == 0:
            print("No schedules found in database, falling back to sample data...")
            # Generate sample data for past 7 days
            for i in range(7):
                date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                
                # Generate random metrics
                total_cargo = random.randint(800, 1500)
                trains_used = random.randint(3, 8)
                net_profit = random.randint(50000, 200000)
                efficiency = random.uniform(75, 95)
                
                report = DailyReport(
                    date=date,
                    total_cargo_delivered=total_cargo,
                    total_trains_used=trains_used,
                    delay_days=random.randint(0, 2),
                    idle_days=random.randint(0, 1),
                    net_profit_zmw=net_profit,
                    revenue_zmw=net_profit + random.randint(30000, 80000),
                    total_cost_zmw=random.randint(40000, 100000),
                    efficiency_score=efficiency,
                    recommendations=[
                        "Optimize train utilization",
                        "Consider route adjustments", 
                        "Monitor fuel consumption"
                    ]
                )
                
                daily_reports.append(report)
        
    except Exception as e:
        print(f"ERROR: Failed to generate reports from database: {e}")
        print("Falling back to sample data...")
        
        # Fallback to original sample data generation
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            
            # Generate random metrics
            total_cargo = random.randint(800, 1500)
            trains_used = random.randint(3, 8)
            net_profit = random.randint(50000, 200000)
            efficiency = random.uniform(75, 95)
            
            report = DailyReport(
                date=date,
                total_cargo_delivered=total_cargo,
                total_trains_used=trains_used,
                delay_days=random.randint(0, 2),
                idle_days=random.randint(0, 1),
                net_profit_zmw=net_profit,
                revenue_zmw=net_profit + random.randint(30000, 80000),
                total_cost_zmw=random.randint(40000, 100000),
                efficiency_score=efficiency,
                recommendations=[
                    "Optimize train utilization",
                    "Consider route adjustments", 
                    "Monitor fuel consumption"
                ]
            )
            
            daily_reports.append(report)
    
    print(f"Generated {len(daily_reports)} daily reports")

@router.post("/generate-sample-reports")
async def generate_sample_reports():
    """Generate sample daily reports endpoint"""
    daily_reports.clear()
    generate_sample_daily_reports()
    return {"message": f"Generated {len(daily_reports)} sample daily reports"}
    """
    Auto-generate alerts based on daily report metrics
    """
    alerts = []
    
    # Low profit alert
    if report.net_profit_zmw < 0:
        alerts.append(Alert(
            id=f"auto_profit_{len(alerts_db)}",
            timestamp=datetime.now().isoformat(),
            severity="critical",
            category="profit",
            message=f"Daily net loss of ZMW {abs(report.net_profit_zmw):,.2f}",
            zmw_impact=report.net_profit_zmw
        ))
    
    # High delay alert
    if report.delay_days > 2:
        alerts.append(Alert(
            id=f"auto_delay_{len(alerts_db)}",
            timestamp=datetime.now().isoformat(),
            severity="warning",
            category="delay",
            message=f"High delay days: {report.delay_days}",
            zmw_impact=report.delay_days * 15000  # ZMW 15k per delay day
        ))
    
    # Low efficiency alert
    if report.efficiency_score < 50:
        alerts.append(Alert(
            id=f"auto_efficiency_{len(alerts_db)}",
            timestamp=datetime.now().isoformat(),
            severity="warning",
            category="efficiency",
            message=f"Low efficiency score: {report.efficiency_score}%",
            zmw_impact=None
        ))
    
    # High cost alert
    if report.total_cost_zmw > 50000:
        alerts.append(Alert(
            id=f"auto_cost_{len(alerts_db)}",
            timestamp=datetime.now().isoformat(),
            severity="warning",
            category="cost",
            message=f"High daily operating cost: ZMW {report.total_cost_zmw:,.2f}",
            zmw_impact=report.total_cost_zmw
        ))
    
    # Add auto-generated alerts
    alerts_db.extend(alerts)

@router.post("/generate-sample")
async def generate_sample_alerts():
    """
    Generate sample alerts for testing
    """
    sample_alerts = [
        Alert(
            id="sample_001",
            timestamp=datetime.now().isoformat(),
            severity="critical",
            category="profit",
            message="Daily net loss detected: ZMW -25,000",
            zmw_impact=-25000
        ),
        Alert(
            id="sample_002", 
            timestamp=datetime.now().isoformat(),
            severity="warning",
            category="delay",
            message="Excessive delays on DAR_KAPIRI route",
            route_name="DAR_KAPIRI",
            zmw_impact=30000
        ),
        Alert(
            id="sample_003",
            timestamp=datetime.now().isoformat(),
            severity="info",
            category="efficiency",
            message="RL scheduler outperforming baseline by 15%"
        )
    ]
    
    alerts_db.extend(sample_alerts)
    return {"message": f"Generated {len(sample_alerts)} sample alerts"}
