from config.database import db
from models.user import User


def get_user_by_email(email):
    return User.query.filter_by(email=email).first()


def get_user_by_id(user_id):
    return User.query.filter_by(id=user_id).first()


def create_user(email, password_hash, role):
    new_user = User(
        email=email,
        password_hash=password_hash,
        role=role
    )
    db.session.add(new_user)
    db.session.commit()
    return new_user


def update_user_password(user_id, new_password_hash):
    user = User.query.filter_by(id=user_id).first()
    if user:
        user.password_hash = new_password_hash
        db.session.commit()
    return user
