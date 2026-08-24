from dao.expense_category_dao import (
    get_category_by_name,
    get_all_categories as get_all_categories_dao,
    get_category_by_id as get_category_by_id_dao,
    create_category as create_category_dao,
    update_category as update_category_dao,
    deactivate_category as deactivate_category_dao
)


def create_category(category_name, description):
    existing_category = get_category_by_name(category_name)
    if existing_category:
        return None, "Category already exists"

    new_category = create_category_dao(
        category_name=category_name,
        description=description
    )
    return new_category, None


def get_all_categories():
    return get_all_categories_dao()


get_all_expense_categories = get_all_categories


def get_category_by_id(category_id):
    category = get_category_by_id_dao(category_id)
    if not category:
        return None, "Category not found"
    return category, None


get_expense_category_by_id = get_category_by_id


def update_category(category_id, category_name=None, description=None, is_active=None):
    category = get_category_by_id_dao(category_id)
    if not category:
        return None, "Category not found"

    updated_category = update_category_dao(
        category=category,
        category_name=category_name,
        description=description,
        is_active=is_active
    )
    return updated_category, None


def deactivate_category(category_id):
    category = get_category_by_id_dao(category_id)
    if not category:
        return None, "Category not found"

    deactivated = deactivate_category_dao(category)
    return deactivated, None