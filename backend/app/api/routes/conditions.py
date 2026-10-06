"""Public current-condition endpoint."""

from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from ...services.public_data import get_current_conditions


router = APIRouter(prefix="/api/v1", tags=["Conditions"])


@router.get("/current-conditions", response_model=None)
def current_conditions() -> JSONResponse:
    """Return the latest fresh approved PM2.5 reading."""
    result = get_current_conditions()
    return JSONResponse(status_code=result.http_status_code, content=jsonable_encoder(result.payload))
