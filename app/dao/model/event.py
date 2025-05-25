from dataclasses import dataclass, field
from typing import Optional
from datetime import date, datetime


@dataclass
class Event:

    event_id: Optional[int] = field(metadata={"primary_key": True})
    journey_id: int
    event_title: str
    event_description: str
    event_start_date: datetime
    event_end_date: datetime
    event_location: str