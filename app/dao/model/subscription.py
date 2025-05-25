from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class Subscription:

    subscription_id: Optional[int] = field(metadata={"primary_key": True})
    plan_id: int
    user_id: int
    created_at: Optional[datetime] = field(metadata={"auto_now": True})
    start_date: datetime
    end_date: datetime
    is_gifted: bool