"""PRD generation endpoint."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from apps.api.api.insights._helpers import format_acv, resolve_customers_raw
from apps.api.database import get_db
from apps.api.models import Customer, Feedback, InsightFeedback, Insight, Theme

router = APIRouter()


@router.get("/{insight_id}/generate-prd")
async def generate_prd(insight_id: UUID, db: Session = Depends(get_db)):
    """
    Generate a comprehensive PRD (Product Requirements Document) for an insight.

    Auto-generates 13 sections from existing insight + feedback data:
    Problem & Goal, Who, Voice of Customer, Hypothesis, Use cases, Solution,
    Scope, Acceptance criteria, Success metrics, Experiment plan, GTM,
    Dependencies & risks, Open questions.
    """
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
        .all()
    )

    metrics = insight.theme.metrics if insight.theme and insight.theme.metrics else None
    total_customers = len(customers_data)
    total_acv = sum(c.acv or 0.0 for c in customers_data)
    freq_30d = metrics.freq_30d if metrics else 0
    total_acv_formatted = format_acv(total_acv)

    segment_groups = {"ENT": [], "MM": [], "SMB": []}
    for c in customers_data:
        seg = c.segment.value if hasattr(c.segment, "value") else c.segment
        segment_groups.get(seg, []).append(c)

    segment_breakdown = [
        f"{len(customers)} {segment} ({format_acv(sum(c.acv or 0.0 for c in customers))})"
        for segment, customers in segment_groups.items()
        if customers
    ]
    segment_mix = ", ".join(segment_breakdown) or "No segment data"

    top_accounts = sorted(customers_data, key=lambda x: x.acv or 0, reverse=True)[:3]
    top_accounts_list = [
        f"{i}. {c.name} ({(c.segment.value if hasattr(c.segment, 'value') else c.segment)}, {format_acv(c.acv or 0.0)})"
        for i, c in enumerate(top_accounts, 1)
    ]

    voc_quotes = []
    for f, _score in key_quotes_data[:3]:
        customer = db.query(Customer).filter(Customer.id == f.customer_id).first()
        customer_name = customer.name if customer else "Unknown"
        customer_segment = customer.segment.value if customer else "Unknown"
        customer_acv_fmt = format_acv(customer.acv) if customer and customer.acv else "$0"
        date = f.created_at.strftime("%b %d")
        voc_quotes.append(
            f'"{f.text}" — {customer_name}, {customer_segment} {customer_acv_fmt}, {date}'
        )

    severity_map = {
        "critical": "Resolving this will significantly reduce churn risk and unlock expansion opportunities",
        "high": "Addressing this will improve customer satisfaction and product-market fit",
        "medium": "Implementing this will enhance user experience and competitive positioning",
        "low": "This improvement will optimize workflows and increase product value",
    }
    hypothesis_text = severity_map.get(insight.severity or "medium", severity_map["medium"])

    use_cases = []
    if segment_groups["ENT"]:
        use_cases.append(
            f"Enterprise teams ({len(segment_groups['ENT'])} accounts) need this to maintain compliance and scale operations"
        )
    if segment_groups["MM"]:
        use_cases.append(
            f"Mid-market companies ({len(segment_groups['MM'])} accounts) need this to improve team productivity"
        )
    if segment_groups["SMB"]:
        use_cases.append(
            f"SMB users ({len(segment_groups['SMB'])} accounts) need this to reduce manual work"
        )
    if not use_cases:
        use_cases.append("Users across all segments need this capability to achieve their goals efficiently")

    success_metrics = (
        [
            f"NPS improvement from affected {total_customers} accounts",
            "Reduction in support tickets related to this issue",
            f"Retention rate improvement for {total_acv_formatted} ACV at risk",
        ]
        if insight.severity in ["critical", "high"]
        else [
            "Adoption rate among target customer segments",
            "Time saved per user workflow",
            "Feature satisfaction score (CSAT)",
        ]
    )

    gtm_approach = []
    if total_acv >= 500_000:
        gtm_approach.append("White-glove rollout to top 3 enterprise accounts with dedicated CSM support")
    if segment_groups["ENT"]:
        gtm_approach.append("Enterprise early access program with executive briefings")
    gtm_approach.extend([
        "Product marketing asset creation (blog post, demo video, changelog)",
        "Customer enablement via in-app tooltips and documentation",
    ])

    effort_to_timeline = {"low": "1-2 weeks", "medium": "3-4 weeks", "high": "6-8 weeks"}
    effort_to_beta = {"low": "1 week", "medium": "2 weeks", "high": "3 weeks"}
    timeline_estimate = effort_to_timeline.get(insight.effort or "medium", "3-4 weeks")
    beta_duration = effort_to_beta.get(insight.effort or "medium", "2 weeks")
    affected_segments = ", ".join(seg for seg in ["ENT", "MM", "SMB"] if segment_groups[seg])

    prd_markdown = f"""# {insight.title}

