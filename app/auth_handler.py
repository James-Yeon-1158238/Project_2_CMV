from flask import Blueprint, Response, jsonify, request, session
from app.aspect import token_check
from app.dao.model.premier_user import PremierUser
from app.dao.model.user import User
from app.exception.custom_error import ArgumentError
from app.model.request.user_req_model import LoginRequest, RegisterRequest
from app.model.response.user_res_model import UserInfoResponse
from app.provider.service import subs_service
from app.services import auth_service
from app.session_holder import SessionHolder

auth: Blueprint = Blueprint('auth', __name__)


@auth.post('/register')
def register_endpoint() -> Response:
    req: RegisterRequest = RegisterRequest(request.form)
    if not req.validate():
        raise ArgumentError(req.errors)
    auth_service.user_register(req)
    return jsonify({
        "message": "success",
    }), 200


@auth.post('/login')
def login_endpoint() -> Response:
    req: LoginRequest = LoginRequest(request.form)
    if not req.validate():
        raise ArgumentError(req.errors)
    auth_service.user_login(req, lambda u: SessionHolder.session_hold(session, u) and u)
    return jsonify({
        "message": "success",
    }), 200


@auth.post("/logout")
def logout_endpoint() -> Response:
    SessionHolder.session_evict(session, None)
    return jsonify({
        "message": "success"
    }), 200


@auth.get('/current')
@token_check(options = [])
def current_user_endpoint() -> Response:
    user: User = SessionHolder.current_login()
    premier: PremierUser = subs_service.is_premier_user(user)
    return jsonify({
        "data": UserInfoResponse(user.user_id, user.user_name, user.user_email, user.user_fname, user.user_lname, user.user_location, user.user_description, user.user_photo, user.user_status, user.user_role, premier),
    }), 200