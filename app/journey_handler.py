from flask import Blueprint, Response, jsonify, request
from app.aspect import token_check
from app.exception.custom_error import ArgumentError
from app.model.request.journey_req_model import CreateJourneyRequest, DeleteJourneyRequest, EditJourneyRequest
from app.services import journey_service
from app.session_holder import SessionHolder

journey: Blueprint = Blueprint('journey', __name__)


@journey.post('/create')
@token_check(options = [])
def create_journey_endpoint() -> Response:
    req: CreateJourneyRequest = CreateJourneyRequest(request.form)
    if not req.validate():
        raise ArgumentError(req.errors)
    journey_service.create_journey(req, SessionHolder.current_login().user_id)
    return jsonify({
        "message": "success",
    }), 200


@journey.post('/edit')
@token_check(options = [])
def edit_journey_endpoint() -> Response:
    req: EditJourneyRequest = EditJourneyRequest(request.form)
    if not req.validate():
        raise ArgumentError(req.errors)
    journey_service.edit_journey(req, SessionHolder.current_login())
    return jsonify({
        "message": "success",
    }), 200


@journey.post('/delete')
@token_check(options = [])
def delete_journey_endpoint() -> Response:
    req: DeleteJourneyRequest = DeleteJourneyRequest(request.form)
    if not req.validate():
        raise ArgumentError(req.errors)
    journey_service.delete_journey(req, SessionHolder.current_login().user_id)
    return jsonify({
        "message": "success",
    }), 200