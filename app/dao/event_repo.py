from typing import List
from app.dao.enhance import BaseRepository
from app.dao.model.event import Event
from mysql.connector import pooling


class EventRepository(BaseRepository[Event]):
    
    def __init__(self, connection_pool: pooling.MySQLConnectionPool):
        super().__init__("EVENTS", Event, connection_pool)

    def find_by_event_id(self, event_id: int) -> Event:
        return self.findOneByEventId(event_id)

    def find_by_journey_id(self, journey_id: int) -> List[Event]:
        return self.findByJourneyIdOrderByEventStartDateAsc(journey_id)
    
    def delete_by_event_id(self, event_id: int) -> None:
        return self.deleteByEventId(event_id)
    
    def delete_by_journey_id(self, journey_id: int) -> None:
        return self.deleteByJourneyId(journey_id)