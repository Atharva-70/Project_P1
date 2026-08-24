from config.database import db
from datetime import datetime

class ApprovalHistory(db.Model):
    __tablename__ = "approval_history"

    approval_id = db.Column(
        db.Integer,
        primary_key = True
    )

    claim_id = db.Column(
        db.Integer,
        db.ForeignKey("expense_claims.ex_claim_id"),
        nullable = False
    )

    action = db.Column(
        db.String(255),
        nullable  = False
    )

    action_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable = False
    )

    comments = db.Column(
        db.String(255),
        nullable = False
    )

    action_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    # Relationships
    user = db.relationship("User", backref="approval_actions")

