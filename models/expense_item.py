from config.database import db

class ExpenseItem(db.Model):
    __tablename__ = "expense_items"

    ex_item_id = db.Column(
        db.Integer,
        primary_key = True
    )

    claim_id = db.Column(
        db.Integer,
        db.ForeignKey("expense_claims.ex_claim_id"),
        nullable = False
    )

    category_id = db.Column(
        db.Integer,
        db.ForeignKey("expense_categories.ex_category_id"),
        nullable = False
    )

    amount = db.Column(
        db.Numeric(10,2),
        nullable = False
    )

    expense_date = db.Column(
        db.Date,
        nullable = False
    )

    description = db.Column(
        db.String(1000),
    )