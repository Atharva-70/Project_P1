import unittest
from unittest.mock import patch, MagicMock
from datetime import date
from app import create_app
from models.expense_claim import ExpenseClaim
from models.employee import Employee
from models.reimbursement import Reimbursement
from models.approval_history import ApprovalHistory
from flask_jwt_extended import create_access_token



class TestApprovalAndReimbursementWorkflow(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Initialize Flask test app without database dependencies."""
        cls.app = create_app({
            "TESTING": True,
            "JWT_SECRET_KEY": "SUPER-SECRET-KEY"
        })

    def setUp(self):
        """Set up test client and request context."""
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up request context."""
        self.app_context.pop()

    # --- CLAIM SUBMISSION TESTS ---

    @patch("services.expense_claim_service.create_approval_history_and_update_claim_status")
    @patch("services.expense_claim_service.get_expense_items_by_claim_id")
    @patch("services.expense_claim_service.get_claim_by_id")
    @patch("services.expense_claim_service.get_employee_by_user_id")
    def test_submit_claim_success(
        self, mock_get_emp, mock_get_claim, mock_get_items, mock_update_status
    ):
        """Test employee submitting a draft claim with expense items."""
        token = create_access_token(identity="1", additional_claims={"role": "EMPLOYEE"})

        mock_emp = MagicMock(spec=Employee)
        mock_emp.e_id = 5
        mock_emp.manager_id = 10
        mock_get_emp.return_value = mock_emp

        mock_claim = MagicMock(spec=ExpenseClaim)
        mock_claim.ex_claim_id = 1
        mock_claim.employee_id = 5
        mock_claim.status = "DRAFT"
        mock_claim.claim_number = "CLM-001"
        mock_get_claim.return_value = mock_claim

        # Mock claim has items
        item = MagicMock()
        item.amount = 1500.00
        mock_get_items.return_value = [item]

        response = self.client.post("/expense_claim/1/submit", headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["expense_claim_id"], 1)
        mock_update_status.assert_called_once()

    @patch("services.expense_claim_service.get_expense_items_by_claim_id")
    @patch("services.expense_claim_service.get_claim_by_id")
    @patch("services.expense_claim_service.get_employee_by_user_id")
    def test_submit_claim_empty(self, mock_get_emp, mock_get_claim, mock_get_items):
        """Test submitting an empty claim with no items is rejected with 400."""
        token = create_access_token(identity="1", additional_claims={"role": "EMPLOYEE"})

        mock_emp = MagicMock(spec=Employee)
        mock_emp.e_id = 5
        mock_get_emp.return_value = mock_emp

        mock_claim = MagicMock(spec=ExpenseClaim)
        mock_claim.ex_claim_id = 1
        mock_claim.employee_id = 5
        mock_claim.status = "DRAFT"
        mock_get_claim.return_value = mock_claim

        mock_get_items.return_value = []  # Empty items

        response = self.client.post("/expense_claim/1/submit", headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("without any expense items", data["message"])

    # --- MANAGER APPROVAL & REJECTION TESTS ---

    @patch("services.expense_claim_service.get_claims_by_employee_ids_and_status")
    @patch("services.expense_claim_service.get_subordinates_by_manager_id")
    @patch("services.expense_claim_service.get_employee_by_user_id")
    def test_manager_pending_approvals(self, mock_get_emp, mock_get_subs, mock_get_claims):
        """Test manager viewing pending claim submissions from direct reports."""
        manager_token = create_access_token(identity="2", additional_claims={"role": "MANAGER"})

        mock_mgr = MagicMock(spec=Employee)
        mock_mgr.e_id = 20
        mock_get_emp.return_value = mock_mgr

        sub1 = MagicMock(spec=Employee)
        sub1.e_id = 30
        mock_get_subs.return_value = [sub1]

        claim = MagicMock(spec=ExpenseClaim)
        claim.ex_claim_id = 5
        claim.employee_id = 30
        claim.travel_id = 1
        claim.total_amount = 2500.00
        claim.status = "SUBMITTED"
        claim.claim_number = "CLM-105"
        mock_get_claims.return_value = [claim]

        response = self.client.get("/expense_claim/pending-approvals", headers={"Authorization": f"Bearer {manager_token}"})

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["status"], "SUBMITTED")

    @patch("services.expense_claim_service.get_employee_by_user_id")
    @patch("services.expense_claim_service.get_employee_by_id")
    @patch("services.expense_claim_service.create_approval_history_and_update_claim_status")
    @patch("services.expense_claim_service.get_claim_by_id")
    def test_manager_approve_claim_success(
        self, mock_get_claim, mock_update_status, mock_get_emp, mock_get_mgr
    ):
        """Test manager approving a submitted claim."""
        manager_token = create_access_token(identity="2", additional_claims={"role": "MANAGER"})

        mock_claim = MagicMock(spec=ExpenseClaim)
        mock_claim.ex_claim_id = 5
        mock_claim.status = "SUBMITTED"
        mock_claim.employee_id = 30
        mock_claim.claim_number = "CLM-105"
        mock_get_claim.return_value = mock_claim

        mock_mgr = MagicMock(spec=Employee)
        mock_mgr.e_id = 20
        mock_get_mgr.return_value = mock_mgr

        mock_emp = MagicMock(spec=Employee)
        mock_emp.e_id = 30
        mock_emp.manager_id = 20
        mock_emp.user_id = 3
        mock_get_emp.return_value = mock_emp

        response = self.client.post("/expense_claim/5/approve", json={
            "comments": "Approved"
        }, headers={"Authorization": f"Bearer {manager_token}"})

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("approved successfully", data["message"].lower())
        mock_update_status.assert_called_once_with(
            expense_claim=mock_claim,
            action="APPROVED",
            action_by=2,
            comments="Approved"
        )

    @patch("services.expense_claim_service.get_employee_by_user_id")
    @patch("services.expense_claim_service.get_employee_by_id")
    @patch("services.expense_claim_service.create_approval_history_and_update_claim_status")
    @patch("services.expense_claim_service.get_claim_by_id")
    def test_manager_reject_claim_with_comments(
        self, mock_get_claim, mock_update_status, mock_get_emp, mock_get_mgr
    ):
        """Test manager rejecting a submitted claim with mandatory reason."""
        manager_token = create_access_token(identity="2", additional_claims={"role": "MANAGER"})

        mock_claim = MagicMock(spec=ExpenseClaim)
        mock_claim.ex_claim_id = 6
        mock_claim.status = "SUBMITTED"
        mock_claim.employee_id = 30
        mock_claim.claim_number = "CLM-106"
        mock_get_claim.return_value = mock_claim

        mock_mgr = MagicMock(spec=Employee)
        mock_mgr.e_id = 20
        mock_get_mgr.return_value = mock_mgr

        mock_emp = MagicMock(spec=Employee)
        mock_emp.e_id = 30
        mock_emp.manager_id = 20
        mock_emp.user_id = 3
        mock_get_emp.return_value = mock_emp

        response = self.client.post("/expense_claim/6/reject", json={
            "comments": "Missing official hotel receipt"
        }, headers={"Authorization": f"Bearer {manager_token}"})

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("rejected successfully", data["message"].lower())
        mock_update_status.assert_called_once_with(
            expense_claim=mock_claim,
            action="REJECTED",
            action_by=2,
            comments="Missing official hotel receipt"
        )


    @patch("services.expense_claim_service.get_claim_by_id")
    def test_manager_reject_claim_without_comments_fails(self, mock_get_claim):
        """Test that rejecting a claim without comments is blocked with 400."""
        manager_token = create_access_token(identity="2", additional_claims={"role": "MANAGER"})

        mock_claim = MagicMock(spec=ExpenseClaim)
        mock_claim.ex_claim_id = 6
        mock_claim.status = "SUBMITTED"
        mock_get_claim.return_value = mock_claim

        response = self.client.post("/expense_claim/6/reject", json={
            "comments": ""  # Missing rejection reason
        }, headers={"Authorization": f"Bearer {manager_token}"})

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("required", data["message"].lower())

    @patch("services.expense_claim_service.get_employee_by_user_id")
    @patch("services.expense_claim_service.get_employee_by_id")
    @patch("services.expense_claim_service.get_claim_by_id")
    def test_manager_cannot_approve_unrelated_employee_claim(
        self, mock_get_claim, mock_get_emp, mock_get_mgr
    ):
        """Test that a manager attempting to approve an employee's claim who does not report to them returns 400."""
        manager_token = create_access_token(identity="2", additional_claims={"role": "MANAGER"})

        mock_claim = MagicMock(spec=ExpenseClaim)
        mock_claim.ex_claim_id = 9
        mock_claim.status = "SUBMITTED"
        mock_claim.employee_id = 40
        mock_get_claim.return_value = mock_claim

        # Current manager is ID 20
        mock_mgr = MagicMock(spec=Employee)
        mock_mgr.e_id = 20
        mock_get_mgr.return_value = mock_mgr

        # Claim owner reports to manager ID 99 (not 20!)
        mock_emp = MagicMock(spec=Employee)
        mock_emp.e_id = 40
        mock_emp.manager_id = 99
        mock_get_emp.return_value = mock_emp

        response = self.client.post("/expense_claim/9/approve", json={
            "comments": "Unauthorized approval attempt"
        }, headers={"Authorization": f"Bearer {manager_token}"})

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("not authorized", data["message"].lower())

    @patch("services.expense_claim_service.get_claim_by_id")
    def test_cannot_approve_draft_claim(self, mock_get_claim):
        """Test that attempting to approve a DRAFT claim returns 400 invalid state transition."""
        manager_token = create_access_token(identity="2", additional_claims={"role": "MANAGER"})

        mock_claim = MagicMock(spec=ExpenseClaim)
        mock_claim.ex_claim_id = 10
        mock_claim.status = "DRAFT"
        mock_get_claim.return_value = mock_claim

        response = self.client.post("/expense_claim/10/approve", json={
            "comments": "Approve draft"
        }, headers={"Authorization": f"Bearer {manager_token}"})

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("only submitted claims can be approved", data["message"].lower())

    @patch("services.expense_claim_service.get_claim_by_id")
    @patch("services.expense_claim_service.get_employee_by_user_id")
    def test_cannot_submit_already_approved_claim(self, mock_get_emp, mock_get_claim):
        """Test that attempting to submit an already APPROVED claim returns 400 invalid state transition."""
        emp_token = create_access_token(identity="1", additional_claims={"role": "EMPLOYEE"})

        mock_emp = MagicMock(spec=Employee)
        mock_emp.e_id = 5
        mock_get_emp.return_value = mock_emp

        mock_claim = MagicMock(spec=ExpenseClaim)
        mock_claim.ex_claim_id = 11
        mock_claim.employee_id = 5
        mock_claim.status = "APPROVED"
        mock_get_claim.return_value = mock_claim

        response = self.client.post("/expense_claim/11/submit", headers={"Authorization": f"Bearer {emp_token}"})

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("only draft or rejected claims can be submitted", data["message"].lower())


    # --- FINANCE VERIFICATION TESTS ---

    @patch("services.expense_claim_service.get_claims_by_status")
    def test_finance_queue_list(self, mock_get_claims):
        """Test Finance team viewing queue of approved claims."""
        finance_token = create_access_token(identity="4", additional_claims={"role": "FINANCE"})

        mock_claim = MagicMock(spec=ExpenseClaim)
        mock_claim.ex_claim_id = 7
        mock_claim.employee_id = 10
        mock_claim.travel_id = 1
        mock_claim.total_amount = 4500.00
        mock_claim.status = "APPROVED"
        mock_claim.claim_number = "CLM-107"
        mock_get_claims.return_value = [mock_claim]

        response = self.client.get("/expense_claim/finance-queue", headers={"Authorization": f"Bearer {finance_token}"})

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["status"], "APPROVED")

    @patch("services.expense_claim_service.get_employee_by_id")
    @patch("services.expense_claim_service.create_approval_history_and_update_claim_status")
    @patch("services.expense_claim_service.get_claim_by_id")
    def test_finance_verify_claim_success(
        self, mock_get_claim, mock_update_status, mock_get_emp
    ):
        """Test Finance team verifying an approved claim."""
        finance_token = create_access_token(identity="4", additional_claims={"role": "FINANCE"})

        mock_claim = MagicMock(spec=ExpenseClaim)
        mock_claim.ex_claim_id = 7
        mock_claim.status = "APPROVED"
        mock_claim.employee_id = 10
        mock_claim.claim_number = "CLM-107"
        mock_get_claim.return_value = mock_claim

        mock_emp = MagicMock(spec=Employee)
        mock_emp.user_id = 1
        mock_get_emp.return_value = mock_emp

        response = self.client.post("/expense_claim/7/finance-verify", json={
            "comments": "Invoices verified against GST"
        }, headers={"Authorization": f"Bearer {finance_token}"})

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("verified by finance", data["message"].lower())

    # --- REIMBURSEMENT PAYOUT TESTS ---

    @patch("services.reimbursement_service.get_employee_by_id")
    @patch("services.reimbursement_service.create_approval_history_and_update_claim_status")
    @patch("services.reimbursement_service.create_reimbursement")
    @patch("services.reimbursement_service.get_reimbursement_by_claim_id")
    @patch("services.reimbursement_service.get_claim_by_id")
    def test_process_reimbursement_payout_success(
        self, mock_get_claim, mock_get_reim, mock_create_reim, mock_update_status, mock_get_emp
    ):
        """Test Finance team processing reimbursement payout with bank reference."""
        finance_token = create_access_token(identity="4", additional_claims={"role": "FINANCE"})

        mock_claim = MagicMock(spec=ExpenseClaim)
        mock_claim.ex_claim_id = 7
        mock_claim.status = "FINANCE VERIFIED"
        mock_claim.total_amount = 4500.00
        mock_claim.employee_id = 10
        mock_claim.claim_number = "CLM-107"
        mock_get_claim.return_value = mock_claim

        mock_get_reim.return_value = None

        mock_reim = MagicMock(spec=Reimbursement)

        mock_reim.reim_id = 1
        mock_reim.claim_id = 7
        mock_reim.amount = 4500.00
        mock_reim.status = "PAID"
        mock_reim.payment_reference = "UTR-HDFC-998877"
        mock_reim.processed_by = 4
        mock_reim.processed_date = date.today()
        mock_create_reim.return_value = mock_reim

        mock_emp = MagicMock(spec=Employee)
        mock_emp.user_id = 1
        mock_get_emp.return_value = mock_emp

        response = self.client.post("/reimbursements/process", json={
            "claim_id": 7,
            "payment_reference": "UTR-HDFC-998877"
        }, headers={"Authorization": f"Bearer {finance_token}"})

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "PAID")
        self.assertEqual(data["payment_reference"], "UTR-HDFC-998877")
        mock_update_status.assert_called_once()

    @patch("services.reimbursement_service.get_claim_by_id")
    def test_process_reimbursement_unverified_claim_fails(self, mock_get_claim):
        """Test that attempting to pay an unverified claim is blocked with 400."""
        finance_token = create_access_token(identity="4", additional_claims={"role": "FINANCE"})

        mock_claim = MagicMock(spec=ExpenseClaim)
        mock_claim.ex_claim_id = 8
        mock_claim.status = "SUBMITTED"  # Not yet finance verified
        mock_get_claim.return_value = mock_claim

        response = self.client.post("/reimbursements/process", json={
            "claim_id": 8,
            "payment_reference": "UTR-12345"
        }, headers={"Authorization": f"Bearer {finance_token}"})

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("FINANCE VERIFIED", data["message"])

    # --- AUDIT TRAIL TIMELINE TEST ---

    @patch("services.approval_history_service.get_employee_by_user_id")
    @patch("services.approval_history_service.get_user_by_id")
    @patch("services.approval_history_service.get_approval_history_by_claim_id")
    @patch("services.approval_history_service.get_claim_by_id")
    def test_get_claim_history_timeline(
        self, mock_get_claim, mock_get_history, mock_get_user, mock_get_emp
    ):
        """Test retrieving chronological audit trail history for a claim."""
        token = create_access_token(identity="1", additional_claims={"role": "EMPLOYEE"})

        mock_get_claim.return_value = MagicMock(spec=ExpenseClaim)

        rec1 = MagicMock(spec=ApprovalHistory)
        rec1.approval_id = 1
        rec1.claim_id = 5
        rec1.action = "SUBMITTED"
        rec1.action_by = 1
        rec1.comments = "Submitted claim"
        rec1.action_at = None

        mock_get_history.return_value = [rec1]
        mock_get_user.return_value = None

        response = self.client.get("/expense_claim/5/history", headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["action"], "SUBMITTED")


if __name__ == "__main__":
    unittest.main()
