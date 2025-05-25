from app.dao import user_repo, journey_repo, event_repo, user_view_repo, event_photo_repo, subs_repo, premier_user_repo, comment_repo
from app import connection_pool


user_view_repo = user_view_repo.UserViewRepository(connection_pool)
user_repo = user_repo.UserRepository(connection_pool)
journey_repo = journey_repo.JourneyRepository(connection_pool)
event_repo = event_repo.EventRepository(connection_pool)
event_photo_repo = event_photo_repo.EventPhotoRepository(connection_pool)
subs_repo = subs_repo.SubscriptionRepository(connection_pool)
premier_user_repo = premier_user_repo.PremierUserRepository(connection_pool)
comment_repo = comment_repo.CommentRepository(connection_pool)