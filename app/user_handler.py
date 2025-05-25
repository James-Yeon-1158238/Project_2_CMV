from flask import Blueprint, Response, jsonify, redirect, request, render_template, current_app, jsonify, session, url_for
from app.session_holder import SessionHolder
from app.exception.custom_error import AccessDeclinedError, ArgumentError
import os

from app.aspect import token_check
from app.constant.user_role import Role
from app.services import user_service
from flask_bcrypt import Bcrypt
from app.dao import user_repo
from app.dao.model.user import User

bcrypt = Bcrypt()

# Define Blueprint for user-related routes
user: Blueprint = Blueprint('user', __name__)

# Admin-only endpoint to get list of users, optionally filtered by search query
@user.get('/list')
@token_check(options = [Role.ADMIN])
def list_user_endpoint() -> Response:
    query_str: str = request.args.get('query_str', type = str)
    res = user_service.list_users(query_str, lambda x: x)
    return jsonify({
        "data": res
    }), 200

#  currently not implemented
@user.post('/edit')
def edit_user_endpoint() -> Response:
    return jsonify({
        "data": None
    }), 200
      
@user.post('/profile/update')
@token_check(options=[])
def update_profile_info() -> Response:
    current_user = SessionHolder.current_login()
    if not current_user:
        raise AccessDeclinedError("You must be logged in.")

    update_data = {
        "user_name": request.form.get("user_name"),
        "user_email": request.form.get("email"),
        "user_fname": request.form.get("first_name"),
        "user_lname": request.form.get("last_name"),
        "user_location": request.form.get("location"),
        "user_description": request.form.get("description")
    }

    try:
        user_service.update_user_profile(current_user.user_id, update_data)

        # Rewrite session
        SessionHolder.session_evict(session, current_user)
        updated_user = user_repo.find_by_user_id(current_user.user_id)
        SessionHolder.session_hold(session, updated_user)

        return redirect(url_for("page.profile_page", info_updated="true"))

    except ArgumentError as e:
        return redirect(url_for("page.profile_page", error_message=str(e)))


    
@user.post('/change-password')
@token_check(options=[])
def change_password() -> Response:
    current_user = SessionHolder.current_login()
    if not current_user:
        raise AccessDeclinedError("You must be logged in.")
    
    current_password = request.form.get("current_password")
    new_password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")

    if new_password != confirm_password:
        return redirect(url_for("page.profile_page", password_error="mismatch"))
    
    if not bcrypt.check_password_hash(current_user.password_hash, current_password):
        return redirect(url_for("page.profile_page", password_error="incorrect"))

    new_password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
    current_user.password_hash = new_password_hash
    user_repo.save_or_update(current_user)

    SessionHolder.session_evict(session, current_user)
    SessionHolder.session_hold(session, current_user)

    return redirect(url_for("page.profile_page", password_updated="true"))

@user.post('/profile/photo')
@token_check(options=[])
def upload_profile_photo() -> Response:
    current_user = SessionHolder.current_login()
    if not current_user:
        raise AccessDeclinedError("You must be logged in.")
    
    photo = request.files.get("photo")
    if not photo:
        return redirect(url_for("page.profile_page", error_message="No file uploaded"))

    from app import static_dir
    from app.utils import file_utils

    try:
        photo_path = file_utils.save_file_to_static(photo, static_dir)
        photo_path = photo_path.replace("../static/", "").replace("static/", "")
 

        current_user.user_photo = photo_path
        user_repo.save_or_update(current_user)

        SessionHolder.session_evict(session, current_user)
        SessionHolder.session_hold(session, current_user)

        return redirect(url_for("page.profile_page", photo_updated="true"))
    except Exception as e:
        return redirect(url_for("page.profile_page", error_message="Failed to upload image"))
    

@user.post("/admin/update")
@token_check(options=[Role.ADMIN])
def admin_update_user_profile() -> Response:
    admin = SessionHolder.current_login()
    if not admin or admin.user_role != "admin":
        raise AccessDeclinedError("Only admins can update user profiles.")

    user_id = request.form.get("user_id", type=int)
    if not user_id:
        return redirect(url_for("page.accounts_page"))

    description = request.form.get("description", "")
    user_status = request.form.get("user_status")
    user_role = request.form.get("user_role")
    remove_photo = request.form.get("remove_photo")  # optional checkbox
    photo_file = request.files.get("user_photo")

    from app import static_dir
    from app.utils import file_utils

    try:
        update_data = {
            "user_description": description,
            "user_status": user_status,
            "user_role": user_role
        }

        if remove_photo:
            update_data["user_photo"] = ""
        elif photo_file and photo_file.filename:
            # Save new photo
            photo_path = file_utils.save_file_to_static(photo_file, static_dir)
            photo_path = photo_path.replace("../static/", "").replace("static/", "")

            update_data["user_photo"] = photo_path

        user_service.admin_update_user_profile(user_id, update_data)
        return redirect(url_for("page.accounts_page", success=True))

    except ArgumentError as e:
        current_app.logger.error(f"Admin profile update error: {e}")
        return redirect(url_for("page.accounts_page", error=str(e)))
    
@user.post('/profile/remove-photo')
@token_check(options=[])
def remove_profile_photo() -> Response:
    current_user = SessionHolder.current_login()
    if not current_user:
        raise AccessDeclinedError("You must be logged in.")

    current_user.user_photo = ""
    user_repo.save_or_update(current_user)

    SessionHolder.session_evict(session, current_user)
    SessionHolder.session_hold(session, current_user)

    return redirect(url_for("page.profile_page", photo_updated="true"))

