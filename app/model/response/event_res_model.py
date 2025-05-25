from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Optional

from app.dao.model.event_photo import EventPhoto
from app.model.response.basic_response import RoleAccessResponse


@dataclass
class EventResponse(RoleAccessResponse):

    event_id: int
    journey_id: int
    event_title: str
    event_description: str
    event_start_date: datetime
    event_end_date: datetime
    event_location: str
    event_photos: List[EventPhoto]

