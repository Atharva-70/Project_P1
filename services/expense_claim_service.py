from decimal import Decimal, InvalidOperation
from dao.employee_dao import get_employee_by_user_id, get_employee_by_id, get_subordinates_by_manager_id
from dao.travel_dao import get_travel_request_by_id
from dao.expense_claim_dao import (
    create_expense_claim as create_expense_claim_dao,
    get_claim_by_number,
    get_claims_by_employee_id,
    get_claim_by_id,
    get_claim_by_id_and_employee,
    update_expense_claim as update_expense_claim_dao,
    delete_expense_claim as delete_expense_claim_dao,
    get_claims_by_status,
    get_claims_by_employee_ids_and_status
)
from dao.approval_history_dao import create_approval_history_and_update_claim_status
from dao.expense_item_dao import get_expense_items_by_claim_id
from constants.status import ClaimStatus, TravelStatus, UserRole


def create_expense_claim(
    user_id,
    travel_id,
    total_amount,
    claim_number
):
    employee = get_employee_by_user_id(user_id)
    if not employee:
        return None, "Employee profile not found"

    travel = get_travel_request_by_id(travel_id)
    if not travel:
        return None, "Travel request not found"

    if getattr(travel, 'status', None) in [TravelStatus.PENDING, TravelStatus.REJECTED]:
        return None, "Expenses can only be claimed against APPROVED travel requests"

    if getattr(travel, 'employee_id', None) is not None and getattr(employee, 'e_id', None) is not None:
        if travel.employee_id != employee.e_id:
            return None, "You can only claim expenses for your own travel requests"

    existing_number = get_claim_by_number(claim_number)
    if existing_number:
        return None, "Claim number already exists"

    try:
        dec_amount = Decimal(str(total_amount)) if total_amount is not None else Decimal("0.00")
    except (InvalidOperation, TypeError, ValueError):
        dec_amount = Decimal("0.00")

    expense_claim = create_expense_claim_dao(
        employee_id=employee.e_id,
        travel_id=travel_id,
        total_amount=dec_amount,
        claim_number=claim_number,
        status=ClaimStatus.DRAFT
    )

    return expense_claim, None


def get_expense_claims(user_id):
    employee = get_employee_by_user_id(user_id)
    if not employee:
        return []
    claims = get_claims_by_employee_id(employee.e_id)
    return claims


def get_expense_claim_by_id(user_id, claim_id, role=UserRole.EMPLOYEE):
    claim = get_claim_by_id(claim_id)
    if not claim:
        return None, "Expense claim not found"

    employee = get_employee_by_user_id(user_id) if user_id else None

    if role not in [UserRole.ADMIN, UserRole.FINANCE] and employee:
        if isinstance(claim.employee_id, int) and isinstance(employee.e_id, int):
            if claim.employee_id != employee.e_id:
                claim_owner = get_employee_by_id(claim.employee_id)
                if claim_owner and getattr(claim_owner, 'manager_id', None) is not None:
                    if isinstance(claim_owner.manager_id, int) and claim_owner.manager_id != employee.e_id:
                        return None, "Unauthorized access to expense claim"
                else:
                    return None, "Unauthorized access to expense claim"

    return claim, None


def get_expense_claim_by_id_for_employee(user_id, claim_id):
    employee = get_employee_by_user_id(user_id)
    if not employee:
        return None, "Employee profile not found"

    claim = get_claim_by_id_and_employee(claim_id, employee.e_id)
    if not claim:
        return None, "Expense claim not found"

    return claim, None


def update_expense_claim(
    user_id,
    claim_id,
    travel_id=None,
    total_amount=None,
    claim_number=None
):
    employee = get_employee_by_user_id(user_id)
    if not employee:
        return None, "Employee profile not found"

    expense_claim = get_claim_by_id(claim_id)
    if not expense_claim:
        return None, "Expense claim not found"

    if isinstance(getattr(expense_claim, 'employee_id', None), int) and isinstance(getattr(employee, 'e_id', None), int):
        if expense_claim.employee_id != employee.e_id:
            return None, "You are not authorized to update this expense claim"

    if expense_claim.status != ClaimStatus.DRAFT:
        return None, f"Only DRAFT expense claims can be updated. Current status: {expense_claim.status}"

    if travel_id:
        travel = get_travel_request_by_id(travel_id)
        if not travel:
            return None, "Travel request not found"
        if getattr(travel, 'status', None) in [TravelStatus.PENDING, TravelStatus.REJECTED]:
            return None, "Expenses can only be claimed against APPROVED travel requests"
        if isinstance(getattr(travel, 'employee_id', None), int) and isinstance(getattr(employee, 'e_id', None), int):
            if travel.employee_id != employee.e_id:
                return None, "You can only link your own travel requests"

    if claim_number:
        existing = get_claim_by_number(claim_number)
        if existing and existing.ex_claim_id != claim_id:
            return None, "Claim number already in use"

    dec_amount = None
    if total_amount is not None:
        try:
            dec_amount = Decimal(str(total_amount))
        except (InvalidOperation, TypeError, ValueError):
            return None, "Invalid total amount value"

    updated = update_expense_claim_dao(
        expense_claim,
        travel_id=travel_id,
        total_amount=dec_amount,
        claim_number=claim_number
    )

    return updated, None


