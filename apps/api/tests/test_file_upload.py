"""Unit tests for FileUploadService CSV parsing helpers."""

import pytest

from apps.api.services.file_upload import COLUMN_ALIASES, _get_field


# ---------------------------------------------------------------------------
# _get_field
# ---------------------------------------------------------------------------


def test_get_field_primary_key():
    """The canonical (first) alias resolves correctly."""
    row = {"Feedback": "Great product!"}
    assert _get_field(row, "text") == "Great product!"


def test_get_field_secondary_alias():
    """A non-primary alias also resolves."""
    row = {"comment": "Needs improvement"}
    assert _get_field(row, "text") == "Needs improvement"


def test_get_field_customer_alias():
    row = {"company": "Acme Corp"}
    assert _get_field(row, "customer") == "Acme Corp"


def test_get_field_acv_alias():
    row = {"annual_contract_value": "120000"}
    assert _get_field(row, "acv") == "120000"


def test_get_field_missing_returns_none():
    """Returns None when no alias matches any key in the row."""
    row = {"unrelated_column": "value"}
    assert _get_field(row, "text") is None


def test_get_field_empty_string_treated_as_missing():
    """An empty string value is falsy and should not be returned."""
    row = {"Feedback": "", "text": "Actual value"}
    assert _get_field(row, "text") == "Actual value"


def test_get_field_unknown_key_returns_none():
    """An unknown key not in COLUMN_ALIASES returns None gracefully."""
    row = {"Feedback": "something"}
    assert _get_field(row, "nonexistent_key") is None


# ---------------------------------------------------------------------------
# COLUMN_ALIASES structure
# ---------------------------------------------------------------------------


def test_column_aliases_has_required_keys():
    required = {"text", "customer", "acv", "contact", "timestamp"}
    assert required.issubset(set(COLUMN_ALIASES.keys()))


def test_column_aliases_values_are_lists():
    for key, aliases in COLUMN_ALIASES.items():
        assert isinstance(aliases, list), f"Aliases for '{key}' should be a list"
        assert len(aliases) > 0, f"Aliases for '{key}' should not be empty"


# ---------------------------------------------------------------------------
# ACV / timestamp parsing (via _parse_csv indirectly via _get_field)
# ---------------------------------------------------------------------------


def test_get_field_acv_canonical():
    row = {"ACV": "50000"}
    assert _get_field(row, "acv") == "50000"


def test_get_field_timestamp_date_alias():
    row = {"date": "2024-01-15"}
    assert _get_field(row, "timestamp") == "2024-01-15"


def test_get_field_timestamp_created_at_alias():
    row = {"created_at": "2024-06-01T12:00:00Z"}
    assert _get_field(row, "timestamp") == "2024-06-01T12:00:00Z"
