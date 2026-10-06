"""Read and update anonymous alert preferences."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.alert_preference import AlertPreference


class AlertPreferenceRepository:
    """Persist a single alert preference per anonymous browser UUID."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, browser_id: UUID) -> AlertPreference | None:
        return self._session.scalar(
            select(AlertPreference).where(AlertPreference.browser_id == browser_id)
        )

    def upsert(
        self, *, browser_id: UUID, threshold_ug_m3: Decimal, enabled: bool
    ) -> AlertPreference:
        preference = self.get(browser_id)
        if preference is None:
            preference = AlertPreference(
                browser_id=browser_id,
                threshold_ug_m3=threshold_ug_m3,
                enabled=enabled,
            )
            self._session.add(preference)
        else:
            preference.threshold_ug_m3 = threshold_ug_m3
            preference.enabled = enabled
        self._session.flush()
        return preference
