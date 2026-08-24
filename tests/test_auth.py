import unittest
from unittest.mock import patch, MagicMock
from app import create_app
from models.user import User
from models.expense_category import ExpenseCategory
from flask_jwt_extended import create_access_token


class TestAuthenticationAuthorization(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = create_app({
            "TESTING": True,
            "JWT_SECRET_KEY": "SUPER-SECRET-KEY"
        })

    def setUp(self):
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    # REGISTRATION

    @patch("services.auth_service.create_employee")
    @patch("services.auth_service.create_user")
    @patch("services.auth_service.get_user_by_email")
    def test_register_user_success(self, mock_get_user, mock_create_user, mock_create_emp):
        # Mock: Email is not taken
        mock_get_user.return_value = None

        # Mock: User created and returned by DAO
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.email = "new_emp@company.com"
        mock_user.role = "EMPLOYEE"
        mock_create_user.return_value = mock_user

        response = self.client.post("/register", json={
            "email": "new_emp@company.com",
            "password": "Password@123",
            "role": "EMPLOYEE"
        })

        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data["email"], "new_emp@company.com")
        self.assertEqual(data["role"], "EMPLOYEE")
        self.assertEqual(data["user_id"], 1)

        # Verify DAOs were called with expected arguments
        mock_get_user.assert_called_once_with("new_emp@company.com")
        mock_create_user.assert_called_once()

    @patch("services.auth_service.get_user_by_email")        # Mock: Email already exists in database
    def test_register_duplicate_user(self, mock_get_user):

        existing_user = MagicMock(spec=User)
        existing_user.email = "duplicate@company.com"
        mock_get_user.return_value = existing_user

        response = self.client.post("/register", json={
            "email": "duplicate@company.com",
            "password": "Password@123",
            "role": "EMPLOYEE"
        })

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["message"], "User already exists")

    def test_register_missing_fields(self):  # Missing password and role
        response = self.client.post("/register", json={
            "email": "incomplete@company.com"
        })

        self.assertEqual(response.status_code, 400) # missing field returns 400
        data = response.get_json()
        self.assertIn("required", data["message"].lower())

    # LOGIN  

    @patch("services.auth_service.verify_password")
    @patch("services.auth_service.get_user_by_email")
    def test_login_success(self, mock_get_user, mock_verify_password):
        # Mock user record
        mock_user = MagicMock(spec=User)
        mock_user.id = 5
        mock_user.email = "john@company.com"
        mock_user.password_hash = "hashed_pass"
        mock_user.role = "EMPLOYEE"
        mock_user.is_active = True

        mock_get_user.return_value = mock_user
        mock_verify_password.return_value = True

        response = self.client.post("/login", json={
            "email": "john@company.com",
            "password": "Password@123"
        })

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("access_token", data)
        self.assertEqual(data["email"], "john@company.com")
        self.assertEqual(data["role"], "EMPLOYEE")
        self.assertEqual(data["user_id"], 5)

    @patch("services.auth_service.verify_password")
    @patch("services.auth_service.get_user_by_email")
    def test_login_invalid_password(self, mock_get_user, mock_verify_password):
        mock_user = MagicMock(spec=User)
        mock_user.email = "john@company.com"
        mock_user.password_hash = "hashed_pass"
        mock_user.is_active = True

        mock_get_user.return_value = mock_user
        mock_verify_password.return_value = False  # Password mismatch

        response = self.client.post("/login", json={
            "email": "john@company.com",
            "password": "WrongPassword"
        })

        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertEqual(data["message"], "Invalid password")

    @patch("services.auth_service.get_user_by_email")
    def test_login_nonexistent_user(self, mock_get_user): # 401 when user not  found
        mock_get_user.return_value = None

        response = self.client.post("/login", json={
            "email": "nonexistent@company.com",
            "password": "Password@123"
        })

        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertEqual(data["message"], "User not found")

    @patch("services.auth_service.verify_password")
    @patch("services.auth_service.get_user_by_email")
    def test_login_inactive_user(self, mock_get_user, mock_verify_password):
        """Test login fails with 401 when user account is deactivated."""
        mock_user = MagicMock(spec=User)
        mock_user.email = "inactive@company.com"
        mock_user.password_hash = "hashed_pass"
        mock_user.is_active = False  # Deactivated account

        mock_get_user.return_value = mock_user
        mock_verify_password.return_value = True

        response = self.client.post("/login", json={
            "email": "inactive@company.com",
            "password": "Password@123"
        })

        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertEqual(data["message"], "User Account is inactive")

    #  JWT TOKEN & ROUTE TESTS 

    def test_valid_jwt(self):
        """Test accessing protected route with a valid JWT token."""
        token = create_access_token(identity="10", additional_claims={"role": "MANAGER"})

        response = self.client.get("/profile", headers={
            "Authorization": f"Bearer {token}"
        })

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["user_id"], "10")
        self.assertEqual(data["role"], "MANAGER")

    def test_without_jwt(self):
        """Test accessing protected route without a JWT token returns 401."""
        response = self.client.get("/profile")
        self.assertEqual(response.status_code, 401)

    # RBAC TESTS 

    @patch("services.expense_category_service.create_category_dao")
    @patch("services.expense_category_service.get_category_by_name")
    def test_role_based_access_admin(self, mock_get_cat, mock_create_cat):
        admin_token = create_access_token(identity="1", additional_claims={"role": "ADMIN"})

        mock_get_cat.return_value = None
        mock_category = MagicMock(spec=ExpenseCategory)
        mock_category.ex_category_id = 1
        mock_category.category_name = "Flight"
        mock_category.description = "Air travel"
        mock_create_cat.return_value = mock_category

        response = self.client.post("/categories", json={
            "category_name": "Flight",
            "description": "Air travel"
        }, headers={
            "Authorization": f"Bearer {admin_token}"
        })

        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data["category_name"], "Flight")

    def test_role_based_access_forbidden_for_employee(self):
        """Test that an EMPLOYEE token is rejected with 403 Forbidden on Admin endpoints."""
        employee_token = create_access_token(identity="2", additional_claims={"role": "EMPLOYEE"})

        response = self.client.post("/categories", json={
            "category_name": "Prohibited Category",
            "description": "Should be blocked"
        }, headers={
            "Authorization": f"Bearer {employee_token}"
        })

        self.assertEqual(response.status_code, 403)
        data = response.get_json()
        self.assertEqual(data["message"], "Access forbidden")


if __name__ == "__main__":
    unittest.main()
