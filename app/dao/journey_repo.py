from app.dao.enhance import BaseRepository
from app.dao.model.journey import Journey
from mysql.connector import pooling


class JourneyRepository(BaseRepository[Journey]):
    
    def __init__(self, connection_pool: pooling.MySQLConnectionPool):
        super().__init__("JOURNEYS", Journey, connection_pool)

    def find_by_journey_id(self, journey_id: int) -> Journey:
        return self.findOneByJourneyId(journey_id)
    
    def delete_by_journey_id(self, journey_id: int) -> None:
        return self.deleteByJourneyId(journey_id)