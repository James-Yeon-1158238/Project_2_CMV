from typing import List
from app.dao.enhance import BaseRepository
from app.dao.model.event_photo import EventPhoto
from mysql.connector import pooling


class EventPhotoRepository(BaseRepository[EventPhoto]):
    
    def __init__(self, connection_pool: pooling.MySQLConnectionPool):
        super().__init__("EVENT_PHOTOS", EventPhoto, connection_pool)

    def find_by_event_id(self, event_id: int) -> List[EventPhoto]:
        return self.findByEventIdOrderByEventPhotoIdAsc(event_id)
    
    def find_by_event_id_in(self, event_ids: List[int]) -> List[EventPhoto]:
        return self.findByEventIdIn(event_ids)
    
    def update_by_event_id(self, ids: List[int], event_id: int) -> None:
        return self.updateByEventPhotoIdIn(ids, event_id = event_id)

    def delete_by_event_id(self, event_id: int) -> None:
        return self.deleteByEventId(event_id)
    
    def delete_by_event_photo_id(self, event_photo_id: int) -> None:
        return self.deleteByEventPhotoId(event_photo_id)