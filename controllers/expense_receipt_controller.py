from controllers import expense_category_controller
from flask_jwt_extended import jwt_required
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
from services.expense_receipt_service import create_expense_receipt

expense_receipt_bp = Blueprint("expense_receipt", __name__)
@expense_receipt_bp.route("/expense_receipt", methods=['POST'])
@jwt_required()
def create_receipt():
    expense_item_id = request.form.get("expense_item_id")
    file = request.files.get("file")
    
    if not expense_item_id or not file:
        return jsonify({
            "message": "Expense item ID and file are required"
        }), 400

    filename = secure_filename(file.filename)
    upload_folder = "uploads/receipts"

    os.makedirs(
        upload_folder,
        exist_ok=True
    )
    

    file_path = os.path.join(
        upload_folder,
        filename
    )
    
    file.save(file_path)

    file_size = os.path.getsize(file_path)

    expense_receipt, error = create_expense_receipt(
    int(expense_item_id),
    filename,
    file_path,
    file_size
    )   

    if error:
        return jsonify({
            "message": error
        }), 400

    return jsonify({
        "message": "Expense receipt uploaded successfully",
        "receipt_id": expense_receipt.ex_receipt_id,
        "expense_item_id": expense_receipt.expense_item_id,
        "file_name": expense_receipt.file_name,
        "file_path": expense_receipt.file_path,
        "file_size": expense_receipt.file_size
    }), 201
    