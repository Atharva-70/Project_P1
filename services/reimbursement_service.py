from datetime import date
from decimal import Decimal, InvalidOperation
from dao.reimbursement_dao import (
    get_reimbursement_by_claim_id,
    create_reimbursement,
    update_reimbursement_payment,
    get_all_reimbursements,
    get_reimbursement_by_id
)
from dao.expense_claim_dao import get_claim_by_id
from dao.approval_history_dao import create_approval_history_and_update_claim_status
from dao.employee_dao import get_employee_by_id, get_employee_by_user_id
from constants.status import ClaimStatus, ReimbursementStatus



def process_claim_reimbursement(user_id, claim_id, payment_reference):
    claim = get_claim_by_id(claim_id)
    if not claim:
        return None, "Expense claim not found"

    if claim.status != ClaimStatus.FINANCE_VERIFIED:
        return None, f"Only FINANCE VERIFIED claims can be reimbursed. Current status: {claim.status}"

    if not payment_reference or not payment_reference.strip():
        return None, "Payment reference is required"

    try:
        amount = Decimal(str(claim.total_amount))
    except (InvalidOperation, TypeError, ValueError):
        amount = Decimal("0.00")

    existing_reim = get_reimbursement_by_claim_id(claim_id)
    today = date.today()

    if existing_reim:
        reim = update_reimbursement_payment(
            reimbursement=existing_reim,
            payment_reference=payment_reference.strip(),
            processed_by=user_id,
            processed_date=today,
            status=ReimbursementStatus.PAID
        )
    else:
        reim = create_reimbursement(
            claim_id=claim_id,
            amount=amount,
            status=ReimbursementStatus.PAID,
            payment_reference=payment_reference.strip(),
            processed_by=user_id,
            processed_date=today
        )

    create_approval_history_and_update_claim_status(
        expense_claim=claim,
        action=ClaimStatus.REIMBURSED,
        action_by=user_id,
        comments=f"Reimbursement processed. Reference: {payment_reference.strip()}"
    )

    return reim, None


def get_reimbursement_by_claim(claim_id):
    reim = get_reimbursement_by_claim_id(claim_id)
    if not reim:
        return None, "Reimbursement record not found"
    return reim, None


def get_all_processed_reimbursements():
    return get_all_reimbursements()
