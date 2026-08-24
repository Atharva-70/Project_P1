from decimal import Decimal, InvalidOperation
from dao.expense_policy_dao import (
    get_policy_by_id,
    get_policy_by_category_id,
    get_all_policies,
    create_policy as create_policy_dao,
    update_policy as update_policy_dao,
    delete_policy as delete_policy_dao
)
from dao.expense_category_dao import get_category_by_id


def create_expense_policy(category_id, max_amount):
    category = get_category_by_id(category_id)
    if not category:
        return None, "Expense category not found"

    try:
        dec_amount = Decimal(str(max_amount))
        if dec_amount <= Decimal("0.00"):
            return None, "Maximum allowed amount must be greater than 0"
    except (InvalidOperation, TypeError, ValueError):
        return None, "Invalid max amount value"

    existing_policy = get_policy_by_category_id(category_id)
    if existing_policy:
        return None, "An active policy already exists for this category"

    policy = create_policy_dao(
        category_id=category_id,
        max_amount=dec_amount,
        is_active=True
    )
    return policy, None


def get_all_expense_policies():
    return get_all_policies()


def get_expense_policy_by_id(policy_id):
    policy = get_policy_by_id(policy_id)
    if not policy:
        return None, "Expense policy not found"
    return policy, None


def update_expense_policy(policy_id, max_amount=None, is_active=None):
    policy = get_policy_by_id(policy_id)
    if not policy:
        return None, "Expense policy not found"

    dec_amount = None
    if max_amount is not None:
        try:
            dec_amount = Decimal(str(max_amount))
            if dec_amount <= Decimal("0.00"):
                return None, "Maximum allowed amount must be greater than 0"
        except (InvalidOperation, TypeError, ValueError):
            return None, "Invalid max amount value"

    updated = update_policy_dao(
        policy=policy,
        max_amount=dec_amount,
        is_active=is_active
    )
    return updated, None


def validate_expense_against_policy(category_id, amount):
    policy = get_policy_by_category_id(category_id)
    if policy:
        try:
            item_amount = Decimal(str(amount))
            policy_limit = Decimal(str(policy.max_amount))
            if item_amount > policy_limit:
                return False, f"Expense amount ₹{item_amount} exceeds company policy limit of ₹{policy_limit} for this category"
        except (InvalidOperation, TypeError, ValueError):
            return False, "Invalid expense amount"
    return True, None
