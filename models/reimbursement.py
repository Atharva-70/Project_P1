from config.database import db
from constants.status import ReimbursementStatus


class Reimbursement(db.Model):
    __tablename__ = "reimbursements"

    reim_id = db.Column(
        db.Integer,
        primary_key=True
    )

    claim_id = db.Column(
        db.Integer,
        db.ForeignKey("expense_claims.ex_claim_id"),
        nullable=False,
        unique=True
    )

    amount = db.Column(
        db.Numeric(10, 2),
        nullable=False
    )

    status = db.Column(
        db.String(255),
        default=ReimbursementStatus.PENDING,
        nullable=False
    )

    payment_reference = db.Column(
        db.String(255),
        nullable=True
    )

    processed_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    processed_date = db.Column(
        db.Date,
        nullable=True
    )

    # Relationships
    processor = db.relationship("User", backref="processed_reimbursements")


Reimbursements = Reimbursement