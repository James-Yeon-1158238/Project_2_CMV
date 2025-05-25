from typing import List
from flask import Blueprint, Response, jsonify, request

from app.aspect import token_check
from app.model.response.event_res_model import EventResponse
from app.exception.custom_error import ArgumentError
from app.model.request.event_req_model import (
    AddEventRequest,
    EditEventRequest,
    EventDeleteRequest,
    EventPhotoAddRequest,
)
from app.provider.context.event_context import EventContext
from app.provider.service import event_service
from app.session_holder import SessionHolder
from werkzeug.datastructures import CombinedMultiDict
from werkzeug.datastructures import FileStorage
from app.dao import comment_repo
from app import get_connection


event: Blueprint = Blueprint("event", __name__)


@event.post("/add")
@token_check(options=[])
def add_event_endpoint() -> Response:
    req: AddEventRequest = AddEventRequest(CombinedMultiDict([request.form]))
    if not req.validate():
        raise ArgumentError(req.errors)
    req.event_photo_ids = request.form.getlist('event_photo_ids')
    context: EventContext = EventContext()
    context.current_user = SessionHolder.current_login()
    event_service.add_event(req, context)
    return jsonify({
        "message": "success",
    }), 200

@event.post("/edit")
@token_check(options=[])
def edit_event_endpoint() -> Response:
    req: EditEventRequest = EditEventRequest(CombinedMultiDict([request.form]))
    if not req.validate():
        raise ArgumentError(req.errors)
    req.event_photo_ids = request.form.getlist('event_photo_ids')
    context: EventContext = EventContext()
    context.current_user = SessionHolder.current_login()
    event_service.edit_event(req, context)
    return jsonify({
        "message": "success"
    }), 200

@event.post("/addEventPhoto")
@token_check(options=[])
def add_event_photo_endpoint() -> Response:
    req: EventPhotoAddRequest = EventPhotoAddRequest(CombinedMultiDict([request.form, request.files]))
    context: EventContext = EventContext()
    context.current_user = SessionHolder.current_login()
    return jsonify({
        "data": event_service.add_event_photo(req, context) 
    }), 200

@event.get("/deleteEventPhoto")
@token_check(options=[])
def delete_event_photo_endpoint() -> Response:
    photo_id: int = request.args.get("event_photo_id", type = int)
    context: EventContext = EventContext()
    context.current_user = SessionHolder.current_login()
    event_service.delete_event_photo(photo_id, context)
    return jsonify({
        "data": "success"
    }), 200


@event.get("/list")
def list_event_endpoint() -> Response:
    journey_id: int = request.args.get("journey_id", type=int)
    context: EventContext = EventContext()
    return jsonify({
        "data": event_service.list_events(journey_id, lambda j, e, p: EventResponse(True, True, e.event_id, e.journey_id, e.event_title, e.event_description, e.event_start_date, e.event_end_date, e.event_location, p), context)
    }), 200



@event.get("/locations")
@token_check(options=[])
def event_locations_endpoint() -> Response:
    locations: List[str] = event_service.list_event_locations(lambda x: x.event_location, EventContext())
    return jsonify({
        "data": locations
    }), 200


@event.post("/delete")
@token_check(options=[])
def event_delete_endpoint() -> Response:
    req: EventDeleteRequest = EventDeleteRequest(request.form)
    context: EventContext = EventContext()
    context.current_user = SessionHolder.current_login()
    event_service.delete_event(req, context)
    return jsonify({
        "message": "success"
    }), 200


@event.post("/comment")
@token_check(options=[])
def post_comment_endpoint() -> Response:
    user = SessionHolder.current_login()
    if not user:
        return jsonify({"success": False, "message": "Please login first."}), 401

    event_id: int = request.form.get("event_id", type=int)
    comment_text: str = request.form.get("comment_text", "").strip()

    if not event_id or not comment_text:
        return jsonify({"success": False, "message": "Missing event_id or comment_text"}), 400

    from app.dao.model.comment import Comment
    import datetime

    comment = Comment(
        comment_id=None,
        event_id=event_id,
        user_id=user.user_id,
        comment_text=comment_text,
        created_at=datetime.datetime.now(),
        is_hidden=False
    )

    comment_repo.save(comment)

    return jsonify({"success": True, "message": "Comment posted successfully"}), 200

@event.post("/reportComment")
def report_comment_api():
    user = SessionHolder.current_login()
    if not user:
        return jsonify({"success": False, "message": "Please login first."}), 401

    data = request.get_json()
    comment_id = data.get("comment_id")
    reason = data.get("reason")

    if not comment_id or not reason:
        return jsonify({"success": False, "message": "Missing comment_id or reason"}), 400

    if comment_repo.has_user_reported(comment_id, user.user_id):
        return jsonify({"success": False, "message": "You have already reported this comment."}), 400

    comment_repo.insert_comment_report(comment_id, user.user_id, reason)
    return jsonify({"success": True, "message": "Thank you for your report."})

@event.get("/getCommentsWithStatus")
@token_check(options=[])
def get_comments_with_report_status() -> Response:
    user = SessionHolder.current_login()
    if not user:
        return jsonify({"success": False, "message": "Please login first."}), 401

    event_id: int = request.args.get("event_id", type=int)
    if not event_id:
        return jsonify({"success": False, "message": "Missing event_id"}), 400

    comments = comment_repo.find_visible_by_event_id(event_id)
    reported_ids = comment_repo.get_reported_comment_ids_by_user(user.user_id)

    result = []
    for c in comments:
        result.append({
            "comment_id": c.comment_id,
            "comment_text": c.comment_text,
            "user_id": c.user_id,
            "created_at": c.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            "has_reported": c.comment_id in reported_ids
        })

    return jsonify({"success": True, "data": result}), 200
