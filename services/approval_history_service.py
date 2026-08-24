from dao.expense_claim_dao import get_claim_by_id
from dao.approval_history_dao import (
    create_approval_history_and_update_claim_status,
    get_approval_history_by_claim_id
)
from dao.user_dao import get_user_by_id
from dao.employee_dao import get_employee_by_user_id


def process_claim_action(
    claim_id,
    action,
    action_by,
    comments
):
    expense_claim = get_claim_by_id(claim_id)
    if not expense_claim:
        return None, "Expense claim not found"

    approval_history = create_approval_history_and_update_claim_status(
        expense_claim=expense_claim,
        action=action,
        action_by=action_by,
        comments=comments
    )

    return approval_history, None


def get_claim_history(claim_id):
    expense_claim = get_claim_by_id(claim_id)
    if not expense_claim:
        return None, "Expense claim not found"

    history_records = get_approval_history_by_claim_id(claim_id)
    timeline = []
    for record in history_records:
        user = get_user_by_id(record.action_by)
        emp = get_employee_by_user_id(record.action_by) if user else None

        actor_name = f"{emp.first_name} {emp.last_name}" if emp else (user.email if user else f"User #{record.action_by}")
        actor_role = user.role if user else "UNKNOWN"

        timeline.append({
            "approval_id": record.approval_id,
            "claim_id": record.claim_id,
            "action": record.action,
            "action_by": record.action_by,
            "actor_name": actor_name,
            "actor_role": actor_role,
            "comments": record.comments,
            "action_at": record.action_at.isoformat() if record.action_at else None
        })

    return timeline, None