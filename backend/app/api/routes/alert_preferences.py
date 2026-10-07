"""
API Route: Anonymous Alert Preferences.

Endpoints:
- GET /api/v1/alert-preferences/{browser_id}: Retrieve saved PM2.5 alert threshold settings.
- PUT /api/v1/alert-preferences/{browser_id}: Create or update PM2.5 alert threshold settings.
"""

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ...services.user_features import get_alert_preference, save_alert_preference


class AlertPreferenceRequest(BaseModel):
    """
    Request model to configure alert threshold.

    Attributes:
        threshold_ug_m3: PM2.5 alert limit in ug/m3 (strictly positive up to 2000 ug/m3).
        enabled: Boolean flag to activate or deactivate the threshold alert.
    """

    threshold_ug_m3: Decimal = Field(gt=0, le=2000)
    enabled: bool = True


router = APIRouter(prefix="/api/v1", tags=["Alert preferences"])


@router.get("/alert-preferences/{browser_id}", response_model=None)
def read_alert_preference(browser_id: UUID) -> JSONResponse:
    """
    Retrieve stored alert preferences for an anonymous browser UUID.

    Args:
        browser_id: Unique anonymous client UUID.

    Returns:
        JSON response with configured threshold or default not_configured status.
    """
    result = get_alert_preference(browser_id)
    return JSONResponse(status_code=result.http_status_code, content=jsonable_encoder(result.payload))


@router.put("/alert-preferences/{browser_id}", response_model=None)
def update_alert_preference(
    browser_id: UUID, request: AlertPreferenceRequest
) -> JSONResponse:
    """
    Create or update PM2.5 alert threshold preferences for an anonymous browser client.

    Args:
        browser_id: Unique anonymous client UUID.
        request: AlertPreferenceRequest payload containing threshold and enabled state.

    Returns:
        JSON response confirming saved alert preferences.
    """
    result = save_alert_preference(
        browser_id=browser_id,
        threshold_ug_m3=request.threshold_ug_m3,
        enabled=request.enabled,
    )
    return JSONResponse(status_code=result.http_status_code, content=jsonable_encoder(result.payload))
