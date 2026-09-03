import os
from datetime import datetime, timezone
from werkzeug.utils import secure_filename
from dao.expense_item_dao import get_expense_item_by_id
from dao.expense_claim_dao import get_claim_by_id
from dao.employee_dao import get_employee_by_user_id, get_employee_by_id
from dao.user_dao import get_user_by_id
from dao.expense_receipt_dao import (
    get_receipt_by_id,
    get_receipts_by_item_id,
    create_expense_receipt as create_expense_receipt_dao
)
from constants.status import ClaimStatus


# ReportLab imports for automated PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def upload_and_save_receipt(user_id, expense_item_id, file, upload_folder="uploads/receipts"):
    if not file or not file.filename:
        return None, "Receipt file is required", 400

    filename = secure_filename(file.filename)
    if not allowed_file(filename):
        return None, f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}", 400

    employee = get_employee_by_user_id(user_id)
    if not employee:
        return None, "Employee profile not found", 404

    expense_item = get_expense_item_by_id(expense_item_id)
    if not expense_item:
        return None, "Expense item not found", 404

    # Verify claim ownership
    claim = get_claim_by_id(expense_item.claim_id)
    if not claim:
        return None, "Associated expense claim not found", 404

    if claim.employee_id != employee.e_id:
        return None, "You are not authorized to upload receipts for this expense item", 403

    if claim.status not in [ClaimStatus.DRAFT, ClaimStatus.SUBMITTED, ClaimStatus.REJECTED]:
        return None, f"Cannot attach receipts to claims in {claim.status} status", 400

    # Check for duplicate receipt filename for this item
    existing_receipts = get_receipts_by_item_id(expense_item_id)
    if existing_receipts and any(getattr(r, 'file_name', None) == filename for r in existing_receipts):
        return None, f"Receipt with filename '{filename}' already uploaded for this item", 400

    # Ensure upload directory exists
    os.makedirs(upload_folder, exist_ok=True)


    # Save to disk
    file_path = os.path.join(upload_folder, f"{expense_item_id}_{filename}")
    file.save(file_path)

    file_size = os.path.getsize(file_path)
    if file_size > MAX_FILE_SIZE_BYTES:
        if os.path.exists(file_path):
            os.remove(file_path)
        return None, "File size exceeds the 5 MB limit", 400

    expense_receipt = create_expense_receipt_dao(
        expense_item_id=expense_item_id,
        file_name=filename,
        file_path=file_path,
        file_size=file_size
    )

    return expense_receipt, None, 201


