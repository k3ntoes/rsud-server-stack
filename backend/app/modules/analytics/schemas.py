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
