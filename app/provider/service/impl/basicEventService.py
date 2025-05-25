from typing import Callable, List
from app import T
from app.dao.model import journey
from app.dao.model.event import Event
from app.dao.model.event_photo import EventPhoto
from app.dao.model.journey import Journey
from app.dao.transaction import transactional
from app.exception.custom_error import OperationNotAllowedError
from app.model.request.event_req_model import AddEventRequest, EditEventRequest, EventDeleteRequest

from app.model.response.basic_response import RoleAccessResponse
from app.provider.context.event_context import EventContext
from app.provider.service.eventService import EventService


class BasicEventService(EventService):

    def __init__(self, delegate: EventService):
        self._delegate = delegate

    
    @transactional
    def add_event(self, req: AddEventRequest, context: EventContext) -> None:
        from app.provider.service import subs_service
        context.is_current_user_premier = subs_service.is_premier_user(context.current_user)
        if not context.is_current_user_premier:
            if len(req.get_event_photos()) > 1:
                raise OperationNotAllowedError("only premier users can upload multi photos")
        return self._delegate.add_event(req, context)

    
    @transactional
    def edit_event(self, req: EditEventRequest, context: EventContext) -> None:
        from app.provider.service import subs_service
        context.is_current_user_premier = subs_service.is_premier_user(context.current_user)
        if not context.is_current_user_premier:
            if len(req.get_event_photos()) > 1:
                raise OperationNotAllowedError("only premier users can upload multi photos")
        return self._delegate.edit_event(req, context)

    
    def list_events(self, journey_id: int, convert: Callable[[Journey, Event, List[EventPhoto]], RoleAccessResponse], context: EventContext) -> List[RoleAccessResponse]:
        from app.provider.service import subs_service
        if context.need_premier_check:
            context.is_journey_owner_premier = subs_service.is_premier_user(context.jorney_owner)
            if context.is_journey_owner_premier:
                return self._delegate.list_events(journey_id, convert, context)
            def wrapper(journey: Journey, event: Event, photos: List[EventPhoto]) -> RoleAccessResponse:
                return convert(journey, event, photos[:1])
            return self._delegate.list_events(journey_id, wrapper, context)
        return self._delegate.list_events(journey_id, convert, context)


    
    def list_event_locations(self, convert: Callable[[Event], T], context: EventContext) -> List[T]:
        return self._delegate.list_event_locations(convert, context)

    
    @transactional
    def delete_event(self, req: EventDeleteRequest, context: EventContext) -> None:
        return self._delegate.delete_event(req, context)