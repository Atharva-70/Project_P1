from flask_jwt_extended import jwt_required
from flask import Blueprint, jsonify, request
from utils.role_required import role_required
from utils.serializers import policy_to_dict
from services.expense_policy_service import  create_expense_policy, get_all_expense_policies, get_expense_policy_by_id, update_expense_policy


expense_policy_bp = Blueprint("expense_policy", __name__)


@expense_policy_bp.route("/expense_policy", methods=['POST'])
@expense_policy_bp.route("/policies", methods=['POST'])
@jwt_required()
@role_required("ADMIN")
def add_policy():
    data = request.get_json() or {}

    category_id = data.get("category_id")
    max_amount = data.get("max_amount")

    if not category_id or max_amount is None:
        return jsonify({"message": "Missing category_id or max_amount"}), 400

    policy, error = create_expense_policy(category_id, max_amount)
    if error:
        return jsonify({"message": error}), 400

    res = policy_to_dict(policy)
    res["message"] = "Expense policy created successfully"
    return jsonify(res), 201


@expense_policy_bp.route("/expense_policy", methods=['GET'])
@expense_policy_bp.route("/policies", methods=['GET'])
@jwt_required()
def get_policies():
    policies = get_all_expense_policies()
    return jsonify([policy_to_dict(p) for p in policies]), 200


@expense_policy_bp.route("/expense_policy/<int:policy_id>", methods=['GET'])
@expense_policy_bp.route("/policies/<int:policy_id>", methods=['GET'])
@jwt_required()
def get_policy(policy_id):
    policy, error = get_expense_policy_by_id(policy_id)
    if error:
        return jsonify({"message": error}), 404

    return jsonify(policy_to_dict(policy)), 200


@expense_policy_bp.route("/expense_policy/<int:policy_id>", methods=['PATCH'])
@expense_policy_bp.route("/policies/<int:policy_id>", methods=['PATCH'])
@jwt_required()
@role_required("ADMIN")
def update_policy_details(policy_id):
    data = request.get_json() or {}

    max_amount = data.get("max_amount")
    is_active = data.get("is_active")

    policy, error = update_expense_policy(
        policy_id=policy_id,
        max_amount=max_amount,
        is_active=is_active
    )
    if error:
        return jsonify({"message": error}), 400

    res = policy_to_dict(policy)
    res["message"] = "Expense policy updated successfully"
    return jsonify(res), 200
