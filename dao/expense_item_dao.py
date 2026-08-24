from config.database import db
from models.expense_item import ExpenseItem


def get_expense_item_by_id(item_id):
    return ExpenseItem.query.filter_by(ex_item_id=item_id).first()


def get_expense_items_by_claim_id(claim_id):
    return ExpenseItem.query.filter_by(claim_id=claim_id).all()


def create_expense_item(claim_id, category_id, amount, expense_date, description):
    expense_item = ExpenseItem(
        claim_id=claim_id,
        category_id=category_id,
        amount=amount,
        expense_date=expense_date,
        description=description
    )
    db.session.add(expense_item)
    db.session.commit()
    return expense_item


def update_expense_item(expense_item, category_id=None, amount=None, expense_date=None, description=None):
    if category_id is not None:
        expense_item.category_id = category_id
    if amount is not None:
        expense_item.amount = amount
    if expense_date is not None:
        expense_item.expense_date = expense_date
    if description is not None:
        expense_item.description = description
    db.session.commit()
    return expense_item


def delete_expense_item(expense_item):
    db.session.delete(expense_item)
    db.session.commit()
