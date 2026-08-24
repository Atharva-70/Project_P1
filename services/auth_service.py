import bcrypt
from dao.user_dao import get_user_by_email, create_user, get_user_by_id, update_user_password
from dao.employee_dao import create_employee
from constants.status import UserRole


def hash_password(password: str) -> str:
    pass_bytes = password.encode("utf-8")
    hashed_pass = bcrypt.hashpw(pass_bytes, bcrypt.gensalt())
    return hashed_pass.decode("utf-8")


def verify_password(password: str, stored_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))


def register_user(email, password, role=UserRole.EMPLOYEE, first_name=None, last_name=None):
    existing = get_user_by_email(email)
    if existing:
        return None, "User already exists"

    hashed = hash_password(password)
    new_user = create_user(
        email=email,
        password_hash=hashed,
        role=role
    )

    fn = first_name.strip() if first_name else email.split('@')[0].capitalize()
    ln = last_name.strip() if last_name else ""
    emp_code = f"EMP-{new_user.id:04d}"

    create_employee(
        user_id=new_user.id,
        emp_code=emp_code,
        first_name=fn,
        last_name=ln
    )

    return new_user, None


def login_user(email, password):
    user = get_user_by_email(email)

    if not user:
        return None, "User not found"

    if not verify_password(password, user.password_hash):
        return None, "Invalid password"

    if not user.is_active:
        return None, "User Account is inactive"

    return user, None


def change_password(user_id, current_password, new_password):
    user = get_user_by_id(user_id)
    if not user:
        return None, "User not found"

    if not verify_password(current_password, user.password_hash):
        return None, "Current password is incorrect"

    if len(new_password) < 6:
        return None, "New password must be at least 6 characters"

    new_hash = hash_password(new_password)
    update_user_password(user_id, new_hash)
    return user, None
