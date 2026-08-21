from config.database import db
from models.expense_receipt import ExpenseReceipt
from models.expense_item import ExpenseItem

def create_expense_receipt(
    expense_item_id,
    file_name,
    file_path,
    file_size
):
    expense_item = ExpenseItem.query.filter_by(
        ex_item_id = expense_item_id
    ).first()

    if not expense_item:
        return None, "Expense item not found"

    expense_receipt = ExpenseReceipt(
        expense_item_id = expense_item_id,
        file_name = file_name,
        file_path = file_path,
        file_size = file_size
    )

    db.session.add(expense_receipt)
    db.session.commit()
    
    return expense_receipt, None
    