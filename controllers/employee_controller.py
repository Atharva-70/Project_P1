from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.role_required import role_required
from utils.serializers import employee_to_dict
from services.employee_service import create_employee,get_my_profile,update_my_profile,get_subordinates

employee_bp = Blueprint("employee", __name__)

@employee_bp.route("/employee", methods=['POST'])
@employee_bp.route("/employees", methods=['POST'])
@jwt_required()
@role_required("ADMIN")
def add_employee():
    data = request.get_json() or {}

    user_id = data.get("user_id")
    emp_code = data.get("emp_code")
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    manager_id = data.get("manager_id")

    if not user_id or not emp_code or not first_name or not last_name:
        return jsonify({"message": "Missing required fields"}), 400

    employee, error = create_employee(
        user_id=user_id,
        emp_code=emp_code,
        first_name=first_name,
        last_name=last_name,
        manager_id=manager_id
    )

    if error:
        return jsonify({"message": error}), 400

    res = employee_to_dict(employee)
    res["message"] = "Employee created successfully"
    return jsonify(res), 201


@employee_bp.route("/employee/me", methods=['GET'])
@employee_bp.route("/employees/me", methods=['GET'])
@jwt_required()
def get_profile():
    user_id = int(get_jwt_identity())
    profile_data, error = get_my_profile(user_id)

    if error:
        return jsonify({"message": error}), 404

    return jsonify(profile_data), 200


@employee_bp.route("/employee/me", methods=['PUT'])
@employee_bp.route("/employees/me", methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}

    first_name = data.get("first_name")
    last_name = data.get("last_name")

    updated_employee, error = update_my_profile(
        user_id=user_id,
        first_name=first_name,
        last_name=last_name
    )

    if error:
        return jsonify({"message": error}), 400

    res = employee_to_dict(updated_employee)
    res["message"] = "Employee profile updated successfully"
    return jsonify(res), 200


@employee_bp.route("/employee/subordinates", methods=['GET'])
@employee_bp.route("/employees/subordinates", methods=['GET'])

@jwt_required()
@role_required("MANAGER", "ADMIN")
def list_subordinates():
    user_id = int(get_jwt_identity())
    subordinates, error = get_subordinates(user_id)

    if error:
        return jsonify({"message": error}), 400

    return jsonify(subordinates), 200