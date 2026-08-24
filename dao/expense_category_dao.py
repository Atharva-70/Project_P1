from config.database import db
from models.expense_category import ExpenseCategory


def get_category_by_name(category_name):
    return ExpenseCategory.query.filter_by(category_name=category_name).first()


def get_all_categories():
    return ExpenseCategory.query.all()


def get_category_by_id(category_id):
    return ExpenseCategory.query.get(category_id)


def create_category(category_name, description):
    new_category = ExpenseCategory(
        category_name=category_name,
        description=description
    )
    db.session.add(new_category)
    db.session.commit()
    return new_category


def update_category(category, category_name=None, description=None, is_active=None):
    if category_name is not None:
        category.category_name = category_name
    if description is not None:
        category.description = description
    if is_active is not None:
        category.is_active = is_active

    db.session.commit()
    return category


def deactivate_category(category):
    category.is_active = False
    db.session.commit()
    return category
