from app.dao.enhance import BaseRepository
from app.dao.model.subscription import Subscription
from mysql.connector import pooling


class SubscriptionRepository(BaseRepository[Subscription]):
    
    def __init__(self, connection_pool: pooling.MySQLConnectionPool):
        super().__init__("SUBSCRIPTIONS", Subscription, connection_pool)
