from pydantic import BaseModel


class RoomScoreOut(BaseModel):
    room_id: int
    year_month: str
    total_score: int
    max_score: int
    score_pct: float
    inspection_count: int

    model_config = {"from_attributes": True}


class IssueFrequencyOut(BaseModel):
    item_id: int
    item_name_snapshot: str
    year_month: str
    score_zero_count: int

    model_config = {"from_attributes": True}


class InspectorPerformanceOut(BaseModel):
    inspector_id: int
    username: str
    total_inspections: int

    model_config = {"from_attributes": True}


class DashboardSummaryOut(BaseModel):
    monthly_inspection_count: int
    avg_score_pct: float


class DashboardOut(BaseModel):
    pending_count: int
    total_rooms: int
    monthly_inspection_count: int
    avg_score_pct: float
    # Effective month the stats refer to — falls back to the latest month with
    # data when the requested month is empty; None when no stats exist at all.
    year_month: str | None = None
