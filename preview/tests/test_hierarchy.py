"""Tests for manager resolution and cycle detection."""

from preview.services.hierarchy import analyze_hierarchy
from preview.services.models import AcceptedEmployee


def _emp(eid, email, manager_id="", manager_email="", row=2, name="", dept="Eng"):
    return AcceptedEmployee(
        row_number=row,
        employee_id=eid,
        employee_name=name or eid,
        email=email,
        manager_id=manager_id,
        manager_email=manager_email,
        department=dept,
    )


class TestRootDetection:
    def test_blank_manager_fields_means_root(self):
        employees = [_emp("E1", "e1@x.com")]
        result = analyze_hierarchy(employees)
        assert len(result.roots) == 1
        assert result.roots[0].employee_id == "E1"

    def test_with_manager_is_not_root(self):
        employees = [
            _emp("M1", "m1@x.com"),
            _emp("E1", "e1@x.com", manager_id="M1"),
        ]
        result = analyze_hierarchy(employees)
        root_ids = [r.employee_id for r in result.roots]
        assert "M1" in root_ids
        assert "E1" not in root_ids


class TestManagerResolution:
    def test_lookup_by_id(self):
        employees = [
            _emp("M1", "m1@x.com"),
            _emp("E1", "e1@x.com", manager_id="M1"),
        ]
        result = analyze_hierarchy(employees)
        assert result.manager_reports[0].employee_id == "M1"
        assert result.manager_reports[0].direct_report_count == 1

    def test_lookup_by_email(self):
        employees = [
            _emp("M1", "m1@x.com"),
            _emp("E1", "e1@x.com", manager_email="m1@x.com"),
        ]
        result = analyze_hierarchy(employees)
        assert result.manager_reports[0].employee_id == "M1"

    def test_both_fields_must_agree(self):
        employees = [
            _emp("M1", "m1@x.com"),
            _emp("M2", "m2@x.com"),
            _emp("E1", "e1@x.com", manager_id="M1", manager_email="m2@x.com"),
        ]
        result = analyze_hierarchy(employees)
        assert len(result.errors) == 1
        assert "different employees" in result.errors[0].message

    def test_self_management_error(self):
        employees = [_emp("E1", "e1@x.com", manager_id="E1")]
        result = analyze_hierarchy(employees)
        assert len(result.errors) == 1
        assert "themselves" in result.errors[0].message

    def test_manager_not_found(self):
        employees = [_emp("E1", "e1@x.com", manager_id="GHOST")]
        result = analyze_hierarchy(employees)
        assert len(result.errors) == 1
        assert "not found" in result.errors[0].message


class TestCycleDetection:
    def test_simple_cycle(self):
        employees = [
            _emp("A", "a@x.com", manager_id="B"),
            _emp("B", "b@x.com", manager_id="A"),
        ]
        result = analyze_hierarchy(employees)
        cycle_ids = {e.employee_id for e in result.cycle_members}
        assert cycle_ids == {"A", "B"}

    def test_employee_reporting_into_cycle_is_not_flagged(self):
        employees = [
            _emp("A", "a@x.com", manager_id="B"),
            _emp("B", "b@x.com", manager_id="A"),
            _emp("C", "c@x.com", manager_id="A"),
        ]
        result = analyze_hierarchy(employees)
        cycle_ids = {e.employee_id for e in result.cycle_members}
        assert cycle_ids == {"A", "B"}
        assert "C" not in cycle_ids

    def test_no_cycle(self):
        employees = [
            _emp("M1", "m1@x.com"),
            _emp("E1", "e1@x.com", manager_id="M1"),
        ]
        result = analyze_hierarchy(employees)
        assert len(result.cycle_members) == 0

    def test_three_node_cycle(self):
        employees = [
            _emp("A", "a@x.com", manager_id="C"),
            _emp("B", "b@x.com", manager_id="A"),
            _emp("C", "c@x.com", manager_id="B"),
        ]
        result = analyze_hierarchy(employees)
        cycle_ids = {e.employee_id for e in result.cycle_members}
        assert cycle_ids == {"A", "B", "C"}
