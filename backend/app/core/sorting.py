from sqlalchemy import asc, desc
from sqlalchemy.sql import Select

from app.modules.auth.models import User
from app.modules.master.models import Room, InspectionItem
from app.modules.inspection.models import Inspection

# Allowlist per model — prevents SQL injection via arbitrary column names
_SORTABLE: dict = {
    User: {"username", "role", "is_active", "created_at"},
    Room: {"name", "is_active", "updated_at"},
    InspectionItem: {"name", "is_active", "updated_at"},
    Inspection: {"business_date", "status", "created_at", "room_id"},
}


def apply_sorting(
    query: Select,
    model: type,
    sort_by: str | None,
    sort_order: str = "asc",
) -> Select:
    """Apply ORDER BY to query if sort_by is a valid column for the model."""
    allowed = _SORTABLE.get(model)
    if not allowed or sort_by not in allowed:
        return query
    col = getattr(model, sort_by, None)
    if col is None:
        return query
    order_fn = desc if sort_order == "desc" else asc
    return query.order_by(order_fn(col))
