from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from flask import Blueprint, jsonify, request
from utils.serializers import user_to_dict
from services.auth_service import register_user, login_user
from constants.status import UserRole

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=['POST'])
def register():
    data = request.get_json() or {}

    email = data.get("email")
    password = data.get("password")
    role = data.get("role", UserRole.EMPLOYEE)
    first_name = data.get("first_name")
    last_name = data.get("last_name")

    if not email or not password:
        return jsonify({"message": "Email and password are required"}), 400

    user, error = register_user(
        email=email,
        password=password,
        role=role,
        first_name=first_name,
        last_name=last_name
    )

    if error:
        return jsonify({"message": error}), 400

    res = user_to_dict(user)
    res["message"] = "User registered successfully"
    return jsonify(res), 201


@auth_bp.route("/login", methods=['POST'])
def login():
    data = request.get_json() or {}

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"message": "Email and password are required"}), 400

    user, error = login_user(email=email, password=password)

    if error:
        return jsonify({"message": error}), 401

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            "role": user.role,
            "email": user.email
        }
    )

    return jsonify({
        "message": "Login successfully",
        "access_token": access_token,
        "email": user.email,
        "role": user.role,
        "user_id": user.id
    }), 200



@auth_bp.route("/profile", methods=['GET'])
@jwt_required()
def profile():
    user_id = get_jwt_identity()
    claims = get_jwt()
    return jsonify({
        "user_id": user_id,
        "role": claims.get("role")
    }), 200