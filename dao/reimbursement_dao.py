from config.database import db
from models.reimbursement import Reimbursement
from constants.status import ReimbursementStatus


def get_reimbursement_by_id(reim_id):
    return Reimbursement.query.get(reim_id)


def get_reimbursement_by_claim_id(claim_id):
    return Reimbursement.query.filter_by(claim_id=claim_id).first()


def get_all_reimbursements():
    return Reimbursement.query.all()


def get_reimbursements_by_status(status):
    return Reimbursement.query.filter_by(status=status).all()


def create_reimbursement(
    claim_id,
    amount,
    status=ReimbursementStatus.PENDING,
    payment_reference=None,
    processed_by=None,
    processed_date=None
):
    reimbursement = Reimbursement(
        claim_id=claim_id,
        amount=amount,
        status=status,
        payment_reference=payment_reference,
        processed_by=processed_by,
        processed_date=processed_date
    )
    db.session.add(reimbursement)
    db.session.commit()
    return reimbursement


def update_reimbursement_payment(
    reimbursement,
    payment_reference,
    processed_by,
    processed_date,
    status=ReimbursementStatus.PAID
):
    reimbursement.payment_reference = payment_reference
    reimbursement.processed_by = processed_by
    reimbursement.processed_date = processed_date
    reimbursement.status = status
    db.session.commit()
    return reimbursement
