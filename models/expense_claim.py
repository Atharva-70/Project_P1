from config.database import db

class ExpenseClaim(db.Model):
    __tablename__ = "expense_claims"

    ex_claim_id = db.Column(
        db.Integer,
        primary_key = True
    )

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("employees.e_id"),
        nullable = False
    )

    travel_id = db.Column(
        db.Integer,
        db.ForeignKey("travel_requests.travel_id"),
        nullable = False
    )

    total_amount = db.Column(
        db.Numeric(10,2),
        nullable = False
    )

    status = db.Column(
        db.String(255),
        nullable = False,
        default = "DRAFT"
    )

    claim_number = db.Column(
        db.String(255),
        unique = True,
        nullable = False
    )