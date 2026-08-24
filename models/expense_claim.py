from config.database import db
from constants.status import ClaimStatus


class ExpenseClaim(db.Model):
    __tablename__ = "expense_claims"

    ex_claim_id = db.Column(
        db.Integer,
        primary_key=True
    )

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("employees.e_id"),
        nullable=False
    )

    travel_id = db.Column(
        db.Integer,
        db.ForeignKey("travel_requests.travel_id"),
        nullable=False
    )

    total_amount = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=0.00
    )

    status = db.Column(
        db.String(255),
        nullable=False,
        default=ClaimStatus.DRAFT
    )

    claim_number = db.Column(
        db.String(255),
        unique=True,
        nullable=False
    )

    # Relationships
    employee = db.relationship("Employee", backref="expense_claims")
    travel_request = db.relationship("TravelRequest", backref="expense_claims")
    items = db.relationship("ExpenseItem", backref="claim", cascade="all, delete-orphan")
    history = db.relationship("ApprovalHistory", backref="claim", cascade="all, delete-orphan", order_by="ApprovalHistory.action_at")
    reimbursement = db.relationship("Reimbursement", backref="claim", uselist=False)