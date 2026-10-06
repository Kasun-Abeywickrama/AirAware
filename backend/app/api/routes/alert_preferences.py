"""Anonymous browser alert-preference endpoints."""

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ...services.user_features import get_alert_preference, save_alert_preference


class AlertPreferenceRequest(BaseModel):
    threshold_ug_m3: Decimal = Field(gt=0, le=2000)
    enabled: bool = True


router = APIRouter(prefix="/api/v1", tags=["Alert preferences"])


@router.get("/alert-preferences/{browser_id}", response_model=None)
def read_alert_preference(browser_id: UUID) -> JSONResponse:
    """Return a saved preference or an anonymous not-configured state."""
    result = get_alert_preference(browser_id)
    return JSONResponse(status_code=result.http_status_code, content=jsonable_encoder(result.payload))


@router.put("/alert-preferences/{browser_id}", response_model=None)
def update_alert_preference(
    browser_id: UUID, request: AlertPreferenceRequest
) -> JSONResponse:
    """Create or update an anonymous stored preference without sending notifications."""
    result = save_alert_preference(
        browser_id=browser_id,
        threshold_ug_m3=request.threshold_ug_m3,
        enabled=request.enabled,
    )
    return JSONResponse(status_code=result.http_status_code, content=jsonable_encoder(result.payload))
