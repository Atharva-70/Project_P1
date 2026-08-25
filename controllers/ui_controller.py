from math import ceil
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
from services.auth_service import login_user, register_user, change_password
from services.employee_service import get_my_profile, update_my_profile
from services.travel_service import create_travel_request,get_user_travel_requests,get_pending_travel_approvals,approve_travel,reject_travel
from services.expense_claim_service import create_expense_claim,get_expense_claims,get_expense_claim_by_id,delete_expense_claim,submit_expense_claim,get_pending_manager_approvals,approve_expense_claim_by_manager,reject_expense_claim_by_manager,get_finance_verification_queue,verify_expense_claim_by_finance
from services.expense_item_service import  create_expense_item, delete_expense_item
from dao.expense_item_dao import get_expense_items_by_claim_id
from services.expense_category_service import get_all_categories
from services.expense_receipt_service import upload_and_save_receipt
from services.approval_history_service import get_claim_history
from services.reimbursement_service import process_claim_reimbursement
from services.dashboard_service import get_employee_dashboard,get_reports_summary
from dao.expense_claim_dao import get_claims_by_status

ui_bp = Blueprint("ui", __name__)
def login_required_ui(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to access the portal.", "danger")
            return redirect(url_for("ui.login"))
        return f(*args, **kwargs)
    return decorated_function


@ui_bp.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("ui.dashboard"))
    return redirect(url_for("ui.login"))


# auth routes

