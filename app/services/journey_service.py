from app.constant.journey_status import JourneyStatus
from app.constant.user_role import Role
from app.dao import event_repo, journey_repo
from app.dao.model.journey import Journey
from app.dao.model.user import User
from app.exception.custom_error import OperationNotAllowedError
from app.model.request.journey_req_model import CreateJourneyRequest, DeleteJourneyRequest, EditJourneyRequest
from app.dao.transaction import transactional


class JourneyService:

    def get_journey(self, journey_id: int) -> Journey:
        return journey_repo.find_by_journey_id(journey_id)

    @transactional
    def create_journey(self, req: CreateJourneyRequest, user_id: int) -> None:
        insert: Journey = Journey(None, user_id, None, None, req.get_title(), req.get_desc(), req.get_start_date(), req.get_status())
        journey_repo.save_or_update(insert)

    def check_edit_permission(self, journey: Journey, current_user: User) -> None:
        if journey.user_id != current_user.user_id:
            if journey.get_joureny_status_enum() is not JourneyStatus.PUBLIC:
                raise OperationNotAllowedError('this journey is not allowed to edit')
            if current_user.get_role_enum() is Role.TRAVELLER:
                raise OperationNotAllowedError('edit operation is only for admin and editor')

    @transactional
    def edit_journey(self, req: EditJourneyRequest, current_user: User) -> None:
        journey: Journey = self.get_journey(req.get_journey_id())
        if not journey:
            raise OperationNotAllowedError('current journey not found')
        self.check_edit_permission(journey, current_user)
        journey.journey_title = req.get_title()
        journey.journey_description = req.get_desc()
        journey.journey_start_date = req.get_start_date()
        journey_repo.save_or_update(journey)
    
    @transactional
    def delete_journey(self, req: DeleteJourneyRequest, user_id: int) -> None:
        journey: Journey = self.get_journey(req.get_journey_id())
        if not journey:
            raise OperationNotAllowedError('current journey not found')
        if journey.user_id != user_id:
            raise OperationNotAllowedError('you are not the owner of this journey')
        journey_repo.delete_by_journey_id(journey.journey_id)
        event_repo.delete_by_journey_id(journey.journey_id)