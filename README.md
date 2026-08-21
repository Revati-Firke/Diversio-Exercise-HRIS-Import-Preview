# HRIS Import Preview

Small Django app for uploading an HRIS CSV and checking:

- required/duplicate employee data
- manager relationships
- root employees
- cycle detection in the reporting hierarchy

## Minimal usage

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py runserver
```

Then open:

```text
http://127.0.0.1:8000/
```

Upload a CSV file such as `sample_hris.csv` from the project root.

## What the app does

The app reads the CSV, validates the rows, resolves manager relationships, and flags issues in a preview page.

The main flow is:

```text
CSV -> parser -> validator -> hierarchy analysis -> preview results
```

## Minimal project understanding

- `preview/services/parser.py` — reads and normalizes the CSV
- `preview/services/validator.py` — checks required values and duplicates
- `preview/services/hierarchy.py` — resolves managers and detects cycles
- `preview/services/analyzer.py` — coordinates the full check
- `preview/views.py` — renders the upload/results pages

## Run tests

```bash
python -m pytest -v
```

## Notes

- The project is designed as a lightweight preview tool, not a database-backed app.
- `sample_hris.csv` is included for quick demo/testing.

## AI Tools Used

Cursor AI agent (Claude) — used for scaffolding and understanding the hierarchy/cycle detection logic. It helped with minimal project understanding and iterative refinement, while the final code was reviewed and validated manually.
