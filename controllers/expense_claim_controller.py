from flask_jwt_extended import get_jwt_identity, jwt_required, get_jwt
from flask import Blueprint, jsonify, request
from utils.role_required import role_required
from utils.serializers import claim_to_dict
from services.expense_claim_service import (
    create_expense_claim,
    get_expense_claims,
    get_expense_claim_by_id,
    update_expense_claim,
    delete_expense_claim,
    submit_expense_claim,
    get_pending_manager_approvals,
    approve_expense_claim_by_manager,
    reject_expense_claim_by_manager,
    get_finance_verification_queue,
    verify_expense_claim_by_finance
)

expense_claim_bp = Blueprint("expense_claim", __name__)


@expense_claim_bp.route("/expense_claim", methods=['POST'])
@expense_claim_bp.route("/expense_claims", methods=['POST'])
@jwt_required()
def create_claim():
    data = request.get_json() or {}

    travel_id = data.get("travel_id")
    total_amount = data.get("total_amount", 0.0)
    claim_number = data.get("claim_number")

    if not travel_id or not claim_number:
        return jsonify({"message": "Missing travel_id or claim_number"}), 400

    user_id = int(get_jwt_identity())
    expense_claim, error = create_expense_claim(
        user_id,
        travel_id,
        total_amount,
        claim_number
    )

    if error:
        return jsonify({"message": error}), 400

    res = claim_to_dict(expense_claim)
    res["message"] = "Expense claim created successfully"
    return jsonify(res), 201


@expense_claim_bp.route("/expense_claim", methods=['GET'])
@expense_claim_bp.route("/expense_claims", methods=['GET'])
@jwt_required()
def get_claims():
    user_id = int(get_jwt_identity())
    expense_claims = get_expense_claims(user_id)
    return jsonify([claim_to_dict(c) for c in expense_claims]), 200


@expense_claim_bp.route("/expense_claim/<int:claim_id>", methods=["GET"])
@expense_claim_bp.route("/expense_claims/<int:claim_id>", methods=["GET"])
@jwt_required()
def get_claim(claim_id):

    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role", "EMPLOYEE")

    expense_claim, error = get_expense_claim_by_id(user_id, claim_id, role=role)
    if error:
        status_code = 403 if "Unauthorized" in error else 404
        return jsonify({"message": error}), status_code

    return jsonify(claim_to_dict(expense_claim)), 200


@expense_claim_bp.route("/expense_claim/<int:claim_id>", methods=['PATCH'])
@jwt_required()
def update_claim(claim_id):
    data = request.get_json() or {}
    user_id = int(get_jwt_identity())

    travel_id = data.get("travel_id")
    total_amount = data.get("total_amount")
    claim_number = data.get("claim_number")

    expense_claim, error = update_expense_claim(
        user_id,
        claim_id,
        travel_id,
        total_amount,
        claim_number
    )

    if error:
        return jsonify({"message": error}), 400

    res = claim_to_dict(expense_claim)
    res["message"] = "Expense claim updated successfully"
    return jsonify(res), 200


@expense_claim_bp.route("/expense_claim/<int:claim_id>", methods=['DELETE'])
@jwt_required()
def delete_claim(claim_id):
    user_id = int(get_jwt_identity())
    _, error = delete_expense_claim(user_id, claim_id)

    if error:
        return jsonify({"message": error}), 400

    return jsonify({
        "message": "Expense claim deleted successfully",
        "expense_claim_id": claim_id
    }), 200


@expense_claim_bp.route("/expense_claim/<int:claim_id>/submit", methods=['POST'])
@jwt_required()
def submit_claim(claim_id):
    user_id = int(get_jwt_identity())
    claim, error = submit_expense_claim(user_id, claim_id)

    if error:
        return jsonify({"message": error}), 400

    return jsonify({
        "message": "Expense claim submitted for approval successfully",
        "expense_claim_id": claim.ex_claim_id,
        "status": claim.status,
        "total_amount": str(claim.total_amount)
    }), 200


@expense_claim_bp.route("/expense_claim/pending-approvals", methods=['GET'])
@jwt_required()
@role_required("MANAGER", "ADMIN")
def pending_approvals():
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role")

    pending_claims, error = get_pending_manager_approvals(user_id, role)
    if error:
        return jsonify({"message": error}), 400

    return jsonify([claim_to_dict(c) for c in pending_claims]), 200


@expense_claim_bp.route("/expense_claim/<int:claim_id>/approve", methods=['POST'])
@jwt_required()
@role_required("MANAGER", "ADMIN")
def approve_claim(claim_id):
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role", "MANAGER")

    data = request.get_json() or {}
    comments = data.get("comments", "Approved by Manager")

    claim, error = approve_expense_claim_by_manager(user_id, claim_id, comments, role=role)
    if error:
        return jsonify({"message": error}), 400

    return jsonify({
        "message": "Expense claim approved successfully",
        "expense_claim_id": claim.ex_claim_id,
        "status": claim.status
    }), 200


@expense_claim_bp.route("/expense_claim/<int:claim_id>/reject", methods=['POST'])
@jwt_required()
@role_required("MANAGER", "ADMIN")
def reject_claim(claim_id):
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role", "MANAGER")

    data = request.get_json() or {}
    comments = data.get("comments")

    claim, error = reject_expense_claim_by_manager(user_id, claim_id, comments, role=role)
    if error:
        return jsonify({"message": error}), 400

    return jsonify({
        "message": "Expense claim rejected successfully",
        "expense_claim_id": claim.ex_claim_id,
        "status": claim.status
    }), 200


@expense_claim_bp.route("/expense_claim/finance-queue", methods=['GET'])
@jwt_required()
@role_required("FINANCE", "ADMIN")
def finance_queue():
    claims = get_finance_verification_queue()
    return jsonify([claim_to_dict(c) for c in claims]), 200


@expense_claim_bp.route("/expense_claim/<int:claim_id>/finance-verify", methods=['POST'])
@jwt_required()
@role_required("FINANCE", "ADMIN")
def finance_verify(claim_id):
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    comments = data.get("comments", "Verified by Finance")

    claim, error = verify_expense_claim_by_finance(user_id, claim_id, comments)
    if error:
        return jsonify({"message": error}), 400

    return jsonify({
        "message": "Expense claim verified by finance successfully",
        "expense_claim_id": claim.ex_claim_id,
        "status": claim.status
    }), 200
