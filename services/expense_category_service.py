from config.database import db
from models.expense_category import ExpenseCategory

def create_category(category_name, description):
    existing_category = ExpenseCategory.query.filter_by(
        category_name=category_name
    ).first()

    if existing_category:
        return None, "Category already exists"

    new_category = ExpenseCategory(
        category_name=category_name,
        description=description
    )

    db.session.add(new_category)
    db.session.commit()

    return new_category, None

def get_all_categories():
    categories = ExpenseCategory.query.all()

    return categories

def get_category_by_id(category_id):
    category = ExpenseCategory.query.get(category_id)

    return category

def update_category(category_id, category_name, description, is_active):
    category = ExpenseCategory.query.get(category_id)

    if not category:
        return None, "Category not found"

    if category_name:
        category.category_name = category_name

    if description is not None:
        category.description = description

    if is_active is not None:
        category.is_active = is_active

    db.session.commit()

    return category, None

def deactivate_category(category_id):
    category = ExpenseCategory.query.get(category_id)

    if not category:
        return None, "Category not found"

    category.is_active = False

    db.session.commit()

    return category, None