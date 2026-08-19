"""Tests for identity validation logic."""

from preview.services.models import RawRow
from preview.services.validator import validate_identities


def _row(num, eid="E1", email="a@b.com", **kw):
    return RawRow(
        row_number=num,
        employee_id=eid,
        employee_name=kw.get("name", "Test"),
        email=email,
        manager_id=kw.get("manager_id", ""),
        manager_email=kw.get("manager_email", ""),
        department=kw.get("department", "Eng"),
    )


class TestRequiredFields:
    def test_missing_employee_id_is_rejected(self):
        rows = [_row(2, eid="", email="a@b.com")]
        accepted, errors = validate_identities(rows)
        assert len(accepted) == 0
        assert any("Missing employee_id" in e.message for e in errors)

    def test_missing_email_is_rejected(self):
        rows = [_row(2, eid="E1", email="")]
        accepted, errors = validate_identities(rows)
        assert len(accepted) == 0
        assert any("Missing email" in e.message for e in errors)

    def test_valid_row_is_accepted(self):
        rows = [_row(2)]
        accepted, errors = validate_identities(rows)
        assert len(accepted) == 1
        assert len(errors) == 0


class TestUniqueness:
    def test_all_rows_with_duplicate_id_are_invalid(self):
        rows = [
            _row(2, eid="E1", email="a@b.com"),
            _row(3, eid="E1", email="c@d.com"),
        ]
        accepted, errors = validate_identities(rows)
        assert len(accepted) == 0
        assert len(errors) == 2
        assert all("Duplicate employee_id" in e.message for e in errors)

    def test_all_rows_with_duplicate_email_are_invalid(self):
        rows = [
            _row(2, eid="E1", email="same@x.com"),
            _row(3, eid="E2", email="same@x.com"),
        ]
        accepted, errors = validate_identities(rows)
        assert len(accepted) == 0
        assert len(errors) == 2
        assert all("Duplicate email" in e.message for e in errors)

    def test_non_duplicates_pass(self):
        rows = [
            _row(2, eid="E1", email="a@x.com"),
            _row(3, eid="E2", email="b@x.com"),
        ]
        accepted, errors = validate_identities(rows)
        assert len(accepted) == 2
        assert len(errors) == 0
