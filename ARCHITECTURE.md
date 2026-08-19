# HRIS Import Preview — Architecture

## Overview

A Django web application that accepts an HRIS CSV upload and presents a detailed
import preview: validation errors, employee hierarchy, and cycle detection.
No data is persisted — all analysis happens in memory per request.

---

## Design Principles

| Principle | How it's applied |
|---|---|
| **Single Responsibility** | Each service module handles exactly one concern (parsing, validation, hierarchy). |
| **Separation of Concerns** | Business logic lives in plain Python services with no Django dependency. Views are thin controllers. |
| **Dependency Inversion** | Services operate on dataclasses, not Django models or HTTP objects. |
| **Fail Fast** | Validation errors are collected early; invalid rows are excluded from downstream analysis. |
| **Testability** | All logic can be unit-tested without a web server or browser. |

---

## Project Structure

```
diversio-Engineer-Exercise/
├── manage.py
├── requirements.txt
├── README.md
├── ARCHITECTURE.md
├── sample.csv
│
├── config/                      # Django project configuration
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
└── preview/                     # Django app
    ├── __init__.py
    ├── urls.py
    ├── views.py                 # Thin controller layer
    │
    ├── services/                # Pure business logic (no Django imports)
    │   ├── __init__.py
    │   ├── models.py            # Dataclasses shared across services
    │   ├── parser.py            # CSV reading and normalization
    │   ├── validator.py         # Identity validation (required + uniqueness)
    │   ├── hierarchy.py         # Manager resolution, roots, cycles
    │   └── analyzer.py          # Orchestrator: parse → validate → hierarchy
    │
    ├── templates/
    │   └── preview/
    │       ├── upload.html      # File upload form
    │       └── results.html     # Analysis results display
    │
    └── tests/
        ├── __init__.py
        ├── test_validator.py
        └── test_hierarchy.py
```

---

## Data Flow

```
                   ┌──────────┐
  CSV Upload ────▶ │  View    │  (thin controller)
                   └────┬─────┘
                        │
                        ▼
                   ┌──────────┐
                   │ Analyzer │  (orchestrator)
                   └────┬─────┘
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
     ┌─────────┐  ┌───────────┐  ┌───────────┐
     │ Parser  │  │ Validator │  │ Hierarchy │
     └─────────┘  └───────────┘  └───────────┘
          │             │             │
          ▼             ▼             ▼
      RawRow[]    AcceptedRows    HierarchyResult
                  + Errors[]      (roots, reports,
                                   cycles, errors)
```

### Step-by-step

1. **Parser** — Reads CSV bytes, handles BOM, produces a list of `RawRow`
   dataclasses with original row numbers and normalized values.

2. **Validator** — Checks required fields (`employee_id`, `email`) and
   uniqueness. Returns accepted rows and row-level errors. All rows sharing
   a duplicated ID or email are marked invalid.

3. **Hierarchy** — Takes accepted rows and resolves manager references:
   - Both fields blank → root employee.
   - Only `manager_id` → lookup by employee ID.
   - Only `manager_email` → lookup by normalized email.
   - Both present → both must resolve to the same employee.
   - Detects self-management, missing managers, and conflicting references.
   - Finds reporting cycles (only employees *in* the cycle, not those
     reporting into one).

4. **Analyzer** — Orchestrates steps 1–3, merges errors, and returns a
   single `AnalysisResult` dataclass to the view.

5. **View** — Passes the uploaded file to the analyzer, renders results
   in an HTML template.

---

## Key Data Models (dataclasses)

```python
@dataclass
class RawRow:
    row_number: int          # 1-based source row number
    employee_id: str
    employee_name: str
    email: str
    manager_id: str
    manager_email: str
    department: str

@dataclass
class ValidationError:
    row_number: int
    employee_id: str
    message: str

@dataclass
class AcceptedEmployee:
    row_number: int
    employee_id: str
    employee_name: str
    email: str
    manager_id: str         # raw (trimmed) value
    manager_email: str      # normalized (lowercased)
    department: str

@dataclass
class HierarchyResult:
    roots: list              # employees with no manager
    manager_reports: dict    # manager_id → count of direct reports
    cycle_members: list      # employees that are part of a cycle
    errors: list             # manager resolution errors

@dataclass
class AnalysisResult:
    total_rows: int
    accepted_employees: list
    validation_errors: list
    roots: list
    manager_reports: dict
    cycle_members: list
```

---

## Cycle Detection Algorithm

Uses iterative DFS with three coloring states:

| Color | Meaning |
|---|---|
| **White** | Unvisited |
| **Gray** | In current DFS path (on the recursion stack) |
| **Black** | Fully explored, not in a cycle |

When a gray node is encountered during traversal, all nodes on the path from
that node back to itself are members of a cycle. Only those nodes are marked —
employees who merely report into a cycle participant are not flagged.

**Complexity for N employees:**
- Time: O(N) — each node visited once.
- Space: O(N) — color map + parent tracking.

---

## Error Handling Strategy

| Scenario | Behavior |
|---|---|
| Non-CSV or empty file | User-friendly error on upload page |
| Missing required headers | Clear error listing missing columns |
| Missing `employee_id` or `email` | Row-level validation error |
| Duplicate ID or email | All rows sharing the duplicate are invalid |
| Manager not found | Manager-level error; employee stays accepted |
| Self-management | Manager-level error |
| Conflicting manager references | Manager-level error |
| Reporting cycle | Flagged in cycle members list |

---

## Scalability Notes (for ~100K rows)

- **Single-pass parsing** — CSV is read once with Python's `csv` module.
- **Dictionary lookups** — Employee-by-ID and employee-by-email maps give O(1)
  resolution. Total manager resolution is O(N).
- **Cycle detection** — O(N) time and space via DFS.
- **No database** — Everything in memory; a 100K-row CSV with typical HRIS
  fields fits comfortably in a few hundred MB.
- **Streaming not needed** at this scale, but the parser could be adapted to
  yield rows for very large files.
