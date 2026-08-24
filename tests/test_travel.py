import unittest
from unittest.mock import patch, MagicMock
from datetime import date
from app import create_app
from models.travel_request import TravelRequest
from models.employee import Employee
from flask_jwt_extended import create_access_token


class TestTravelRequestWorkflow(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Initialize Flask test app without database dependencies."""
        cls.app = create_app({
            "TESTING": True,
            "JWT_SECRET_KEY": "SUPER-SECRET-KEY"
        })

    def setUp(self):
        """Set up test client and application context."""
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up application context."""
        self.app_context.pop()

    # --- CREATION & VALIDATION TESTS ---

    @patch("services.travel_service.create_travel_request_dao")
    @patch("services.travel_service.get_travel_request_by_number")
    @patch("services.travel_service.get_employee_by_user_id")
    def test_create_travel_request_success(self, mock_get_emp, mock_get_num, mock_create_dao):
        """Test successful creation of a business travel request."""
        token = create_access_token(identity="1", additional_claims={"role": "EMPLOYEE"})

        # Mock employee
        mock_emp = MagicMock(spec=Employee)
        mock_emp.e_id = 10
        mock_get_emp.return_value = mock_emp

        # Mock unique travel request number
        mock_get_num.return_value = None

        # Mock created travel request
        mock_travel = MagicMock(spec=TravelRequest)
        mock_travel.travel_id = 1
        mock_travel.employee_id = 10
        mock_travel.source = "Mumbai"
        mock_travel.destination = "Bengaluru"
        mock_travel.purpose = "Client meeting"
        mock_travel.start_date = date(2026, 9, 1)
        mock_travel.end_date = date(2026, 9, 5)
        mock_travel.status = "PENDING"
        mock_travel.travel_request_number = "TRV-2026-001"
        mock_create_dao.return_value = mock_travel

        response = self.client.post("/travel", json={
            "source": "Mumbai",
            "destination": "Bengaluru",
            "purpose": "Client meeting",
            "start_date": "2026-09-01",
            "end_date": "2026-09-05",
            "travel_request_number": "TRV-2026-001"
        }, headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data["travel_id"], 1)
        self.assertEqual(data["status"], "PENDING")
        self.assertEqual(data["source"], "Mumbai")
        self.assertEqual(data["destination"], "Bengaluru")

    def test_create_travel_request_invalid_dates_fails(self):
        """Test that end_date occurring before start_date is rejected with 400."""
        token = create_access_token(identity="1", additional_claims={"role": "EMPLOYEE"})

        response = self.client.post("/travel", json={
            "source": "Delhi",
            "destination": "Pune",
            "purpose": "Conference",
            "start_date": "2026-09-10",
            "end_date": "2026-09-02",  # End date before start date
            "travel_request_number": "TRV-2026-002"
        }, headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("end date cannot be before start date", data["message"].lower())

    def test_create_travel_request_invalid_date_format_fails(self):
        """Test that malformed date formats are rejected with 400."""
        token = create_access_token(identity="1", additional_claims={"role": "EMPLOYEE"})

        response = self.client.post("/travel", json={
            "source": "Delhi",
            "destination": "Pune",
            "purpose": "Conference",
            "start_date": "01/09/2026",  # Malformed date
            "end_date": "2026-09-05",
            "travel_request_number": "TRV-2026-003"
        }, headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("yyyy-mm-dd", data["message"].lower())

    @patch("services.travel_service.get_travel_request_by_number")
    @patch("services.travel_service.get_employee_by_user_id")
    def test_create_travel_request_duplicate_number_fails(self, mock_get_emp, mock_get_num):
        """Test that duplicate travel request numbers are rejected with 400."""
        token = create_access_token(identity="1", additional_claims={"role": "EMPLOYEE"})

        mock_emp = MagicMock(spec=Employee)
        mock_emp.e_id = 10
        mock_get_emp.return_value = mock_emp

        # Existing travel request with same number
        mock_get_num.return_value = MagicMock(spec=TravelRequest)

        response = self.client.post("/travel", json={
            "source": "Chennai",
            "destination": "Hyderabad",
            "purpose": "Training",
            "start_date": "2026-09-01",
            "end_date": "2026-09-05",
            "travel_request_number": "DUPLICATE-001"
        }, headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["message"], "Travel request number already exists")

    # --- LIST & DETAILS TESTS ---

    @patch("services.travel_service.get_travel_requests_by_employee_id")
    @patch("services.travel_service.get_employee_by_user_id")
    def test_list_my_travel_requests(self, mock_get_emp, mock_get_requests):
        """Test employee listing their own travel requests."""
        token = create_access_token(identity="1", additional_claims={"role": "EMPLOYEE"})

        mock_emp = MagicMock(spec=Employee)
        mock_emp.e_id = 10
        mock_get_emp.return_value = mock_emp

        mock_trv = MagicMock(spec=TravelRequest)
        mock_trv.travel_id = 5
        mock_trv.employee_id = 10
        mock_trv.source = "Mumbai"
        mock_trv.destination = "Goa"
        mock_trv.purpose = "Annual Meet"
        mock_trv.start_date = date(2026, 10, 1)
        mock_trv.end_date = date(2026, 10, 3)
        mock_trv.status = "APPROVED"
        mock_trv.travel_request_number = "TRV-101"
        mock_get_requests.return_value = [mock_trv]

        response = self.client.get("/travel", headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["travel_id"], 5)
        self.assertEqual(data[0]["status"], "APPROVED")

    @patch("services.travel_service.get_travel_request_by_id_dao")
    def test_get_single_travel_request_success(self, mock_get_dao):
        """Test retrieving a specific travel request by ID."""
        token = create_access_token(identity="1", additional_claims={"role": "EMPLOYEE"})

        mock_trv = MagicMock(spec=TravelRequest)
        mock_trv.travel_id = 2
        mock_trv.employee_id = 10
        mock_trv.source = "Kolkata"
        mock_trv.destination = "Delhi"
        mock_trv.purpose = "Audit"
        mock_trv.start_date = date(2026, 11, 1)
        mock_trv.end_date = date(2026, 11, 4)
        mock_trv.status = "PENDING"
        mock_trv.travel_request_number = "TRV-002"
        mock_get_dao.return_value = mock_trv

        response = self.client.get("/travel/2", headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["travel_id"], 2)
        self.assertEqual(data["destination"], "Delhi")

    @patch("services.travel_service.get_travel_request_by_id_dao")
    def test_get_single_travel_request_not_found(self, mock_get_dao):
        """Test requesting a non-existent travel request ID returns 404."""
        token = create_access_token(identity="1", additional_claims={"role": "EMPLOYEE"})
        mock_get_dao.return_value = None

        response = self.client.get("/travel/999", headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertEqual(data["message"], "Travel request not found")

    # --- MANAGER APPROVAL & REJECTION WORKFLOW TESTS ---

    @patch("services.travel_service.get_travel_requests_by_employee_ids_and_status")
    @patch("services.travel_service.get_subordinates_by_manager_id")
    @patch("services.travel_service.get_employee_by_user_id")
    def test_manager_pending_travel_queue(self, mock_get_emp, mock_get_subs, mock_get_reqs):
        """Test manager viewing pending travel requests from their direct reports."""
        manager_token = create_access_token(identity="2", additional_claims={"role": "MANAGER"})

        mock_mgr = MagicMock(spec=Employee)
        mock_mgr.e_id = 20
        mock_get_emp.return_value = mock_mgr

        sub1 = MagicMock(spec=Employee)
        sub1.e_id = 30
        mock_get_subs.return_value = [sub1]

        mock_trv = MagicMock(spec=TravelRequest)
        mock_trv.travel_id = 7
        mock_trv.employee_id = 30
        mock_trv.source = "Bengaluru"
        mock_trv.destination = "Singapore"
        mock_trv.purpose = "Expo"
        mock_trv.start_date = date(2026, 12, 1)
        mock_trv.end_date = date(2026, 12, 5)
        mock_trv.status = "PENDING"
        mock_trv.travel_request_number = "TRV-SG-01"
        mock_get_reqs.return_value = [mock_trv]

        response = self.client.get("/travel/pending-approvals", headers={"Authorization": f"Bearer {manager_token}"})

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["destination"], "Singapore")

    @patch("services.travel_service.update_travel_request_status")
    @patch("services.travel_service.get_travel_request_by_id_dao")
    def test_manager_approve_travel_request(self, mock_get_dao, mock_update_dao):
        """Test manager approving a pending travel request."""
        manager_token = create_access_token(identity="2", additional_claims={"role": "MANAGER"})

        mock_trv = MagicMock(spec=TravelRequest)
        mock_trv.travel_id = 7
        mock_trv.status = "PENDING"
        mock_get_dao.return_value = mock_trv

        updated_trv = MagicMock(spec=TravelRequest)
        updated_trv.travel_id = 7
        updated_trv.status = "APPROVED"
        mock_update_dao.return_value = updated_trv

        response = self.client.post("/travel/7/approve", headers={"Authorization": f"Bearer {manager_token}"})

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "APPROVED")
        mock_update_dao.assert_called_once_with(mock_trv, "APPROVED")

    @patch("services.travel_service.update_travel_request_status")
    @patch("services.travel_service.get_travel_request_by_id_dao")
    def test_manager_reject_travel_request(self, mock_get_dao, mock_update_dao):
        """Test manager rejecting a pending travel request."""
        manager_token = create_access_token(identity="2", additional_claims={"role": "MANAGER"})

        mock_trv = MagicMock(spec=TravelRequest)
        mock_trv.travel_id = 8
        mock_trv.status = "PENDING"
        mock_get_dao.return_value = mock_trv

        updated_trv = MagicMock(spec=TravelRequest)
        updated_trv.travel_id = 8
        updated_trv.status = "REJECTED"
        mock_update_dao.return_value = updated_trv

        response = self.client.post("/travel/8/reject", headers={"Authorization": f"Bearer {manager_token}"})

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "REJECTED")
        mock_update_dao.assert_called_once_with(mock_trv, "REJECTED")

    def test_employee_cannot_approve_travel_403(self):
        """Test that regular employees receive 403 Forbidden when attempting to approve travel."""
        employee_token = create_access_token(identity="3", additional_claims={"role": "EMPLOYEE"})

        response = self.client.post("/travel/7/approve", headers={"Authorization": f"Bearer {employee_token}"})

        self.assertEqual(response.status_code, 403)
        data = response.get_json()
        self.assertEqual(data["message"], "Access forbidden")


if __name__ == "__main__":
    unittest.main()
