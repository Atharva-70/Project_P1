from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from utils.serializers import item_to_dict
from services.expense_item_service import create_expense_item,get_items_by_claim,update_expense_item,delete_expense_item


expense_item_bp = Blueprint("expense_item", __name__)


@expense_item_bp.route("/expense_item", methods=['POST'])
@expense_item_bp.route("/expense_items", methods=['POST'])
@jwt_required()
def create_item():
    data = request.get_json() or {}

    claim_id = data.get("claim_id")
    category_id = data.get("category_id")
    amount = data.get("amount")
    expense_date = data.get("expense_date")
    description = data.get("description")

    if not claim_id or not category_id or amount is None or not expense_date or not description:
        return jsonify({"message": "Missing required fields"}), 400

    try:
        expense_date = datetime.strptime(expense_date, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"message": "Expense date must be in YYYY-MM-DD format"}), 400

    user_id = int(get_jwt_identity())
    expense_item, error = create_expense_item(
        user_id,
        claim_id,
        category_id,
        amount,
        expense_date,
        description
    )

    if error:
        return jsonify({"message": error}), 400

    res = item_to_dict(expense_item)
    res["message"] = "Expense item created successfully"
    return jsonify(res), 201


@expense_item_bp.route("/expense_claim/<int:claim_id>/items", methods=['GET'])
@expense_item_bp.route("/expense_claims/<int:claim_id>/items", methods=['GET'])
@jwt_required()
def get_claim_items(claim_id):
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role", "EMPLOYEE")

    items, error = get_items_by_claim(user_id, claim_id, role=role)
    if error:
        status_code = 403 if "Unauthorized" in error else 404
        return jsonify({"message": error}), status_code

    return jsonify([item_to_dict(item) for item in items]), 200


@expense_item_bp.route("/expense_item/<int:item_id>", methods=['PUT'])
@expense_item_bp.route("/expense_items/<int:item_id>", methods=['PUT'])
@jwt_required()
def update_item(item_id):
    data = request.get_json() or {}
    user_id = int(get_jwt_identity())

    category_id = data.get("category_id")
    amount = data.get("amount")
    expense_date_str = data.get("expense_date")
    description = data.get("description")

    expense_date = None
    if expense_date_str:
        try:
            expense_date = datetime.strptime(expense_date_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"message": "Expense date must be in YYYY-MM-DD format"}), 400

    updated_item, error = update_expense_item(
        user_id=user_id,
        item_id=item_id,
        category_id=category_id,
        amount=amount,
        expense_date=expense_date,
        description=description
    )

    if error:
        return jsonify({"message": error}), 400

    res = item_to_dict(updated_item)
    res["message"] = "Expense item updated successfully"
    return jsonify(res), 200


@expense_item_bp.route("/expense_item/<int:item_id>", methods=['DELETE'])
@expense_item_bp.route("/expense_items/<int:item_id>", methods=['DELETE'])

@jwt_required()
def delete_item(item_id):
    user_id = int(get_jwt_identity())
    _, error = delete_expense_item(user_id, item_id)
    if error:
        return jsonify({"message": error}), 400

    return jsonify({
        "message": "Expense item deleted successfully",
        "expense_item_id": item_id
    }), 200