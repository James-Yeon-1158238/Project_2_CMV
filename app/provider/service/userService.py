from abc import ABC, abstractmethod

from app.dao import user_repo
from app.dao.model.user import User


class UserService(ABC):

    def get_user_by_id(self, user_id: int) -> User:
        return user_repo.find_by_user_id(user_id)
