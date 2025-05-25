from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Optional

@dataclass
class UserInfoResponse:

    user_id: int
    user_name: str
    user_email: str
    user_fname: str
    user_lname: str
    user_location: str
    user_description: str
    user_photo: str
    user_status: str
    user_role: str
    premier: bool