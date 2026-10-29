#!/usr/bin/env python3
"""Turn a plain CSV file into a small, filterable website.

Usage:
    python3 build.py data/your-file.csv
    python3 build.py data/your-file.csv -o site -t "My Table"
    python3 build.py data/your-file.csv --no-pages

By default the site is written to the `site/` folder, and a GitHub Actions
workflow is written to `.github/workflows/deploy-pages.yml` so first-time
publishers can deploy to GitHub Pages with no code changes.

Requires Python 3.8+ and uses only the standard library.
"""

import argparse
import csv
import datetime
import html
import json
import pathlib
import sys

COPYRIGHT = "Copyright (c) 2026 Asdale Dynamics, LLC"

PAGES_WORKFLOW = """name: Deploy to GitHub Pages

on:
  push:
    branches:
      - main

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - name: Check out the repository
        uses: actions/checkout@v4
      - name: Set up GitHub Pages
        uses: actions/configure-pages@v5
      - name: Upload the site folder
        uses: actions/upload-pages-artifact@v3
        with:
          path: {site_dir}
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
"""


def read_csv(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel
        reader = csv.reader(f, dialect)
        rows = [row for row in reader]
    if not rows:
        raise SystemExit(f"That file ({path}) appears to be empty.")
    headers = rows[0]
    cleaned = []
    seen = {}
    for i, name in enumerate(headers, start=1):
        name = (name or "").strip()
        if not name:
            name = f"Column {i}"
        if name in seen:
            seen[name] += 1
            name = f"{name} ({seen[name]})"
        else:
            seen[name] = 1
        cleaned.append(name)
    records = []
    for row in rows[1:]:
        record = {}
        for i, name in enumerate(cleaned):
            record[name] = row[i] if i < len(row) else ""
        records.append(record)
    return cleaned, records


def page_title(csv_path):
    stem = pathlib.Path(csv_path).stem.replace("-", " ").replace("_", " ").strip()
    if not stem:
        stem = "My Table"
    words = []
    for word in stem.split():
        words.append(word.capitalize() if word.islower() else word)
    return " ".join(words)


def build_site(csv_path, out_dir, title=None, pages=True):
    csv_path = pathlib.Path(csv_path)
    out_dir = pathlib.Path(out_dir)
    headers, records = read_csv(csv_path)
    title = (title or page_title(csv_path)).strip()

    payload = json.dumps(
        {"title": title, "headers": headers, "rows": records},
        ensure_ascii=False,
        separators=(",", ":"),
    ).replace("</", "<\\/")

    page_html = PAGE_TEMPLATE.format(
        title=html.escape(title),
        build_date=datetime.date.today().isoformat(),
        payload=payload,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    index_path = out_dir / "index.html"
    index_path.write_text(page_html, encoding="utf-8")

    if pages:
        repo_root = out_dir.parent
        workflow_dir = repo_root / ".github" / "workflows"
        workflow_dir.mkdir(parents=True, exist_ok=True)
        workflow_path = workflow_dir / "deploy-pages.yml"
        site_dir = out_dir.resolve().name
        workflow_path.write_text(
            PAGES_WORKFLOW.format(site_dir=json.dumps(site_dir)), encoding="utf-8"
        )
    return index_path, len(headers), len(records)


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="A searchable, sortable table generated from a CSV file.">
<style>
  :root {{
    --bg: #fdfbf7;
    --card: #ffffff;
    --ink: #2b2b2b;
    --muted: #6b6b6b;
    --accent: #2f6f4f;
    --accent-soft: #eaf3ee;
    --line: #e3e0d8;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    background: var(--bg);
    color: var(--ink);
    line-height: 1.55;
  }}
  header, main, footer {{ max-width: 62rem; margin: 0 auto; padding: 0 1rem; }}
  header {{ padding-top: 2rem; }}
  h1 {{ font-size: 1.75rem; margin: 0 0 .25rem; }}
  .sub {{ color: var(--muted); margin: 0; }}
  .toolbar {{
    display: flex; flex-wrap: wrap; gap: .75rem; align-items: center;
    margin: 1.25rem 0 1rem;
  }}
  label {{ font-weight: 600; }}
  #search {{
    flex: 1 1 14rem; max-width: 22rem;
    padding: .6rem .8rem; font-size: 1rem;
    border: 1px solid var(--line); border-radius: .5rem; background: var(--card);
  }}
  #search:focus {{ outline: 2px solid var(--accent); outline-offset: 1px; }}
  .count {{ color: var(--muted); font-size: .95rem; }}
  .table-card {{
    background: var(--card); border: 1px solid var(--line);
    border-radius: .75rem; overflow-x: auto;
  }}
  table {{ border-collapse: collapse; width: 100%; min-width: 40rem; }}
  th, td {{ text-align: left; padding: .55rem .8rem; border-bottom: 1px solid var(--line); }}
  thead th {{
    position: sticky; top: 0; background: var(--accent-soft); cursor: pointer;
    white-space: nowrap; user-select: none;
  }}
  thead th:hover {{ background: #dceae2; }}
  thead th .arrow {{ font-size: .8em; color: var(--accent); }}
  tbody tr:hover {{ background: #f7f5ef; }}
  .empty-note {{ padding: 1.25rem; color: var(--muted); font-style: italic; }}
  footer {{
    color: var(--muted); font-size: .9rem;
    padding: 2rem 1rem 2.5rem; text-align: center;
  }}
  footer a {{ color: var(--accent); }}
</style>
</head>
<body>
<header>
  <h1>{title}</h1>
  <p class="sub">Search the box below or tap a column header to sort. Built {build_date}.</p>
</header>
<main>
  <div class="toolbar">
    <label for="search">Search</label>
    <input type="search" id="search" placeholder="Type to filter rows..." autocomplete="off">
    <span class="count" id="count" role="status"></span>
  </div>
  <div class="table-card">
    <table aria-describedby="count">
      <thead id="thead"></thead>
      <tbody id="tbody"></tbody>
    </table>
    <div class="empty-note" id="empty-note" hidden>No rows match your search.</div>
  </div>
</main>
<footer>
  Built from a CSV with
  <a href="https://github.com/dylanasdale/csv-to-table-site-template">csv-to-table-site-template</a>,
  a free tool by Asdale Dynamics, LLC.
</footer>
<script>
"use strict";
var DATA = {payload};
var headers = DATA.headers;
var state = {{ query: "", sortCol: null, sortDir: 1 }};

var thead = document.getElementById("thead");
var tbody = document.getElementById("tbody");
var search = document.getElementById("search");
var count = document.getElementById("count");
var emptyNote = document.getElementById("empty-note");

function isNumeric(values) {{
  var seen = 0;
  for (var i = 0; i < values.length; i++) {{
    if (values[i] === "" || values[i] === null) continue;
    if (isNaN(Number(values[i]))) return false;
    seen++;
  }}
  return seen > 0;
}}

function buildHead() {{
  var tr = document.createElement("tr");
  headers.forEach(function (h, idx) {{
    var th = document.createElement("th");
    th.setAttribute("scope", "col");
    th.tabIndex = 0;
    th.textContent = h;
    th.setAttribute("aria-label", "Sort by " + h);
    function toggle() {{ setSort(idx); }}
    th.addEventListener("click", toggle);
    th.addEventListener("keydown", function (e) {{
      if (e.key === "Enter" || e.key === " ") {{ e.preventDefault(); toggle(); }}
    }});
    tr.appendChild(th);
  }});
  thead.appendChild(tr);
}}

function setSort(idx) {{
  if (state.sortCol === idx) {{
    if (state.sortDir === 1) state.sortDir = -1; else state.sortCol = null;
  }} else {{
    state.sortCol = idx;
    state.sortDir = 1;
  }}
  render();
}}

function compare(a, b, col, dir) {{
  var colName = headers[col];
  var va = a[colName], vb = b[colName];
  var emptyA = va === "" || va === null;
  var emptyB = vb === "" || vb === null;
  if (emptyA && emptyB) return 0;
  if (emptyA) return 1;
  if (emptyB) return -1;
  if (numericCols[col]) {{
    var na = Number(va), nb = Number(vb);
    return (na - nb) * dir;
  }}
  return String(va).localeCompare(String(vb), undefined, {{ sensitivity: "base", numeric: true }}) * dir;
}}

var numericCols = {{}};

function render() {{
  var tr = thead.rows[0];
  if (tr) {{
    for (var i = 0; i < tr.cells.length; i++) {{
      var th = tr.cells[i];
      th.removeAttribute("aria-sort");
      var base = th.textContent.replace(/\\s*[\\u2191\\u2193]\\s*$/, "");
      th.textContent = base;
      if (i === state.sortCol) {{
        th.setAttribute("aria-sort", state.sortDir === 1 ? "ascending" : "descending");
        th.textContent = base + (state.sortDir === 1 ? " \\u2191" : " \\u2193");
      }}
    }}
  }}

  var q = state.query.trim().toLowerCase();
  var match = DATA.rows.filter(function (r) {{
    if (!q) return true;
    return headers.some(function (h) {{
      return String(r[h] || "").toLowerCase().indexOf(q) !== -1;
    }});
  }});
  if (state.sortCol !== null) {{
    match = match.slice().sort(function (a, b) {{ return compare(a, b, state.sortCol, state.sortDir); }});
  }}

  tbody.innerHTML = "";
  match.forEach(function (r) {{
    var tr = document.createElement("tr");
    headers.forEach(function (h) {{
      var td = document.createElement("td");
      td.textContent = String(r[h] == null ? "" : r[h]);
      tr.appendChild(td);
    }});
    tbody.appendChild(tr);
  }});

  var n = match.length, total = DATA.rows.length;
  count.textContent = "Showing " + n + " of " + total + " row" + (total === 1 ? "" : "s");
  emptyNote.hidden = n !== 0;
}}

buildHead();
headers.forEach(function (h, idx) {{
  numericCols[idx] = isNumeric(DATA.rows.map(function (r) {{ return r[h]; }}));
}});
search.addEventListener("input", function () {{ state.query = search.value; render(); }});
render();
</script>
</body>
</html>
"""


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Turn a CSV file into a small filterable website."
    )
    parser.add_argument("csv", help="path to your CSV file (first row = column names)")
    parser.add_argument(
        "-o", "--out", default="site", help="output folder (default: site)"
    )
    parser.add_argument(
        "-t", "--title", default=None, help='page title (default: based on the file name, e.g. "My File")'
    )
    parser.add_argument(
        "--no-pages",
        action="store_true",
        help="skip writing the GitHub Pages deploy workflow",
    )
    args = parser.parse_args(argv)

    try:
        index_path, ncols, nrows = build_site(
            args.csv, args.out, title=args.title, pages=not args.no_pages
        )
    except FileNotFoundError:
        raise SystemExit(f"Could not find the file: {args.csv}")
    except OSError as exc:
        raise SystemExit(f"Could not read that file: {exc}")

    print(f"Done! Wrote {index_path} ({ncols} columns, {nrows} rows).")
    if not args.no_pages:
        print("Also wrote the GitHub Pages workflow (.github/workflows/deploy-pages.yml).")
    print('Open the site folder in a browser, or run: python3 -m http.server 8000 -d ' + str(pathlib.Path(args.out)))


if __name__ == "__main__":
    main()
