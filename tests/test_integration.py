import unittest
import io
from decimal import Decimal
from datetime import date
from app import create_app
from config.database import db
from models.user import User
from models.employee import Employee
from models.expense_category import ExpenseCategory
from models.expense_policy import ExpensePolicy
from models.travel_request import TravelRequest
from models.expense_claim import ExpenseClaim
from models.expense_item import ExpenseItem
from models.expense_receipt import ExpenseReceipt
from models.approval_history import ApprovalHistory
from models.reimbursement import Reimbursement
from constants.status import ClaimStatus, TravelStatus, ReimbursementStatus, UserRole
from flask_jwt_extended import create_access_token


class TestRealDatabaseWorkflowIntegration(unittest.TestCase):
    """
    Real integration tests using an in-memory SQLite database.
    Tests end-to-end workflow transitions, database relationships, and business integrity without mocks.
    """

    @classmethod
    def setUpClass(cls):
        cls.app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "JWT_SECRET_KEY": "INTEGRATION-TEST-SECRET-KEY-32BYTES-LONG!"
        })

    def setUp(self):
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _create_user_and_employee(self, email, role, first_name, last_name, emp_code, manager_id=None):
        user = User(
            email=email,
            password_hash="pbkdf2:sha256:fakehash",
            role=role,
            is_active=True
        )
        db.session.add(user)
        db.session.flush()

        emp = Employee(
            user_id=user.id,
            emp_code=emp_code,
            first_name=first_name,
            last_name=last_name,
            manager_id=manager_id
        )
        db.session.add(emp)
        db.session.commit()
        return user, emp

    def test_full_end_to_end_expense_lifecycle(self):
        """
        Complete end-to-end test from travel request to final reimbursement payout:
        1. Setup Admin, Manager, Employee, and Finance users.
        2. Admin creates Category and Policy limit.
        3. Employee submits Travel Request.
        4. Manager approves Travel Request.
        5. Employee creates Claim against approved travel.
        6. Employee adds item within policy limit & uploads receipt.
        7. Employee submits Claim.
        8. Manager approves Claim.
        9. Finance verifies Claim.
        10. Finance processes Reimbursement payout.
        11. Audit history timeline & relationships verification.
        """
        # 1. Setup Users
        admin_user, admin_emp = self._create_user_and_employee(
            "admin@corp.com", UserRole.ADMIN, "System", "Admin", "EMP-0001"
        )
        mgr_user, mgr_emp = self._create_user_and_employee(
            "manager@corp.com", UserRole.MANAGER, "Sarah", "Connor", "EMP-0002"
        )
        emp_user, emp_emp = self._create_user_and_employee(
            "john@corp.com", UserRole.EMPLOYEE, "John", "Doe", "EMP-0003", manager_id=mgr_emp.e_id
        )
        fin_user, fin_emp = self._create_user_and_employee(
            "finance@corp.com", UserRole.FINANCE, "Frank", "Finance", "EMP-0004"
        )

        admin_token = create_access_token(identity=str(admin_user.id), additional_claims={"role": UserRole.ADMIN})
        mgr_token = create_access_token(identity=str(mgr_user.id), additional_claims={"role": UserRole.MANAGER})
        emp_token = create_access_token(identity=str(emp_user.id), additional_claims={"role": UserRole.EMPLOYEE})
        fin_token = create_access_token(identity=str(fin_user.id), additional_claims={"role": UserRole.FINANCE})

        # 2. Admin creates Expense Category and Policy
        cat_resp = self.client.post("/categories", json={
            "category_name": "Air Travel",
            "description": "Domestic business flights"
        }, headers={"Authorization": f"Bearer {admin_token}"})
        self.assertEqual(cat_resp.status_code, 201)
        cat_id = cat_resp.get_json()["category_id"]

        pol_resp = self.client.post("/policies", json={
            "category_id": cat_id,
            "max_amount": 10000.00
        }, headers={"Authorization": f"Bearer {admin_token}"})
        self.assertEqual(pol_resp.status_code, 201)

        # 3. Employee submits Travel Request
        trv_resp = self.client.post("/travel", json={
            "source": "Mumbai",
            "destination": "Bengaluru",
            "purpose": "Tech Conference 2026",
            "start_date": "2026-10-01",
            "end_date": "2026-10-05",
            "travel_request_number": "TRV-2026-INTEG-001"
        }, headers={"Authorization": f"Bearer {emp_token}"})
        self.assertEqual(trv_resp.status_code, 201)
        travel_id = trv_resp.get_json()["travel_id"]
        self.assertEqual(trv_resp.get_json()["status"], TravelStatus.PENDING)

        # 4. Manager approves Travel Request
        appr_trv_resp = self.client.post(f"/travel/{travel_id}/approve", headers={"Authorization": f"Bearer {mgr_token}"})
        self.assertEqual(appr_trv_resp.status_code, 200)
        self.assertEqual(appr_trv_resp.get_json()["status"], TravelStatus.APPROVED)

        # 5. Employee creates Claim against approved travel
        claim_resp = self.client.post("/expense_claim", json={
            "travel_id": travel_id,
            "claim_number": "CLM-INTEG-2026-001"
        }, headers={"Authorization": f"Bearer {emp_token}"})
        self.assertEqual(claim_resp.status_code, 201)
        claim_id = claim_resp.get_json()["expense_claim_id"]
        self.assertEqual(claim_resp.get_json()["status"], ClaimStatus.DRAFT)

        # 6. Employee adds item within policy limit
        item_resp = self.client.post("/expense_item", json={
            "claim_id": claim_id,
            "category_id": cat_id,
            "amount": 7500.00,
            "expense_date": "2026-10-02",
            "description": "Flight Ticket BOM to BLR"
        }, headers={"Authorization": f"Bearer {emp_token}"})
        self.assertEqual(item_resp.status_code, 201)
        item_id = item_resp.get_json()["expense_item_id"]

        # Upload receipt for item
        receipt_data = {
            "expense_item_id": str(item_id),
            "file": (io.BytesIO(b"%PDF-1.4 official flight invoice"), "flight_ticket.pdf")
        }
        rcpt_resp = self.client.post("/expense_receipt", data=receipt_data, content_type="multipart/form-data",
                                     headers={"Authorization": f"Bearer {emp_token}"})
        self.assertEqual(rcpt_resp.status_code, 201)

        # 7. Employee submits Claim
        submit_resp = self.client.post(f"/expense_claim/{claim_id}/submit", headers={"Authorization": f"Bearer {emp_token}"})
        self.assertEqual(submit_resp.status_code, 200)
        self.assertEqual(submit_resp.get_json()["status"], ClaimStatus.SUBMITTED)

        # 8. Manager approves Claim
        mgr_appr_resp = self.client.post(f"/expense_claim/{claim_id}/approve", json={
            "comments": "Approved after reviewing ticket and agenda."
        }, headers={"Authorization": f"Bearer {mgr_token}"})
        self.assertEqual(mgr_appr_resp.status_code, 200)
        self.assertEqual(mgr_appr_resp.get_json()["status"], ClaimStatus.APPROVED)

        # 9. Finance verifies Claim
        fin_ver_resp = self.client.post(f"/expense_claim/{claim_id}/finance-verify", json={
            "comments": "GST invoice verified with airline."
        }, headers={"Authorization": f"Bearer {fin_token}"})
        self.assertEqual(fin_ver_resp.status_code, 200)
        self.assertEqual(fin_ver_resp.get_json()["status"], ClaimStatus.FINANCE_VERIFIED)

        # 10. Finance processes Reimbursement payout
        pay_resp = self.client.post("/reimbursements/process", json={
            "claim_id": claim_id,
            "payment_reference": "NEFT-HDFC-99887766"
        }, headers={"Authorization": f"Bearer {fin_token}"})
        self.assertEqual(pay_resp.status_code, 200)
        self.assertEqual(pay_resp.get_json()["status"], ReimbursementStatus.PAID)
        self.assertEqual(pay_resp.get_json()["payment_reference"], "NEFT-HDFC-99887766")

        # 11. Verify DB Relationships and Timeline History
        db_claim = ExpenseClaim.query.get(claim_id)
        self.assertEqual(db_claim.status, ClaimStatus.REIMBURSED)
        self.assertEqual(Decimal(str(db_claim.total_amount)), Decimal("7500.00"))
        self.assertEqual(len(db_claim.items), 1)
        self.assertEqual(len(db_claim.items[0].receipts), 1)
        self.assertIsNotNone(db_claim.reimbursement)
        self.assertEqual(db_claim.reimbursement.status, ReimbursementStatus.PAID)

        # Check Timeline
        history_resp = self.client.get(f"/expense_claim/{claim_id}/history", headers={"Authorization": f"Bearer {emp_token}"})
        self.assertEqual(history_resp.status_code, 200)
        history_list = history_resp.get_json()
        self.assertEqual(len(history_list), 4)
        actions = [h["action"] for h in history_list]
        self.assertEqual(actions, [
            ClaimStatus.SUBMITTED,
            ClaimStatus.APPROVED,
            ClaimStatus.FINANCE_VERIFIED,
            ClaimStatus.REIMBURSED
        ])

    def test_policy_limit_breach_rejected(self):
        """Test that policy limit breaches are strictly rejected during real item insertion."""
        admin_user, _ = self._create_user_and_employee("admin@corp.com", UserRole.ADMIN, "Admin", "User", "EMP-01")
        emp_user, emp_emp = self._create_user_and_employee("emp@corp.com", UserRole.EMPLOYEE, "Emp", "User", "EMP-02")

        admin_token = create_access_token(identity=str(admin_user.id), additional_claims={"role": UserRole.ADMIN})
        emp_token = create_access_token(identity=str(emp_user.id), additional_claims={"role": UserRole.EMPLOYEE})

        # Category with 2000 limit
        cat = ExpenseCategory(category_name="Meals", description="Daily meals", is_active=True)
        db.session.add(cat)
        db.session.flush()

        pol = ExpensePolicy(category_id=cat.ex_category_id, max_amount=Decimal("2000.00"), is_active=True)
        db.session.add(pol)

        trv = TravelRequest(
            employee_id=emp_emp.e_id, source="CityA", destination="CityB", purpose="Work",
            start_date=date(2026, 9, 1), end_date=date(2026, 9, 3), status=TravelStatus.APPROVED,
            travel_request_number="TRV-MEALS-01"
        )
        db.session.add(trv)
        db.session.flush()

        claim = ExpenseClaim(
            employee_id=emp_emp.e_id, travel_id=trv.travel_id, total_amount=Decimal("0.00"),
            claim_number="CLM-MEALS-01", status=ClaimStatus.DRAFT
        )
        db.session.add(claim)
        db.session.commit()

        # Item with 2500 (exceeds 2000 limit)
        resp = self.client.post("/expense_item", json={
            "claim_id": claim.ex_claim_id,
            "category_id": cat.ex_category_id,
            "amount": 2500.00,
            "expense_date": "2026-09-02",
            "description": "Team Dinner"
        }, headers={"Authorization": f"Bearer {emp_token}"})

        self.assertEqual(resp.status_code, 400)
        self.assertIn("exceeds company policy limit", resp.get_json()["message"].lower())

    def test_manager_ownership_enforcement_during_approval(self):
        """Test that a manager cannot approve claims belonging to employees who don't report to them."""
        mgr1_user, mgr1_emp = self._create_user_and_employee("mgr1@corp.com", UserRole.MANAGER, "Mgr", "One", "MGR-01")
        mgr2_user, mgr2_emp = self._create_user_and_employee("mgr2@corp.com", UserRole.MANAGER, "Mgr", "Two", "MGR-02")
        emp_user, emp_emp = self._create_user_and_employee("emp@corp.com", UserRole.EMPLOYEE, "Emp", "Rep1", "EMP-03", manager_id=mgr1_emp.e_id)

        # Claim submitted by employee under manager 1
        trv = TravelRequest(
            employee_id=emp_emp.e_id, source="A", destination="B", purpose="Audit",
            start_date=date(2026, 9, 1), end_date=date(2026, 9, 3), status=TravelStatus.APPROVED,
            travel_request_number="TRV-AUDIT-01"
        )
        db.session.add(trv)
        db.session.flush()

        claim = ExpenseClaim(
            employee_id=emp_emp.e_id, travel_id=trv.travel_id, total_amount=Decimal("500.00"),
            claim_number="CLM-AUDIT-01", status=ClaimStatus.SUBMITTED
        )
        db.session.add(claim)
        db.session.commit()

        # Manager 2 attempts to approve Manager 1's subordinate claim
        mgr2_token = create_access_token(identity=str(mgr2_user.id), additional_claims={"role": UserRole.MANAGER})
        resp = self.client.post(f"/expense_claim/{claim.ex_claim_id}/approve", json={
            "comments": "Sneaky approval"
        }, headers={"Authorization": f"Bearer {mgr2_token}"})

        self.assertEqual(resp.status_code, 400)
        self.assertIn("not authorized to approve claims for this employee", resp.get_json()["message"].lower())

    def test_unauthorized_claim_and_item_view_prevented(self):
        """Test that employees cannot view another employee's claim or items."""
        _, emp1_emp = self._create_user_and_employee("emp1@corp.com", UserRole.EMPLOYEE, "Alice", "A", "EMP-A")
        emp2_user, emp2_emp = self._create_user_and_employee("emp2@corp.com", UserRole.EMPLOYEE, "Bob", "B", "EMP-B")

        trv = TravelRequest(
            employee_id=emp1_emp.e_id, source="A", destination="B", purpose="Visit",
            start_date=date(2026, 9, 1), end_date=date(2026, 9, 2), status=TravelStatus.APPROVED,
            travel_request_number="TRV-VISIT-01"
        )
        db.session.add(trv)
        db.session.flush()

        claim = ExpenseClaim(
            employee_id=emp1_emp.e_id, travel_id=trv.travel_id, total_amount=Decimal("100.00"),
            claim_number="CLM-ALICE-01", status=ClaimStatus.DRAFT
        )
        db.session.add(claim)
        db.session.commit()

        # Bob tries to access Alice's claim
        bob_token = create_access_token(identity=str(emp2_user.id), additional_claims={"role": UserRole.EMPLOYEE})
        view_claim_resp = self.client.get(f"/expense_claim/{claim.ex_claim_id}", headers={"Authorization": f"Bearer {bob_token}"})
        self.assertEqual(view_claim_resp.status_code, 403)

        view_items_resp = self.client.get(f"/expense_claim/{claim.ex_claim_id}/items", headers={"Authorization": f"Bearer {bob_token}"})
        self.assertEqual(view_items_resp.status_code, 403)

    def test_duplicate_receipt_filename_blocked(self):
        """Test that duplicate receipt filenames on the same item return 400."""
        emp_user, emp_emp = self._create_user_and_employee("emp@corp.com", UserRole.EMPLOYEE, "Charlie", "C", "EMP-C")
        emp_token = create_access_token(identity=str(emp_user.id), additional_claims={"role": UserRole.EMPLOYEE})

        cat = ExpenseCategory(category_name="Taxi", is_active=True)
        db.session.add(cat)
        db.session.flush()

        trv = TravelRequest(
            employee_id=emp_emp.e_id, source="A", destination="B", purpose="Ride",
            start_date=date(2026, 9, 1), end_date=date(2026, 9, 2), status=TravelStatus.APPROVED,
            travel_request_number="TRV-RIDE-01"
        )
        db.session.add(trv)
        db.session.flush()

        claim = ExpenseClaim(
            employee_id=emp_emp.e_id, travel_id=trv.travel_id, total_amount=Decimal("300.00"),
            claim_number="CLM-RIDE-01", status=ClaimStatus.DRAFT
        )
        db.session.add(claim)
        db.session.commit()

        item = ExpenseItem(
            claim_id=claim.ex_claim_id, category_id=cat.ex_category_id, amount=Decimal("300.00"),
            expense_date=date(2026, 9, 1), description="Uber ride"
        )
        db.session.add(item)
        db.session.commit()

        # First upload
        data1 = {
            "expense_item_id": str(item.ex_item_id),
            "file": (io.BytesIO(b"pdf byte content 1"), "uber_bill.pdf")
        }
        r1 = self.client.post("/expense_receipt", data=data1, content_type="multipart/form-data",
                              headers={"Authorization": f"Bearer {emp_token}"})
        self.assertEqual(r1.status_code, 201)

        # Duplicate upload
        data2 = {
            "expense_item_id": str(item.ex_item_id),
            "file": (io.BytesIO(b"pdf byte content 2"), "uber_bill.pdf")
        }
        r2 = self.client.post("/expense_receipt", data=data2, content_type="multipart/form-data",
                              headers={"Authorization": f"Bearer {emp_token}"})
        self.assertEqual(r2.status_code, 400)
        self.assertIn("already uploaded", r2.get_json()["message"].lower())


if __name__ == "__main__":
    unittest.main()
