import unittest
from unittest.mock import patch, MagicMock
import io
from app import create_app
from models.expense_receipt import ExpenseReceipt
from models.expense_item import ExpenseItem
from models.expense_claim import ExpenseClaim
from models.employee import Employee
from flask_jwt_extended import create_access_token


class TestReceiptFileHandlingAndSecurity(unittest.TestCase):

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

    # --- UPLOAD & FILE TYPE TESTS ---

    @patch("services.expense_receipt_service.create_expense_receipt_dao")
    @patch("os.path.getsize")
    @patch("werkzeug.datastructures.FileStorage.save")
    @patch("services.expense_receipt_service.get_claim_by_id")
    @patch("services.expense_receipt_service.get_expense_item_by_id")
    @patch("services.expense_receipt_service.get_employee_by_user_id")
    def test_valid_pdf_upload_success(
        self, mock_get_emp, mock_get_item, mock_get_claim, mock_save, mock_getsize, mock_create_dao
    ):
        """Test uploading a valid PDF receipt."""
        token = create_access_token(identity="1", additional_claims={"role": "EMPLOYEE"})

        mock_emp = MagicMock(spec=Employee)
        mock_emp.e_id = 5
        mock_get_emp.return_value = mock_emp

        mock_item = MagicMock(spec=ExpenseItem)
        mock_item.ex_item_id = 10
        mock_item.claim_id = 1
        mock_get_item.return_value = mock_item

        mock_claim = MagicMock(spec=ExpenseClaim)
        mock_claim.employee_id = 5
        mock_claim.status = "DRAFT"
        mock_get_claim.return_value = mock_claim

        mock_getsize.return_value = 1024 * 100  # 100 KB (valid)

        mock_receipt = MagicMock(spec=ExpenseReceipt)
        mock_receipt.ex_receipt_id = 1
        mock_receipt.expense_item_id = 10
        mock_receipt.file_name = "hotel_bill.pdf"
        mock_receipt.file_size = 102400
        mock_create_dao.return_value = mock_receipt

        data = {
            "expense_item_id": "10",
            "file": (io.BytesIO(b"%PDF-1.4 dummy pdf content"), "hotel_bill.pdf")
        }

        response = self.client.post("/expense_receipt", data=data, content_type="multipart/form-data",
                                    headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 201)
        res_data = response.get_json()
        self.assertEqual(res_data["file_name"], "hotel_bill.pdf")

    @patch("services.expense_receipt_service.create_expense_receipt_dao")
    @patch("os.path.getsize")
    @patch("werkzeug.datastructures.FileStorage.save")
    @patch("services.expense_receipt_service.get_claim_by_id")
    @patch("services.expense_receipt_service.get_expense_item_by_id")
    @patch("services.expense_receipt_service.get_employee_by_user_id")
    def test_valid_image_upload_success(
        self, mock_get_emp, mock_get_item, mock_get_claim, mock_save, mock_getsize, mock_create_dao
    ):
        """Test uploading a valid PNG image receipt."""
        token = create_access_token(identity="1", additional_claims={"role": "EMPLOYEE"})

        mock_emp = MagicMock(spec=Employee)
        mock_emp.e_id = 5
        mock_get_emp.return_value = mock_emp

        mock_item = MagicMock(spec=ExpenseItem)
        mock_item.ex_item_id = 10
        mock_item.claim_id = 1
        mock_get_item.return_value = mock_item

        mock_claim = MagicMock(spec=ExpenseClaim)
        mock_claim.employee_id = 5
        mock_claim.status = "DRAFT"
        mock_get_claim.return_value = mock_claim

        mock_getsize.return_value = 50000

        mock_receipt = MagicMock(spec=ExpenseReceipt)
        mock_receipt.ex_receipt_id = 2
        mock_receipt.expense_item_id = 10
        mock_receipt.file_name = "taxi_receipt.png"
        mock_receipt.file_size = 50000
        mock_create_dao.return_value = mock_receipt

        data = {
            "expense_item_id": "10",
            "file": (io.BytesIO(b"fake image bytes"), "taxi_receipt.png")
        }

        response = self.client.post("/expense_receipt", data=data, content_type="multipart/form-data",
                                    headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 201)
        res_data = response.get_json()
        self.assertEqual(res_data["file_name"], "taxi_receipt.png")

    def test_invalid_file_type_fails(self):
        """Test that uploading invalid file types (e.g. .exe or .txt) returns 400."""
        token = create_access_token(identity="1", additional_claims={"role": "EMPLOYEE"})

        data = {
            "expense_item_id": "10",
            "file": (io.BytesIO(b"binary content"), "script.exe")
        }

        response = self.client.post("/expense_receipt", data=data, content_type="multipart/form-data",
                                    headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 400)
        res_data = response.get_json()
        self.assertIn("invalid file type", res_data["message"].lower())

    @patch("os.remove")
    @patch("os.path.exists")
    @patch("os.path.getsize")
    @patch("werkzeug.datastructures.FileStorage.save")
    @patch("services.expense_receipt_service.get_claim_by_id")
    @patch("services.expense_receipt_service.get_expense_item_by_id")
    @patch("services.expense_receipt_service.get_employee_by_user_id")
    def test_file_size_exceeding_5mb_fails(
        self, mock_get_emp, mock_get_item, mock_get_claim, mock_save, mock_getsize, mock_exists, mock_remove
    ):
        """Test that files exceeding 5 MB limit are rejected with 400 and removed."""
        token = create_access_token(identity="1", additional_claims={"role": "EMPLOYEE"})

        mock_emp = MagicMock(spec=Employee)
        mock_emp.e_id = 5
        mock_get_emp.return_value = mock_emp

        mock_item = MagicMock(spec=ExpenseItem)
        mock_item.claim_id = 1
        mock_get_item.return_value = mock_item

        mock_claim = MagicMock(spec=ExpenseClaim)
        mock_claim.employee_id = 5
        mock_claim.status = "DRAFT"
        mock_get_claim.return_value = mock_claim

        # File size exceeds 5MB (e.g. 6 MB)
        mock_getsize.return_value = 6 * 1024 * 1024
        mock_exists.return_value = True

        data = {
            "expense_item_id": "10",
            "file": (io.BytesIO(b"large file content"), "huge_receipt.pdf")
        }

        response = self.client.post("/expense_receipt", data=data, content_type="multipart/form-data",
                                    headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 400)
        res_data = response.get_json()
        self.assertIn("5 mb limit", res_data["message"].lower())

    # --- ACCESS CONTROL & UNAUTHORIZED DOWNLOAD TESTS ---

    @patch("services.expense_receipt_service.get_employee_by_id")
    @patch("services.expense_receipt_service.get_employee_by_user_id")
    @patch("services.expense_receipt_service.get_claim_by_id")
    @patch("services.expense_receipt_service.get_expense_item_by_id")
    @patch("services.expense_receipt_service.get_receipt_by_id")
    def test_unauthorized_document_download_fails_403(
        self, mock_get_receipt, mock_get_item, mock_get_claim, mock_get_user_emp, mock_get_owner_emp
    ):
        """Test that an unauthorized employee attempting to download another employee's receipt gets 403."""
        # Unrelated employee token
        token = create_access_token(identity="99", additional_claims={"role": "EMPLOYEE"})

        mock_receipt = MagicMock(spec=ExpenseReceipt)
        mock_receipt.expense_item_id = 10
        mock_get_receipt.return_value = mock_receipt

        mock_item = MagicMock(spec=ExpenseItem)
        mock_item.claim_id = 1
        mock_get_item.return_value = mock_item

        # Claim belongs to employee ID 5
        mock_claim = MagicMock(spec=ExpenseClaim)
        mock_claim.employee_id = 5
        mock_get_claim.return_value = mock_claim

        # Current user is employee ID 99 (not owner)
        unrelated_emp = MagicMock(spec=Employee)
        unrelated_emp.e_id = 99
        mock_get_user_emp.return_value = unrelated_emp

        # Claim owner's manager is NOT 99
        owner_emp = MagicMock(spec=Employee)
        owner_emp.manager_id = 10  # Different manager
        mock_get_owner_emp.return_value = owner_emp

        response = self.client.get("/expense_receipt/1/download", headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 403)
        res_data = response.get_json()
        self.assertEqual(res_data["message"], "Unauthorized document access")

    @patch("services.expense_receipt_service.get_claim_by_id")
    @patch("services.expense_receipt_service.get_expense_item_by_id")
    @patch("services.expense_receipt_service.get_receipt_by_id")
    def test_finance_admin_can_access_any_receipt(
        self, mock_get_receipt, mock_get_item, mock_get_claim
    ):
        """Test that Finance Admin has global access to view/download receipts."""
        finance_token = create_access_token(identity="4", additional_claims={"role": "FINANCE"})

        mock_receipt = MagicMock(spec=ExpenseReceipt)
        mock_receipt.expense_item_id = 10
        mock_receipt.file_path = "uploads/receipts/bill.pdf"
        mock_get_receipt.return_value = mock_receipt

        mock_item = MagicMock(spec=ExpenseItem)
        mock_item.claim_id = 1
        mock_get_item.return_value = mock_item

        mock_claim = MagicMock(spec=ExpenseClaim)
        mock_claim.employee_id = 5
        mock_get_claim.return_value = mock_claim

        # Patching os.path.exists to verify download path authorization
        with patch("os.path.exists", return_value=False):
            # File not on disk will return 404 from controller AFTER authorization passes
            response = self.client.get("/expense_receipt/1/download", headers={"Authorization": f"Bearer {finance_token}"})
            # 404 means authorization passed (didn't get 403 Forbidden!)
            self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
