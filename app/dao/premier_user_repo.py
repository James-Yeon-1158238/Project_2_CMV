from app.dao.enhance import BaseRepository
from app.dao.model.premier_user import PremierUser
from mysql.connector import pooling


class PremierUserRepository(BaseRepository[PremierUser]):
    
    def __init__(self, connection_pool: pooling.MySQLConnectionPool):
        super().__init__("PREMIER_USERS", PremierUser, connection_pool)

    def find_by_user_id(self, user_id: int) -> PremierUser:
        return self.findOneByUserId(user_id)
    
    def delete_by_user_id(self, user_id: int) -> None:
        return self.deleteByUserId(user_id)