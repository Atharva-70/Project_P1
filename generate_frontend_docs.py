from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output" / "pdf" / "ExpenseFlow_Frontend_Pages_Documentation.pdf"


class BrandedCanvas(canvas.Canvas):
    """Adds a restrained, consistent header and page number to every content page."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_chrome(total_pages)
            super().showPage()
        super().save()

    def _draw_chrome(self, total_pages):
        if self._pageNumber == 1:
            return
        self.saveState()
        self.setStrokeColor(colors.HexColor("#dbe4f0"))
        self.setLineWidth(0.5)
        self.line(40, 752, 572, 752)
        self.setFillColor(colors.HexColor("#475569"))
        self.setFont("Helvetica-Bold", 8)
        self.drawString(40, 762, "ExpenseFlow | Frontend Pages & Functionality")
        self.setFont("Helvetica", 8)
        self.drawRightString(572, 762, "Server-rendered Flask UI")
        self.line(40, 40, 572, 40)
        self.drawString(40, 27, "ExpenseFlow - Corporate Travel & Expense Management")
        self.drawRightString(572, 27, f"Page {self._pageNumber} of {total_pages}")
        self.restoreState()


def build_styles():
    base = getSampleStyleSheet()
    palette = {
        "navy": "#12355b",
        "blue": "#2563eb",
        "ink": "#0f172a",
        "body": "#334155",
        "muted": "#64748b",
        "line": "#dbe4f0",
        "wash": "#f4f8ff",
        "green": "#15803d",
    }
    return {
        "cover_title": ParagraphStyle(
            "CoverTitle", parent=base["Title"], fontName="Helvetica-Bold", fontSize=28,
            leading=33, textColor=colors.HexColor(palette["navy"]), alignment=TA_CENTER,
            spaceAfter=9,
        ),
        "cover_subtitle": ParagraphStyle(
            "CoverSubtitle", parent=base["BodyText"], fontSize=12, leading=18,
            textColor=colors.HexColor(palette["muted"]), alignment=TA_CENTER,
        ),
        "h1": ParagraphStyle(
            "H1", parent=base["Heading1"], fontName="Helvetica-Bold", fontSize=20,
            leading=25, textColor=colors.HexColor(palette["navy"]), spaceBefore=0, spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "H2", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=13,
            leading=17, textColor=colors.HexColor(palette["ink"]), spaceBefore=12, spaceAfter=5,
        ),
        "body": ParagraphStyle(
            "Body", parent=base["BodyText"], fontName="Helvetica", fontSize=9.3,
            leading=13.3, textColor=colors.HexColor(palette["body"]), spaceAfter=5,
        ),
        "small": ParagraphStyle(
            "Small", parent=base["BodyText"], fontName="Helvetica", fontSize=8.1,
            leading=10.8, textColor=colors.HexColor(palette["muted"]),
        ),
        "label": ParagraphStyle(
            "Label", parent=base["BodyText"], fontName="Helvetica-Bold", fontSize=8.2,
            leading=10.5, textColor=colors.HexColor(palette["blue"]), spaceAfter=3,
        ),
        "table": ParagraphStyle(
            "Table", parent=base["BodyText"], fontName="Helvetica", fontSize=8.1,
            leading=10.3, textColor=colors.HexColor(palette["body"]),
        ),
        "table_head": ParagraphStyle(
            "TableHead", parent=base["BodyText"], fontName="Helvetica-Bold", fontSize=8.1,
            leading=10.3, textColor=colors.white,
        ),
        "callout": ParagraphStyle(
            "Callout", parent=base["BodyText"], fontName="Helvetica", fontSize=8.8,
            leading=12.4, textColor=colors.HexColor(palette["body"]),
        ),
        "footer": ParagraphStyle(
            "Footer", parent=base["BodyText"], fontName="Helvetica", fontSize=8,
            leading=11, textColor=colors.HexColor(palette["muted"]), alignment=TA_CENTER,
        ),
        "palette": palette,
    }


def p(text, style):
    return Paragraph(text, style)


def bullet_list(items, styles):
    return [p(f"• {item}", styles["body"]) for item in items]


def table(rows, widths, styles, header=True):
    formatted = []
    for row_index, row in enumerate(rows):
        formatted.append([p(cell, styles["table_head"] if header and row_index == 0 else styles["table"]) for cell in row])
    t = Table(formatted, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor(styles["palette"]["line"])),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    if header:
        commands += [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(styles["palette"]["navy"]))]
        if len(rows) > 1:
            commands += [("BACKGROUND", (0, 1), (-1, -1), colors.white)]
    t.setStyle(TableStyle(commands))
    return t


def callout(title, text, styles):
    content = [[p(f"<b>{title}</b><br/>{text}", styles["callout"])]]
    t = Table(content, colWidths=[7.15 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(styles["palette"]["wash"])),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#bfdbfe")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


PAGES = [
    {
        "title": "1. Shared application shell",
        "template": "templates/base.html",
        "route": "Applied to every page through Jinja template inheritance",
        "roles": "Public header for anonymous visitors; authenticated navigation is session-aware.",
        "purpose": "Provides the common visual frame: the ExpenseFlow brand, top navigation, current-user badge, sign-out action, flash messages, and the main content container.",
        "elements": [
            "Unauthenticated visitors see Login and Register actions.",
            "Signed-in users see Dashboard, Travel Requests, Expense Claims, Profile, and Logout.",
            "Manager/Admin sessions also see Manager Approvals; Finance/Admin sessions also see Finance Queue and Reports.",
            "The active navigation item is highlighted through the active_page value supplied by the UI controller.",
            "Flash messages communicate successful actions and validation failures after form submissions.",
        ],
        "actions": "Session-driven navigation only. Logout calls <b>GET /logout</b> and clears the browser session.",
        "notes": "The shared stylesheet is <b>static/css/style.css</b>. It defines the card layout, tables, forms, buttons, status badges, responsive controls, and the blue/slate visual system used throughout the portal.",
    },
    {
        "title": "2. Sign in",
        "template": "templates/auth/login.html",
        "route": "GET /login and POST /login",
        "roles": "Public. Successful sign-in creates a browser session for an Employee, Manager, Finance user, or Admin.",
        "purpose": "Authenticates a user and redirects the browser to the dashboard. It is the entry point for the server-rendered portal, separate from the JSON API login flow.",
        "elements": [
            "Corporate Email field with browser email validation.",
            "Password field.",
            "Sign In button and a link to the registration page.",
            "Validation or authentication failures are shown through flash alerts.",
        ],
        "actions": "The controller passes the email and password to <b>login_user</b>. On success it stores user_id, email, user_name, and role in Flask session storage, then redirects to <b>/dashboard</b>.",
        "notes": "If the request body is JSON, the UI route delegates to the REST API login handler instead of rendering or redirecting a page.",
    },
    {
        "title": "3. Employee registration",
        "template": "templates/auth/register.html",
        "route": "GET /register and POST /register",
        "roles": "Public. New browser registrations are intentionally created with the EMPLOYEE role.",
        "purpose": "Creates a new employee account from a browser form and returns the user to sign in after successful registration.",
        "elements": [
            "First Name and Last Name fields.",
            "Corporate Email field.",
            "Password field.",
            "Register Account button plus a link back to Sign In.",
        ],
        "actions": "The controller validates the minimum required details, calls <b>register_user</b> with role=EMPLOYEE and the name values, displays errors as flash messages, and redirects to <b>/login</b> after success.",
        "notes": "Role selection is not exposed on this page, preventing public self-registration as Manager, Finance, or Admin.",
    },
    {
        "title": "4. Employee dashboard",
        "template": "templates/employee/dashboard.html",
        "route": "GET /dashboard",
        "roles": "Authenticated users. The page is protected by login_required_ui.",
        "purpose": "Gives an employee a compact overview of personal claim activity and the quickest route to create or review claims.",
        "elements": [
            "Summary cards for total claims, draft claims, submitted claims, and reimbursed amount.",
            "A Recent Expense Claims table showing claim number, linked travel request, total, status, and View Details action.",
            "Quick links to the complete claim list and the claim creation form.",
        ],
        "actions": "The controller obtains dashboard metrics with <b>get_employee_dashboard(user_id)</b>, retrieves the current user's claims, limits the recent list to five entries, and renders the page.",
        "notes": "Status badges visually distinguish approval, finance verification, reimbursement, rejection, and draft/submitted states.",
    },
    {
        "title": "5. Employee profile and password",
        "template": "templates/employee/profile.html",
        "route": "GET /profile; POST /profile/update; POST /profile/change-password",
        "roles": "Authenticated browser session for profile edits and password changes.",
        "purpose": "Lets the user maintain personal details and payment information used by the reimbursement process, then separately change their password.",
        "elements": [
            "Employee code display badge.",
            "Editable name, phone number, and department fields.",
            "Bank account number and IFSC code fields for reimbursement transfers.",
            "Current password, new password, and confirmation fields in a separate password form.",
        ],
        "actions": "Profile changes call <b>update_my_profile</b>; password changes validate matching confirmation before calling <b>change_password</b>. Both actions redirect back to the page with a flash result.",
        "notes": "When no browser session is present, GET /profile delegates to the JWT-protected REST API profile handler rather than rendering the template.",
    },
    {
        "title": "6. Travel request list",
        "template": "templates/travel/travel_list.html",
        "route": "GET /travel-requests",
        "roles": "Authenticated users. The list is scoped to the signed-in employee.",
        "purpose": "Shows each business trip initiated by the current employee and its approval outcome before related expenses are claimed.",
        "elements": [
            "New Travel Request button.",
            "Table columns for request number, route, travel dates, business purpose, and current status.",
            "Empty-state message when no travel requests exist.",
        ],
        "actions": "The controller retrieves the current employee's requests via <b>get_user_travel_requests(user_id)</b> and renders them in a status-aware table.",
        "notes": "Approved, rejected, and pending review requests are surfaced with distinct status badges.",
    },
    {
        "title": "7. New travel request",
        "template": "templates/travel/travel_form.html",
        "route": "GET /travel-requests/new and POST /travel-requests/new",
        "roles": "Authenticated users.",
        "purpose": "Collects a business itinerary for manager pre-approval before travel costs are incurred.",
        "elements": [
            "Travel request number.",
            "Origin and destination cities.",
            "Departure and return dates.",
            "Business purpose / meeting details text area.",
            "Cancel and Submit Travel Request actions.",
        ],
        "actions": "On submission, the controller calls <b>create_travel_request</b> using the session user ID. Successful requests redirect to the travel list; service validation errors keep the user on the form with a flash message.",
        "notes": "The page uses native date controls. The service remains responsible for business checks such as unique request number and valid date range.",
    },
    {
        "title": "8. Expense claim list",
        "template": "templates/claims/claim_list.html",
        "route": "GET /claims",
        "roles": "Authenticated users. Claims are retrieved for the signed-in employee.",
        "purpose": "Acts as the employee's claim worklist, making it easy to find drafts, track lifecycle status, and open a claim for management.",
        "elements": [
            "Create New Claim action.",
            "Search field for claim number.",
            "Status filters: All, Drafts, Submitted, Approved, and Reimbursed.",
            "Table with linked travel request, total amount, state, status guidance, and Manage action.",
            "Five-record pagination with Previous and Next controls when required.",
        ],
        "actions": "The controller applies optional status/search filtering in memory, calculates pagination using five records per page, and supplies the filtered list to the template.",
        "notes": "Rejected claims display an explicit correction notice. The search placeholder mentions travel, but the implemented filter currently checks the claim number only.",
    },
    {
        "title": "9. Initialize expense claim",
        "template": "templates/claims/claim_create.html",
        "route": "GET /claims/new and POST /claims/new",
        "roles": "Authenticated users.",
        "purpose": "Creates the DRAFT container that will hold an employee's itemized expenses and receipts.",
        "elements": [
            "Expense claim number field.",
            "Select list of the employee's travel requests, showing route and status.",
            "Instructional notice describing the subsequent item and receipt process.",
            "Cancel and Create Claim Draft actions.",
        ],
        "actions": "The page loads travel requests with <b>get_user_travel_requests</b>. Submission calls <b>create_expense_claim</b> with total_amount=0.0 and then redirects directly to the new claim's detail page.",
        "notes": "The UI presents all of the employee's travel requests. The underlying service is responsible for validating the referenced travel request.",
    },
    {
        "title": "10. Claim details, items, receipts, and audit history",
        "template": "templates/claims/claim_details.html",
        "route": "GET /claims/<claim_id> plus item, receipt, and submission POST actions",
        "roles": "Authenticated users. Draft and rejected claims expose editing controls; review states display the record as read-only.",
        "purpose": "This is the central work page for a single claim. It combines the claim summary, itemized expense entry, receipt management, submission, rejection feedback, and workflow timeline.",
        "elements": [
            "Claim number, travel association, total, and current-state badge.",
            "Rejection notice with manager comments when the claim is rejected.",
            "Itemized expenses table with category, date, description, amount, and attached receipt links.",
            "Add Expense Line Item form: category, amount, date, and business justification.",
            "Receipt controls: Generate PDF Receipt or upload PDF/PNG/JPG/JPEG.",
            "Delete item control and Submit for Manager Approval action for DRAFT/REJECTED claims.",
            "Chronological Audit Trail & Approval History panel.",
        ],
        "actions": "The page calls <b>get_expense_claim_by_id</b>, item/category lookups, and <b>get_claim_history</b>. It posts to create/delete items, upload/generate receipts, and submit the claim. Receipt links open the protected receipt-view endpoint in a new tab.",
        "notes": "The form controls are conditionally hidden once a claim enters review. Claim totals are updated by the expense-item service after additions, edits, or deletion.",
    },
    {
        "title": "11. Manager review and approvals",
        "template": "templates/manager/approvals.html",
        "route": "GET /approvals; POST approval/rejection actions",
        "roles": "Navigation is shown for MANAGER and ADMIN sessions. The page uses the session user and role to load the applicable review queues.",
        "purpose": "Gives managers a focused operational queue for decisions on subordinate travel requests and submitted expense claims.",
        "elements": [
            "Pending Travel Requests table with employee, itinerary, dates, purpose, Approve, and Reject actions.",
            "Pending Expense Claims table with linked claim number, employee, route, total, Approve, and Reject actions.",
            "Required rejection-reason input beside each claim rejection action.",
            "Empty-state messages when there is nothing to review.",
        ],
        "actions": "Travel decisions call <b>approve_travel</b> or <b>reject_travel</b>. Claim decisions call <b>approve_expense_claim_by_manager</b> or <b>reject_expense_claim_by_manager</b>. A successful claim approval advances the record to Finance.",
        "notes": "Admins receive the broader queues supplied by the services; managers receive the queues determined from their direct-report hierarchy.",
    },
    {
        "title": "12. Finance operations dashboard",
        "template": "templates/finance/finance_dashboard.html",
        "route": "GET /finance; POST finance verification and reimbursement actions",
        "roles": "Navigation is shown for FINANCE and ADMIN sessions.",
        "purpose": "Supports the two finance steps after manager review: verify approved claims, then disburse finance-verified claims.",
        "elements": [
            "Verification Queue for manager-approved claims.",
            "Inspect Line Items link to open the claim detail/audit view.",
            "Verify Claim action.",
            "Reimbursement Payouts queue for finance-verified claims.",
            "Employee bank details, disbursal amount, payment-reference field, and Disburse action.",
        ],
        "actions": "The page loads approved claims with <b>get_finance_verification_queue</b> and finance-verified claims by status. Verify posts to <b>/claims/<claim_id>/finance-verify</b>; payout posts to <b>/claims/<claim_id>/process-reimbursement</b> with a bank reference.",
        "notes": "The workflow transition is APPROVED -> FINANCE VERIFIED -> REIMBURSED. The created reimbursement record is marked PAID and includes the finance user and processing date.",
    },
    {
        "title": "13. Financial reports and analytics",
        "template": "templates/finance/reports.html",
        "route": "GET /reports",
        "roles": "Navigation is shown for FINANCE and ADMIN sessions.",
        "purpose": "Presents a concise operational summary of verification, reimbursement, and category-level expense activity.",
        "elements": [
            "Metric cards for claims awaiting verification, verified claims, reimbursements paid, and total disbursed.",
            "Expense Distribution by Category table.",
            "Category name, item count, total disbursed, and policy-status display.",
        ],
        "actions": "The controller calls <b>get_reports_summary()</b>, extracts finance_overview and expenses_by_category, and passes both datasets to the template. This page is read-only.",
        "notes": "Empty states ensure the report remains understandable when no expense records have yet been created.",
    },
]


def page_section(page, styles):
    story = [p(page["title"], styles["h1"]), Spacer(1, 7)]
    metadata = table([
        ["Template", "Route / request pattern", "Audience"],
        [page["template"], page["route"], page["roles"]],
    ], [1.55 * inch, 2.95 * inch, 2.65 * inch], styles)
    story.extend([metadata, Spacer(1, 12)])
    story.extend([p("Purpose", styles["h2"]), p(page["purpose"], styles["body"]), p("What the user can see and do", styles["h2"])])
    story.extend(bullet_list(page["elements"], styles))
    story.extend([p("Controller and workflow behavior", styles["h2"]), p(page["actions"], styles["body"]), callout("Implementation note", page["notes"], styles), Spacer(1, 12)])
    return story


def build_pdf():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    styles = build_styles()
    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=letter, leftMargin=40, rightMargin=40, topMargin=58, bottomMargin=52,
        title="ExpenseFlow Frontend Pages & Functionality", author="ExpenseFlow Project Team",
    )
    story = []

    # Cover
    story.extend([Spacer(1, 1.45 * inch), p("ExpenseFlow", styles["cover_title"]), p("Frontend Pages & Functionality", styles["cover_title"]), Spacer(1, 0.15 * inch), p("A page-by-page reference for the server-rendered Flask web portal", styles["cover_subtitle"]), Spacer(1, 0.55 * inch)])
    cover_rows = [
        ["Frontend approach", "Jinja2 server-rendered templates with a shared CSS design system"],
        ["Application scope", "Corporate travel requests, expenses, approvals, finance verification, and reimbursement"],
        ["Document scope", "11 user-facing page templates plus the shared application shell"],
        ["Reference files", "controllers/ui_controller.py, templates/, and static/css/style.css"],
    ]
    story.append(table(cover_rows, [1.55 * inch, 5.6 * inch], styles, header=False))
    story.extend([Spacer(1, 0.5 * inch), callout("How to use this document", "Each section identifies the template and browser route, explains the page's job in the user journey, lists the controls visible to the user, and summarizes the controller/service behavior triggered by those controls.", styles), Spacer(1, 1.0 * inch), p("Prepared for the ExpenseFlow Project", styles["footer"]), p("August 2026", styles["footer"]), PageBreak()])

    # Overview and lifecycle
    story.extend([p("Frontend overview", styles["h1"]), p("ExpenseFlow uses Flask sessions for the browser experience and Jinja2 template inheritance for a consistent, server-rendered interface. The UI controller receives form requests, delegates business work to the existing service layer, then redirects back to a page with a flash message. The REST API controllers continue to serve JSON clients separately.", styles["body"]), p("Page inventory", styles["h2"])])
    inventory = [["Area", "Pages", "Primary user task"],
        ["Shared", "Application shell", "Navigate, see account context, receive messages"],
        ["Access", "Sign in; registration", "Authenticate or create an employee account"],
        ["Employee", "Dashboard; profile", "Track activity and maintain personal/payment data"],
        ["Travel", "Travel list; new travel request", "Request and track business travel"],
        ["Claims", "Claim list; initialize claim; claim details", "Create, itemize, document, and submit expenses"],
        ["Manager", "Manager review and approvals", "Approve or reject travel and claims"],
        ["Finance", "Finance operations; reports", "Verify, reimburse, and review operational totals"],
    ]
    story.append(table(inventory, [1.05 * inch, 2.35 * inch, 3.75 * inch], styles))
    story.extend([p("End-to-end user journey", styles["h2"]), table([
        ["Step", "Frontend page", "Outcome"],
        ["1", "Register / Sign in", "Session established and user redirected to Dashboard"],
        ["2", "Travel Requests", "Employee submits an itinerary; it enters PENDING review"],
        ["3", "Initialize Expense Claim", "A DRAFT claim is linked to a travel request"],
        ["4", "Claim Details", "Employee adds policy-checked items and receipt evidence"],
        ["5", "Manager Approvals", "Submitted claims are approved or rejected with a reason"],
        ["6", "Finance Operations", "Approved claim is verified, then paid with a reference"],
        ["7", "Reports", "Finance/Admin reviews category and reimbursement summaries"],
    ], [0.55 * inch, 2.2 * inch, 4.4 * inch], styles), Spacer(1, 13), callout("Role-aware navigation", "The shared navigation presents Manager Approvals to MANAGER/ADMIN sessions and Finance Queue plus Reports to FINANCE/ADMIN sessions. Page routes also require a signed-in browser session through login_required_ui.", styles), PageBreak()])

    for index, page in enumerate(PAGES):
        story.extend(page_section(page, styles))
        if index < len(PAGES) - 1:
            story.append(PageBreak())

    story.extend([PageBreak(), p("Frontend-to-backend interaction map", styles["h1"]), p("The web UI does not reimplement business rules. UI routes collect browser form data, call the service layer, and return the user to a page. Service functions retain responsibility for ownership checks, workflow state, monetary-policy validation, persistence, and approval-history changes.", styles["body"]), table([
        ["UI area", "Representative UI controller calls", "Business result"],
        ["Authentication", "login_user; register_user; change_password", "Browser session, employee registration, secure password change"],
        ["Travel", "create_travel_request; get_user_travel_requests", "Travel requests and self-service tracking"],
        ["Claims", "create_expense_claim; submit_expense_claim", "Draft creation and submission lifecycle"],
        ["Items & receipts", "create_expense_item; upload_and_save_receipt; generate_pdf_receipt", "Line-item evidence and recalculated totals"],
        ["Manager review", "approve/reject travel; approve/reject claim", "Approval decisions and audit history"],
        ["Finance", "verify_expense_claim_by_finance; process_claim_reimbursement", "Finance verification and PAID reimbursement"],
        ["Analytics", "get_employee_dashboard; get_reports_summary", "Employee and finance visibility"],
    ], [1.35 * inch, 3.45 * inch, 2.35 * inch], styles), Spacer(1, 16), p("Status lifecycle visible in the UI", styles["h2"]), table([
        ["Object", "Lifecycle shown across the pages"],
        ["Travel request", "PENDING -> APPROVED or REJECTED"],
        ["Expense claim", "DRAFT -> SUBMITTED -> APPROVED -> FINANCE VERIFIED -> REIMBURSED; a SUBMITTED claim can also become REJECTED"],
        ["Reimbursement", "A finance-verified claim becomes REIMBURSED after a PAID reimbursement record is created with a payment reference"],
    ], [1.35 * inch, 5.8 * inch], styles), Spacer(1, 18), callout("Scope note", "This PDF documents the current server-rendered frontend and its implemented workflow. It is complementary to the backend architecture documentation; it does not replace the REST API, DAO, service, model, or test documentation.", styles)])

    doc.build(story, canvasmaker=BrandedCanvas)


if __name__ == "__main__":
    build_pdf()
    print(OUTPUT)
