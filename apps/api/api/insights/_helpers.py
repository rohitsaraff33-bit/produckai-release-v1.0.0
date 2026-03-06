"""Shared helpers used across insight route modules."""

from types import SimpleNamespace
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from apps.api.api.insights.schemas import CustomerInfo
from apps.api.models import Customer, Feedback, InsightFeedback


def format_acv(amount: float) -> str:
    """Format a dollar amount as a compact currency string."""
    if amount >= 1_000_000:
        return f"${amount / 1_000_000:.2f}M"
    elif amount >= 1_000:
        return f"${amount / 1_000:.0f}k"
    return f"${amount:.0f}"


def resolve_customers(
    insight, db: Session
) -> Tuple[List[CustomerInfo], float]:
    """Return (customers, total_acv) from the insight's immutable snapshot or a live DB query.

    Prefers the immutable ``affected_customers`` JSON field stored at insight
    generation time so that customer counts are stable even if the live DB
    changes.  Falls back to a dynamic join for legacy insights that predate the
    immutable field.
    """
    if insight.affected_customers:
        customers_list = [
            CustomerInfo(
                id=c["id"],
                name=c["name"],
                segment=c["segment"],
                acv=c["acv"],
            )
            for c in insight.affected_customers
        ]
        total_acv = sum(c["acv"] for c in insight.affected_customers)
        return customers_list, total_acv

    # Fallback: dynamic query for legacy insights
    customer_ids_subq = (
        db.query(Customer.id.distinct())
        .join(Feedback, Feedback.customer_id == Customer.id)
        .join(InsightFeedback, InsightFeedback.feedback_id == Feedback.id)
        .filter(InsightFeedback.insight_id == insight.id)
        .subquery()
    )
    customers_data = (
        db.query(Customer).filter(Customer.id.in_(customer_ids_subq)).all()
    )
    customers_list = [
        CustomerInfo(
            id=str(c.id),
            name=c.name,
            segment=c.segment.value,
            acv=c.acv or 0.0,
        )
        for c in customers_data
    ]
    total_acv = sum(c.acv or 0.0 for c in customers_data)
    return customers_list, total_acv


def resolve_customers_raw(insight, db: Session):
    """Like resolve_customers but returns raw objects (SimpleNamespace or ORM models).

    Used by prd.py and ai_prompt.py which need attribute access (c.name, c.acv, etc.)
    rather than CustomerInfo Pydantic models.
    """
    if insight.affected_customers:
        return [SimpleNamespace(**c) for c in insight.affected_customers]

    customer_ids_subq = (
        db.query(Customer.id.distinct())
        .join(Feedback, Feedback.customer_id == Customer.id)
        .join(InsightFeedback, InsightFeedback.feedback_id == Feedback.id)
        .filter(InsightFeedback.insight_id == insight.id)
        .subquery()
    )
    return db.query(Customer).filter(Customer.id.in_(customer_ids_subq)).all()


def format_metrics(insight) -> Optional[dict]:
    """Return theme metrics as a plain dict, or None if unavailable."""
    if not (insight.theme and insight.theme.metrics):
        return None
    m = insight.theme.metrics
    return {
        "freq_30d": m.freq_30d,
        "freq_90d": m.freq_90d,
        "acv_sum": m.acv_sum,
        "sentiment": m.sentiment,
        "trend": m.trend,
        "score": m.score,
    }
