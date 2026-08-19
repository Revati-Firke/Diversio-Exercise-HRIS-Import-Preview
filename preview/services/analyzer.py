"""
Orchestrator: ties parsing, validation, and hierarchy analysis into
a single entry point for the view layer.
"""

from __future__ import annotations

from .hierarchy import analyze_hierarchy
from .models import AnalysisResult
from .parser import ParseError, parse_csv
from .validator import validate_identities


def analyze_upload(file_bytes: bytes) -> AnalysisResult:
    """Run the full import-preview pipeline on raw file bytes.

    Raises ParseError for structurally invalid files.
    """
    rows = parse_csv(file_bytes)
    accepted, validation_errors = validate_identities(rows)
    hierarchy = analyze_hierarchy(accepted)

    return AnalysisResult(
        total_rows=len(rows),
        accepted_employees=accepted,
        validation_errors=validation_errors,
        hierarchy=hierarchy,
    )