@ui_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.is_json:
        from controllers.auth_controller import login as api_login
        return api_login()

    if session.get("user_id") and request.method == "GET":
        return redirect(url_for("ui.dashboard"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user, error = login_user(email, password)
        if error:
            flash(error, "danger")
            return render_template("auth/login.html")

        # get employee name
        emp, _ = get_my_profile(user.id)
        user_name = f"{emp['first_name']} {emp['last_name']}".strip() if emp and emp.get("first_name") else user.email

        # Save session
        session["user_id"] = user.id
        session["email"] = user.email
        session["user_name"] = user_name
        session["role"] = user.role
        flash(f"Welcome back, {user_name}!", "success")
        return redirect(url_for("ui.dashboard"))

    return render_template("auth/login.html")


@ui_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.is_json:
        from controllers.auth_controller import register as register_api
        return register_api()

    if session.get("user_id") and request.method == "GET":
        return redirect(url_for("ui.dashboard"))

    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        password = request.form.get("password")
        role = "EMPLOYEE"  # default employee
        if not email or not password or not first_name:
            flash("First name, email, and password are required.", "danger")
            return render_template("auth/register.html")

        user, error = register_user(
            email=email,
            password=password,
            role=role,
            first_name=first_name,
            last_name=last_name
        )
        if error:
            flash(error, "danger")
            return render_template("auth/register.html")

        flash(f"Account created successfully for {first_name}! Please sign in.", "success")
        return redirect(url_for("ui.login"))

    return render_template("auth/register.html")



@ui_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("ui.login"))


# dashboard

@ui_bp.route("/dashboard")
@login_required_ui
def dashboard():
    user_id = session.get("user_id")
    stats, _ = get_employee_dashboard(user_id)
    recent_claims = get_expense_claims(user_id)
    if recent_claims:
        recent_claims = recent_claims[:5]

    return render_template(
        "employee/dashboard.html",
        active_page="dashboard",
        stats=stats,
        recent_claims=recent_claims
    )


@ui_bp.route("/profile", methods=["GET"])
def profile_view():
    if session.get("user_id"):
        user_id = session.get("user_id")
        emp, _ = get_my_profile(user_id)
        return render_template("employee/profile.html", employee=emp, active_page="profile")

    from controllers.auth_controller import profile as api_profile
    return api_profile()


@ui_bp.route("/profile/update", methods=["POST"])
@login_required_ui
def profile_update():
    user_id = session.get("user_id")
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    phone = request.form.get("phone")
    department = request.form.get("department")
    bank_account_number = request.form.get("bank_account_number")
    bank_ifsc_code = request.form.get("bank_ifsc_code")

    emp, error = update_my_profile(
        user_id=user_id,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        department=department,
        bank_account_number=bank_account_number,
        bank_ifsc_code=bank_ifsc_code
    )

    if error:
        flash(error, "danger")
    else:
        flash("Profile updated successfully!", "success")

    return redirect(url_for("ui.profile_view"))


@ui_bp.route("/profile/change-password", methods=["POST"])
@login_required_ui
def change_password():
    user_id = session.get("user_id")
    current_password = request.form.get("current_password")
    new_password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")

    if not current_password or not new_password:
        flash("All password fields are required.", "danger")
        return redirect(url_for("ui.profile_view"))

    if new_password != confirm_password:
        flash("New password and confirmation do not match.", "danger")
        return redirect(url_for("ui.profile_view"))

    user, error = change_password(user_id, current_password, new_password)
    if error:
        flash(error, "danger")
    else:
        flash("Password changed successfully!", "success")

    return redirect(url_for("ui.profile_view"))


#  travel_req

@ui_bp.route("/travel-requests")
@login_required_ui
def travel_list():
    user_id = session.get("user_id")
    travel_requests, _ = get_user_travel_requests(user_id)
    return render_template(
        "travel/travel_list.html",
        travel_requests=travel_requests,
        active_page="travel"
    )


@ui_bp.route("/travel-requests/new", methods=["GET", "POST"])
@login_required_ui
def travel_new():
    if request.method == "POST":
        user_id = session.get("user_id")
        source = request.form.get("source")
        destination = request.form.get("destination")
        purpose = request.form.get("purpose")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        travel_request_number = request.form.get("travel_request_number")

        trv, error = create_travel_request(
            user_id=user_id,
            source=source,
            destination=destination,
            purpose=purpose,
            start_date=start_date,
            end_date=end_date,
            travel_request_number=travel_request_number
        )

        if error:
            flash(error, "danger")
            return render_template("travel/travel_form.html", active_page="travel")

        flash("Travel request submitted successfully!", "success")
        return redirect(url_for("ui.travel_list"))

    return render_template("travel/travel_form.html", active_page="travel")


#  expense_claims

@ui_bp.route("/claims")
@login_required_ui
def claim_list():
    user_id = session.get("user_id")
    status_filter = request.args.get("status")
    search_query = request.args.get("search", "").strip().lower()
    page = request.args.get("page", 1, type=int)
    per_page = 5

    claims = get_expense_claims(user_id)

    if status_filter:
        claims = [c for c in claims if c.status == status_filter]

    if search_query:
        claims = [c for c in claims if search_query in c.claim_number.lower()]

    total_claims = len(claims)
    total_pages = ceil(total_claims / per_page) if total_claims > 0 else 1
    page = max(1, min(page, total_pages))
    paginated_claims = claims[(page - 1) * per_page : page * per_page]

    return render_template(
        "claims/claim_list.html",
        claims=paginated_claims,
        current_status=status_filter,
        search_query=search_query,
        page=page,
        total_pages=total_pages,
        active_page="claims"
    )



@ui_bp.route("/claims/new", methods=["GET", "POST"])
@login_required_ui
def claim_new():
    user_id = session.get("user_id")
    if request.method == "POST":
        travel_id = request.form.get("travel_id")
        claim_number = request.form.get("claim_number")

        claim, error = create_expense_claim(
            user_id=user_id,
            travel_id=int(travel_id),
            total_amount=0.0,
            claim_number=claim_number
        )

        if error:
            flash(error, "danger")
            travel_requests, _ = get_user_travel_requests(user_id)
            return render_template("claims/claim_create.html", travel_requests=travel_requests, active_page="claims")

        flash("Draft claim initialized! Add your itemized expenses below.", "success")
        return redirect(url_for("ui.claim_details", claim_id=claim.ex_claim_id))

    travel_requests, _ = get_user_travel_requests(user_id)
    return render_template("claims/claim_create.html", travel_requests=travel_requests, active_page="claims")


@ui_bp.route("/claims/<int:claim_id>")
@login_required_ui
def claim_details(claim_id):
    user_id = session.get("user_id")
    claim, error = get_expense_claim_by_id(user_id, claim_id, role=session.get("role", "EMPLOYEE"))
    if error:
        flash(error, "danger")
        return redirect(url_for("ui.claim_list"))

    items = get_expense_items_by_claim_id(claim_id)
    categories = get_all_categories()
    history, _ = get_claim_history(claim_id)

    return render_template(
        "claims/claim_details.html",
        claim=claim,
        items=items,
        categories=categories,
        history=history,
        active_page="claims"
    )


@ui_bp.route("/claims/<int:claim_id>/submit", methods=["POST"])
@login_required_ui
def claim_submit(claim_id):
    user_id = session.get("user_id")
    claim, error = submit_expense_claim(user_id, claim_id)
    if error:
        flash(error, "danger")
    else:
        flash(f"Claim #{claim.claim_number} successfully submitted for Manager approval!", "success")

    return redirect(url_for("ui.claim_details", claim_id=claim_id))


#  expense items

@ui_bp.route("/claims/<int:claim_id>/items/new", methods=["POST"])
@login_required_ui
def item_create(claim_id):
    user_id = session.get("user_id")
    category_id = request.form.get("category_id")
    amount = request.form.get("amount")
    expense_date = request.form.get("expense_date")
    description = request.form.get("description")

    item, error = create_expense_item(
        user_id=user_id,
        claim_id=claim_id,
        category_id=int(category_id),
        amount=float(amount),
        expense_date=expense_date,
        description=description
    )

    if error:
        flash(error, "danger")
    else:
        flash("Expense line item added successfully!", "success")

    return redirect(url_for("ui.claim_details", claim_id=claim_id))


@ui_bp.route("/items/<int:item_id>/delete", methods=["POST"])
@login_required_ui
def item_delete(item_id):
    user_id = session.get("user_id")
    success, error = delete_expense_item(user_id, item_id)
    if error:
        flash(error, "danger")
        return redirect(url_for("ui.claim_list"))

    flash("Line item removed.", "success")
    return redirect(request.referrer or url_for("ui.claim_list"))


#expense receipt

@ui_bp.route("/items/<int:item_id>/receipt", methods=["POST"])
@login_required_ui
def item_receipt_upload(item_id):
    user_id = session.get("user_id")
    if "file" not in request.files:
        flash("No file selected for upload.", "danger")
        return redirect(request.referrer or url_for("ui.claim_list"))

    file = request.files["file"]
    receipt, error, status_code = upload_and_save_receipt(user_id, item_id, file)
    if error:
        flash(error, "danger")
    else:
        flash(f"Receipt '{receipt.file_name}' uploaded and verified successfully!", "success")

    return redirect(request.referrer or url_for("ui.claim_list"))


@ui_bp.route("/items/<int:item_id>/generate-receipt", methods=["POST"])
@login_required_ui
def item_generate_receipt(item_id):
    user_id = session.get("user_id")
    from services.expense_receipt_service import generate_pdf_receipt
    receipt, error, status_code = generate_pdf_receipt(user_id, item_id)
    if error:
        flash(error, "danger")
    else:
        flash(f"Official PDF receipt '{receipt.file_name}' generated and attached!", "success")

    return redirect(request.referrer or url_for("ui.claim_list"))


# manager approvals

@ui_bp.route("/approvals")
@login_required_ui
def manager_approvals():
    user_id = session.get("user_id")
    role = session.get("role")

    pending_travel, _ = get_pending_travel_approvals(user_id, role)
    pending_claims, _ = get_pending_manager_approvals(user_id, role)

    return render_template(
        "manager/approvals.html",
        pending_travel=pending_travel or [],
        pending_claims=pending_claims or [],
        active_page="approvals"
    )


@ui_bp.route("/travel-requests/<int:travel_id>/approve", methods=["POST"])
@login_required_ui
def travel_approve(travel_id):
    trv, error = approve_travel(travel_id)
    if error:
        flash(error, "danger")
    else:
        flash(f"Travel request #{trv.travel_request_number} approved!", "success")
    return redirect(url_for("ui.manager_approvals"))


@ui_bp.route("/travel-requests/<int:travel_id>/reject", methods=["POST"])
@login_required_ui
def travel_reject(travel_id):
    trv, error = reject_travel(travel_id)
    if error:
        flash(error, "danger")
    else:
        flash(f"Travel request #{trv.travel_request_number} rejected.", "success")
    return redirect(url_for("ui.manager_approvals"))


@ui_bp.route("/claims/<int:claim_id>/approve", methods=["POST"])
@login_required_ui
def claim_approve(claim_id):
    user_id = session.get("user_id")
    claim, error = approve_expense_claim_by_manager(user_id, claim_id)
    if error:
        flash(error, "danger")
    else:
        flash(f"Claim #{claim.claim_number} approved and forwarded to Finance!", "success")
    return redirect(url_for("ui.manager_approvals"))


@ui_bp.route("/claims/<int:claim_id>/reject", methods=["POST"])
@login_required_ui
def claim_reject(claim_id):
    user_id = session.get("user_id")
    comments = request.form.get("comments")
    claim, error = reject_expense_claim_by_manager(user_id, claim_id, comments)
    if error:
        flash(error, "danger")
    else:
        flash(f"Claim #{claim.claim_number} rejected. Employee has been notified.", "success")
    return redirect(url_for("ui.manager_approvals"))

#  finance

@ui_bp.route("/finance")
@login_required_ui
def finance_dashboard():
    approved_claims = get_finance_verification_queue()
    verified_claims = get_claims_by_status("FINANCE VERIFIED")

    return render_template(
        "finance/finance_dashboard.html",
        approved_claims=approved_claims or [],
        verified_claims=verified_claims or [],
        active_page="finance"
    )


@ui_bp.route("/claims/<int:claim_id>/finance-verify", methods=["POST"])
@login_required_ui
def finance_verify(claim_id):
    user_id = session.get("user_id")
    claim, error = verify_expense_claim_by_finance(user_id, claim_id)
    if error:
        flash(error, "danger")
    else:
        flash(f"Claim #{claim.claim_number} verified and moved to Reimbursement queue!", "success")
    return redirect(url_for("ui.finance_dashboard"))


@ui_bp.route("/claims/<int:claim_id>/process-reimbursement", methods=["POST"])
@login_required_ui
def process_reimbursement(claim_id):
    user_id = session.get("user_id")
    payment_reference = request.form.get("payment_reference")

    reim, error = process_claim_reimbursement(user_id, claim_id, payment_reference)
    if error:
        flash(error, "danger")
    else:
        flash(f"Reimbursement paid! Bank Reference: {reim.payment_reference}", "success")
    return redirect(url_for("ui.finance_dashboard"))


# report

@ui_bp.route("/reports")
@login_required_ui
def reports():
    summary, _ = get_reports_summary()
    category_stats = summary.get("expenses_by_category", []) if summary else []
    finance_overview = summary.get("finance_overview", {}) if summary else {}
    return render_template(
        "finance/reports.html",
        category_stats=category_stats or [],
        finance_overview=finance_overview,
        active_page="reports"
    )
