from app.dao.enhance import BaseRepository
from app.dao.model.user import User, UserView
from mysql.connector import pooling

class UserViewRepository(BaseRepository[User]):
    
    def __init__(self, connection_pool: pooling.MySQLConnectionPool):
        super().__init__("USER_VIEW", UserView, connection_pool)