from datetime import datetime
from app.constant.user_role import Role
from app.dao import premier_user_repo
from app.dao.model.premier_user import PremierUser
from app.dao.model.user import User
from app.dao.transaction import transactional


class SubscriptionService:

    @transactional
    def get_premier_user(self, user_id: int) -> PremierUser:
        premier_user: PremierUser = premier_user_repo.find_by_user_id(user_id)
        if not premier_user:
            return None
        if premier_user.premier_end_at <= datetime.now():
            premier_user_repo.delete_by_user_id(user_id)
            return None
        return premier_user
    
    
    def is_premier_user(self, user: User) -> bool:
        if user.get_role_enum() in [Role.ADMIN, Role.EDITOR]:
            return True
        premier_user: PremierUser =self.get_premier_user(user.user_id)
        return premier_user is not None
        