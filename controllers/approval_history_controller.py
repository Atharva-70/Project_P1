from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from services.approval_history_service import get_claim_history

approval_history_bp = Blueprint("approval_history", __name__)
@approval_history_bp.route("/expense_claim/<int:claim_id>/history", methods=['GET'])
@jwt_required()
def get_history(claim_id):
    timeline, error = get_claim_history(claim_id)
    if error:
        return jsonify({"message": error}), 404

    return jsonify(timeline), 200