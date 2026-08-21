import bcrypt
from config.database import db
from models.user import User


def hash_password(password):
    pass_bytes = password.encode("utf-8")

    hashed_pass = bcrypt.hashpw(
        pass_bytes,
        bcrypt.gensalt()
    )

    return hashed_pass.decode("utf-8")


def verify_password(password, stored_hash):
    return bcrypt.checkpw(
        password.encode("utf-8"),
        stored_hash.encode("utf-8")
    )

def register_user(email, password, role):
    existing = User.query.filter_by(email = email).first()
    if existing:
        return None, "User already exists"

    hashed = hash_password(password)
    new_user = User(
        email = email,
        password_hash = hashed,
        role = role
    )

    db.session.add(new_user)
    db.session.commit()

    return new_user, None


def login_user(email, password):
    user = User.query.filter_by(email=email).first()

    if not user:
        return None, "User not found"

    if not verify_password(password, user.password_hash):
        return None, "Invalid password"

    if not user.is_active:
        return None, "User Account is inactive"

    return user, None
    