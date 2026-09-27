"""Public saved-forecast endpoint."""

from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from ...services.public_data import get_latest_forecasts


router = APIRouter(prefix="/api/v1", tags=["Forecasts"])


@router.get("/forecasts/latest", response_model=None)
def latest_forecasts() -> JSONResponse:
    """Return the latest complete, successful forecast run."""
    result = get_latest_forecasts()
    return JSONResponse(status_code=result.http_status_code, content=jsonable_encoder(result.payload))
