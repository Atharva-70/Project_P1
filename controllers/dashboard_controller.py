from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from utils.role_required import role_required
from services.dashboard_service import search_expense_claims,get_employee_dashboard,get_manager_dashboard,get_finance_dashboard,get_reports_summary

dashboard_bp = Blueprint("dashboard", __name__)
@dashboard_bp.route("/expense_claim/search", methods=["GET"])
@jwt_required()
def search_claims():
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role")

    claim_id = request.args.get("claim_id", type=int)
    employee_id = request.args.get("employee_id", type=int)
    category_id = request.args.get("category_id", type=int)
    status = request.args.get("status")
    min_amount = request.args.get("min_amount", type=float)
    max_amount = request.args.get("max_amount", type=float)
    date_from_str = request.args.get("date_from")
    date_to_str = request.args.get("date_to")

    date_from = None
    date_to = None
    if date_from_str:
        try:
            date_from = datetime.strptime(date_from_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"message": "date_from must be in YYYY-MM-DD format"}), 400

    if date_to_str:
        try:
            date_to = datetime.strptime(date_to_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"message": "date_to must be in YYYY-MM-DD format"}), 400

    results, error = search_expense_claims(
        user_id=user_id,
        role=role,
        claim_id=claim_id,
        employee_id=employee_id,
        category_id=category_id,
        status=status,
        min_amount=min_amount,
        max_amount=max_amount,
        date_from=date_from,
        date_to=date_to
    )

    if error:
        return jsonify({"message": error}), 400

    return jsonify(results), 200


@dashboard_bp.route("/dashboard/employee", methods=["GET"])
@jwt_required()
def employee_dashboard():
    user_id = int(get_jwt_identity())
    dashboard_data, error = get_employee_dashboard(user_id)

    if error:
        return jsonify({"message": error}), 400

    return jsonify(dashboard_data), 200


@dashboard_bp.route("/dashboard/manager", methods=["GET"])
@jwt_required()
@role_required("MANAGER", "ADMIN")
def manager_dashboard():
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role")

    dashboard_data, error = get_manager_dashboard(user_id, role)
    if error:
        return jsonify({"message": error}), 400

    return jsonify(dashboard_data), 200


@dashboard_bp.route("/dashboard/finance", methods=["GET"])
@jwt_required()
@role_required("FINANCE", "ADMIN")
def finance_dashboard():
    dashboard_data, error = get_finance_dashboard()
    if error:
        return jsonify({"message": error}), 400

    return jsonify(dashboard_data), 200


@dashboard_bp.route("/reports/summary", methods=["GET"])
@jwt_required()
@role_required("FINANCE", "ADMIN")
def reports_summary():
    report_data, error = get_reports_summary()
    if error:
        return jsonify({"message": error}), 400

    return jsonify(report_data), 200
