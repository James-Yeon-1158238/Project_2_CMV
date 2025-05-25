from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class PremierUser:

    premier_id: Optional[int] = field(metadata={"primary_key": True})
    user_id: int
    premier_start_at: datetime
    premier_end_at: datetime