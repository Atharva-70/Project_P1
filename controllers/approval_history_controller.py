from flask_jwt_extended import get_jwt_identity
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from services.approval_history_service import process_claim_action

approval_history_bp = Blueprint("approval_history", __name__)

@approval_history_bp.route("/approval_history", methods=['POST'])
@jwt_required()
def approval_history():
    data = request.get_json()

    claim_id = data.get("claim_id")
    action = data.get("action")
    comments = data.get("comments")

    if not claim_id or not action or not comments:
        return jsonify({
            "message": "All fields are required"
        }), 400
    action_by = int(get_jwt_identity())
    history, error = process_claim_action(claim_id, action, action_by, comments)
    
    if error:
        return jsonify({
            "message" : error
        }), 400

    return jsonify({
        "message" : "Claim action processed successfully",
        "approval_id" : history.approval_id,
        "claim_id" : history.claim_id,
        "action" : history.action,
        "comments" : history.comments,
        "action_at" : history.action_at.isoformat()
    }), 201