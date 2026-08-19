"""
Shared data structures for the HRIS import preview pipeline.

All service modules communicate through these plain dataclasses,
keeping the business logic decoupled from Django.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RawRow:
    """A single row from the CSV after normalization, tagged with its source line."""

    row_number: int
    employee_id: str
    employee_name: str
    email: str
    manager_id: str
    manager_email: str
    department: str


@dataclass
class RowError:
    """A validation or hierarchy error tied to a specific source row."""

    row_number: int
    employee_id: str
    message: str


@dataclass
class AcceptedEmployee:
    """An employee that passed identity validation."""

    row_number: int
    employee_id: str
    employee_name: str
    email: str
    manager_id: str
    manager_email: str
    department: str


@dataclass
class ManagerReport:
    """A manager and how many direct reports they have."""

    employee_id: str
    employee_name: str
    direct_report_count: int


@dataclass
class HierarchyResult:
    roots: list[AcceptedEmployee] = field(default_factory=list)
    manager_reports: list[ManagerReport] = field(default_factory=list)
    cycle_members: list[AcceptedEmployee] = field(default_factory=list)
    errors: list[RowError] = field(default_factory=list)


@dataclass
class AnalysisResult:
    total_rows: int
    accepted_employees: list[AcceptedEmployee]
    validation_errors: list[RowError]
    hierarchy: HierarchyResult
