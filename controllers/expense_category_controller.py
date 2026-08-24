from flask_jwt_extended import jwt_required
from flask import Blueprint, jsonify, request
from utils.role_required import role_required
from utils.serializers import category_to_dict
from services.expense_category_service import (
    create_category,
    get_all_expense_categories,
    get_expense_category_by_id,
    update_category,
    deactivate_category
)

expense_category_bp = Blueprint("expense_category", __name__)


@expense_category_bp.route("/expense_category", methods=['POST'])
@expense_category_bp.route("/categories", methods=['POST'])
@jwt_required()
@role_required("ADMIN")
def add_category():
    data = request.get_json() or {}

    category_name = data.get("category_name")
    description = data.get("description")

    if not category_name or not description:
        return jsonify({"message": "Missing category_name or description"}), 400

    category, error = create_category(category_name, description)
    if error:
        return jsonify({"message": error}), 400

    res = category_to_dict(category)
    res["message"] = "Expense category created successfully"
    return jsonify(res), 201


@expense_category_bp.route("/expense_category", methods=['GET'])
@expense_category_bp.route("/categories", methods=['GET'])
@jwt_required()
def get_categories():
    categories = get_all_expense_categories()
    return jsonify([category_to_dict(c) for c in categories]), 200


@expense_category_bp.route("/expense_category/<int:category_id>", methods=['GET'])
@expense_category_bp.route("/categories/<int:category_id>", methods=['GET'])
@jwt_required()
def get_category(category_id):
    category, error = get_expense_category_by_id(category_id)
    if error:
        return jsonify({"message": error}), 404

    return jsonify(category_to_dict(category)), 200


@expense_category_bp.route("/expense_category/<int:category_id>", methods=['PATCH'])
@expense_category_bp.route("/categories/<int:category_id>", methods=['PATCH'])
@jwt_required()
@role_required("ADMIN")
def update_category_details(category_id):
    data = request.get_json() or {}

    category_name = data.get("category_name")
    description = data.get("description")
    is_active = data.get("is_active")

    category, error = update_category(
        category_id=category_id,
        category_name=category_name,
        description=description,
        is_active=is_active
    )
    if error:
        return jsonify({"message": error}), 400

    res = category_to_dict(category)
    res["message"] = "Expense category updated successfully"
    return jsonify(res), 200


@expense_category_bp.route("/expense_category/<int:category_id>", methods=['DELETE'])
@expense_category_bp.route("/categories/<int:category_id>", methods=['DELETE'])
@jwt_required()
@role_required("ADMIN")
def delete_category(category_id):
    category, error = deactivate_category(category_id)
    if error:
        return jsonify({"message": error}), 400

    return jsonify({
        "message": "Expense category deactivated successfully",
        "category_id": category_id
    }), 200