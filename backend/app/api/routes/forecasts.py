"""
API Route: Machine Learning Air Quality Forecasts.

Endpoints:
- GET /api/v1/forecasts/latest: Returns latest 1h, 6h, and 24h predictions with conformal uncertainty bounds and XAI factor importance.
- GET /api/v1/forecasts/history: Returns historical observation and forecast time series for frontend charts.
"""

from fastapi import APIRouter, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from ...services.public_data import get_latest_forecasts
from ...services.user_features import get_forecast_history


router = APIRouter(prefix="/api/v1", tags=["Forecasts"])


@router.get("/forecasts/latest", response_model=None)
def latest_forecasts() -> JSONResponse:
    """
    Fetch the latest multi-horizon forecast predictions (1-hour, 6-hour, and 24-hour).

    Includes:
    - Point estimates (predicted PM2.5 in ug/m3).
    - Conformal prediction lower and upper uncertainty bounds.
    - XAI feature importance breakdown (12-factor ontology) and scientific disclaimer.

    Returns:
        JSON response with 3-horizon predictions or HTTP 503 if unavailable.
    """
    result = get_latest_forecasts()
    return JSONResponse(status_code=result.http_status_code, content=jsonable_encoder(result.payload))


@router.get("/forecasts/history", response_model=None)
def forecast_history(hours: int = Query(default=72, ge=1, le=168)) -> JSONResponse:
    """
    Fetch historical PM2.5 observations and issued forecasts for the specified time window.

    Used by the frontend to render the 'Historical Trend & Model Evaluation' comparison chart.

    Args:
        hours: Past time window in hours (between 1 and 168 hours; default: 72).

    Returns:
        JSON response with arrays of historical observations and forecast points.
    """
    result = get_forecast_history(hours)
    return JSONResponse(status_code=result.http_status_code, content=jsonable_encoder(result.payload))
