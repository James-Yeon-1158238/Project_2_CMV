from app.services.auth_service import AuthService
from app.services.event_service import EventService
from app.services.journey_service import JourneyService
from app.services.user_service import UserService

auth_service = AuthService()
journey_service = JourneyService()
event_service = EventService()
user_service = UserService()