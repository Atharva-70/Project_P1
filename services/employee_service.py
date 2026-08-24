from dao.employee_dao import (
    get_employee_by_user_id,
    get_employee_by_emp_code,
    get_employee_by_id,
    get_subordinates_by_manager_id,
    create_employee as create_employee_dao,
    update_employee as update_employee_dao
)
from dao.user_dao import get_user_by_id


def create_employee(
    user_id,
    emp_code,
    first_name,
    last_name,
    manager_id=None
):
    existing_employee = get_employee_by_user_id(user_id)
    if existing_employee:
        return None, "Employee profile already exists"

    existing_code = get_employee_by_emp_code(emp_code)
    if existing_code:
        return None, "Employee code already exists"

    employee = create_employee_dao(
        user_id=user_id,
        emp_code=emp_code,
        first_name=first_name,
        last_name=last_name,
        manager_id=manager_id
    )

    return employee, None


def get_my_profile(user_id):
    employee = get_employee_by_user_id(user_id)
    if not employee:
        return None, "Employee profile not found"

    user = get_user_by_id(user_id)

    manager_info = None
    if employee.manager_id:
        manager = get_employee_by_id(employee.manager_id)
        if manager:
            manager_info = {
                "manager_id": manager.e_id,
                "manager_name": f"{manager.first_name} {manager.last_name}",
                "manager_code": manager.emp_code
            }

    profile_data = {
        "employee_id": employee.e_id,
        "user_id": employee.user_id,
        "email": user.email if user else None,
        "role": user.role if user else None,
        "emp_code": employee.emp_code,
        "first_name": employee.first_name,
        "last_name": employee.last_name,
        "full_name": f"{employee.first_name} {employee.last_name}",
        "manager": manager_info
    }

    return profile_data, None


def update_my_profile(user_id, first_name=None, last_name=None):
    employee = get_employee_by_user_id(user_id)
    if not employee:
        return None, "Employee profile not found"

    if not first_name and not last_name:
        return None, "Nothing to update"

    updated = update_employee_dao(
        employee=employee,
        first_name=first_name,
        last_name=last_name
    )

    return updated, None


def get_my_subordinates(user_id):
    manager = get_employee_by_user_id(user_id)
    if not manager:
        return [], "Employee profile not found"

    subordinates = get_subordinates_by_manager_id(manager.e_id)
    sub_list = []
    for sub in subordinates:
        sub_user = get_user_by_id(sub.user_id)
        sub_list.append({
            "employee_id": sub.e_id,
            "emp_code": sub.emp_code,
            "first_name": sub.first_name,
            "last_name": sub.last_name,
            "full_name": f"{sub.first_name} {sub.last_name}",
            "email": sub_user.email if sub_user else None
        })

    return sub_list, None