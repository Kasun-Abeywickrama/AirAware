"""Public saved-forecast endpoint."""

from fastapi import APIRouter, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from ...services.public_data import get_latest_forecasts
from ...services.user_features import get_forecast_history


router = APIRouter(prefix="/api/v1", tags=["Forecasts"])


@router.get("/forecasts/latest", response_model=None)
def latest_forecasts() -> JSONResponse:
    """Return the latest complete, successful forecast run."""
    result = get_latest_forecasts()
    return JSONResponse(status_code=result.http_status_code, content=jsonable_encoder(result.payload))


@router.get("/forecasts/history", response_model=None)
def forecast_history(hours: int = Query(default=72, ge=1, le=168)) -> JSONResponse:
    """Return recent approved observations and stored forecast values for charting."""
    result = get_forecast_history(hours)
    return JSONResponse(status_code=result.http_status_code, content=jsonable_encoder(result.payload))
