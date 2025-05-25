from abc import ABC, abstractmethod

from app.constant.journey_status import JourneyStatus
from app.constant.user_role import Role
from app.dao.model.journey import Journey
from app.dao.model.user import User
from app.provider.context.event_context import EventContext


class AccessStrategy(ABC):

    @staticmethod
    def getAccessStrategy(user: User) -> 'AccessStrategy':
        if not user:
            return DeclinedAccessStrategy()
        if user.get_role_enum() is Role.TRAVELLER:
            return TravellorAccessStrategy()
        if user.get_role_enum() is Role.EDITOR:
            return EditorAccessStrategy()
        if user.get_role_enum() is Role.MODERATOR:
            return ModeratorAccessStrategy()
        if user.get_role_enum() is Role.ADMIN:
            return AdminAccessStrategy()
        return None

    @abstractmethod
    def can_edit_event(self, context: EventContext) -> bool:
        pass
    
    @abstractmethod
    def can_delete_event(self, context: EventContext) -> bool:
        pass

    @abstractmethod
    def can_access_full_event(self, context: EventContext) -> bool:
        pass


class AdminAccessStrategy(AccessStrategy):

    def __init__(self):
        self._delegate = TravellorAccessStrategy()

    def can_edit_event(self, context: EventContext) -> bool:
        journey: Journey = context.journey
        return (journey.get_joureny_status_enum() in [JourneyStatus.PUBLIC, JourneyStatus.SHARE]) or self._delegate.can_edit_event(context)
    
    def can_delete_event(self, context: EventContext) -> bool:
        journey: Journey = context.journey
        return (journey.get_joureny_status_enum() in [JourneyStatus.PUBLIC, JourneyStatus.SHARE]) or self._delegate.can_delete_event(context)
    
    def can_access_full_event(self, context: EventContext) -> bool:
        context.need_premier_check = False
        return True


class EditorAccessStrategy(AccessStrategy):

    def __init__(self):
        self._delegate = AdminAccessStrategy()

    def can_edit_event(self, context: EventContext) -> bool:
        return self._delegate.can_edit_event(context)
    
    def can_delete_event(self, context: EventContext) -> bool:
        return self._delegate.can_delete_event(context)
    
    def can_access_full_event(self, context: EventContext) -> bool:
        return self._delegate.can_access_full_event(context)
    

class ModeratorAccessStrategy(AccessStrategy):

    def __init__(self):
        self._delegate = TravellorAccessStrategy()

    def can_edit_event(self, context: EventContext) -> bool:
        return self._delegate.can_edit_event(context)
    
    def can_delete_event(self, context: EventContext) -> bool:
        return self._delegate.can_delete_event(context)
    
    def can_access_full_event(self, context: EventContext) -> bool:
        return self._delegate.can_access_full_event(context)


class TravellorAccessStrategy(AccessStrategy):

    def can_edit_event(self, context: EventContext) -> bool:
        return context.current_user.user_id == context.journey.user_id
    
    def can_delete_event(self, context: EventContext) -> bool:
        return context.current_user.user_id == context.journey.user_id
    
    def can_access_full_event(self, context: EventContext) -> bool:
        if context.current_user.user_id == context.journey.user_id:
            context.need_premier_check = False
            return True
        return False


class DeclinedAccessStrategy(AccessStrategy):

    def can_edit_event(self, context: EventContext) -> bool:
        return False
    
    def can_delete_event(self, context: EventContext) -> bool:
        return False
    
    def can_access_full_event(self, context: EventContext) -> bool:
        return False
