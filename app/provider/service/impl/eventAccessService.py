from typing import Callable, List
from app import T
from app.dao.model.event import Event
from app.dao.model.event_photo import EventPhoto
from app.dao.model.journey import Journey
from app.dao.model.user import User
from app.dao.transaction import transactional
from app.exception.custom_error import AccessDeclinedError, OperationNotAllowedError
from app.model.request.event_req_model import AddEventRequest, EditEventRequest, EventDeleteRequest

from app.model.response.basic_response import RoleAccessResponse
from app.provider.context.event_context import EventContext
from app.provider.service.eventService import EventService
from app.provider.strategy.access_strategy import AccessStrategy


class EventAccessService(EventService):

    def __init__(self, delegate: EventService):
        self._delegate = delegate

    
    @transactional
    def add_event(self, req: AddEventRequest, context: EventContext) -> None:
        from app.provider.service import journey_service, user_service
        journey: Journey = journey_service.get_journey(req.get_journey_id())
        if not journey:
            raise OperationNotAllowedError("can not find current journey")
        context.journey = journey
        context.jorney_owner = user_service.get_user_by_id(journey.user_id)
        return self._delegate.add_event(req, context)

    
    @transactional
    def edit_event(self, req: EditEventRequest, context: EventContext) -> None:
        from app.provider.service import journey_service, user_service
        journey: Journey = journey_service.get_journey(req.get_journey_id())
        if not journey:
            raise OperationNotAllowedError("can not find current journey")
        context.journey = journey
        context.jorney_owner = user_service.get_user_by_id(journey.user_id)
        strategy: AccessStrategy = AccessStrategy.getAccessStrategy(context.current_user)
        if not strategy.can_edit_event(context):
            raise AccessDeclinedError("you are not allowed to operate this")
        return self._delegate.edit_event(req, context)
    
    
    def list_events(self, journey_id: int, convert: Callable[[Journey, Event, List[EventPhoto]], RoleAccessResponse], context: EventContext) -> List[RoleAccessResponse]:
        from app.provider.service import journey_service, user_service
        journey: Journey = journey_service.get_journey(journey_id)
        if not journey:
            raise OperationNotAllowedError("can not find current journey")
        context.journey = journey
        context.jorney_owner = user_service.get_user_by_id(journey.user_id)
        strategy: AccessStrategy = AccessStrategy.getAccessStrategy(context.current_user)
        can_access_full: bool = strategy.can_access_full_event(context)
        def wrapper(journey: Journey, event: Event, photos: List[EventPhoto]) -> T:
            visable_photos: List[EventPhoto] = photos if can_access_full else photos[:1]
            res: RoleAccessResponse = convert(journey, event, visable_photos)
            res.can_edit = strategy.can_edit_event(context)
            res.can_delete = strategy.can_delete_event(context)
            return res
        return self._delegate.list_events(journey_id, wrapper, context)

    
    def list_event_locations(self, convert: Callable[[Event], T], context: EventContext) -> List[T]:
        return self._delegate.list_event_locations(convert, context)

    
    @transactional
    def delete_event(self, req: EventDeleteRequest, context: EventContext) -> None:
        from app.provider.service import journey_service, user_service
        journey: Journey = journey_service.get_journey(req.get_journey_id())
        if not journey:
            raise OperationNotAllowedError("can not find current journey")
        context.journey = journey
        context.jorney_owner = user_service.get_user_by_id(journey.user_id)
        strategy: AccessStrategy = AccessStrategy.getAccessStrategy(context.current_user)
        if not strategy.can_delete_event(context):
            raise AccessDeclinedError("you are not allowed to operate this")
        return self._delegate.delete_event(req, context)