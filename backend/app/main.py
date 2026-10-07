"""Main application entrypoint.

Initializes the FastAPI application, mounts API route controllers,
and defines system-level liveness and database connectivity endpoints.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from . import database
from .api.routes.status import router as status_router
from .api.routes.conditions import router as conditions_router
from .api.routes.forecasts import router as forecasts_router
from .api.routes.activity_plans import router as activity_plans_router
from .api.routes.alert_preferences import router as alert_preferences_router

# Initialize FastAPI application with OpenAPI metadata
app = FastAPI(
    title="AirAware API",
    description="Backend API for the AirAware PM2.5 decision-support application.",
    version="0.1.0",
)

# Register feature-specific API routers under standard REST paths
app.include_router(status_router)             # /api/v1/status (Service health & data pipeline states)
app.include_router(conditions_router)         # /api/v1/current-conditions (Latest verified PM2.5)
app.include_router(forecasts_router)          # /api/v1/forecasts (Multi-horizon forecasts & history)
app.include_router(activity_plans_router)      # /api/v1/activity-plans (Optimal outdoor activity windows)
app.include_router(alert_preferences_router)   # /api/v1/alert-preferences (Browser alert thresholds)


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    """Lightweight liveness probe to verify that the HTTP server is responsive."""
    return {"status": "ok"}


@app.get("/health/database", tags=["System"], response_model=None)
def database_health_check():
    """Readiness probe to check if the backend can connect to PostgreSQL."""
    if database.check_database_connection():
        return {"status": "ok", "database": "connected"}

    # Return HTTP 503 if PostgreSQL cannot be reached
    return JSONResponse(
        status_code=503,
        content={"status": "unavailable", "database": "unreachable"},
    )
