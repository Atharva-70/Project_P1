from flask import Blueprint, request, jsonify
from services.expense_category_service import create_category, get_all_categories, get_category_by_id, update_category, deactivate_category
from flask_jwt_extended import jwt_required
from utils.role_required import role_required

expense_category_bp = Blueprint("expense_category", __name__)

@expense_category_bp.route("/categories", methods=["POST"])
@jwt_required()
@role_required("ADMIN")
def add_category():
    data = request.get_json()

    category_name = data.get("category_name")
    description = data.get("description")

    if not category_name:
        return jsonify({
            "message": "Category name is required"
        }), 400

    category, error = create_category(
        category_name,
        description
    )

    if error:
        return jsonify({
            "message": error
        }), 400

    return jsonify({
        "message": "Category created successfully",
        "category_id": category.ex_category_id,
        "category_name": category.category_name,
        "description": category.description
    }), 201

@expense_category_bp.route("/categories", methods=["GET"])
def get_categories():
    categories = get_all_categories()

    category_list = []

    for category in categories:
        category_list.append({
            "category_id": category.ex_category_id,
            "category_name": category.category_name,
            "description": category.description,
            "is_active": category.is_active
        })

    return jsonify(category_list), 200

@expense_category_bp.route("/categories/<int:category_id>", methods=["GET"])
def get_category(category_id):
    category = get_category_by_id(category_id)

    if not category:
        return jsonify({
            "message": "Category not found"
        }), 404

    return jsonify({
        "category_id": category.ex_category_id,
        "category_name": category.category_name,
        "description": category.description,
        "is_active": category.is_active
    }), 200

@expense_category_bp.route("/categories", methods=["POST"])
@jwt_required()
@role_required("ADMIN")
def update_category_details(category_id):
    data = request.get_json()

    category_name = data.get("category_name")
    description = data.get("description")
    is_active = data.get("is_active")

    category, error = update_category(
        category_id,
        category_name,
        description,
        is_active
    )

    if error:
        return jsonify({
            "message": error
        }), 404

    return jsonify({
        "message": "Category updated successfully",
        "category_id": category.ex_category_id,
        "category_name": category.category_name,
        "description": category.description,
        "is_active": category.is_active
    }), 200

@expense_category_bp.route("/categories", methods=["POST"])
@jwt_required()
@role_required("ADMIN")
def delete_category(category_id):

    category, error = deactivate_category(category_id)

    if error:
        return jsonify({
            "message": error
        }), 404

    return jsonify({
        "message": "Category deactivated successfully",
        "category_id": category.ex_category_id,
        "is_active": category.is_active
    }), 200