from config.database import db
from models.employee import Employee


def create_employee(
    user_id,
    emp_code,
    first_name,
    last_name,
    manager_id=None
):
    existing_employee = Employee.query.filter_by(
        user_id=user_id
    ).first()

    if existing_employee:
        return None, "Employee profile already exists"

    existing_code = Employee.query.filter_by(
        emp_code=emp_code
    ).first()

    if existing_code:
        return None, "Employee code already exists"

    employee = Employee(
        user_id=user_id,
        emp_code=emp_code,
        first_name=first_name,
        last_name=last_name,
        manager_id=manager_id
    )

    db.session.add(employee)
    db.session.commit()

    return employee, None