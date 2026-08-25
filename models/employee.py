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

    phone = db.Column(
        db.String(20),
        nullable=True
    )

    department = db.Column(
        db.String(100),
        nullable=True
    )

    bank_account_number = db.Column(
        db.String(50),
        nullable=True
    )

    bank_ifsc_code = db.Column(
        db.String(20),
        nullable=True
    )

    manager_id = db.Column(
        db.Integer,
        db.ForeignKey("employees.e_id"),
        nullable=True
    )

