"""Pydantic response models for insight endpoints."""

from typing import List, Optional

from pydantic import BaseModel


class CustomerInfo(BaseModel):
    """Customer information for an insight."""

    id: str
    name: str
    segment: str
    acv: float

    class Config:
        from_attributes = True


class InsightListResponse(BaseModel):
    """Insight list item (top-level)."""

    id: str
    theme_id: Optional[str] = None
    title: str
    description: Optional[str]
    impact: Optional[str]
    recommendation: Optional[str]
    severity: str
    effort: str
    priority_score: int
    created_at: str
    updated_at: str
    metrics: Optional[dict]
    feedback_count: int
    customers: List[CustomerInfo]
    total_acv: float

    class Config:
        from_attributes = True


class InsightDetailResponse(BaseModel):
    """Detailed insight with supporting feedback."""

    id: str
    theme_id: Optional[str] = None
    title: str
    description: Optional[str]
    impact: Optional[str]
    recommendation: Optional[str]
    severity: str
    effort: str
    priority_score: int
    created_at: str
    updated_at: str
    metrics: Optional[dict]
    feedback_count: int
    customers: List[CustomerInfo]
    total_acv: float
    key_quotes: List[dict]
    supporting_feedback: List[dict]

    class Config:
        from_attributes = True


class FilterCountsResponse(BaseModel):
    """Quick filter counts."""

    enterprise_blockers: int
    high_priority: int
    trending: int

    class Config:
        from_attributes = True
