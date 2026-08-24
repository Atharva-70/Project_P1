from config.database import db
from models.expense_claim import ExpenseClaim
from models.expense_item import ExpenseItem
from models.travel_request import TravelRequest
from models.reimbursement import Reimbursement
from models.expense_category import ExpenseCategory
from models.employee import Employee
from constants.status import ClaimStatus, TravelStatus, ReimbursementStatus
from sqlalchemy import func


def search_claims(
    employee_id=None,
    claim_id=None,
    category_id=None,
    status=None,
    min_amount=None,
    max_amount=None,
    date_from=None,
    date_to=None
):
    query = ExpenseClaim.query

    if claim_id:
        query = query.filter(ExpenseClaim.ex_claim_id == claim_id)

    if employee_id:
        query = query.filter(ExpenseClaim.employee_id == employee_id)

    if status:
        query = query.filter(ExpenseClaim.status == status)

    if min_amount is not None:
        query = query.filter(ExpenseClaim.total_amount >= min_amount)

    if max_amount is not None:
        query = query.filter(ExpenseClaim.total_amount <= max_amount)

    if category_id or date_from or date_to:
        query = query.join(ExpenseItem, ExpenseClaim.ex_claim_id == ExpenseItem.claim_id)
        if category_id:
            query = query.filter(ExpenseItem.category_id == category_id)
        if date_from:
            query = query.filter(ExpenseItem.expense_date >= date_from)
        if date_to:
            query = query.filter(ExpenseItem.expense_date <= date_to)

    return query.distinct().all()


def get_employee_claim_stats(employee_id):
    claims = ExpenseClaim.query.filter_by(employee_id=employee_id).all()
    total_claims = len(claims)
    pending_claims = sum(1 for c in claims if c.status in [ClaimStatus.DRAFT, ClaimStatus.SUBMITTED])
    approved_claims = sum(1 for c in claims if c.status in [ClaimStatus.APPROVED, ClaimStatus.FINANCE_VERIFIED, ClaimStatus.REIMBURSED])
    rejected_claims = sum(1 for c in claims if c.status == ClaimStatus.REJECTED)

    # Total reimbursed amount
    reimbursed_total = db.session.query(func.coalesce(func.sum(Reimbursement.amount), 0))\
        .join(ExpenseClaim, Reimbursement.claim_id == ExpenseClaim.ex_claim_id)\
        .filter(ExpenseClaim.employee_id == employee_id, Reimbursement.status == ReimbursementStatus.PAID)\
        .scalar()

    # Recent claims
    recent_claims = ExpenseClaim.query.filter_by(employee_id=employee_id)\
        .order_by(ExpenseClaim.ex_claim_id.desc()).limit(5).all()

    return {
        "total_claims": total_claims,
        "pending_claims": pending_claims,
        "approved_claims": approved_claims,
        "rejected_claims": rejected_claims,
        "reimbursed_amount": str(reimbursed_total),
        "recent_claims": recent_claims
    }


def get_manager_stats(subordinate_emp_ids):
    if not subordinate_emp_ids:
        return {
            "pending_travel_requests": 0,
            "pending_expense_claims": 0,
            "approved_claims": 0,
            "rejected_claims": 0
        }

    pending_travel = TravelRequest.query.filter(
        TravelRequest.employee_id.in_(subordinate_emp_ids),
        TravelRequest.status == TravelStatus.PENDING
    ).count()

    claims = ExpenseClaim.query.filter(ExpenseClaim.employee_id.in_(subordinate_emp_ids)).all()
    pending_claims = sum(1 for c in claims if c.status == ClaimStatus.SUBMITTED)
    approved_claims = sum(1 for c in claims if c.status in [ClaimStatus.APPROVED, ClaimStatus.FINANCE_VERIFIED, ClaimStatus.REIMBURSED])
    rejected_claims = sum(1 for c in claims if c.status == ClaimStatus.REJECTED)

    return {
        "pending_travel_requests": pending_travel,
        "pending_expense_claims": pending_claims,
        "approved_claims": approved_claims,
        "rejected_claims": rejected_claims
    }


def get_finance_stats():
    awaiting_verification = ExpenseClaim.query.filter_by(status=ClaimStatus.APPROVED).count()
    verified_claims = ExpenseClaim.query.filter_by(status=ClaimStatus.FINANCE_VERIFIED).count()
    completed_reimbursements = Reimbursement.query.filter_by(status=ReimbursementStatus.PAID).count()

    total_reimbursed = db.session.query(func.coalesce(func.sum(Reimbursement.amount), 0))\
        .filter(Reimbursement.status == ReimbursementStatus.PAID)\
        .scalar()


    return {
        "claims_awaiting_verification": awaiting_verification,
        "verified_claims": verified_claims,
        "completed_reimbursements": completed_reimbursements,
        "total_reimbursement_amount": str(total_reimbursed)
    }


def get_category_breakdown():
    results = db.session.query(
        ExpenseCategory.category_name,
        func.coalesce(func.sum(ExpenseItem.amount), 0),
        func.count(ExpenseItem.ex_item_id)
    ).join(ExpenseItem, ExpenseCategory.ex_category_id == ExpenseItem.category_id)\
     .group_by(ExpenseCategory.category_name).all()

    return [{"category": r[0], "total_amount": str(r[1]), "item_count": r[2]} for r in results]
