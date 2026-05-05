"""Risk analysis API routes.

Endpoints for schedule risk assessment and bottleneck detection.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/risk", tags=["risk_analysis"])


class RiskIssue(BaseModel):
    """Historical risk issue record."""
    date: str
    issue_type: str
    duration_minutes: int
    description: Optional[str] = None


class RiskAnalysisRequest(BaseModel):
    """Request for risk analysis."""
    schedule_id: str = Field(..., description="Schedule identifier")
    route: str = Field(..., description="Route name")
    planned_departure: str = Field(..., description="Planned departure time (ISO format)")
    historical_issues: List[RiskIssue] = Field(default=[], description="Past issues")


class BottleneckInfo(BaseModel):
    """Identified bottleneck."""
    location: str
    type: str
    severity: str  # low, medium, high
    probability: float = Field(..., ge=0, le=1)


class RiskRecommendation(BaseModel):
    """Risk mitigation recommendation."""
    action: str
    impact: str
    priority: str  # low, medium, high


class RiskAnalysisResponse(BaseModel):
    """Risk analysis results."""
    schedule_id: str
    risk_score: float = Field(..., ge=0, le=1, description="Overall risk score (0-1)")
    risk_level: str  # low, medium, high, critical
    bottlenecks: List[BottleneckInfo]
    recommendations: List[RiskRecommendation]
    analysis_timestamp: str


def calculate_risk_score(historical_issues: List[Dict], route: str) -> float:
    """Calculate risk score based on historical issues."""
    if not historical_issues:
        return 0.3  # Base risk
    
    # Count recent issues (within last 30 days)
    recent_count = 0
    total_delay = 0
    
    for issue in historical_issues:
        try:
            issue_date = datetime.fromisoformat(issue["date"].replace('Z', '+00:00'))
            days_ago = (datetime.utcnow() - issue_date).days
            
            if days_ago <= 30:
                recent_count += 1
                total_delay += issue.get("duration_minutes", 0)
        except:
            pass
    
    # Risk factors
    frequency_risk = min(recent_count / 5, 1.0)  # Max at 5 issues
    severity_risk = min(total_delay / 300, 1.0)  # Max at 5 hours delay
    
    # Weighted combination
    risk_score = (frequency_risk * 0.4 + severity_risk * 0.6)
    return min(risk_score, 1.0)


def get_bottlenecks(route: str, risk_score: float) -> List[BottleneckInfo]:
    """Identify potential bottlenecks based on route and risk."""
    bottlenecks = []
    
    # Route-specific bottlenecks
    route_bottlenecks = {
        "DAR_KAPIRI": ["Dar_es_Salaam_Port", "Makambako_Junction", "Kapiri_Mposhi_Terminal"],
        "DAR_MBeya": ["Dar_es_Salaam_Port", "Makambako_Junction", "Mbeya_Station"],
        "KAPIRI_MBeya": ["Kapiri_Mposhi_Terminal", "Nakonde_Border", "Mbeya_Station"]
    }
    
    locations = route_bottlenecks.get(route, ["Main_Terminal", "Junction_Point"])
    
    for i, location in enumerate(locations):
        probability = min(risk_score + (i * 0.1), 0.95)
        severity = "high" if probability > 0.7 else "medium" if probability > 0.4 else "low"
        
        bottlenecks.append(BottleneckInfo(
            location=location,
            type="congestion" if i == 0 else "capacity",
            severity=severity,
            probability=round(probability, 2)
        ))
    
    return bottlenecks


def get_recommendations(risk_score: float, bottlenecks: List[BottleneckInfo]) -> List[RiskRecommendation]:
    """Generate recommendations based on risk analysis."""
    recommendations = []
    
    if risk_score > 0.7:
        recommendations.append(RiskRecommendation(
            action="Add 30-minute buffer to schedule",
            impact="Reduces delay propagation",
            priority="high"
        ))
        recommendations.append(RiskRecommendation(
            action="Pre-position backup equipment",
            impact="Enables quick response to failures",
            priority="high"
        ))
    elif risk_score > 0.4:
        recommendations.append(RiskRecommendation(
            action="Monitor weather conditions closely",
            impact="Early warning for disruptions",
            priority="medium"
        ))
    else:
        recommendations.append(RiskRecommendation(
            action="Maintain standard operations",
            impact="Baseline performance",
            priority="low"
        ))
    
    # Add bottleneck-specific recommendations
    for bottleneck in bottlenecks:
        if bottleneck.severity == "high":
            recommendations.append(RiskRecommendation(
                action=f"Avoid peak hours at {bottleneck.location}",
                impact="Reduces congestion delays",
                priority="high"
            ))
    
    return recommendations


@router.post("/analyze", response_model=RiskAnalysisResponse)
def analyze_risk(request: RiskAnalysisRequest) -> RiskAnalysisResponse:
    """
    Analyze schedule risks and identify bottlenecks.
    
    **Example:**
    ```json
    {
      "schedule_id": "sched_001",
      "route": "DAR_KAPIRI",
      "planned_departure": "2026-02-12T08:00:00",
      "historical_issues": [
        {"date": "2026-01-15", "issue_type": "delay", "duration_minutes": 45}
      ]
    }
    ```
    """
    try:
        # Calculate risk score
        risk_score = calculate_risk_score(
            [issue.dict() for issue in request.historical_issues],
            request.route
        )
        
        # Determine risk level
        if risk_score < 0.3:
            risk_level = "low"
        elif risk_score < 0.6:
            risk_level = "medium"
        elif risk_score < 0.8:
            risk_level = "high"
        else:
            risk_level = "critical"
        
        # Identify bottlenecks
        bottlenecks = get_bottlenecks(request.route, risk_score)
        
        # Generate recommendations
        recommendations = get_recommendations(risk_score, bottlenecks)
        
        return RiskAnalysisResponse(
            schedule_id=request.schedule_id,
            risk_score=round(risk_score, 2),
            risk_level=risk_level,
            bottlenecks=bottlenecks,
            recommendations=recommendations,
            analysis_timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Risk analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


@router.get("/status")
def risk_status():
    """Check risk analysis service status."""
    return {
        "service": "operational",
        "version": "1.0",
        "capabilities": [
            "risk_scoring",
            "bottleneck_detection",
            "recommendation_engine"
        ]
    }
