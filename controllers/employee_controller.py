from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from services.employee_service import create_employee


employee_bp = Blueprint("employee", __name__)


@employee_bp.route("/employees", methods=["POST"])
@jwt_required()
def add_employee():
    data = request.get_json()

    emp_code = data.get("emp_code")
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    manager_id = data.get("manager_id")

    if not emp_code or not first_name or not last_name:
        return jsonify({
            "message": "Employee code, first name, and last name are required"
        }), 400

    user_id = int(get_jwt_identity())

    employee, error = create_employee(
        user_id,
        emp_code,
        first_name,
        last_name,
        manager_id
    )

    if error:
        return jsonify({
            "message": error
        }), 400

    return jsonify({
        "message": "Employee profile created successfully",
        "employee_id": employee.e_id,
        "user_id": employee.user_id,
        "emp_code": employee.emp_code,
        "first_name": employee.first_name,
        "last_name": employee.last_name,
        "manager_id": employee.manager_id
    }), 201