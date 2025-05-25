from app.provider.service.eventService import EventService
from app.provider.service.impl.basicEventService import BasicEventService
from app.provider.service.impl.eventAccessService import EventAccessService
from app.provider.service.impl.premierEventService import PremierEventService
from app.provider.service.journeyService import JourneyService
from app.provider.service.subscriptionService import SubscriptionService
from app.provider.service.userService import UserService

event_service: EventService = EventAccessService(BasicEventService(PremierEventService()))
journey_service: JourneyService = JourneyService()
user_service: UserService = UserService()
subs_service: SubscriptionService = SubscriptionService()