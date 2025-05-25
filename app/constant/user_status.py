from enum import Enum

class UserStatus(Enum):

    ACTIVE = ("active")
    BLOCKED = ("blocked")
    BANNED = ("banned")

    def __new__(cls, value: str):
        """
        Custom constructor for UserStatus enum to associate the status with its value.

        Args:
            cls (type): The enum class.
            value (str): The status value (active or inactive).
        """
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    @classmethod
    def of(cls, name: str) -> 'UserStatus':
        return cls.__members__.get(name.upper(), None)