import os
from flask import Blueprint, request, jsonify, send_file, session
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from utils.serializers import receipt_to_dict
from services.expense_receipt_service import (
    upload_and_save_receipt,
    get_receipt_for_download
)

expense_receipt_bp = Blueprint("expense_receipt", __name__)


@expense_receipt_bp.route("/expense_receipt", methods=['POST'])
@expense_receipt_bp.route("/expense_receipts", methods=['POST'])
@jwt_required()
def create_receipt():
    expense_item_id = request.form.get("expense_item_id")
    file = request.files.get("file")

    if not expense_item_id or not file:
        return jsonify({"message": "Expense item ID and file are required"}), 400

    user_id = int(get_jwt_identity())

    expense_receipt, error, status_code = upload_and_save_receipt(
        user_id=user_id,
        expense_item_id=int(expense_item_id),
        file=file
    )

    if error:
        return jsonify({"message": error}), status_code

    res = receipt_to_dict(expense_receipt)
    res["message"] = "Expense receipt uploaded successfully"
    return jsonify(res), status_code


@expense_receipt_bp.route("/expense_receipt/<int:receipt_id>/download", methods=['GET'])
@expense_receipt_bp.route("/expense_receipts/<int:receipt_id>/download", methods=['GET'])
@jwt_required(optional=True)
def download_receipt(receipt_id):
    jwt_id = get_jwt_identity()
    if jwt_id:
        user_id = int(jwt_id)
        claims = get_jwt()
        role = claims.get("role")
    else:
        user_id = session.get("user_id")
        role = session.get("role")

    if not user_id:
        return jsonify({"message": "Authentication required"}), 401

    receipt, error, status_code = get_receipt_for_download(user_id, role, receipt_id)
    if error:
        return jsonify({"message": error}), status_code

    if not os.path.exists(receipt.file_path):
        return jsonify({"message": "File not found on server disk"}), 404

    return send_file(
        receipt.file_path,
        as_attachment=True,
        download_name=receipt.file_name
    )


@expense_receipt_bp.route("/expense_receipt/<int:receipt_id>/view", methods=['GET'])
@expense_receipt_bp.route("/expense_receipts/<int:receipt_id>/view", methods=['GET'])

@jwt_required(optional=True)
def view_receipt(receipt_id):
    jwt_id = get_jwt_identity()
    if jwt_id:
        user_id = int(jwt_id)
        claims = get_jwt()
        role = claims.get("role")
    else:
        user_id = session.get("user_id")
        role = session.get("role")

    if not user_id:
        return jsonify({"message": "Authentication required"}), 401

    receipt, error, status_code = get_receipt_for_download(user_id, role, receipt_id)
    if error:
        return jsonify({"message": error}), status_code

    if not os.path.exists(receipt.file_path):
        return jsonify({"message": "File not found on server disk"}), 404

    return send_file(
        receipt.file_path,
        as_attachment=False
    )