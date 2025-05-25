from dataclasses import dataclass
from datetime import datetime

@dataclass
class Comment:
    comment_id: int
    event_id: int
    user_id: int
    comment_text: str
    created_at: datetime
    is_hidden: bool = False
