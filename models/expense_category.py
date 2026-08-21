from config.database import db

class ExpenseCategory(db.Model):

    __tablename__ = "expense_categories"

    ex_category_id = db.Column(
        db.Integer,
        primary_key = True
    )

    category_name = db.Column(
        db.String(255),
        unique = True,
        nullable = False
    )

    description = db.Column(
        db.String(255),
        nullable = True
    )

    is_active = db.Column(
        db.Boolean,
        nullable = False,
        default = True
    )