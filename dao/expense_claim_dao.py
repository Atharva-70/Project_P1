from config.database import db
from models.expense_claim import ExpenseClaim


def get_claim_by_number(claim_number):
    return ExpenseClaim.query.filter_by(claim_number=claim_number).first()


def get_claim_by_id(claim_id):
    return ExpenseClaim.query.filter_by(ex_claim_id=claim_id).first()


def get_claim_by_id_and_employee(claim_id, employee_id):
    return ExpenseClaim.query.filter_by(
        ex_claim_id=claim_id,
        employee_id=employee_id
    ).first()


def get_claims_by_employee_id(employee_id):
    return ExpenseClaim.query.filter_by(employee_id=employee_id).all()


def get_claims_by_status(status):
    return ExpenseClaim.query.filter_by(status=status).all()


def get_claims_by_employee_ids_and_status(employee_ids, status):
    if not employee_ids:
        return []
    return ExpenseClaim.query.filter(
        ExpenseClaim.employee_id.in_(employee_ids),
        ExpenseClaim.status == status
    ).all()


def create_expense_claim(employee_id, travel_id, total_amount, claim_number, status="DRAFT"):
    expense_claim = ExpenseClaim(
        employee_id=employee_id,
        travel_id=travel_id,
        total_amount=total_amount,
        status=status,
        claim_number=claim_number
    )
    db.session.add(expense_claim)
    db.session.commit()
    return expense_claim


def update_expense_claim(expense_claim, travel_id=None, total_amount=None, claim_number=None, status=None):
    if travel_id is not None:
        expense_claim.travel_id = travel_id
    if total_amount is not None:
        expense_claim.total_amount = total_amount
    if claim_number is not None:
        expense_claim.claim_number = claim_number
    if status is not None:
        expense_claim.status = status

    db.session.commit()
    return expense_claim


def delete_expense_claim(expense_claim):
    db.session.delete(expense_claim)
    db.session.commit()