def generate_pdf_receipt(user_id, expense_item_id, upload_folder="uploads/receipts"):
    """
    Uses ReportLab to generate a clean, official PDF invoice/receipt on demand.
    """
    employee = get_employee_by_user_id(user_id)
    if not employee:
        return None, "Employee profile not found", 404

    expense_item = get_expense_item_by_id(expense_item_id)
    if not expense_item:
        return None, "Expense item not found", 404

    claim = get_claim_by_id(expense_item.claim_id)
    if not claim:
        return None, "Associated claim not found", 404

    if claim.employee_id != employee.e_id:
        return None, "You are not authorized to generate receipts for this item", 403

    user = get_user_by_id(employee.user_id)
    category_name = expense_item.category.category_name if expense_item.category else "Business Expense"
    travel_route = f"{claim.travel_request.source} -> {claim.travel_request.destination}" if claim.travel_request else "General Corporate Travel"

    # Ensure directory exists
    os.makedirs(upload_folder, exist_ok=True)

    timestamp = int(datetime.now(timezone.utc).timestamp())
    filename = f"Digital_Receipt_Item_{expense_item_id}_{timestamp}.pdf"
    file_path = os.path.join(upload_folder, filename)

    # Create ReportLab Document
    doc = SimpleDocTemplate(
        file_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#2563eb'),
        spaceAfter=4,
        fontName="Helvetica-Bold"
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=14
    )

    section_header = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#0f172a'),
        fontName="Helvetica-Bold",
        spaceBefore=10,
        spaceAfter=6
    )

    body_text = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1e293b')
    )

    elements = []

    # 1. Header & Title
    elements.append(Paragraph("ExpenseFlow Enterprise System", title_style))
    elements.append(Paragraph("OFFICIAL DIGITAL EXPENSE RECEIPT & TAX INVOICE", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563eb'), spaceAfter=14))

    # 2. Metadata Grid (2-Column Info Table)
    now_str = datetime.now(timezone.utc).strftime("%d %b %Y, %I:%M %p UTC")
    meta_left = f"""
    <b>Receipt ID:</b> REC-{expense_item_id}-{timestamp}<br/>
    <b>Issue Date:</b> {now_str}<br/>
    <b>Claim Reference:</b> #{claim.claim_number}<br/>
    <b>Travel Itinerary:</b> {travel_route}
    """

    meta_right = f"""
    <b>Employee Name:</b> {employee.first_name} {employee.last_name}<br/>
    <b>Employee Code:</b> {employee.emp_code}<br/>
    <b>Corporate Email:</b> {user.email if user else 'N/A'}<br/>
    <b>Role / Designation:</b> {user.role if user else 'EMPLOYEE'}
    """

    meta_table = Table(
        [[Paragraph(meta_left, body_text), Paragraph(meta_right, body_text)]],
        colWidths=[270, 270]
    )
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 16))

    # 3. Itemized Bill Table
    elements.append(Paragraph("Itemized Expense Details", section_header))

    item_data = [
        [
            Paragraph("<b>Category</b>", body_text),
            Paragraph("<b>Expense Date</b>", body_text),
            Paragraph("<b>Business Purpose / Description</b>", body_text),
            Paragraph("<b>Amount (INR)</b>", body_text)
        ],
        [
            Paragraph(f"<b>{category_name}</b>", body_text),
            Paragraph(str(expense_item.expense_date), body_text),
            Paragraph(str(expense_item.description or 'Official Expense'), body_text),
            Paragraph(f"<b>INR {expense_item.amount:,.2f}</b>", body_text)
        ],
        [
            Paragraph("", body_text),
            Paragraph("", body_text),
            Paragraph("<b>TOTAL REIMBURSEMENT VALUE:</b>", body_text),
            Paragraph(f"<b>INR {expense_item.amount:,.2f}</b>", body_text)
        ]
    ]

    item_table = Table(item_data, colWidths=[120, 85, 230, 105])
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eff6ff')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1d4ed8')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f1f5f9')),
    ]))
    elements.append(item_table)

    # Build Document
    doc.build(elements)

    file_size = os.path.getsize(file_path)

    # Save record in database
    expense_receipt = create_expense_receipt_dao(
        expense_item_id=expense_item_id,
        file_name=filename,
        file_path=file_path,
        file_size=file_size
    )

    return expense_receipt, None, 201


def get_receipt_for_download(user_id, role, receipt_id):
    receipt = get_receipt_by_id(receipt_id)
    if not receipt:
        return None, "Receipt not found", 404

    expense_item = get_expense_item_by_id(receipt.expense_item_id)
    if not expense_item:
        return None, "Associated expense item not found", 404

    claim = get_claim_by_id(expense_item.claim_id)
    if not claim:
        return None, "Associated expense claim not found", 404

    # Admin and Finance have global viewing access
    if role in ["ADMIN", "FINANCE"]:
        return receipt, None, 200

    # Check if user is the employee owner
    current_employee = get_employee_by_user_id(user_id)
    if not current_employee:
        return None, "Unauthorized document access", 403

    if claim.employee_id == current_employee.e_id:
        return receipt, None, 200

    # Check if user is the manager of the claim's owner
    claim_owner = get_employee_by_id(claim.employee_id)
    if claim_owner and claim_owner.manager_id == current_employee.e_id:
        return receipt, None, 200

    return None, "Unauthorized document access", 403