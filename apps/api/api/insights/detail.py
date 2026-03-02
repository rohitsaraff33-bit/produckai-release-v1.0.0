"""Single-insight detail endpoint."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload

from apps.api.api.insights._helpers import format_metrics, resolve_customers
from apps.api.api.insights.schemas import InsightDetailResponse
from apps.api.database import get_db
from apps.api.models import Feedback, InsightFeedback, Insight, Theme

router = APIRouter()


@router.get("/{insight_id}", response_model=InsightDetailResponse)
async def get_insight(insight_id: UUID, db: Session = Depends(get_db)):
    """Get detailed insight information with supporting feedback and key quotes."""
    insight = (
        db.query(Insight)
        .filter(Insight.id == insight_id)
        .options(joinedload(Insight.theme).joinedload(Theme.metrics))
        .first()
    )

    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")

    # Key quotes (is_key_quote=1)
    key_quotes_data = (
        db.query(Feedback, InsightFeedback.relevance_score)
        .join(InsightFeedback, Feedback.id == InsightFeedback.feedback_id)
        .filter(InsightFeedback.insight_id == insight.id, InsightFeedback.is_key_quote == 1)
        .order_by(desc(InsightFeedback.relevance_score))
        .all()
    )
    key_quotes = [_serialize_feedback(f, score) for f, score in key_quotes_data]

    # Supporting feedback (is_key_quote=0, limited to 20)
    supporting_data = (
        db.query(Feedback, InsightFeedback.relevance_score)
        .join(InsightFeedback, Feedback.id == InsightFeedback.feedback_id)
        .filter(InsightFeedback.insight_id == insight.id, InsightFeedback.is_key_quote == 0)
        .order_by(desc(InsightFeedback.relevance_score))
        .limit(20)
        .all()
    )
    supporting_feedback = [_serialize_feedback(f, score) for f, score in supporting_data]

    feedback_count = (
        db.query(func.count(InsightFeedback.feedback_id))
        .filter(InsightFeedback.insight_id == insight.id)
        .scalar()
    )

    customers_list, total_acv = resolve_customers(insight, db)

    # Detail view exposes dup_penalty too
    metrics_dict = None
    if insight.theme and insight.theme.metrics:
        m = insight.theme.metrics
        metrics_dict = {
            "freq_30d": m.freq_30d,
            "freq_90d": m.freq_90d,
            "acv_sum": m.acv_sum,
            "sentiment": m.sentiment,
            "trend": m.trend,
            "dup_penalty": m.dup_penalty,
            "score": m.score,
        }

    return InsightDetailResponse(
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
        key_quotes=key_quotes,
        supporting_feedback=supporting_feedback,
    )


def _serialize_feedback(f: Feedback, score) -> dict:
    return {
        "id": str(f.id),
        "text": f.text,
        "source": f.source.value,
        "source_id": f.source_id,
        "account": f.account,
        "created_at": f.created_at.isoformat(),
        "confidence": score,
        "meta": f.meta,
        "doc_url": f.doc_url,
        "speaker": f.speaker,
        "started_at": f.started_at.isoformat() if f.started_at else None,
        "ended_at": f.ended_at.isoformat() if f.ended_at else None,
    }
