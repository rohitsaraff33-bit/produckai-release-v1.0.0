"""AI prototype prompt generation endpoint."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from apps.api.api.insights._helpers import format_acv, resolve_customers_raw
from apps.api.database import get_db
from apps.api.models import Customer, Feedback, InsightFeedback, Insight, Theme

router = APIRouter()

_INTEGRATION_KEYWORDS = {
    "salesforce", "hubspot", "marketo", "slack", "teams", "microsoft teams",
    "google", "zoom", "jira", "confluence", "notion", "linear",
}


@router.get("/{insight_id}/generate-ai-prompt")
async def generate_ai_prototype_prompt(
    insight_id: UUID,
    prototype_type: str = Query(
        default="mvp",
        enum=["ui_component", "feature_flow", "mvp", "technical_poc"],
    ),
    db: Session = Depends(get_db),
):
    """Generate a structured AI prototype prompt from insight data."""
    insight = (
        db.query(Insight)
        .filter(Insight.id == insight_id)
        .options(joinedload(Insight.theme).joinedload(Theme.metrics))
        .first()
    )
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")

    customers_data = resolve_customers_raw(insight, db)

    key_quotes_data = (
        db.query(Feedback, InsightFeedback.relevance_score)
        .join(InsightFeedback, Feedback.id == InsightFeedback.feedback_id)
        .filter(InsightFeedback.insight_id == insight.id, InsightFeedback.is_key_quote == 1)
        .order_by(desc(InsightFeedback.relevance_score))
        .limit(3)
        .all()
    )

    total_customers = len(customers_data)
    total_acv = sum(c.acv or 0.0 for c in customers_data)
    total_acv_formatted = format_acv(total_acv)

    segment_groups: dict[str, list] = {"ENT": [], "MM": [], "SMB": []}
    for c in customers_data:
        seg = c.segment.value if hasattr(c.segment, "value") else c.segment
        segment_groups.get(seg, []).append(c)

    customer_evidence = []
    for f, _score in key_quotes_data:
        customer = db.query(Customer).filter(Customer.id == f.customer_id).first()
        if customer:
            customer_evidence.append(
                f'"{f.text}" — {customer.name}, {customer.segment.value} {format_acv(customer.acv or 0)}'
            )

    all_feedback_text = [f.text.lower() for f, _ in key_quotes_data]
    integrations = [
        kw.title()
        for kw in _INTEGRATION_KEYWORDS
        if any(kw in text for text in all_feedback_text)
    ]

    recommended_tool, recommendation_reason = _recommend_tool(
        prototype_type, total_acv, segment_groups, insight
    )

    prototype_descriptions = {
        "ui_component": "a UI component prototype (layout, navigation, form elements)",
        "feature_flow": "a feature flow prototype (multi-step workflow)",
        "mvp": "a functional MVP (end-to-end feature with backend)",
        "technical_poc": "a technical proof-of-concept (validate feasibility)",
    }
    effort_timeline = {"low": "1-2 weeks", "medium": "3-4 weeks", "high": "6-8 weeks"}
    timeline_str = effort_timeline.get(insight.effort or "medium", "3-4 weeks")

    target_users_str = ", ".join(
        f"{len(segment_groups[seg])} {seg}" for seg in ["ENT", "MM", "SMB"] if segment_groups[seg]
    )
    target_segments_str = ", ".join(seg for seg in ["ENT", "MM", "SMB"] if segment_groups[seg])
    top_customer_names = ", ".join(
        c.name
        for c in sorted(customers_data, key=lambda x: x.acv or 0, reverse=True)[:3]
    )

    prototype_prompt = f"""# Build: {insight.title}

## Context
Create {prototype_descriptions[prototype_type]} based on validated customer feedback from {total_customers} account{"s" if total_customers != 1 else ""} ({total_acv_formatted} ACV).

## User Problem
{insight.description or "Customer feedback indicates a critical gap that needs to be addressed."}

## Customer Evidence
{chr(10).join(customer_evidence) if customer_evidence else "Multiple customers have reported this issue"}

## Requirements
- Severity: {(insight.severity or "medium").upper()} priority
- Estimated effort: {(insight.effort or "medium").upper()} ({timeline_str})
- Target segments: {target_segments_str}
- Must be production-ready: {"Yes - Enterprise customers" if segment_groups["ENT"] else "Start simple, iterate"}

## Design Constraints
- Target users: {target_users_str}
- {f"Must integrate with: {', '.join(integrations)}" if integrations else "Consider integration points mentioned in feedback"}
- {"Focus on compliance and security (Enterprise users)" if segment_groups["ENT"] else "Focus on ease of use and quick setup"}

## Success Criteria
- Solves the core problem described in customer evidence
- {"Handles enterprise-scale requirements (SSO, permissions, audit logs)" if segment_groups["ENT"] else "Quick to set up and use"}
- Can be validated with {min(3, total_customers)} customer{"s" if min(3, total_customers) != 1 else ""}

## Recommended Approach
{insight.recommendation or "Start with user interviews to validate requirements, then design and build MVP iteratively"}

---

**Next Steps:**
1. Review the customer evidence and requirements above
2. Design 2-3 UI variations for the main workflow
3. Implement core functionality based on highest-priority requirements
4. Prepare for customer testing with {top_customer_names}
"""

    return {
        "prompt": prototype_prompt,
        "recommended_tool": recommended_tool,
        "recommendation_reason": recommendation_reason,
        "insight_id": str(insight_id),
        "metadata": {
            "total_customers": total_customers,
            "total_acv": total_acv_formatted,
            "severity": insight.severity or "medium",
            "effort": insight.effort or "medium",
            "has_enterprise_customers": len(segment_groups["ENT"]) > 0,
            "integrations": integrations,
        },
    }


def _recommend_tool(
    prototype_type: str, total_acv: float, segment_groups: dict, insight
) -> tuple[str, str]:
    if prototype_type == "ui_component":
        return "v0", "Best for UI components and design system elements"
    if prototype_type == "technical_poc":
        return "Bolt", "Best for quick technical proof-of-concept"
    if total_acv >= 500_000 or segment_groups["ENT"]:
        return "Lovable", "High-value feature for Enterprise accounts requires production-quality MVP"
    if insight.severity in ["critical", "high"]:
        return "Lovable", "High-severity feature requires full-stack MVP with backend"
    return "Bolt", "Best for quick functional demo and validation"
