from config.database import db


class Employee(db.Model):
    __tablename__ = "employees"

    e_id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        unique=True,
        nullable=False
    )

    emp_code = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )

    first_name = db.Column(
        db.String(100),
        nullable=False
    )

    last_name = db.Column(
        db.String(100),
        nullable=False
    )

    manager_id = db.Column(
        db.Integer,
        db.ForeignKey("employees.e_id"),
        nullable=True
    )

    # Self-referential relationship for manager hierarchy
    manager = db.relationship(
        "Employee",
        remote_side=[e_id],
        backref="subordinates"
    )