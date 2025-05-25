from dataclasses import dataclass, field
from typing import Optional
from datetime import date, datetime


@dataclass
class EventPhoto:

    event_photo_id: Optional[int] = field(metadata={"primary_key": True})
    event_id: int
    event_photo_address: str