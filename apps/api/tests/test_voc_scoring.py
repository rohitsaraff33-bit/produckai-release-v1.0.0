"""Unit tests for VOCScoringService._upsert_voc_score."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from apps.api.models.artifacts import JiraTicket, VOCScore
from apps.api.services.voc_scoring import VOCScoringService


@pytest.fixture
def service():
    with patch("apps.api.services.voc_scoring.get_embedding_service"):
        svc = VOCScoringService.__new__(VOCScoringService)
        svc.embedding_service = MagicMock()
        return svc


def _mock_ticket():
    ticket = MagicMock(spec=JiraTicket)
    ticket.id = uuid4()
    return ticket


def _score_fields():
    return {
        "customer_count": 5,
        "total_acv": 150_000.0,
        "feedback_volume": 12,
        "ent_customer_count": 2,
        "mm_customer_count": 2,
        "smb_customer_count": 1,
        "customer_score": 0.7,
        "acv_score": 0.8,
        "segment_score": 0.9,
        "volume_score": 0.6,
        "voc_score": 75.0,
        "recommended_priority": "high",
    }


def test_upsert_creates_when_missing(service):
    """When no existing score is found, a new VOCScore is added to the session."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    ticket = _mock_ticket()

    result = service._upsert_voc_score(db, ticket, _score_fields())

    db.add.assert_called_once()
    added = db.add.call_args[0][0]
    assert isinstance(added, VOCScore)
    assert added.voc_score == 75.0
    db.flush.assert_called_once()


def test_upsert_updates_when_existing(service):
    """When an existing score is found, it is updated in-place without db.add."""
    db = MagicMock()
    existing = MagicMock(spec=VOCScore)
    db.query.return_value.filter.return_value.first.return_value = existing
    ticket = _mock_ticket()

    result = service._upsert_voc_score(db, ticket, _score_fields())

    db.add.assert_not_called()
    assert existing.voc_score == 75.0
    assert existing.recommended_priority == "high"
    db.flush.assert_called_once()


def test_zero_score_fields(service):
    """_create_zero_score produces a VOCScore with all numeric fields at zero."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    ticket = _mock_ticket()

    service._create_zero_score(db, ticket)

    added = db.add.call_args[0][0]
    assert added.voc_score == 0.0
    assert added.customer_count == 0
    assert added.total_acv == 0.0
    assert added.recommended_priority == "low"


def test_upsert_returns_score_object(service):
    """_upsert_voc_score always returns a VOCScore-compatible object."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    ticket = _mock_ticket()

    result = service._upsert_voc_score(db, ticket, _score_fields())

    assert result is not None
