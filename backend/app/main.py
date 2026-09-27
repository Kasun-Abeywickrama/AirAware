from fastapi import FastAPI
from fastapi.responses import JSONResponse

from . import database
from .api.routes.status import router as status_router

app = FastAPI(
    title="AirAware API",
    description="Backend API for the AirAware PM2.5 decision-support application.",
    version="0.1.0",
)
app.include_router(status_router)


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    """Return the backend liveness status."""
    return {"status": "ok"}


@app.get("/health/database", tags=["System"], response_model=None)
def database_health_check():
    """Return whether the application can reach PostgreSQL."""
    if database.check_database_connection():
        return {"status": "ok", "database": "connected"}

    return JSONResponse(
        status_code=503,
        content={"status": "unavailable", "database": "unreachable"},
    )
