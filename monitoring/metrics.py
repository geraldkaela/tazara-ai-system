"""
Monitoring and Metrics Module for TAZARA AI System
Provides Prometheus metrics, health checks, and performance monitoring
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import FastAPI, Request, Response
from fastapi.middleware import Middleware
from fastapi.middleware.base import BaseHTTPMiddleware
import time
import psutil
import asyncio
from typing import Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Prometheus Metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Active database connections'
)

SYSTEM_CPU_USAGE = Gauge(
    'system_cpu_usage_percent',
    'System CPU usage percentage'
)

SYSTEM_MEMORY_USAGE = Gauge(
    'system_memory_usage_percent',
    'System memory usage percentage'
)

RAILWAY_METRICS = Gauge(
    'railway_operational_metrics',
    'Railway operational metrics',
    ['metric_type', 'route']
)

SCHEDULE_CREATION_COUNT = Counter(
    'schedule_creation_total',
    'Total schedules created',
    ['status', 'ai_type']
)

ALERT_GENERATION_COUNT = Counter(
    'alert_generation_total',
    'Total alerts generated',
    ['severity', 'type']
)

class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware to track HTTP requests and system metrics"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Update metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code
        ).inc()
        
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        return response

class SystemMetricsCollector:
    """Collects system and application metrics"""
    
    def __init__(self):
        self.is_running = False
        self.collection_task = None
    
    async def start_collection(self):
        """Start collecting system metrics"""
        if not self.is_running:
            self.is_running = True
            self.collection_task = asyncio.create_task(self._collect_metrics())
            logger.info("📊 Started system metrics collection")
    
    async def stop_collection(self):
        """Stop collecting system metrics"""
        if self.is_running:
            self.is_running = False
            if self.collection_task:
                self.collection_task.cancel()
                try:
                    await self.collection_task
                except asyncio.CancelledError:
                    pass
            logger.info("🛑 Stopped system metrics collection")
    
    async def _collect_metrics(self):
        """Collect system metrics periodically"""
        while self.is_running:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                SYSTEM_CPU_USAGE.set(cpu_percent)
                
                # Memory usage
                memory = psutil.virtual_memory()
                SYSTEM_MEMORY_USAGE.set(memory.percent)
                
                # Active connections (placeholder - would need actual DB connection monitoring)
                ACTIVE_CONNECTIONS.set(10)  # Example value
                
                # Collect railway-specific metrics
                await self._collect_railway_metrics()
                
                # Sleep for 30 seconds
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
                await asyncio.sleep(30)
    
    async def _collect_railway_metrics(self):
        """Collect railway-specific operational metrics"""
        try:
            # This would connect to your database to get real metrics
            # For now, setting example values
            RAILWAY_METRICS.labels(metric_type='cargo_delivered', route='DAR_KAPIRI').set(1500)
            RAILWAY_METRICS.labels(metric_type='trains_deployed', route='DAR_KAPIRI').set(6)
            RAILWAY_METRICS.labels(metric_type='efficiency', route='DAR_KAPIRI').set(85.5)
            
        except Exception as e:
            logger.error(f"Error collecting railway metrics: {e}")

class HealthChecker:
    """Health check system for application components"""
    
    def __init__(self):
        self.checks = {}
    
    def register_check(self, name: str, check_func):
        """Register a health check function"""
        self.checks[name] = check_func
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all registered health checks"""
        results = {}
        overall_healthy = True
        
        for name, check_func in self.checks.items():
            try:
                result = await check_func()
                results[name] = {
                    "status": "healthy" if result else "unhealthy",
                    "timestamp": datetime.now().isoformat(),
                    "details": result if isinstance(result, dict) else {}
                }
                if not result:
                    overall_healthy = False
            except Exception as e:
                results[name] = {
                    "status": "error",
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e)
                }
                overall_healthy = False
        
        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "checks": results
        }

# Health check functions
async def check_database_health() -> bool:
    """Check database connectivity"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='localhost',
            database='tazara_multi_route',
            user='tazara',
            password='tazara123',
            connect_timeout=5
        )
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

async def check_redis_health() -> bool:
    """Check Redis connectivity"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, password='redis123')
        r.ping()
        return True
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False

async def check_file_system_health() -> bool:
    """Check file system accessibility"""
    try:
        import os
        # Check if we can write to logs directory
        test_file = "/tmp/health_check_test"
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        return True
    except Exception as e:
        logger.error(f"File system health check failed: {e}")
        return False

async def check_ai_models_health() -> bool:
    """Check if AI models are accessible"""
    try:
        import os
        # Check if model files exist
        model_path = "reinforcement_rl/models"
        if os.path.exists(model_path):
            return True
        return False
    except Exception as e:
        logger.error(f"AI models health check failed: {e}")
        return False

# Initialize monitoring components
metrics_collector = SystemMetricsCollector()
health_checker = HealthChecker()

# Register health checks
health_checker.register_check("database", check_database_health)
health_checker.register_check("redis", check_redis_health)
health_checker.register_check("file_system", check_file_system_health)
health_checker.register_check("ai_models", check_ai_models_health)

# Metrics tracking functions
def track_schedule_creation(status: str, ai_type: str):
    """Track schedule creation metrics"""
    SCHEDULE_CREATION_COUNT.labels(status=status, ai_type=ai_type).inc()

def track_alert_generation(severity: str, alert_type: str):
    """Track alert generation metrics"""
    ALERT_GENERATION_COUNT.labels(severity=severity, type=alert_type).inc()

def update_railway_metrics(metric_type: str, route: str, value: float):
    """Update railway operational metrics"""
    RAILWAY_METRICS.labels(metric_type=metric_type, route=route).set(value)

def get_metrics_summary() -> Dict[str, Any]:
    """Get summary of current metrics"""
    try:
        # System metrics
        cpu_usage = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        
        return {
            "system": {
                "cpu_usage_percent": cpu_usage,
                "memory_usage_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_usage_percent": psutil.disk_usage('/').percent
            },
            "application": {
                "active_connections": 10,  # Would get from actual DB
                "uptime_hours": time.time() / 3600,  # Would track actual uptime
                "last_request_time": datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error getting metrics summary: {e}")
        return {"error": str(e)}

# FastAPI integration
def add_monitoring_to_app(app: FastAPI):
    """Add monitoring middleware and endpoints to FastAPI app"""
    
    # Add monitoring middleware
    app.add_middleware(MonitoringMiddleware)
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return await health_checker.run_all_checks()
    
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        return Response(
            generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )
    
    @app.get("/metrics/summary")
    async def metrics_summary():
        """Metrics summary endpoint"""
        return get_metrics_summary()
    
    # Start metrics collection on startup
    @app.on_event("startup")
    async def startup_event():
        await metrics_collector.start_collection()
    
    @app.on_event("shutdown")
    async def shutdown_event():
        await metrics_collector.stop_collection()

# Example usage
if __name__ == "__main__":
    # Test the monitoring system
    async def test_monitoring():
        # Start metrics collection
        await metrics_collector.start_collection()
        
        # Track some example metrics
        track_schedule_creation("success", "deep_rl")
        track_alert_generation("warning", "efficiency")
        update_railway_metrics("cargo_delivered", "DAR_KAPIRI", 1500)
        
        # Get health status
        health = await health_checker.run_all_checks()
        print("Health status:", health)
        
        # Get metrics summary
        summary = get_metrics_summary()
        print("Metrics summary:", summary)
        
        # Stop collection
        await metrics_collector.stop_collection()
    
    asyncio.run(test_monitoring())
