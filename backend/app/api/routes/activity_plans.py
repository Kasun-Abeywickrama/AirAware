"""Comparative outdoor activity planning endpoint."""

from datetime import date

from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from ...services.user_features import create_activity_plan


class ActivityPlanRequest(BaseModel):
    date: date
    duration_minutes: int = Field(ge=60, le=1440)

    @field_validator("duration_minutes")
    @classmethod
    def duration_must_be_whole_hours(cls, value: int) -> int:
        if value % 60 != 0:
            raise ValueError("duration_minutes must be a whole number of hours.")
        return value


router = APIRouter(prefix="/api/v1", tags=["Activity planning"])


@router.post("/activity-plans", response_model=None)
def activity_plans(request: ActivityPlanRequest) -> JSONResponse:
    """Return the best available future windows for an outdoor activity."""
    result = create_activity_plan(
        requested_date=request.date, duration_minutes=request.duration_minutes
    )
    return JSONResponse(status_code=result.http_status_code, content=jsonable_encoder(result.payload))
