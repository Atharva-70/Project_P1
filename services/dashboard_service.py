from dao.employee_dao import get_employee_by_user_id, get_subordinates_by_manager_id
from dao.dashboard_dao import (
    search_claims as search_claims_dao,
    get_employee_claim_stats,
    get_manager_stats,
    get_finance_stats,
    get_category_breakdown
)
from utils.serializers import claim_to_dict
from constants.status import UserRole


def search_expense_claims(
    user_id,
    role,
    claim_id=None,
    employee_id=None,
    category_id=None,
    status=None,
    min_amount=None,
    max_amount=None,
    date_from=None,
    date_to=None
):
    employee = get_employee_by_user_id(user_id)

    target_emp_id = employee_id
    if role == UserRole.EMPLOYEE:
        if not employee:
            return [], "Employee profile not found"
        target_emp_id = employee.e_id

    claims = search_claims_dao(
        employee_id=target_emp_id,
        claim_id=claim_id,
        category_id=category_id,
        status=status,
        min_amount=min_amount,
        max_amount=max_amount,
        date_from=date_from,
        date_to=date_to
    )

    results = [claim_to_dict(c) for c in claims]
    return results, None


def get_employee_dashboard(user_id):
    employee = get_employee_by_user_id(user_id)
    if not employee:
        return None, "Employee profile not found"

    stats = get_employee_claim_stats(employee.e_id)
    recent = [claim_to_dict(c) for c in stats["recent_claims"]]

    return {
        "employee_name": f"{employee.first_name} {employee.last_name}",
        "emp_code": employee.emp_code,
        "total_claims": stats["total_claims"],
        "pending_claims": stats["pending_claims"],
        "approved_claims": stats["approved_claims"],
        "rejected_claims": stats["rejected_claims"],
        "reimbursed_amount": stats["reimbursed_amount"],
        "recent_claims": recent
    }, None


def get_manager_dashboard(user_id, role):
    employee = get_employee_by_user_id(user_id)
    if not employee:
        return None, "Manager profile not found"

    subordinates = get_subordinates_by_manager_id(employee.e_id)
    sub_ids = [s.e_id for s in subordinates] if subordinates else []

    stats = get_manager_stats(sub_ids)
    return {
        "manager_name": f"{employee.first_name} {employee.last_name}",
        "subordinates_count": len(sub_ids),
        "pending_travel_requests": stats["pending_travel_requests"],
        "pending_expense_claims": stats["pending_expense_claims"],
        "approved_claims": stats["approved_claims"],
        "rejected_claims": stats["rejected_claims"]
    }, None


def get_finance_dashboard():
    stats = get_finance_stats()
    return stats, None


def get_reports_summary():
    category_summary = get_category_breakdown()
    finance_stats = get_finance_stats()

    return {
        "finance_overview": finance_stats,
        "expenses_by_category": category_summary
    }, None
