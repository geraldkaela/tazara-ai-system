from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, Response
from api.middleware.auth_middleware import add_auth_middleware

from api.routes.health import router as health_router
from api.routes.upload import router as upload_router
from api.routes.evaluate import router as evaluate_router
from api.routes.compare import router as compare_router
from api.routes.alerts import router as alerts_router
from api.routes.multi_route import router
from api.routes.predictive_analytics import router as predictive_analytics_router
from api.routes.analytics_dashboard import router as analytics_dashboard_router
from api.routes.risk_analysis import router as risk_analysis_router
from api.routes.labor_optimization import router as labor_optimization_router
from api.routes.analytics import router as analytics_router
from api.routes.config import router as config_router
from api.routes.simulation import router as simulation_router
from api.routes.workflow import router as workflow_router
from api.auth.auth import router as auth_router
from api.routes.priority_simple import router as priority_queue_router
from api.routes.priority_debug import router as priority_debug_router
from api.routes.priority_auto_scheduler import router as priority_auto_scheduler_router

# -------------------------------------------------
# APP INITIALIZATION
# -------------------------------------------------
app = FastAPI(
    title="TAZARA AI Scheduling System",
    description=(
        "AI-powered railway scheduling and decision support system. "
        "Supports baseline scheduling, reinforcement learning, "
        "audit logging, and external data ingestion."
    ),
    version="3.0.0"
)

# -------------------------------------------------
# CORS (for future UI / dashboard)
# -------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten later for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add authentication middleware
app = add_auth_middleware(app)

# -------------------------------------------------
# STATIC FILES (New Dashboard)
# -------------------------------------------------
app.mount("/dashboard", StaticFiles(directory="dashboard/static"), name="dashboard")

# -------------------------------------------------
# ROUTERS
# -------------------------------------------------
app.include_router(auth_router, tags=["Authentication"])
app.include_router(health_router, prefix="/health", tags=["Health"])
app.include_router(upload_router, prefix="/upload", tags=["Upload"])
app.include_router(evaluate_router, prefix="/evaluate", tags=["Evaluate"])
app.include_router(compare_router, prefix="/compare", tags=["Compare"])
app.include_router(alerts_router, prefix="/alerts", tags=["Alerts"])
app.include_router(router, prefix="/multi-route", tags=["Multi-Route"])
app.include_router(predictive_analytics_router, tags=["Forecasting"])
app.include_router(analytics_dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(risk_analysis_router, tags=["Risk Analysis"])
app.include_router(labor_optimization_router, tags=["Labor Optimization"])
app.include_router(analytics_router, tags=["Analytics"])
app.include_router(config_router, prefix="/api/config", tags=["Configuration"])
app.include_router(simulation_router)
app.include_router(workflow_router, prefix="/api/workflow", tags=["Workflow"])
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(priority_queue_router, prefix="/priority", tags=["Priority Queue"])
app.include_router(priority_debug_router, prefix="/priority", tags=["Priority Debug"])
app.include_router(priority_auto_scheduler_router, prefix="/priority", tags=["Priority Auto-Scheduler"])

# -------------------------------------------------
# AUTHENTICATION MIDDLEWARE
# -------------------------------------------------
add_auth_middleware(app)

# -------------------------------------------------
# ROOT ENDPOINT
# -------------------------------------------------
@app.get("/")
def root():
    return RedirectResponse(url="/dashboard/index.html")

# -------------------------------------------------
# SYSTEM METADATA (Industry-style endpoint)
# -------------------------------------------------
@app.get("/system/info")
async def system_info():
    """Return system information and available endpoints."""
    return {
        "system": "TAZARA AI Multi-Route Scheduling System",
        "version": "2.1",
        "description": "AI-powered railway scheduling with priority queue management",
        "features": [
            "Priority-based order scheduling",
            "Multi-route optimization",
            "Real-time dashboard",
            "Alert management",
            "Auto-scheduling with AI"
        ],
        "next_targets": [
            "/dashboard/login.html",
            "/auth/token",
            "/priority/queue",
            "/priority/auto-schedule",
            "/multi-route/status",
            "/alerts/summary"
        ]
    }

@app.get("/favicon.ico")
async def favicon():
    """Return empty response for favicon requests."""
    return Response(content="", media_type="image/x-icon")
