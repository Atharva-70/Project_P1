from config.database import db
from constants.status import TravelStatus


class TravelRequest(db.Model):
    __tablename__ = "travel_requests"

    travel_id = db.Column(
        db.Integer,
        primary_key=True
    )

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("employees.e_id"),
        nullable=False
    )

    source = db.Column(
        db.String(255),
        nullable=False
    )

    destination = db.Column(
        db.String(255),
        nullable=False
    )

    purpose = db.Column(
        db.String(255),
        nullable=False
    )

    start_date = db.Column(
        db.Date,
        nullable=False
    )

    end_date = db.Column(
        db.Date,
        nullable=False
    )

    status = db.Column(
        db.String(255),
        nullable=False,
        default=TravelStatus.PENDING
    )

    travel_request_number = db.Column(
        db.String(255),
        unique=True,
        nullable=False
    )

    # Relationships
    employee = db.relationship("Employee", backref="travel_requests")
