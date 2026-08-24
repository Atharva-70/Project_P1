from dao.employee_dao import get_employee_by_user_id, get_subordinates_by_manager_id
from dao.travel_dao import (
    create_travel_request as create_travel_request_dao,
    get_travel_request_by_number,
    get_travel_requests_by_employee_id,
    get_travel_request_by_id,
    get_travel_requests_by_status,
    get_travel_requests_by_employee_ids_and_status,
    update_travel_request_status
)
from constants.status import TravelStatus, UserRole

# Alias for testing and DAO abstraction consistency
get_travel_request_by_id_dao = get_travel_request_by_id



def create_travel_request(
    user_id,
    source,
    destination,
    purpose,
    start_date,
    end_date,
    travel_request_number
):
    employee = get_employee_by_user_id(user_id)
    if not employee:
        return None, "Employee profile not found"

    if end_date < start_date:
        return None, "End date cannot be before start date"

    existing = get_travel_request_by_number(travel_request_number)
    if existing:
        return None, "Travel request number already exists"

    travel_request = create_travel_request_dao(
        employee_id=employee.e_id,
        source=source,
        destination=destination,
        purpose=purpose,
        start_date=start_date,
        end_date=end_date,
        travel_request_number=travel_request_number
    )

    return travel_request, None


def get_user_travel_requests(user_id):
    employee = get_employee_by_user_id(user_id)
    if not employee:
        return [], "Employee profile not found"

    requests = get_travel_requests_by_employee_id(employee.e_id)
    return requests, None


def get_travel_request(travel_id):
    req = get_travel_request_by_id_dao(travel_id)
    if not req:
        return None, "Travel request not found"
    return req, None


def get_pending_travel_approvals(user_id, role=UserRole.MANAGER):
    if role == UserRole.ADMIN:
        requests = get_travel_requests_by_status(TravelStatus.PENDING)
        return requests, None

    employee = get_employee_by_user_id(user_id)
    if not employee:
        return [], "Manager profile not found"

    subordinates = get_subordinates_by_manager_id(employee.e_id)
    if not subordinates:
        return [], None

    sub_ids = [s.e_id for s in subordinates]
    requests = get_travel_requests_by_employee_ids_and_status(sub_ids, TravelStatus.PENDING)
    return requests, None


def approve_travel(travel_id):
    travel_request = get_travel_request_by_id_dao(travel_id)
    if not travel_request:
        return None, "Travel request not found"

    if travel_request.status != TravelStatus.PENDING:
        return None, f"Only PENDING requests can be approved. Current status: {travel_request.status}"

    updated = update_travel_request_status(travel_request, TravelStatus.APPROVED)
    return updated, None


def reject_travel(travel_id):
    travel_request = get_travel_request_by_id_dao(travel_id)
    if not travel_request:
        return None, "Travel request not found"

    if travel_request.status != TravelStatus.PENDING:
        return None, f"Only PENDING requests can be rejected. Current status: {travel_request.status}"

    updated = update_travel_request_status(travel_request, TravelStatus.REJECTED)
    return updated, None