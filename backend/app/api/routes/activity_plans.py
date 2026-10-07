"""
API Route: Exposure-Aware Activity Planner.

Endpoint:
- POST /api/v1/activity-plans: Evaluates future consecutive forecast hours and recommends
  optimal outdoor activity windows that minimize predicted PM2.5 exposure.
"""

from datetime import date

from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from ...services.user_features import create_activity_plan


class ActivityPlanRequest(BaseModel):
    """
    Request model for activity plan recommendation.

    Attributes:
        date: Target calendar date for planned activity.
        duration_minutes: Planned activity duration (must be a whole multiple of 60 min, between 60 and 1440 min).
    """

    date: date
    duration_minutes: int = Field(ge=60, le=1440)

    @field_validator("duration_minutes")
    @classmethod
    def duration_must_be_whole_hours(cls, value: int) -> int:
        """Enforce that activity duration is specified in full hour increments."""
        if value % 60 != 0:
            raise ValueError("duration_minutes must be a whole number of hours.")
        return value


router = APIRouter(prefix="/api/v1", tags=["Activity planning"])


@router.post("/activity-plans", response_model=None)
def activity_plans(request: ActivityPlanRequest) -> JSONResponse:
    """
    Generate ranked outdoor activity windows for a specified date and duration.

    Uses a sliding-window algorithm to identify intervals with the lowest predicted
    average PM2.5 concentration, accompanied by uncertainty estimates and health notices.

    Args:
        request: ActivityPlanRequest containing target date and duration.

    Returns:
        JSON response with top 5 recommended time intervals.
    """
    result = create_activity_plan(
        requested_date=request.date, duration_minutes=request.duration_minutes
    )
    return JSONResponse(status_code=result.http_status_code, content=jsonable_encoder(result.payload))
