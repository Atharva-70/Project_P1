import unittest
from unittest.mock import patch, MagicMock
from datetime import date
from app import create_app
from models.expense_claim import ExpenseClaim
from models.expense_item import ExpenseItem
from models.employee import Employee
from models.expense_category import ExpenseCategory
from models.expense_policy import ExpensePolicy
from flask_jwt_extended import create_access_token


class TestExpenseCRUDAndValidation(unittest.TestCase):

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

    # --- EXPENSE CLAIM CRUD TESTS ---

    @patch("services.expense_claim_service.create_expense_claim_dao")
    @patch("services.expense_claim_service.get_claim_by_number")
    @patch("services.expense_claim_service.get_travel_request_by_id")
    @patch("services.expense_claim_service.get_employee_by_user_id")
    def test_create_expense_claim_success(self, mock_get_emp, mock_get_trv, mock_get_num, mock_create_dao):
        """Test creating a new draft expense claim."""
        token = create_access_token(identity="1", additional_claims={"role": "EMPLOYEE"})

        mock_emp = MagicMock(spec=Employee)
        mock_emp.e_id = 5
        mock_get_emp.return_value = mock_emp

        mock_trv = MagicMock()
        mock_trv.status = "APPROVED"
        mock_trv.employee_id = 5
        mock_get_trv.return_value = mock_trv
        mock_get_num.return_value = None


        mock_claim = MagicMock(spec=ExpenseClaim)
        mock_claim.ex_claim_id = 1
        mock_claim.employee_id = 5
        mock_claim.travel_id = 1
        mock_claim.total_amount = 0.0
        mock_claim.status = "DRAFT"
        mock_claim.claim_number = "CLM-2026-001"
        mock_create_dao.return_value = mock_claim

        response = self.client.post("/expense_claim", json={
            "travel_id": 1,
            "claim_number": "CLM-2026-001"
        }, headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data["expense_claim_id"], 1)
        self.assertEqual(data["status"], "DRAFT")

    @patch("services.expense_claim_service.get_claims_by_employee_id")
    @patch("services.expense_claim_service.get_employee_by_user_id")
    def test_get_expense_claims_list(self, mock_get_emp, mock_get_claims):
        """Test listing user's expense claims."""
        token = create_access_token(identity="1", additional_claims={"role": "EMPLOYEE"})

        mock_emp = MagicMock(spec=Employee)
        mock_emp.e_id = 5
        mock_get_emp.return_value = mock_emp

        mock_claim = MagicMock(spec=ExpenseClaim)
        mock_claim.ex_claim_id = 10
        mock_claim.employee_id = 5
        mock_claim.travel_id = 2
        mock_claim.total_amount = 1200.00
        mock_claim.status = "DRAFT"
        mock_claim.claim_number = "CLM-010"
        mock_get_claims.return_value = [mock_claim]

        response = self.client.get("/expense_claim", headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["expense_claim_id"], 10)

    @patch("services.expense_claim_service.get_claim_by_id")
    @patch("services.expense_claim_service.get_employee_by_user_id")
    def test_get_single_expense_claim(self, mock_get_emp, mock_get_claim):
        """Test fetching a single expense claim by ID."""
        token = create_access_token(identity="1", additional_claims={"role": "EMPLOYEE"})

        mock_emp = MagicMock(spec=Employee)
        mock_emp.e_id = 5
        mock_get_emp.return_value = mock_emp

        mock_claim = MagicMock(spec=ExpenseClaim)
        mock_claim.ex_claim_id = 3
        mock_claim.employee_id = 5
        mock_claim.travel_id = 1
        mock_claim.total_amount = 3500.00
        mock_claim.status = "APPROVED"
        mock_claim.claim_number = "CLM-003"
        mock_get_claim.return_value = mock_claim

        response = self.client.get("/expense_claim/3", headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["expense_claim_id"], 3)
        self.assertEqual(data["status"], "APPROVED")

    @patch("services.expense_claim_service.delete_expense_claim_dao")
    @patch("services.expense_claim_service.get_claim_by_id")
    @patch("services.expense_claim_service.get_employee_by_user_id")
    def test_delete_draft_expense_claim(self, mock_get_emp, mock_get_claim, mock_delete_dao):
        """Test deleting a draft expense claim."""
        token = create_access_token(identity="1", additional_claims={"role": "EMPLOYEE"})

        mock_emp = MagicMock(spec=Employee)
        mock_emp.e_id = 5
        mock_get_emp.return_value = mock_emp

        mock_claim = MagicMock(spec=ExpenseClaim)
        mock_claim.ex_claim_id = 4
        mock_claim.employee_id = 5
        mock_claim.status = "DRAFT"
        mock_get_claim.return_value = mock_claim

        response = self.client.delete("/expense_claim/4", headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 200)
        mock_delete_dao.assert_called_once_with(mock_claim)

    # --- EXPENSE ITEM CRUD & POLICY VALIDATION TESTS ---

    @patch("services.expense_item_service.recalculate_claim_total")
    @patch("services.expense_item_service.create_expense_item_dao")
    @patch("services.expense_item_service.validate_expense_against_policy")
    @patch("services.expense_item_service.get_category_by_id")
    @patch("services.expense_item_service.get_claim_by_id")
    @patch("services.expense_item_service.get_employee_by_user_id")
    def test_create_expense_item_success(
        self, mock_get_emp, mock_get_claim, mock_get_cat, mock_val_policy, mock_create_dao, mock_recalc
    ):
        """Test creating an expense item within policy limit."""
        token = create_access_token(identity="1", additional_claims={"role": "EMPLOYEE"})

        mock_emp = MagicMock(spec=Employee)
        mock_emp.e_id = 5
        mock_get_emp.return_value = mock_emp

        mock_claim = MagicMock(spec=ExpenseClaim)
        mock_claim.ex_claim_id = 1
        mock_claim.employee_id = 5
        mock_claim.status = "DRAFT"
        mock_get_claim.return_value = mock_claim

        mock_get_cat.return_value = MagicMock(spec=ExpenseCategory)
        mock_val_policy.return_value = (True, None)  # Within policy

        mock_item = MagicMock(spec=ExpenseItem)
        mock_item.ex_item_id = 100
        mock_item.claim_id = 1
        mock_item.category_id = 2
        mock_item.amount = 800.00
        mock_item.expense_date = date(2026, 8, 20)
        mock_item.description = "Team lunch"
        mock_create_dao.return_value = mock_item

        response = self.client.post("/expense_item", json={
            "claim_id": 1,
            "category_id": 2,
            "amount": 800.00,
            "expense_date": "2026-08-20",
            "description": "Team lunch"
        }, headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data["expense_item_id"], 100)
        self.assertEqual(data["amount"], "800.0")
        mock_recalc.assert_called_once_with(1)

    @patch("services.expense_item_service.validate_expense_against_policy")
    @patch("services.expense_item_service.get_category_by_id")
    @patch("services.expense_item_service.get_claim_by_id")
    @patch("services.expense_item_service.get_employee_by_user_id")
    def test_create_expense_item_policy_limit_breach_fails(
        self, mock_get_emp, mock_get_claim, mock_get_cat, mock_val_policy
    ):
        """Test that expense exceeding company policy limit is rejected with 400."""
        token = create_access_token(identity="1", additional_claims={"role": "EMPLOYEE"})

        mock_emp = MagicMock(spec=Employee)
        mock_emp.e_id = 5
        mock_get_emp.return_value = mock_emp

        mock_claim = MagicMock(spec=ExpenseClaim)
        mock_claim.ex_claim_id = 1
        mock_claim.employee_id = 5
        mock_claim.status = "DRAFT"
        mock_get_claim.return_value = mock_claim

        mock_get_cat.return_value = MagicMock(spec=ExpenseCategory)

        # Policy Violation Mock: Limit is 1500, user requested 2000
        mock_val_policy.return_value = (False, "Expense amount ₹2000.0 exceeds company policy limit of ₹1500.0 for this category")

        response = self.client.post("/expense_item", json={
            "claim_id": 1,
            "category_id": 2,
            "amount": 2000.00,
            "expense_date": "2026-08-20",
            "description": "Luxury dinner"
        }, headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("exceeds company policy limit", data["message"])

    @patch("services.expense_item_service.get_claim_by_id")
    @patch("services.expense_item_service.get_employee_by_user_id")
    def test_create_expense_item_invalid_amount_fails(self, mock_get_emp, mock_get_claim):
        """Test that negative or zero expense amount is rejected with 400."""
        token = create_access_token(identity="1", additional_claims={"role": "EMPLOYEE"})

        mock_emp = MagicMock(spec=Employee)
        mock_emp.e_id = 5
        mock_get_emp.return_value = mock_emp

        mock_claim = MagicMock(spec=ExpenseClaim)
        mock_claim.ex_claim_id = 1
        mock_claim.employee_id = 5
        mock_claim.status = "DRAFT"
        mock_get_claim.return_value = mock_claim

        response = self.client.post("/expense_item", json={
            "claim_id": 1,
            "category_id": 2,
            "amount": -50.00,
            "expense_date": "2026-08-20",
            "description": "Invalid negative item"
        }, headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("greater than 0", data["message"])

    @patch("services.expense_item_service.get_category_by_id")
    @patch("services.expense_item_service.get_claim_by_id")
    @patch("services.expense_item_service.get_employee_by_user_id")
    def test_create_expense_item_invalid_category_fails(self, mock_get_emp, mock_get_claim, mock_get_cat):
        """Test that non-existent category ID is rejected with 400."""
        token = create_access_token(identity="1", additional_claims={"role": "EMPLOYEE"})

        mock_emp = MagicMock(spec=Employee)
        mock_emp.e_id = 5
        mock_get_emp.return_value = mock_emp

        mock_claim = MagicMock(spec=ExpenseClaim)
        mock_claim.ex_claim_id = 1
        mock_claim.employee_id = 5
        mock_claim.status = "DRAFT"
        mock_get_claim.return_value = mock_claim

        mock_get_cat.return_value = None  # Category not found

        response = self.client.post("/expense_item", json={
            "claim_id": 1,
            "category_id": 9999,
            "amount": 250.00,
            "expense_date": "2026-08-20",
            "description": "Unknown category"
        }, headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["message"], "Expense category not found")

    @patch("services.expense_item_service.get_expense_items_by_claim_id")
    @patch("services.expense_item_service.get_claim_by_id")
    @patch("services.expense_item_service.get_employee_by_user_id")
    def test_get_items_by_claim(self, mock_get_emp, mock_get_claim, mock_get_items):
        """Test listing all expense items in a claim."""
        token = create_access_token(identity="1", additional_claims={"role": "EMPLOYEE"})

        mock_emp = MagicMock(spec=Employee)
        mock_emp.e_id = 5
        mock_get_emp.return_value = mock_emp

        mock_claim = MagicMock(spec=ExpenseClaim)
        mock_claim.employee_id = 5
        mock_get_claim.return_value = mock_claim


        item1 = MagicMock(spec=ExpenseItem)
        item1.ex_item_id = 1
        item1.claim_id = 1
        item1.category_id = 2
        item1.amount = 500.00
        item1.expense_date = date(2026, 8, 15)
        item1.description = "Taxi fare"
        mock_get_items.return_value = [item1]

        response = self.client.get("/expense_claim/1/items", headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["description"], "Taxi fare")

    @patch("services.expense_item_service.recalculate_claim_total")
    @patch("services.expense_item_service.delete_expense_item_dao")
    @patch("services.expense_item_service.get_claim_by_id")
    @patch("services.expense_item_service.get_expense_item_by_id")
    @patch("services.expense_item_service.get_employee_by_user_id")
    def test_delete_expense_item_success(
        self, mock_get_emp, mock_get_item, mock_get_claim, mock_delete_dao, mock_recalc
    ):
        """Test deleting an item and recalculating claim total."""
        token = create_access_token(identity="1", additional_claims={"role": "EMPLOYEE"})

        mock_emp = MagicMock(spec=Employee)
        mock_emp.e_id = 5
        mock_get_emp.return_value = mock_emp

        mock_item = MagicMock(spec=ExpenseItem)
        mock_item.ex_item_id = 10
        mock_item.claim_id = 2
        mock_get_item.return_value = mock_item

        mock_claim = MagicMock(spec=ExpenseClaim)
        mock_claim.ex_claim_id = 2
        mock_claim.employee_id = 5
        mock_claim.status = "DRAFT"
        mock_get_claim.return_value = mock_claim

        response = self.client.delete("/expense_item/10", headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 200)
        mock_delete_dao.assert_called_once_with(mock_item)
        mock_recalc.assert_called_once_with(2)


if __name__ == "__main__":
    unittest.main()
