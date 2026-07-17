from .auth_routes import auth_ns
from .complaint_routes import complaint_ns
from .category_routes import category_ns
from .admin_routes import admin_ns
from .staff_routes import staff_ns
from .notification_routes import notification_ns

__all__ = [
    "auth_ns",
    "complaint_ns",
    "category_ns",
    "admin_ns",
    "staff_ns",
    "notification_ns",
]
