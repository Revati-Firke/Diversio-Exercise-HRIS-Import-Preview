"""
Manager resolution, root detection, and reporting-cycle detection.

Operates on accepted employees only (identity-validated).
"""

from __future__ import annotations

from .models import AcceptedEmployee, HierarchyResult, ManagerReport, RowError


def analyze_hierarchy(employees: list[AcceptedEmployee]) -> HierarchyResult:
    """Resolve manager relationships and detect cycles.

    Returns roots, manager→report counts, cycle members, and manager errors.
    """
    by_id = {e.employee_id: e for e in employees}
    by_email = {e.email: e for e in employees}

    # manager_of[employee_id] = manager's employee_id (or None)
    manager_of: dict[str, str | None] = {}
    roots: list[AcceptedEmployee] = []
    errors: list[RowError] = []

    for emp in employees:
        resolved = _resolve_manager(emp, by_id, by_email)

        if isinstance(resolved, RowError):
            errors.append(resolved)
            # Employee stays accepted but has no relationship and is not a root.
        elif resolved is None:
            roots.append(emp)
        else:
            manager_of[emp.employee_id] = resolved

    # --- Direct-report counts ---
    report_counts: dict[str, int] = {}
    for child_id, parent_id in manager_of.items():
        report_counts[parent_id] = report_counts.get(parent_id, 0) + 1

    manager_reports = [
        ManagerReport(
            employee_id=mid,
            employee_name=by_id[mid].employee_name,
            direct_report_count=count,
        )
        for mid, count in sorted(report_counts.items())
    ]

    # --- Cycle detection ---
    cycle_members = _detect_cycles(manager_of)
    cycle_employees = [by_id[eid] for eid in cycle_members]

    return HierarchyResult(
        roots=roots,
        manager_reports=manager_reports,
        cycle_members=cycle_employees,
        errors=errors,
    )


def _resolve_manager(
    emp: AcceptedEmployee,
    by_id: dict[str, AcceptedEmployee],
    by_email: dict[str, AcceptedEmployee],
) -> str | RowError | None:
    """Resolve an employee's manager.

    Returns:
        - None if the employee is a root (both fields blank).
        - The manager's employee_id on success.
        - A RowError on failure.
    """
    mid = emp.manager_id
    memail = emp.manager_email
    has_id = bool(mid)
    has_email = bool(memail)

    if not has_id and not has_email:
        return None  # root

    found_by_id = by_id.get(mid) if has_id else None
    found_by_email = by_email.get(memail) if has_email else None

    if has_id and has_email:
        if found_by_id is None and found_by_email is None:
            return RowError(
                emp.row_number, emp.employee_id,
                f"Manager not found by id '{mid}' or email '{memail}'.",
            )
        if found_by_id is None:
            return RowError(
                emp.row_number, emp.employee_id,
                f"Manager id '{mid}' not found.",
            )
        if found_by_email is None:
            return RowError(
                emp.row_number, emp.employee_id,
                f"Manager email '{memail}' not found.",
            )
        if found_by_id.employee_id != found_by_email.employee_id:
            return RowError(
                emp.row_number, emp.employee_id,
                f"Manager id '{mid}' and email '{memail}' refer to different employees.",
            )
        manager = found_by_id
    elif has_id:
        if found_by_id is None:
            return RowError(
                emp.row_number, emp.employee_id,
                f"Manager id '{mid}' not found.",
            )
        manager = found_by_id
    else:
        if found_by_email is None:
            return RowError(
                emp.row_number, emp.employee_id,
                f"Manager email '{memail}' not found.",
            )
        manager = found_by_email

    if manager.employee_id == emp.employee_id:
        return RowError(
            emp.row_number, emp.employee_id,
            "Employee lists themselves as their own manager.",
        )

    return manager.employee_id


def _detect_cycles(manager_of: dict[str, str | None]) -> list[str]:
    """Find employees that are members of a reporting cycle.

    Walks each employee's manager chain, tracking the path. If we revisit
    a node already on the current path, everything from that node onward
    is part of a cycle. Employees who merely report into a cycle
    participant are NOT flagged.
    """
    visited: set[str] = set()
    cycle_set: set[str] = set()

    for start in manager_of:
        if start in visited:
            continue

        # Walk the chain from start, recording the path.
        path: list[str] = []
        path_index: dict[str, int] = {}
        node: str | None = start

        while node is not None and node in manager_of:
            if node in cycle_set:
                # Already known cycle member — don't extend.
                break
            if node in visited:
                # Reached a fully-explored non-cycle node — no cycle here.
                break
            if node in path_index:
                # Found a cycle: nodes from first occurrence of node to end of path.
                cycle_set.update(path[path_index[node]:])
                break

            path_index[node] = len(path)
            path.append(node)
            node = manager_of.get(node)

        visited.update(path)

    return sorted(cycle_set)
