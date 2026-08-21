from config.database import db
from models.expense_claim import ExpenseClaim
from models.employee import Employee
from models.travel_request import TravelRequest


def create_expense_claim(
    user_id,
    travel_id,
    total_amount,
    claim_number
):
    employee = Employee.query.filter_by(
        user_id=user_id
    ).first()

    if not employee:
        return None, "Employee profile not found"

    travel_request = TravelRequest.query.filter_by(
        travel_id=travel_id
    ).first()

    if not travel_request:
        return None, "Travel request not found"

    existing_claim = ExpenseClaim.query.filter_by(
        claim_number=claim_number
    ).first()

    if existing_claim:
        return None, "Claim number already exists"

    expense_claim = ExpenseClaim(
        employee_id=employee.e_id,
        travel_id=travel_id,
        total_amount=total_amount,
        status="DRAFT",
        claim_number=claim_number
    )

    db.session.add(expense_claim)
    db.session.commit()

    return expense_claim, None

def get_expense_claims(user_id):

    employee = Employee.query.filter_by(
        user_id=user_id
    ).first()

    if not employee:
        return []

    expense_claims = ExpenseClaim.query.filter_by(
        employee_id=employee.e_id
    ).all()

    return expense_claims

def get_expense_claim_by_id(user_id, claim_id):

    employee = Employee.query.filter_by(
        user_id=user_id
    ).first()

    if not employee:
        return None, "Employee profile not found"

    expense_claim = ExpenseClaim.query.filter_by(
        ex_claim_id=claim_id,
        employee_id = employee.e_id
    ).first()

    if not expense_claim:
        return None, "Expense claim not found"

    if expense_claim.employee_id != employee.e_id:
        return None, "You are not allowed to view this expense claim"

    return expense_claim, None