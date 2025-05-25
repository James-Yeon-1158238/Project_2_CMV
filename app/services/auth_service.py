from typing import Callable
from app import T
from app.constant.user_status import UserStatus
from app.dao import user_repo
from app.dao.model.user import User
from app.exception.custom_error import AccessDeclinedError, ArgumentError, OperationNotAllowedError
from app.model.request.user_req_model import LoginRequest, RegisterRequest
from app.dao.transaction import transactional

class AuthService:

    @transactional
    def user_register(self, req: RegisterRequest) -> None:
        user: User = user_repo.find_by_user_name(req.get_user_name())
        if user:
            raise ArgumentError({'user_name': ['user name already exists']})
        user: User = user_repo.find_by_user_email(req.get_email())
        if user:
            raise ArgumentError({'email': ['email already exists']})
        from app import encrypt
        insert: User = User(None, req.get_user_name(), req.get_email(), encrypt.generate_password_hash(req.get_password()), req.get_first_name(), req.get_last_name(), req.get_location(), req.get_desc(), None, req.get_user_status().value, req.get_role().value, True)
        user_repo.save(insert)


    def user_login(self, req: LoginRequest, on_pass: Callable[[User], T]) -> T:
        user: User = user_repo.find_by_user_name(req.get_user_name())
        if not user:
            user: User = user_repo.find_by_user_email(req.get_user_name())
            if not user:
                raise ArgumentError({'user_name': ['user name or email not exists']})
        from app import encrypt
        if not encrypt.check_password_hash(user.password_hash, req.get_password()):
            raise ArgumentError({'password': ['password is incorrect']})
        if UserStatus.BANNED is user.get_status_enum():
            raise OperationNotAllowedError('login failed! current user is banned')
        return on_pass(user) if on_pass is not None else None