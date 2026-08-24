from config.database import db
from models.expense_policy import ExpensePolicy


def get_policy_by_id(policy_id):
    return ExpensePolicy.query.get(policy_id)


def get_policy_by_category_id(category_id):
    return ExpensePolicy.query.filter_by(
        category_id=category_id,
        is_active=True
    ).first()


def get_all_policies():
    return ExpensePolicy.query.all()


def create_policy(category_id, max_amount, is_active=True):
    policy = ExpensePolicy(
        category_id=category_id,
        max_amount=max_amount,
        is_active=is_active
    )
    db.session.add(policy)
    db.session.commit()
    return policy


def update_policy(policy, max_amount=None, is_active=None):
    if max_amount is not None:
        policy.max_amount = max_amount
    if is_active is not None:
        policy.is_active = is_active
    db.session.commit()
    return policy


def delete_policy(policy):
    db.session.delete(policy)
    db.session.commit()
