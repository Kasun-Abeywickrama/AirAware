"""
API Route: System Health and Pipeline Status.

Endpoint:
- GET /api/v1/status: Returns operational status of database, PM2.5 pipeline, weather pipeline, and ML forecaster.
"""

from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from ...services.status import get_public_status


router = APIRouter(prefix="/api/v1", tags=["Status"])


@router.get("/status", response_model=None)
def service_status() -> JSONResponse:
    """
    Get current operational health status across all AirAware backend components.

    Returns:
        JSON response with system status ('available' or 'limited') and component breakdown.
    """
    result = get_public_status()
    return JSONResponse(
        status_code=result.http_status_code,
        content=jsonable_encoder(result.payload),
    )
