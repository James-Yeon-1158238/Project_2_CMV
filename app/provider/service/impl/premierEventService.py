from ast import Dict
import re
from typing import Callable, List
from app import T
from app.dao import event_photo_repo, event_repo
from app.dao.model.event import Event
from app.dao.model.event_photo import EventPhoto
from app.dao.model.user import User
from app.dao.query_example import QueryExample
from app.dao.transaction import transactional
from app.exception.custom_error import OperationNotAllowedError
from app.model.request.event_req_model import AddEventRequest, EditEventRequest, EventDeleteRequest
from app.model.response.basic_response import RoleAccessResponse
from app.provider.context.event_context import EventContext
from app.provider.service.eventService import EventService
from app.dao.model.journey import Journey
from app.utils import basic_utils, file_utils


class PremierEventService(EventService):
    
    
    @transactional
    def add_event(self, req: AddEventRequest, context: EventContext) -> None:
        insert: Event = Event(None, req.get_journey_id(), req.get_event_title(), req.get_event_desc(), req.get_start_date(), req.get_end_date(), req.get_location())
        event_id: int = event_repo.save_or_update(insert)
        if len(req.get_event_photos()) > 1:
            event_photo_repo.update_by_event_id(req.get_event_photos(), event_id)

    
    @transactional
    def edit_event(self, req: EditEventRequest, context: EventContext) -> None:
        event: Event = self.get_event(req.get_event_id())
        if not event:
            raise OperationNotAllowedError("current event not found")
        event.event_title = req.get_event_title()
        event.event_description = req.get_event_desc()
        event.event_location = req.get_location()
        event_repo.save_or_update(event)
        if len(req.get_event_photos()) > 1:
            event_photo_repo.update_by_event_id(req.event_photo_ids, req.get_event_id())

    
    def list_events(self, journey_id: int, convert: Callable[[Journey, Event, List[EventPhoto]], RoleAccessResponse], context: EventContext) -> List[RoleAccessResponse]:
        event_list: List[Event] = event_repo.find_by_journey_id(journey_id)
        if len(event_list) < 1:
            return list(map(lambda x: convert(context.journey, x, []), event_list))   
        event_photo_list: List[EventPhoto] = event_photo_repo.find_by_event_id_in([e.event_id for e in event_list])
        event_photo_map: Dict[int, List[str]] = basic_utils.to_grouped_map(event_photo_list, lambda ep: ep.event_id, lambda ep: ep, lambda: {})
        return list(map(lambda x: convert(context.journey, x, event_photo_map.get(x.event_id, [])), event_list))

    
    def list_event_locations(self, convert: Callable[[Event], T], context: EventContext) -> List[T]:
        example: QueryExample = QueryExample(
            conditions={},
            fields=["DISTINCT event_location"],
            order_by="event_location ASC",
        )
        return list(map(lambda x: convert(x), event_repo.find_all_by_example(example)))

    
    @transactional
    def delete_event(self, req: EventDeleteRequest, context: EventContext) -> None:
        event: Event = self.get_event(req.get_event_id())
        if not event:
            raise OperationNotAllowedError("current event not found")
        event_repo.delete_by_event_id(req.get_event_id())
        event_photo_repo.delete_by_event_id(req.get_event_id())