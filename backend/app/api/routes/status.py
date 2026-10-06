"""Public service-status endpoint."""

from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from ...services.status import get_public_status


router = APIRouter(prefix="/api/v1", tags=["Status"])


@router.get("/status", response_model=None)
def service_status() -> JSONResponse:
    """Return a safe summary of current application availability."""
    result = get_public_status()
    return JSONResponse(
        status_code=result.http_status_code,
        content=jsonable_encoder(result.payload),
    )
