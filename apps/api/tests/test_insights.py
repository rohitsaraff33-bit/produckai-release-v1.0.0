"""Unit tests for InsightGenerationService helpers."""

from dataclasses import fields

import pytest

from apps.api.services.insights import GeneratedInsight, sanitize_title


def test_sanitize_title_removes_customer_name():
    title = "Acme Corp needs better API performance"
    result = sanitize_title(title, ["Acme Corp"])
    assert "Acme Corp" not in result
    assert "API performance" in result


def test_sanitize_title_case_insensitive():
    title = "GLOBEX requests dashboard improvements"
    result = sanitize_title(title, ["globex"])
    assert "GLOBEX" not in result
    assert "dashboard improvements" in result


def test_sanitize_title_multiple_customers():
    title = "Initech and Umbrella Corp report the same bug"
    result = sanitize_title(title, ["Initech", "Umbrella Corp"])
    assert "Initech" not in result
    assert "Umbrella Corp" not in result


def test_sanitize_title_no_match_unchanged():
    title = "Improve export performance"
    result = sanitize_title(title, ["Acme"])
    assert result.strip() == title.strip()


def test_sanitize_title_returns_string():
    result = sanitize_title("Some title", [])
    assert isinstance(result, str)


def test_generated_insight_has_required_fields():
    """GeneratedInsight dataclass exposes all expected fields."""
    expected = {
        "title", "description", "impact", "recommendation",
        "severity", "effort", "key_quote_indices",
        "supporting_feedback_ids", "affected_customers", "key_quotes",
    }
    actual = {f.name for f in fields(GeneratedInsight)}
    assert expected.issubset(actual)


def test_generated_insight_instantiation():
    insight = GeneratedInsight(
        title="Test insight",
        description="Desc",
        impact="High impact",
        recommendation="Fix it",
        severity="high",
        effort="medium",
        key_quote_indices=[0, 1],
        supporting_feedback_ids=["uuid-1"],
        affected_customers=[{"id": "c1", "name": "Acme", "segment": "ENT", "acv": 50000}],
        key_quotes=["Quote text"],
    )
    assert insight.title == "Test insight"
    assert insight.severity == "high"
