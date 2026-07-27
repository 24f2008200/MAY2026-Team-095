from app.models.category import Category


def get_all_categories():
    categories = (
        Category.query
        .filter_by(is_active=True)
        .order_by(Category.name.asc())
        .all()
    )

    return {
        "success": True,
        "categories": [category.to_dict() for category in categories],
    }, 200
