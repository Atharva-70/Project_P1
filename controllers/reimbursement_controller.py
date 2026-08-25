from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.role_required import role_required
from utils.serializers import reimbursement_to_dict
from services.reimbursement_service import process_claim_reimbursement, get_reimbursement_by_claim,get_all_processed_reimbursements


reimbursement_bp = Blueprint("reimbursement", __name__)


@reimbursement_bp.route("/reimbursements/process", methods=["POST"])
@reimbursement_bp.route("/reimbursement/process", methods=["POST"])
@jwt_required()
@role_required("FINANCE", "ADMIN")
def process_payout():
    data = request.get_json() or {}

    claim_id = data.get("claim_id")
    payment_reference = data.get("payment_reference")

    if not claim_id or not payment_reference:
        return jsonify({"message": "claim_id and payment_reference are required"}), 400

    user_id = int(get_jwt_identity())
    reimbursement, error = process_claim_reimbursement(
        user_id=user_id,
        claim_id=claim_id,
        payment_reference=payment_reference
    )

    if error:
        return jsonify({"message": error}), 400

    res = reimbursement_to_dict(reimbursement)
    res["message"] = "Reimbursement payment processed successfully"
    return jsonify(res), 200


@reimbursement_bp.route("/reimbursements", methods=["GET"])
@reimbursement_bp.route("/reimbursement", methods=["GET"])
@jwt_required()
@role_required("FINANCE", "ADMIN")
def list_reimbursements():
    reimbursements = get_all_processed_reimbursements()
    return jsonify([reimbursement_to_dict(r) for r in reimbursements]), 200


@reimbursement_bp.route("/reimbursements/claim/<int:claim_id>", methods=["GET"])
@reimbursement_bp.route("/reimbursement/claim/<int:claim_id>", methods=["GET"])
@jwt_required()
def get_claim_payout(claim_id):

    reimbursement, error = get_reimbursement_by_claim(claim_id)
    if error:
        return jsonify({"message": error}), 404

    return jsonify(reimbursement_to_dict(reimbursement)), 200

