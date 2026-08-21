from config.database import db

class ExpensePolicy(db.Model):
    __tablename__ = "expense_policies"

    ex_policy_id = db.Column(
        db.Integer,
        primary_key = True
    )

    category_id = db.Column(
        db.Integer,
        db.ForeignKey("expense_categories.ex_category_id"),
        nullable = False,
        unique = True
    )

    max_amount = db.Column(
        db.Numeric(10, 2),
        nullable = False
    )

    is_active = db.Column(
        db.Boolean,
        nullable = False,
        default = True
    )