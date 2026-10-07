"""
API Route: Real-time Air Quality Conditions.

Endpoint:
- GET /api/v1/current-conditions: Returns the latest approved, non-stale PM2.5 measurement.
"""

from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from ...services.public_data import get_current_conditions


router = APIRouter(prefix="/api/v1", tags=["Conditions"])


@router.get("/current-conditions", response_model=None)
def current_conditions() -> JSONResponse:
    """
    Fetch the latest valid PM2.5 observation for the active monitoring station.

    Enforces staleness guardrails: Returns HTTP 503 if data is older than the configured threshold (e.g. 180 min).

    Returns:
        JSON response with PM2.5 measurement, unit, timestamp, and station details.
    """
    result = get_current_conditions()
    return JSONResponse(status_code=result.http_status_code, content=jsonable_encoder(result.payload))
