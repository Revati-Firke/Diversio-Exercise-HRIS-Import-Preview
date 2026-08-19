# HRIS Import Preview

A Django web application that accepts an HRIS CSV upload and presents an import
preview with validation errors, employee hierarchy, and cycle detection.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python manage.py runserver
```

Then open http://127.0.0.1:8000/ and upload a CSV file (`sample_hris.csv` is
included in the repository).

## Test

```bash
python -m pytest -v
```

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full design documentation.

**Key structure:**

- `preview/services/parser.py` — CSV parsing, BOM handling, normalization
- `preview/services/validator.py` — Required field and uniqueness checks
- `preview/services/hierarchy.py` — Manager resolution, root detection, cycle detection
- `preview/services/analyzer.py` — Orchestrator that ties the pipeline together
- `preview/views.py` — Thin Django view layer
- `preview/tests/` — Automated tests for validator and hierarchy logic

All business logic is in plain Python services (no Django dependency), making it
easy to test without driving a browser.

## Assumptions and Known Limitations

- **No database persistence** — all analysis is in-memory per request.
- **File size** — accepts files up to 10 MB (configurable in settings).
- **UTF-8 only** — other encodings are not supported.
- **employee_name and department** — not required for validation; may be blank.
- **Cycle detection** — only flags employees that are direct members of a cycle,
  not employees who merely report into a cycle participant.
- **Manager errors** — an employee with a manager resolution error remains
  accepted but does not produce a reporting relationship and is not classified
  as a root.

## Complexity (for ~100K rows)

| Operation | Time | Space |
|---|---|---|
| CSV parsing | O(N) | O(N) |
| Identity validation | O(N) | O(N) |
| Manager resolution | O(N) | O(N) |
| Cycle detection | O(N) | O(N) |
| **Total** | **O(N)** | **O(N)** |

## Approximate Time Spent

~90 minutes

## AI Tools Used

Cursor AI agent (Claude) — used for scaffolding, code generation, and iterating
on the cycle detection algorithm. All code was reviewed and validated manually.
