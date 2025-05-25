from dataclasses import dataclass
from app.dao.model.journey import Journey
from app.dao.model.user import User
from typing import Optional

@dataclass
class EventContext:

    current_user: Optional[User] = None
    is_current_user_premier: bool = False
    journey: Journey = None
    jorney_owner: Optional[User] = None
    is_journey_owner_premier: bool = False
    need_premier_check: bool = True
