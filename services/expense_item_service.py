from decimal import Decimal, InvalidOperation
from dao.employee_dao import get_employee_by_user_id, get_employee_by_id
from dao.expense_claim_dao import get_claim_by_id, update_expense_claim
from dao.expense_category_dao import get_category_by_id
from dao.expense_item_dao import (
    create_expense_item as create_expense_item_dao,
    get_expense_items_by_claim_id,
    get_expense_item_by_id,
    update_expense_item as update_expense_item_dao,
    delete_expense_item as delete_expense_item_dao
)
from services.expense_policy_service import validate_expense_against_policy
from constants.status import ClaimStatus


def recalculate_claim_total(claim_id):
    claim = get_claim_by_id(claim_id)
    if not claim:
        return
    items = get_expense_items_by_claim_id(claim_id)
    total = sum(Decimal(str(item.amount)) for item in items) if items else Decimal("0.00")
    update_expense_claim(claim, total_amount=total)


def create_expense_item(
    user_id,
    claim_id,
    category_id,
    amount,
    expense_date,
    description
):
    employee = get_employee_by_user_id(user_id)
    if not employee:
        return None, "Employee profile not found"

    expense_claim = get_claim_by_id(claim_id)
    if not expense_claim:
        return None, "Expense claim not found"

    if expense_claim.employee_id != employee.e_id:
        return None, "You cannot add an expense to this claim"

    if expense_claim.status != ClaimStatus.DRAFT:
        return None, f"Items can only be added to DRAFT claims. Current status: {expense_claim.status}"

    try:
        dec_amount = Decimal(str(amount))
        if dec_amount <= Decimal("0.00"):
            return None, "Expense amount must be greater than 0"
    except (InvalidOperation, TypeError, ValueError):
        return None, "Invalid expense amount value"

    category = get_category_by_id(category_id)
    if not category:
        return None, "Expense category not found"

    is_valid, policy_error = validate_expense_against_policy(category_id, dec_amount)
    if not is_valid:
        return None, policy_error

    expense_item = create_expense_item_dao(
        claim_id=claim_id,
        category_id=category_id,
        amount=dec_amount,
        expense_date=expense_date,
        description=description
    )

    recalculate_claim_total(claim_id)
    return expense_item, None


def get_items_by_claim(user_id, claim_id, role="EMPLOYEE"):
    expense_claim = get_claim_by_id(claim_id)
    if not expense_claim:
        return None, "Expense claim not found"

    employee = get_employee_by_user_id(user_id)
    if not employee:
        return None, "Employee profile not found"

    # Authorization guard: owner, manager of owner, FINANCE, or ADMIN
    if role not in ["ADMIN", "FINANCE"]:
        if isinstance(expense_claim.employee_id, int) and isinstance(employee.e_id, int):
            if expense_claim.employee_id != employee.e_id:
                claim_owner = get_employee_by_id(expense_claim.employee_id)
                if not claim_owner or claim_owner.manager_id != employee.e_id:
                    return None, "Unauthorized access to expense items"

    items = get_expense_items_by_claim_id(claim_id)
    return items, None



def update_expense_item(
    user_id,
    item_id,
    category_id=None,
    amount=None,
    expense_date=None,
    description=None
):
    employee = get_employee_by_user_id(user_id)
    if not employee:
        return None, "Employee profile not found"

    expense_item = get_expense_item_by_id(item_id)
    if not expense_item:
        return None, "Expense item not found"

    claim = get_claim_by_id(expense_item.claim_id)
    if not claim:
        return None, "Associated claim not found"

    if claim.employee_id != employee.e_id:
        return None, "You are not authorized to update this expense item"

    if claim.status != ClaimStatus.DRAFT:
        return None, f"Only items in DRAFT claims can be updated. Current claim status: {claim.status}"

    target_category_id = category_id if category_id is not None else expense_item.category_id

    dec_amount = None
    if amount is not None:
        try:
            dec_amount = Decimal(str(amount))
            if dec_amount <= Decimal("0.00"):
                return None, "Expense amount must be greater than 0"
        except (InvalidOperation, TypeError, ValueError):
            return None, "Invalid expense amount value"
    else:
        dec_amount = Decimal(str(expense_item.amount))

    if category_id is not None:
        category = get_category_by_id(category_id)
        if not category:
            return None, "Expense category not found"

    is_valid, policy_error = validate_expense_against_policy(target_category_id, dec_amount)
    if not is_valid:
        return None, policy_error

    updated_item = update_expense_item_dao(
        expense_item=expense_item,
        category_id=category_id,
        amount=dec_amount,
        expense_date=expense_date,
        description=description
    )

    recalculate_claim_total(claim.ex_claim_id)
    return updated_item, None


def delete_expense_item(user_id, item_id):
    employee = get_employee_by_user_id(user_id)
    if not employee:
        return None, "Employee profile not found"

    expense_item = get_expense_item_by_id(item_id)
    if not expense_item:
        return None, "Expense item not found"

    claim = get_claim_by_id(expense_item.claim_id)
    if not claim:
        return None, "Associated claim not found"

    if claim.employee_id != employee.e_id:
        return None, "You are not authorized to delete this expense item"

    if claim.status != ClaimStatus.DRAFT:
        return None, f"Only items in DRAFT claims can be deleted. Current claim status: {claim.status}"

    claim_id = claim.ex_claim_id
    delete_expense_item_dao(expense_item)

    recalculate_claim_total(claim_id)
    return True, None