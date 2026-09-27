from fastapi import FastAPI

app = FastAPI(
    title="AirAware API",
    description="Backend API for the AirAware PM2.5 decision-support application.",
    version="0.1.0",
)


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    """Return the backend liveness status."""
    return {"status": "ok"}
