"""List and filter-count endpoints for insights."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from apps.api.api.insights._helpers import format_metrics, resolve_customers
from apps.api.api.insights.schemas import (
    FilterCountsResponse,
    InsightListResponse,
)
from apps.api.database import get_db
from apps.api.models import Customer, Feedback, InsightFeedback, Insight, Theme, ThemeMetrics

router = APIRouter()


@router.get("", response_model=List[InsightListResponse])
async def list_insights(
    sort_by: str = Query("priority", enum=["priority", "score", "trend", "created_at"]),
    filter: Optional[str] = Query(None, enum=["enterprise_blockers", "high_priority", "trending"]),
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    priority_min: Optional[int] = Query(None, ge=0, le=100, description="Minimum priority score"),
    priority_max: Optional[int] = Query(None, ge=0, le=100, description="Maximum priority score"),
    severity: Optional[List[str]] = Query(None, description="Filter by severity (critical, high, medium, low)"),
    segments: Optional[List[str]] = Query(None, description="Filter by customer segments (ENT, MM, SMB)"),
    effort: Optional[List[str]] = Query(None, description="Filter by effort (low, medium, high)"),
    db: Session = Depends(get_db),
):
    """
    List insights with optional sorting, filtering, and pagination.

    Quick Filter Criteria:
        - enterprise_blockers: severity='critical' OR (severity='high' AND acv_sum >= 50000)
        - high_priority: priority_score >= 70 OR severity IN ('high', 'critical')
        - trending: trend > 0 AND freq_30d >= 3
    """
    query = db.query(Insight).join(Insight.theme).join(Theme.metrics, isouter=True)

    # Quick filters
    if filter == "enterprise_blockers":
        query = query.filter(
            (Insight.severity == "critical")
            | ((Insight.severity == "high") & (ThemeMetrics.acv_sum >= 50000))
        )
    elif filter == "high_priority":
        query = query.filter(
            (Insight.priority_score >= 70) | (Insight.severity.in_(["high", "critical"]))
        )
    elif filter == "trending":
        query = query.filter((ThemeMetrics.trend > 0) & (ThemeMetrics.freq_30d >= 3))

    # Advanced filters
    if priority_min is not None:
        query = query.filter(Insight.priority_score >= priority_min)
    if priority_max is not None:
        query = query.filter(Insight.priority_score <= priority_max)
    if severity:
        query = query.filter(Insight.severity.in_(severity))
    if effort:
        query = query.filter(Insight.effort.in_(effort))
    if segments:
        segment_insight_ids = (
            db.query(InsightFeedback.insight_id.distinct())
            .join(Feedback, Feedback.id == InsightFeedback.feedback_id)
            .join(Customer, Customer.id == Feedback.customer_id)
            .filter(Customer.segment.in_(segments))
            .subquery()
        )
        query = query.filter(Insight.id.in_(segment_insight_ids))

    # Sorting
    if sort_by == "priority":
        query = query.order_by(desc(Insight.priority_score))
    elif sort_by == "score":
        query = query.order_by(desc(ThemeMetrics.score))
    elif sort_by == "trend":
        query = query.order_by(desc(ThemeMetrics.trend))
    else:
        query = query.order_by(desc(Insight.created_at))

    insights = query.offset(offset).limit(limit).all()

    results = []
    for insight in insights:
        feedback_count = (
            db.query(func.count(InsightFeedback.feedback_id))
            .filter(InsightFeedback.insight_id == insight.id)
            .scalar()
        )
        customers_list, total_acv = resolve_customers(insight, db)
        metrics_dict = format_metrics(insight)

        results.append(
            InsightListResponse(
                id=str(insight.id),
                theme_id=str(insight.theme_id) if insight.theme_id else None,
                title=insight.title,
                description=insight.description,
                impact=insight.impact,
                recommendation=insight.recommendation,
                severity=insight.severity or "medium",
                effort=insight.effort or "medium",
                priority_score=insight.priority_score,
                created_at=insight.created_at.isoformat(),
                updated_at=insight.updated_at.isoformat(),
                metrics=metrics_dict,
                feedback_count=feedback_count,
                customers=customers_list,
                total_acv=total_acv,
            )
        )

    return results


@router.get("/filter-counts", response_model=FilterCountsResponse)
async def get_filter_counts(db: Session = Depends(get_db)):
    """Get counts for each quick filter category."""
    base_query = db.query(Insight).join(Insight.theme).join(Theme.metrics, isouter=True)

    enterprise_blockers_count = base_query.filter(
        or_(
            Insight.severity == "critical",
            and_(Insight.severity == "high", ThemeMetrics.acv_sum >= 50000),
        )
    ).count()

    high_priority_count = base_query.filter(
        or_(Insight.priority_score >= 70, Insight.severity.in_(["high", "critical"]))
    ).count()

    trending_count = base_query.filter(
        and_(ThemeMetrics.trend > 0, ThemeMetrics.freq_30d >= 3)
    ).count()

    return FilterCountsResponse(
        enterprise_blockers=enterprise_blockers_count,
        high_priority=high_priority_count,
        trending=trending_count,
    )
