from config.database import db
from models.expense_receipt import ExpenseReceipt


def get_receipt_by_id(receipt_id):
    return ExpenseReceipt.query.filter_by(ex_receipt_id=receipt_id).first()


def get_receipts_by_item_id(item_id):
    return ExpenseReceipt.query.filter_by(expense_item_id=item_id).all()


def create_expense_receipt(expense_item_id, file_name, file_path, file_size):
    expense_receipt = ExpenseReceipt(
        expense_item_id=expense_item_id,
        file_name=file_name,
        file_path=file_path,
        file_size=file_size
    )
    db.session.add(expense_receipt)
    db.session.commit()
    return expense_receipt
