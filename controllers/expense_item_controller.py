from flask_jwt_extended import get_jwt_identity
from logging import error
from datetime import datetime
from flask import jsonify
from flask_jwt_extended import jwt_required
from flask import Blueprint, request
from services.expense_item_service import create_expense_item

expense_item_bp = Blueprint("expense_item", __name__)
@expense_item_bp.route("/expense_item", methods=['POST'])
@jwt_required()
def create_item():
    data = request.get_json()

    claim_id = data.get("claim_id")
    category_id = data.get("category_id")
    amount = data.get("amount")
    expense_date = data.get("expense_date")
    description = data.get("description")

    if not claim_id or not category_id or amount is None or not expense_date or not description:
        return jsonify({
            "message" : "Missing required fields"
        }), 400

    

    try:
        expense_date = datetime.strptime(
            expense_date, 
            "%Y-%m-%d"
        ).date()

    except ValueError:
        return jsonify({
            "message" : "Expense date must be in YYYY-MM-DD format"
        }), 400

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
        return jsonify({
            "message": error
        }), 400

    return jsonify({
        "message": "Expense item created successfully",
        "expense_item_id": expense_item.ex_item_id,
        "claim_id": expense_item.claim_id,
        "category_id": expense_item.category_id,
        "amount": str(expense_item.amount),
        "expense_date": expense_item.expense_date.isoformat(),
        "description": expense_item.description
    }), 201

    
        