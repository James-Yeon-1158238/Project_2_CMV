from dataclasses import dataclass, field

from app.constant.user_role import Role
from app.constant.user_status import UserStatus

@dataclass
class User:

    user_id: int = field(metadata={"primary_key": True})
    user_name: str
    user_email: str
    password_hash: str
    user_fname: str
    user_lname: str
    user_location: str
    user_description: str
    user_photo: str
    user_status: str
    user_role: str
    is_public: bool
    
    def get_role_enum(self) -> Role:
        """
        Converts the role string into a Role enum.

        Returns:
            Role: The corresponding Role enum for the user.
        """
        return Role.of(self.user_role)
    
    def get_status_enum(self) -> UserStatus:
        """
        Converts the status string into a UserStatus enum.

        Returns:
            UserStatus: The corresponding UserStatus enum for the user.
        """
        return UserStatus.of(self.user_status)
    

@dataclass
class UserView(User):

    user_full_name: str