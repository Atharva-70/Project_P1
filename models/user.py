from config.database import db
from constants.status import UserRole


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(
        db.String(200),
        unique=True,
        nullable=False
    )
    password_hash = db.Column(
        db.String(255),
        nullable=False
    )
    role = db.Column(
        db.String(30),
        nullable=False,
        default=UserRole.EMPLOYEE
    )
    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    employee = db.relationship("Employee", backref="user", uselist=False)
