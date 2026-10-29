# STATUS.md

**Project:** csv-to-table-site-template
**Owner:** Asdale Dynamics, LLC
**Date:** 2026-10-29

## What was built

A standalone template that converts any plain CSV file into a small,
filterable website — no JavaScript to write, no package installs, no accounts.

- `build.py` — stdlib-only Python 3.8+ build script. `python3 build.py your-file.csv`
  reads any CSV (any separator: comma/tab/semicolon/pipe, optional BOM, duplicate
  or blank headers, ragged rows) and generates a finished, responsive page with:
  - a live search box that filters every column as you type,
  - clickable column headers for ascending/descending sorting
    (numbers sort numerically, blanks sort to the bottom),
  - a "Showing X of Y rows" counter, `aria-sort` accessibility labels,
  - one self-contained `site/index.html` with the data embedded inline —
    works from a double-click on disk, no server required.
- `.github/workflows/deploy-pages.yml` — written automatically on each build so
  a first-time publisher can turn on GitHub Pages (Settings → Pages → Source:
  GitHub Actions) and never touch code or secrets.
- `data/sample-tools.csv`, `data/sample-inventory.csv`, `data/PracticeTest.csv`
  — sample spreadsheets to practice with.
- `tests/test_build.py` — 17 pytest tests covering the CSV reader (BOM, tabs,
  duplicates, blanks, empty file), generated page structure, embedded data
  integrity, sort/search wiring, the Pages workflow, and CLI end-to-end runs.
- `README.md` — plain-English quick start, own-CSV guide, and publishing steps.
- `LICENSE` — MIT, Copyright (c) 2026 Asdale Dynamics, LLC.
- Complements `markdown-manual-site-template` (long-form docs): this one is for
  tabular data.

## How to run it

```bash
# Build the site (writes site/index.html + the Pages workflow)
python3 build.py data/sample-tools.csv

# Use your own CSV, with an optional output folder and title
python3 build.py data/sample-inventory.csv -o site -t "My Inventory"

# Preview locally
python3 -m http.server 8000 -d site    # visit http://localhost:8000

# Run the test suite
python3 -m pytest
```

## Verification results

- `python3 -m pytest` → **17 passed**, 0 failures.
- Builds verified with all three sample CSVs (`sample-tools.csv`,
  `sample-inventory.csv`, `PracticeTest.csv`); correct column/row counts every time.
- The generated page's JavaScript was executed under Node (v20) with a stubbed
  DOM: parse OK, and the search, sort, and sort-toggle code paths ran without errors.
- CLI tested end-to-end via subprocess, including a friendly error for a
  missing file and for an empty CSV.
- Confirmed the embedded payload contains every row and header, `<` `/script`
  break-outs are neutralized, and the workflow names the correct site folder.

## Known gaps / future ideas

- The local preview command assumes Python's built-in http server; a `just` or
  `make` shortcut could be added later.
- Sorting is single-column only (no shift-click multi-column sort).
- No CSV quote-style edge cases beyond standard `csv.Sniffer` dialects
  (exotic Excel exports with embedded newlines inside quoted fields are
  handled by the `csv` module itself, but not explicitly tested).
- The generated page has no theming options yet (single warm, simple style).
- Could add a `--csv` watcher that rebuilds on file change for live editing.
