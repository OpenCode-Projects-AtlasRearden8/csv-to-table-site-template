# csv-to-table-site-template

Turn a plain spreadsheet (CSV) into a small, searchable, sortable website.
No JavaScript to write, no frameworks to install, no accounts to create.
If you can save a CSV file, you can publish a table site.

Made by [Asdale Dynamics, LLC](https://dylanasdale.github.io) — the same folks
behind *The Massive AI Manual*. Things here are explained like a friend would:
plain English, step by step, never condescending.

## What you get

- `build.py` — a Python script (standard library only, Python 3.8+) that reads
  any CSV and generates a finished website.
- A responsive table page with:
  - a **search box** that filters every column as you type,
  - **clickable column headers** to sort ascending/descending (numbers sort
    numerically, blanks go to the bottom),
  - a live "Showing X of Y rows" counter,
  - no external files: one `index.html`, works straight from your desktop.
- A **GitHub Actions workflow** (`.github/workflows/deploy-pages.yml`) so
  GitHub Pages can host it with nothing else to configure.
- Two sample CSVs in `data/` to practice with.

## Quick start (30 seconds)

1. Put your spreadsheet in this folder as a CSV file.
   In Excel or Google Sheets, that's **File → Save/Download as → CSV**.
2. Open a terminal in this folder and run:

   ```bash
   python3 build.py data/sample-tools.csv
   ```

3. Open the `site` folder and double-click `index.html`. That's the whole site.

To look at it as a real website locally, run:

```bash
python3 -m http.server 8000 -d site
```

then visit http://localhost:8000 in a browser.

## Use your own CSV

```bash
python3 build.py path/to/your-file.csv
python3 build.py path/to/your-file.csv -o site -t "My Book List"
```

- The **first row** of the CSV becomes the column headers.
- Every column is searched and sortable automatically — you never touch the code.
- `-o` picks the output folder (default `site`).
- `-t` sets the page title (default: your file's name, e.g. `PracticeTest.csv`
  becomes "PracticeTest").

The script handles commas, tabs, and semicolons as separators, an optional
BOM (which Excel adds), duplicate or empty header names, and rows with
missing values.

## Publishing to GitHub Pages (first time)

The build writes a `.github/workflows/deploy-pages.yml` file that publishes
your `site` folder automatically:

1. Push this repository to GitHub (main branch).
2. On GitHub, open **Settings → Pages**.
3. Under "Build and deployment", set **Source** to **GitHub Actions**.
4. That's it — every future push rebuilds and republishes the site.

Nothing to install, nothing to code, no secret keys.

## Tests

The template is verified with [pytest](https://pytest.org):

```bash
python3 -m pytest
```

The tests confirm the generated site has the expected structure, that every
CSV row and header makes it into the page, that search and sort wiring is
present, and that the Pages workflow is written correctly.

## Files

| File | What it is |
| --- | --- |
| `build.py` | The whole build: CSV in, website out |
| `data/sample-tools.csv` | Example: beginner-friendly AI tools |
| `data/sample-inventory.csv` | Example: a small reselling inventory |
| `data/PracticeTest.csv` | Scratch file for practice |
| `tests/test_build.py` | pytest checks for the generated site |
| `.github/workflows/deploy-pages.yml` | Free hosting on GitHub Pages |

## Relationship to other Asdale templates

This template is for **tabular data** — inventories, link lists, price
sheets, schedules. For long-form documentation written in Markdown, use the
companion template `markdown-manual-site-template`.

## License

MIT — see `LICENSE`. Copyright (c) 2026 Asdale Dynamics, LLC.