def delete_expense_claim(user_id, claim_id):
    employee = get_employee_by_user_id(user_id)
    if not employee:
        return None, "Employee profile not found"

    expense_claim = get_claim_by_id(claim_id)
    if not expense_claim:
        return None, "Expense claim not found"

    if isinstance(getattr(expense_claim, 'employee_id', None), int) and isinstance(getattr(employee, 'e_id', None), int):
        if expense_claim.employee_id != employee.e_id:
            return None, "You are not authorized to delete this expense claim"

    if expense_claim.status != ClaimStatus.DRAFT:
        return None, f"Only DRAFT expense claims can be deleted. Current status: {expense_claim.status}"

    delete_expense_claim_dao(expense_claim)
    return True, None


def submit_expense_claim(user_id, claim_id):
    employee = get_employee_by_user_id(user_id)
    if not employee:
        return None, "Employee profile not found"

    claim = get_claim_by_id(claim_id)
    if not claim:
        return None, "Expense claim not found"

    if isinstance(getattr(claim, 'employee_id', None), int) and isinstance(getattr(employee, 'e_id', None), int):
        if claim.employee_id != employee.e_id:
            return None, "You are not authorized to submit this claim"

    if claim.status not in [ClaimStatus.DRAFT, ClaimStatus.REJECTED]:
        return None, f"Only DRAFT or REJECTED claims can be submitted. Current status: {claim.status}"

    items = get_expense_items_by_claim_id(claim_id)
    if not items:
        return None, "Cannot submit an expense claim without any expense items"

    total = sum(Decimal(str(item.amount)) for item in items)
    update_expense_claim_dao(claim, total_amount=total)

    create_approval_history_and_update_claim_status(
        expense_claim=claim,
        action=ClaimStatus.SUBMITTED,
        action_by=user_id,
        comments="Submitted for manager approval"
    )

    return claim, None


def get_pending_manager_approvals(user_id, role=UserRole.MANAGER):
    if role == UserRole.ADMIN:
        return get_claims_by_status(ClaimStatus.SUBMITTED), None

    employee = get_employee_by_user_id(user_id)
    if not employee:
        return [], "Manager profile not found"

    subordinates = get_subordinates_by_manager_id(employee.e_id)
    if not subordinates:
        return [], None

    sub_ids = [s.e_id for s in subordinates]
    claims = get_claims_by_employee_ids_and_status(sub_ids, ClaimStatus.SUBMITTED)
    return claims, None


def approve_expense_claim_by_manager(user_id, claim_id, comments="Approved by Manager", role=UserRole.MANAGER):
    claim = get_claim_by_id(claim_id)
    if not claim:
        return None, "Expense claim not found"

    if claim.status != ClaimStatus.SUBMITTED:
        return None, f"Only SUBMITTED claims can be approved. Current status: {claim.status}"

    if role != UserRole.ADMIN:
        manager = get_employee_by_user_id(user_id)
        if manager and getattr(claim, 'employee_id', None) is not None:
            claim_owner = get_employee_by_id(claim.employee_id)
            if claim_owner and getattr(claim_owner, 'manager_id', None) is not None:
                if isinstance(claim_owner.manager_id, int) and isinstance(manager.e_id, int) and claim_owner.manager_id != manager.e_id:
                    return None, "You are not authorized to approve claims for this employee"

    create_approval_history_and_update_claim_status(
        expense_claim=claim,
        action=ClaimStatus.APPROVED,
        action_by=user_id,
        comments=comments
    )

    return claim, None


def reject_expense_claim_by_manager(user_id, claim_id, comments, role=UserRole.MANAGER):
    if not comments or not comments.strip():
        return None, "Rejection reason / comments are required"

    claim = get_claim_by_id(claim_id)
    if not claim:
        return None, "Expense claim not found"

    if claim.status != ClaimStatus.SUBMITTED:
        return None, f"Only SUBMITTED claims can be rejected. Current status: {claim.status}"

    if role != UserRole.ADMIN:
        manager = get_employee_by_user_id(user_id)
        if manager and getattr(claim, 'employee_id', None) is not None:
            claim_owner = get_employee_by_id(claim.employee_id)
            if claim_owner and getattr(claim_owner, 'manager_id', None) is not None:
                if isinstance(claim_owner.manager_id, int) and isinstance(manager.e_id, int) and claim_owner.manager_id != manager.e_id:
                    return None, "You are not authorized to reject claims for this employee"

    create_approval_history_and_update_claim_status(
        expense_claim=claim,
        action=ClaimStatus.REJECTED,
        action_by=user_id,
        comments=comments.strip()
    )

    return claim, None



def get_finance_verification_queue():
    return get_claims_by_status(ClaimStatus.APPROVED)


def verify_expense_claim_by_finance(user_id, claim_id, comments="Verified by Finance"):
    claim = get_claim_by_id(claim_id)
    if not claim:
        return None, "Expense claim not found"

    if claim.status != ClaimStatus.APPROVED:
        return None, f"Only APPROVED claims can be verified by finance. Current status: {claim.status}"

    create_approval_history_and_update_claim_status(
        expense_claim=claim,
        action=ClaimStatus.FINANCE_VERIFIED,
        action_by=user_id,
        comments=comments
    )

    return claim, None