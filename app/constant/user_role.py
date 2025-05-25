from enum import Enum
from typing import List

class Role(Enum):
    """
    Enum representing different user roles and their allowed operations.
    """

    ADMIN = ("admin")
    EDITOR = ("editor")
    MODERATOR = ("moderator")
    TRAVELLER = ("traveller")

    def __new__(cls, value: str):
        """
        Custom constructor for Role enum to associate roles with allowed operations.

        Args:
            cls (type): The enum class.
            value (str): The role value (admin, helper, visitor).
            allowed_operations (List[str]): List of allowed operations for the role.
        """
        obj = object.__new__(cls)
        obj._value_ = value  
        return obj

    @classmethod
    def of(cls, name: str) -> 'Role':
        """
        Returns the Role corresponding to the provided name.

        Args:
            name (str): The role name (e.g., "ADMIN", "HELPER").

        Returns:
            Role: The corresponding Role enum or None if not found.
        """
        return cls.__members__.get(name.upper())