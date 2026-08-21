from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask import Blueprint, jsonify, request
from services.expense_claim_service import create_expense_claim, get_expense_claims, get_expense_claim_by_id

expense_claim_bp = Blueprint("expense_claim", __name__)

@expense_claim_bp.route("/expense_claim", methods=['POST'])
@jwt_required()
def create_claim():
    data = request.get_json()

    travel_id = data.get("travel_id")
    total_amount = data.get("total_amount")
    claim_number = data.get("claim_number")

    if not travel_id or total_amount is None or not claim_number:
        return jsonify({
            "message" : "missing fields"
        }), 400

    user_id = int(get_jwt_identity())

    expense_claim, error = create_expense_claim(
        user_id,
        travel_id,
        total_amount,
        claim_number
    )

    if error:
        return jsonify({
            "message" : error
        }), 400

    return jsonify({
        "message" : "expense_claim created successfully",
        "expense_claim_id" : expense_claim.ex_claim_id,
        "employee_id" : expense_claim.employee_id,
        "travel_id" : expense_claim.travel_id,
        "total_amount": str(expense_claim.total_amount),
        "status" : expense_claim.status,
        "claim_number" : expense_claim.claim_number
    }), 201

@expense_claim_bp.route("/expense_claim", methods=['GET'])
@jwt_required()
def get_claims():
    user_id = int(get_jwt_identity())
    expense_claims = get_expense_claims(user_id)
    claims_data = []
    for claim in expense_claims:
        claims_data.append({
            "expense_claim_id" : claim.ex_claim_id,
            "employee_id" : claim.employee_id,
            "travel_id" : claim.travel_id,
            "total_amount": str(claim.total_amount),
            "status" : claim.status,
            "claim_number" : claim.claim_number
        })
    return jsonify(claims_data), 200

@expense_claim_bp.route(
    "/expense_claim/<int:claim_id>",
    methods=["GET"]
)
@jwt_required()
def get_claim(claim_id):

    user_id = int(get_jwt_identity())

    expense_claim, error = get_expense_claim_by_id(
        user_id,
        claim_id
    )

    if error:
        return jsonify({
            "message": error
        }), 404

    return jsonify({
        "expense_claim_id": expense_claim.ex_claim_id,
        "employee_id": expense_claim.employee_id,
        "travel_id": expense_claim.travel_id,
        "total_amount": str(expense_claim.total_amount),
        "status": expense_claim.status,
        "claim_number": expense_claim.claim_number
    }), 200
