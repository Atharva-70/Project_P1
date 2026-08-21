from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import Blueprint, jsonify, request
from services.travel_service import create_travel_request
from datetime import datetime
travel_bp = Blueprint("travel", __name__)

@travel_bp.route("/travel", methods=['POST'])
@jwt_required()
def create_request():
    data = request.get_json()
    source = data.get("source")
    destination = data.get("destination")
    purpose = data.get("purpose")
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    travel_request_number = data.get("travel_request_number")

    if not source or not destination or not purpose or not start_date or not end_date or not travel_request_number:
        return jsonify({
            "message": "Missing required fields"
        }), 400

    try:
        start_date = datetime.strptime(
            start_date,
            "%Y-%m-%d"
        ).date()

        end_date = datetime.strptime(
            end_date,
            "%Y-%m-%d"
        ).date()

    except ValueError:
        return jsonify({
            "message": "Dates must be in YYYY-MM-DD format"
        }), 400
        
    if end_date < start_date:
        return jsonify({
            "message": "End date cannot be before start date"
        }), 400

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
        return jsonify({
            "message" : error
        }), 400

    return jsonify({
        "message": "Travel request created successfully",
        "travel_id": travel_request.travel_id,
        "employee_id": travel_request.employee_id,
        "source": travel_request.source,
        "destination": travel_request.destination,
        "purpose": travel_request.purpose,
        "status": travel_request.status,
        "travel_request_number": travel_request.travel_request_number
    }), 201


    