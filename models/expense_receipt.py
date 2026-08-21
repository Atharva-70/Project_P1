from config.database import db

class ExpenseReceipt(db.Model):
    __tablename__ = "expense_receipts"

    ex_receipt_id= db.Column(
        db.Integer,
        primary_key = True
    )

    expense_item_id = db.Column(
        db.Integer,
        db.ForeignKey("expense_items.ex_item_id"),
        nullable = False
    )

    file_name = db.Column(
        db.String(255),
        nullable = False
    )

    file_path = db.Column(
        db.String(255),
        nullable = False
    )

    file_size = db.Column(
        db.Integer,
        nullable = False
    )