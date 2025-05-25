from app.dao.enhance import BaseRepository
from app.dao.model.user import User
from mysql.connector import pooling


class UserRepository(BaseRepository[User]):
    
    def __init__(self, connection_pool: pooling.MySQLConnectionPool):
        super().__init__("USERS", User, connection_pool)

    def find_by_user_id(self, user_id: int) -> User:
        return self.findOneByUserId(user_id)
    
    def find_by_user_name(self, user_name: str) -> User:
        return self.findOneByUserName(user_name)
    
    def find_by_user_email(self, user_email: str) -> User:
        return self.findOneByUserEmail(user_email)
