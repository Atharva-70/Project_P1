from config.database import db
from models.travel_request import TravelRequest
from models.employee import Employee


def create_travel_request(
    user_id,
    source,
    destination,
    purpose,
    start_date,
    end_date,
    travel_request_number
):
    employee = Employee.query.filter_by(
        user_id=user_id
    ).first()

    if not employee:
        return None, "Employee profile not found"

    travel_request = TravelRequest(
        employee_id=employee.e_id,
        source=source,
        destination=destination,
        purpose=purpose,
        start_date=start_date,
        end_date=end_date,
        status="DRAFT",
        travel_request_number=travel_request_number
    )

    db.session.add(travel_request)
    db.session.commit()

    return travel_request, None