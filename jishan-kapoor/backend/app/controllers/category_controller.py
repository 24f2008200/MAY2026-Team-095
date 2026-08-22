from typing import Any

from app.services.category_service import get_all_categories


def list_categories_handler() -> tuple[dict[str, Any], int]:
    return get_all_categories()
