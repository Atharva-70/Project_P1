from config.database import db
from models.approval_history import ApprovalHistory


def get_approval_history_by_claim_id(claim_id):
    return ApprovalHistory.query.filter_by(claim_id=claim_id).order_by(ApprovalHistory.action_at.asc()).all()


def create_approval_history_and_update_claim_status(expense_claim, action, action_by, comments):
    """
    Executes claim status update and approval history creation within an atomic transaction.
    """
    try:
        approval_history = ApprovalHistory(
            claim_id=expense_claim.ex_claim_id,
            action=action,
            action_by=action_by,
            comments=comments
        )
        expense_claim.status = action
        db.session.add(approval_history)
        db.session.commit()
        return approval_history
    except Exception:
        db.session.rollback()
        raise
