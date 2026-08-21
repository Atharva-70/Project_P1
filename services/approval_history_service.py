from models import ExpenseClaim
from models import expense_claim
from models.approval_history  import ApprovalHistory
from config.database import db


def process_claim_action(
    claim_id,
    action,
    action_by,
    comments
):
    expense_claim = ExpenseClaim.query.filter_by(
        ex_claim_id = claim_id
    ).first()

    if not expense_claim:
        return None, "Expense claim not found"

    approval_history = ApprovalHistory(
        claim_id = claim_id,
        action = action,
        action_by = action_by,
        comments = comments
    )

    expense_claim.status = action

    db.session.add(approval_history)
    db.session.commit()

    return approval_history, None
    