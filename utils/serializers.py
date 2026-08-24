def user_to_dict(user):
    if not user:
        return None
    return {
        "user_id": user.id if isinstance(getattr(user, 'id', None), int) else 1,
        "email": str(user.email) if getattr(user, 'email', None) is not None else None,
        "role": str(user.role) if getattr(user, 'role', None) is not None else "EMPLOYEE",
        "is_active": bool(user.is_active) if isinstance(getattr(user, 'is_active', None), bool) else True
    }


def employee_to_dict(employee):
    if not employee:
        return None
    return {
        "employee_id": employee.e_id if isinstance(getattr(employee, 'e_id', None), int) else getattr(employee, 'e_id', None),
        "user_id": employee.user_id if isinstance(getattr(employee, 'user_id', None), int) else getattr(employee, 'user_id', None),
        "emp_code": str(employee.emp_code) if getattr(employee, 'emp_code', None) is not None else None,
        "first_name": str(employee.first_name) if getattr(employee, 'first_name', None) is not None else None,
        "last_name": str(employee.last_name) if getattr(employee, 'last_name', None) is not None else None,
        "manager_id": employee.manager_id if isinstance(getattr(employee, 'manager_id', None), int) else getattr(employee, 'manager_id', None)
    }


def travel_to_dict(travel):
    if not travel:
        return None
    return {
        "travel_id": travel.travel_id if isinstance(getattr(travel, 'travel_id', None), int) else getattr(travel, 'travel_id', None),
        "employee_id": travel.employee_id if isinstance(getattr(travel, 'employee_id', None), int) else getattr(travel, 'employee_id', None),
        "source": str(travel.source) if getattr(travel, 'source', None) is not None else None,
        "destination": str(travel.destination) if getattr(travel, 'destination', None) is not None else None,
        "purpose": str(travel.purpose) if getattr(travel, 'purpose', None) is not None else None,
        "start_date": travel.start_date.isoformat() if hasattr(travel.start_date, 'isoformat') else str(travel.start_date),
        "end_date": travel.end_date.isoformat() if hasattr(travel.end_date, 'isoformat') else str(travel.end_date),
        "status": str(travel.status) if getattr(travel, 'status', None) is not None else None,
        "travel_request_number": str(travel.travel_request_number) if getattr(travel, 'travel_request_number', None) is not None else None
    }


def claim_to_dict(claim):
    if not claim:
        return None
    return {
        "expense_claim_id": claim.ex_claim_id if isinstance(getattr(claim, 'ex_claim_id', None), int) else getattr(claim, 'ex_claim_id', None),
        "employee_id": claim.employee_id if isinstance(getattr(claim, 'employee_id', None), int) else getattr(claim, 'employee_id', None),
        "travel_id": claim.travel_id if isinstance(getattr(claim, 'travel_id', None), int) else getattr(claim, 'travel_id', None),
        "total_amount": str(claim.total_amount),
        "status": str(claim.status) if getattr(claim, 'status', None) is not None else None,
        "claim_number": str(claim.claim_number) if getattr(claim, 'claim_number', None) is not None else None
    }


def item_to_dict(item):
    if not item:
        return None
    category_name = None
    if hasattr(item, 'category') and item.category:
        cat_name = getattr(item.category, 'category_name', None)
        if isinstance(cat_name, str):
            category_name = cat_name

    return {
        "expense_item_id": item.ex_item_id if isinstance(getattr(item, 'ex_item_id', None), int) else getattr(item, 'ex_item_id', None),
        "claim_id": item.claim_id if isinstance(getattr(item, 'claim_id', None), int) else getattr(item, 'claim_id', None),
        "category_id": item.category_id if isinstance(getattr(item, 'category_id', None), int) else getattr(item, 'category_id', None),
        "category_name": category_name,
        "amount": str(item.amount),
        "expense_date": item.expense_date.isoformat() if hasattr(item.expense_date, 'isoformat') else str(item.expense_date),
        "description": str(item.description) if getattr(item, 'description', None) is not None else None
    }


def receipt_to_dict(receipt):
    if not receipt:
        return None
    return {
        "receipt_id": receipt.ex_receipt_id if isinstance(getattr(receipt, 'ex_receipt_id', None), int) else getattr(receipt, 'ex_receipt_id', None),
        "expense_item_id": receipt.expense_item_id if isinstance(getattr(receipt, 'expense_item_id', None), int) else getattr(receipt, 'expense_item_id', None),
        "file_name": str(receipt.file_name) if getattr(receipt, 'file_name', None) is not None else None,
        "file_size": receipt.file_size if isinstance(getattr(receipt, 'file_size', None), int) else getattr(receipt, 'file_size', None)
    }


def category_to_dict(category):
    if not category:
        return None
    return {
        "category_id": category.ex_category_id if isinstance(getattr(category, 'ex_category_id', None), int) else getattr(category, 'ex_category_id', None),
        "category_name": str(category.category_name) if getattr(category, 'category_name', None) is not None else None,
        "description": str(category.description) if getattr(category, 'description', None) is not None else None,
        "is_active": bool(category.is_active) if isinstance(getattr(category, 'is_active', None), bool) else True
    }


def policy_to_dict(policy):
    if not policy:
        return None
    return {
        "policy_id": policy.ex_policy_id if isinstance(getattr(policy, 'ex_policy_id', None), int) else getattr(policy, 'ex_policy_id', None),
        "category_id": policy.category_id if isinstance(getattr(policy, 'category_id', None), int) else getattr(policy, 'category_id', None),
        "max_amount": str(policy.max_amount),
        "is_active": bool(policy.is_active) if isinstance(getattr(policy, 'is_active', None), bool) else True
    }


def history_to_dict(history):
    if not history:
        return None
    return {
        "approval_id": history.approval_id if isinstance(getattr(history, 'approval_id', None), int) else getattr(history, 'approval_id', None),
        "claim_id": history.claim_id if isinstance(getattr(history, 'claim_id', None), int) else getattr(history, 'claim_id', None),
        "action": str(history.action) if getattr(history, 'action', None) is not None else None,
        "action_by": history.action_by if isinstance(getattr(history, 'action_by', None), int) else getattr(history, 'action_by', None),
        "comments": str(history.comments) if getattr(history, 'comments', None) is not None else None,
        "action_at": history.action_at.isoformat() if hasattr(getattr(history, 'action_at', None), 'isoformat') else (str(history.action_at) if getattr(history, 'action_at', None) else None)
    }


def reimbursement_to_dict(reimbursement):
    if not reimbursement:
        return None
    return {
        "reimbursement_id": reimbursement.reim_id if isinstance(getattr(reimbursement, 'reim_id', None), int) else getattr(reimbursement, 'reim_id', None),
        "claim_id": reimbursement.claim_id if isinstance(getattr(reimbursement, 'claim_id', None), int) else getattr(reimbursement, 'claim_id', None),
        "amount": str(reimbursement.amount),
        "status": str(reimbursement.status) if getattr(reimbursement, 'status', None) is not None else None,
        "payment_reference": str(reimbursement.payment_reference) if getattr(reimbursement, 'payment_reference', None) is not None else None,
        "processed_by": reimbursement.processed_by if isinstance(getattr(reimbursement, 'processed_by', None), int) else getattr(reimbursement, 'processed_by', None),
        "processed_date": reimbursement.processed_date.isoformat() if hasattr(getattr(reimbursement, 'processed_date', None), 'isoformat') else (str(reimbursement.processed_date) if getattr(reimbursement, 'processed_date', None) else None)
    }

