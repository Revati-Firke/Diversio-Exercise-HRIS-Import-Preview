"""
CSV parsing and value normalization.

Reads an uploaded file into a list of RawRow dataclasses.
Handles UTF-8 BOM, quoted values, and header-order independence.
"""

from __future__ import annotations

import codecs
import csv
import io
from typing import TextIO

from .models import RawRow

REQUIRED_HEADERS = {
    "employee_id",
    "employee_name",
    "email",
    "manager_id",
    "manager_email",
    "department",
}


class ParseError(Exception):
    """Raised when the CSV cannot be parsed at all."""


def parse_csv(file_bytes: bytes) -> list[RawRow]:
    """Parse raw file bytes into normalized RawRow objects.

    Raises ParseError for structurally invalid files (empty, missing headers).
    """
    text = _decode(file_bytes)
    reader = csv.DictReader(io.StringIO(text))

    if reader.fieldnames is None:
        raise ParseError("The file is empty or contains no headers.")

    normalized_headers = {h.strip().lower() for h in reader.fieldnames}
    missing = REQUIRED_HEADERS - normalized_headers
    if missing:
        raise ParseError(f"Missing required headers: {', '.join(sorted(missing))}")

    # Re-create reader with cleaned header names so lookups work
    # regardless of whitespace / casing in the original file.
    header_map = {h.strip().lower(): h for h in reader.fieldnames}

    rows: list[RawRow] = []
    for line_number, raw in enumerate(reader, start=2):  # row 1 is the header
        rows.append(_normalize(line_number, raw, header_map))

    return rows


def _decode(file_bytes: bytes) -> str:
    """Decode bytes to str, stripping a UTF-8 BOM if present."""
    if file_bytes.startswith(codecs.BOM_UTF8):
        file_bytes = file_bytes[len(codecs.BOM_UTF8) :]
    return file_bytes.decode("utf-8")


def _normalize(
    row_number: int, raw: dict[str, str], header_map: dict[str, str]
) -> RawRow:
    """Build a RawRow with trimmed and case-normalized values."""

    def get(field: str) -> str:
        return (raw.get(header_map[field]) or "").strip()

    return RawRow(
        row_number=row_number,
        employee_id=get("employee_id"),
        employee_name=get("employee_name"),
        email=get("email").lower(),
        manager_id=get("manager_id"),
        manager_email=get("manager_email").lower(),
        department=get("department"),
    )
