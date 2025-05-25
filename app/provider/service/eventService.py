from abc import ABC, abstractmethod
import re
from typing import Callable, List

from app import T
from app.dao import event_photo_repo, event_repo
from app.dao.model import journey
from app.dao.model.event import Event
from app.dao.model.event_photo import EventPhoto
from app.dao.model.user import User
from app.dao.model.journey import Journey
from app.model.request.event_req_model import AddEventRequest, EditEventRequest, EventDeleteRequest, EventPhotoAddRequest
from app.model.response.basic_response import RoleAccessResponse
from app.provider.context.event_context import EventContext
from app.utils import file_utils


class EventService(ABC):

    def get_event(self, event_id: int) -> Event:
        return event_repo.find_by_event_id(event_id)
    
    def add_event_photo(self, req: EventPhotoAddRequest, context: EventContext) -> int:
        from app import static_dir
        photo: EventPhoto = EventPhoto(None, req.get_event_id(), file_utils.save_file_to_static(req.get_event_photo(), static_dir))
        return event_photo_repo.save(photo)

    
    def delete_event_photo(self, event_photo_id: int, context: EventContext) -> None:
        return event_photo_repo.delete_by_event_photo_id(event_photo_id)

    @abstractmethod
    def add_event(self, req: AddEventRequest, context: EventContext) -> None:
        pass

    @abstractmethod
    def edit_event(self, req: EditEventRequest, context: EventContext) -> None:
        pass

    @abstractmethod
    def list_events(self, journey_id: int, convert: Callable[[Journey, Event, List[EventPhoto]], RoleAccessResponse], context: EventContext) -> List[RoleAccessResponse]:
        pass

    @abstractmethod
    def list_event_locations(self, convert: Callable[[Event], T], context: EventContext) -> List[T]:
        pass

    @abstractmethod
    def delete_event(self, req: EventDeleteRequest, context: EventContext) -> None:
        pass

