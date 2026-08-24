from config.database import db
from models.employee import Employee
from models.user import User


def get_employee_by_user_id(user_id):
    emp = Employee.query.filter_by(user_id=user_id).first()
    if not emp:
        # Auto-initialize employee profile if missing
        user = User.query.get(user_id)
        if user:
            name_part = user.email.split('@')[0] if user.email else f"User{user_id}"
            emp = create_employee(
                user_id=user.id,
                emp_code=f"EMP-{user.id:04d}",
                first_name=name_part.capitalize(),
                last_name="Staff"
            )
    return emp


def get_employee_by_emp_code(emp_code):
    return Employee.query.filter_by(emp_code=emp_code).first()


def get_employee_by_id(employee_id):
    return Employee.query.filter_by(e_id=employee_id).first()


def get_subordinates_by_manager_id(manager_id):
    return Employee.query.filter_by(manager_id=manager_id).all()


def get_all_employees():
    return Employee.query.all()


def create_employee(user_id, emp_code, first_name, last_name, manager_id=None):
    employee = Employee(
        user_id=user_id,
        emp_code=emp_code,
        first_name=first_name,
        last_name=last_name,
        manager_id=manager_id
    )
    db.session.add(employee)
    db.session.commit()
    return employee


def update_employee(employee, first_name=None, last_name=None, manager_id=None):
    if first_name is not None:
        employee.first_name = first_name
    if last_name is not None:
        employee.last_name = last_name
    if manager_id is not None:
        employee.manager_id = manager_id
    db.session.commit()
    return employee
