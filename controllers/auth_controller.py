from services.auth_services import register_user, login_user, verify_password
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

# request - handle HTTP request
# jsonify - sends back json responses
# Blueprint - Groups related routes together

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods = ["POST"])  #API endpoint fo register
def register():
    data = request.get_json()  #returns j-SON😭😭😭 data from postman

    email = data.get("email")                   
    password = data.get("password")             # extracts each value from the j-SON data
    role = data.get("role")   

    if not email or not password or not role:
        return jsonify({"message": "Email, password, and roles are required"}), 400 

    user, error = register_user(email, password, role)

    if error:
        return jsonify({"message": error}), 400

    return jsonify({
        "message": "User registered successfully",
        "user_id": user.id,
        "email": user.email,
        "role": user.role
    }), 201

'''
Blueprint will create a group of authentication routes.
/register
/login
/logout
'''

@auth_bp.route("/login", methods=['POST'])
def login():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({
            "message": "Email and password are required"
        }), 400

    user, error = login_user(email, password)

    if error:
        return jsonify({
            "message": error
        }), 401

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            "role": user.role
        }
    )

    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "user_id": user.id,
        "email": user.email,
        "role": user.role
    }), 200
    
@auth_bp.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    user_id = get_jwt_identity()
    claims = get_jwt()

    return jsonify({
        "message": "Protected route accessed successfully",
        "user_id": user_id,
        "role": claims["role"]
    }), 200