"""
Identity validation for HRIS rows.

Enforces:
- employee_id and email are required.
- Both must be unique after normalization.
- ALL rows sharing a duplicated value are invalid.
"""

from __future__ import annotations

from collections import Counter

from .models import AcceptedEmployee, RawRow, RowError


def validate_identities(
    rows: list[RawRow],
) -> tuple[list[AcceptedEmployee], list[RowError]]:
    """Return (accepted_employees, errors) after identity checks."""

    errors: list[RowError] = []

    # --- Pass 1: required-field check ---
    has_required: list[RawRow] = []
    for row in rows:
        if not row.employee_id:
            errors.append(RowError(row.row_number, row.employee_id, "Missing employee_id."))
        if not row.email:
            errors.append(RowError(row.row_number, row.employee_id, "Missing email."))
        if row.employee_id and row.email:
            has_required.append(row)

    # --- Pass 2: uniqueness check ---
    id_counts = Counter(r.employee_id for r in has_required)
    email_counts = Counter(r.email for r in has_required)

    duplicate_ids = {eid for eid, count in id_counts.items() if count > 1}
    duplicate_emails = {em for em, count in email_counts.items() if count > 1}

    accepted: list[AcceptedEmployee] = []
    for row in has_required:
        is_dup = False
        if row.employee_id in duplicate_ids:
            errors.append(RowError(
                row.row_number, row.employee_id,
                f"Duplicate employee_id '{row.employee_id}'.",
            ))
            is_dup = True
        if row.email in duplicate_emails:
            errors.append(RowError(
                row.row_number, row.employee_id,
                f"Duplicate email '{row.email}'.",
            ))
            is_dup = True

        if not is_dup:
            accepted.append(AcceptedEmployee(
                row_number=row.row_number,
                employee_id=row.employee_id,
                employee_name=row.employee_name,
                email=row.email,
                manager_id=row.manager_id,
                manager_email=row.manager_email,
                department=row.department,
            ))

    return accepted, errors
