from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from app.constant.journey_status import JourneyStatus

@dataclass
class Journey:

    journey_id: Optional[int] = field(metadata={"primary_key": True})
    user_id: int
    created_at: Optional[datetime] = field(metadata={"auto_now": True})
    updated_at: Optional[datetime] = field(metadata={"auto_now": True})
    journey_title: str
    journey_description: str
    journey_start_date: date
    journey_status: str

    def get_joureny_status_enum(self) -> JourneyStatus:
        return JourneyStatus.of(self.journey_status)