from config.database import db
from models.travel_request import TravelRequest


def get_travel_request_by_id(travel_id):
    return TravelRequest.query.filter_by(travel_id=travel_id).first()


def get_travel_request_by_number(travel_request_number):
    return TravelRequest.query.filter_by(travel_request_number=travel_request_number).first()


def get_travel_requests_by_employee_id(employee_id):
    return TravelRequest.query.filter_by(employee_id=employee_id).all()


def get_travel_requests_by_status(status):
    return TravelRequest.query.filter_by(status=status).all()


def get_travel_requests_by_employee_ids_and_status(employee_ids, status=None):
    if not employee_ids:
        return []
    query = TravelRequest.query.filter(TravelRequest.employee_id.in_(employee_ids))
    if status:
        query = query.filter(TravelRequest.status == status)
    return query.all()


def create_travel_request(
    employee_id,
    source,
    destination,
    purpose,
    start_date,
    end_date,
    travel_request_number,
    status="PENDING"
):
    travel_request = TravelRequest(
        employee_id=employee_id,
        source=source,
        destination=destination,
        purpose=purpose,
        start_date=start_date,
        end_date=end_date,
        status=status,
        travel_request_number=travel_request_number
    )
    db.session.add(travel_request)
    db.session.commit()
    return travel_request


def update_travel_request_status(travel_request, status):
    travel_request.status = status
    db.session.commit()
    return travel_request
