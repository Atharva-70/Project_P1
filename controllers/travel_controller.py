from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from utils.role_required import role_required
from utils.serializers import travel_to_dict
from services.travel_service import (
    create_travel_request,
    get_user_travel_requests,
    get_travel_request,
    get_pending_travel_approvals,
    approve_travel,
    reject_travel
)

travel_bp = Blueprint("travel", __name__)


@travel_bp.route("/travel", methods=['POST'])
@jwt_required()
def create_request():
    data = request.get_json() or {}

    source = data.get("source")
    destination = data.get("destination")
    purpose = data.get("purpose")
    start_date_str = data.get("start_date")
    end_date_str = data.get("end_date")
    travel_request_number = data.get("travel_request_number")

    if not source or not destination or not purpose or not start_date_str or not end_date_str or not travel_request_number:
        return jsonify({"message": "Missing required fields"}), 400

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"message": "Dates must be in YYYY-MM-DD format"}), 400

    if end_date < start_date:
        return jsonify({"message": "End date cannot be before start date"}), 400

    user_id = int(get_jwt_identity())
    travel_request, error = create_travel_request(
        user_id,
        source,
        destination,
        purpose,
        start_date,
        end_date,
        travel_request_number
    )

    if error:
        return jsonify({"message": error}), 400

    res = travel_to_dict(travel_request)
    res["message"] = "Travel request created successfully"
    return jsonify(res), 201


@travel_bp.route("/travel", methods=['GET'])
@jwt_required()
def list_my_travel_requests():
    user_id = int(get_jwt_identity())
    requests, error = get_user_travel_requests(user_id)

    if error:
        return jsonify({"message": error}), 400

    return jsonify([travel_to_dict(r) for r in requests]), 200


@travel_bp.route("/travel/<int:travel_id>", methods=['GET'])
@jwt_required()
def get_single_travel_request(travel_id):
    request_obj, error = get_travel_request(travel_id)

    if error:
        return jsonify({"message": error}), 404

    return jsonify(travel_to_dict(request_obj)), 200


@travel_bp.route("/travel/pending-approvals", methods=['GET'])
@jwt_required()
@role_required("MANAGER", "ADMIN")
def pending_travel_approvals():
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role")

    requests, error = get_pending_travel_approvals(user_id, role)
    if error:
        return jsonify({"message": error}), 400

    return jsonify([travel_to_dict(r) for r in requests]), 200


@travel_bp.route("/travel/<int:travel_id>/approve", methods=['POST'])
@jwt_required()
@role_required("MANAGER", "ADMIN")
def approve_travel_request(travel_id):
    updated, error = approve_travel(travel_id)
    if error:
        return jsonify({"message": error}), 400

    return jsonify({
        "message": "Travel request approved successfully",
        "travel_id": updated.travel_id,
        "status": updated.status
    }), 200


@travel_bp.route("/travel/<int:travel_id>/reject", methods=['POST'])
@jwt_required()
@role_required("MANAGER", "ADMIN")
def reject_travel_request(travel_id):
    updated, error = reject_travel(travel_id)
    if error:
        return jsonify({"message": error}), 400

    return jsonify({
        "message": "Travel request rejected successfully",
        "travel_id": updated.travel_id,
        "status": updated.status
    }), 200