*Generated: {datetime.utcnow().strftime("%b %d, %Y")}* | *Priority: {insight.priority_score}/100* | *Severity: {(insight.severity or 'medium').upper()}*

**TL;DR**: {total_customers} customers ({total_acv_formatted} ACV) reported {freq_30d}× in 30d. {segment_mix}.

---

## Problem & Goal

{insight.description or "Customer feedback indicates a critical gap in our current product that creates friction in workflows and impacts satisfaction."}

**Goal**: {insight.impact or "Deliver capability that resolves customer pain points and improves product-market fit"}

---

## Who

- **Total impact**: {total_customers} customers, {total_acv_formatted} ACV
- **Segment mix**: {segment_mix}
- **Frequency**: {freq_30d} mentions in last 30 days
- **Top accounts**: {", ".join([c.name for c in top_accounts[:3]])}

**Priority accounts**:
{chr(10).join(top_accounts_list) if top_accounts_list else "No priority accounts identified"}

---

## Voice of Customer

**Theme**: {insight.theme.label if insight.theme else "User feedback"}

{chr(10).join([f"{i+1}. {q}" for i, q in enumerate(voc_quotes)]) if voc_quotes else "No key quotes available"}

[View full evidence →](http://localhost:3000/insights/{insight_id})

---

## Hypothesis

{hypothesis_text}. Expected impact: improved retention for {total_acv_formatted} ACV, reduced churn risk, and increased expansion opportunities.

---

## Use cases

{chr(10).join([f"{i+1}. {uc}" for i, uc in enumerate(use_cases)])}

---

## Solution

**Recommended approach**: {insight.recommendation or "Conduct discovery with top 3 affected customers to validate requirements, then design MVP solution with eng team"}

**Effort estimate**: {(insight.effort or 'medium').upper()} - Estimated {timeline_estimate}

---

## Scope

**MVP** (Must-have):
- Core functionality addressing primary pain point from customer feedback
- Integration with existing workflows
- Basic success metrics tracking

**Next** (Should-have):
- Advanced configuration options requested by enterprise accounts
- Enhanced reporting and analytics
- Mobile/API support if mentioned in feedback

**Not in scope**:
- Features not validated by customer evidence
- Capabilities requiring separate architectural decisions
- Items with <3 customer requests

---

## Acceptance criteria

- [ ] Resolves specific pain points mentioned in top 3 customer quotes
- [ ] Tested with at least 1 account from each affected segment ({affected_segments})
- [ ] Performance meets SLA requirements (sub-second response time)
- [ ] Documentation and help resources published
- [ ] Success metrics instrumentation deployed

---

## Success metrics

**Primary**:
{chr(10).join([f"- {m}" for m in success_metrics])}

**Secondary**:
- Feature adoption rate week-over-week
- Customer satisfaction feedback from beta users

---

## Experiment plan

1. **Beta phase** ({beta_duration}): Deploy to 3-5 friendly accounts, gather feedback
2. **Iterate**: Address critical issues found in beta
3. **GA rollout**: Phased release to all affected customers with monitoring

---

## GTM

{chr(10).join([f"- {g}" for g in gtm_approach])}

---

## Dependencies & risks

**Dependencies**:
- Engineering capacity: {(insight.effort or 'medium').upper()} effort estimate
- Design review if UI changes required
- QA test coverage for affected workflows

**Risks**:
- Scope creep if additional requirements emerge during beta
- Technical complexity may extend timeline
- Adoption risk if change management not handled properly

**Mitigation**: Maintain tight scope control, over-communicate with stakeholders, run thorough beta program

---

## Open questions

- What is the exact technical approach? (Requires eng discovery)
- Are there any compliance/security considerations?
- Do we need data migration for existing customer data?
- What is the competitive landscape for this capability?

---

*Auto-generated from ProductAI insights. Data sources: {len(key_quotes_data)} key quotes, {freq_30d} feedback items, {total_customers} customer accounts.*
"""

    return {"prd_markdown": prd_markdown, "insight_id": str(insight_id)}
