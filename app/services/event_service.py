from typing import Callable, List
from zoneinfo import ZoneInfo
from app import T
from app.dao import event_repo, journey_repo
from app.dao.query_example import QueryExample
from app.dao.model.event import Event
from app.dao.model.journey import Journey
from app.dao.model.user import User
from app.exception.custom_error import OperationNotAllowedError

from app.model.request.event_req_model import (
    AddEventRequest,
    EditEventRequest,
    EventDeleteRequest,
)
from app.dao.transaction import transactional

from app.utils import file_utils

nz = ZoneInfo("Pacific/Auckland")

class EventService:

    def get_event(self, event_id: int) -> Event:
        return event_repo.find_by_event_id(event_id)

    @transactional
    def add_event(self, req: AddEventRequest, user_id: int) -> None:
        journey: Journey = journey_repo.find_by_journey_id(req.get_journey_id())
        if not journey:
            raise OperationNotAllowedError("can not find current journey")
        insert: Event = Event(
            None,
            req.get_journey_id(),
            None,
            req.get_event_title(),
            req.get_event_desc(),
            req.get_start_date(),
            req.get_end_date(),
            req.get_location(),
        )
        if req.get_event_photo():
            from app import static_dir
            insert.event_photo = file_utils.save_file_to_static(req.get_event_photo(), static_dir)
        else:
            insert.event_photo = ""
        event_repo.save_or_update(insert)

    @transactional
    def edit_event(self, req: EditEventRequest, current_user: User) -> None:
        event: Event = self.get_event(req.get_event_id())
        if not event:
            raise OperationNotAllowedError("current event not found")
        from app.services import journey_service

        journey: Journey = journey_service.get_journey(event.journey_id)
        if not journey:
            raise OperationNotAllowedError("current journey not found")
        journey_service.check_edit_permission(journey, current_user)
        event.event_title = req.get_event_title()
        event.event_description = req.get_event_desc()
        event.event_location = req.get_location()
        if req.get_event_photo():
            from app import static_dir
            event.event_photo = file_utils.save_file_to_static(req.get_event_photo(), static_dir)
        elif not req.current_event_photo_url:
            event.event_photo = ""
        event_repo.save_or_update(event)

    def list_events(self, journey_id: int, convert: Callable[[Journey, Event], T]) -> List[T]:
        from app.services import journey_service
        journey: Journey = journey_service.get_journey(journey_id)
        if not journey:
            raise OperationNotAllowedError("current journey not found")
        return list(map(lambda x: convert(journey, x), event_repo.find_by_journey_id(journey_id)))

    def list_locations(self, convert: Callable[[Event], T]) -> List[T]:
        example: QueryExample = QueryExample(
            conditions={},
            fields=["DISTINCT event_location"],
            order_by="event_location ASC",
        )
        return list(map(lambda x: convert(x), event_repo.find_all_by_example(example)))

    @transactional
    def delete_event(self, req: EventDeleteRequest, user_id: int) -> None:
        event: Event = self.get_event(req.get_event_id())
        if not event:
            raise OperationNotAllowedError("current event not found")
        from app.services import journey_service

        journey: Journey = journey_service.get_journey(event.journey_id)
        if not journey:
            raise OperationNotAllowedError("current journey not found")
        if journey.user_id != user_id:
            raise OperationNotAllowedError("you are not the owner of this journey")
        event_repo.delete_by_event_id(req.get_event_id())
