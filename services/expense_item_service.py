from config.database import db
from models.expense_item import ExpenseItem
from models.expense_claim import ExpenseClaim
from models.expense_category import ExpenseCategory
from models.employee import Employee


def create_expense_item(
    user_id,
    claim_id,
    category_id,
    amount,
    expense_date,
    description
):
    employee = Employee.query.filter_by(
        user_id=user_id
    ).first()

    if not employee:
        return None, "Employee profile not found"

    expense_claim = ExpenseClaim.query.filter_by(
        ex_claim_id=claim_id
    ).first()

    if expense_claim.employee_id != employee.e_id:
        return None, "You are not allowed to add items to this claim"

    if not expense_claim:
        return None, "Expense claim not found"

    if expense_claim.employee_id != employee.e_id:
        return None, "You cannot add an expense to this claim"

    category = ExpenseCategory.query.filter_by(
        ex_category_id=category_id
    ).first()


    if not category:
        return None, "Expense category not found"

    expense_item = ExpenseItem(
        claim_id=claim_id,
        category_id=category_id,
        amount=amount,
        expense_date=expense_date,
        description=description
    )

    db.session.add(expense_item)
    db.session.commit()

    return expense_item, None