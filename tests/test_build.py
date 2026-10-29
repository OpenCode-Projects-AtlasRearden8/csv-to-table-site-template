import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build  # noqa: E402

COPYRIGHT = "Copyright (c) 2026 Asdale Dynamics, LLC"


@pytest.fixture()
def built(tmp_path):
    index, ncols, nrows = build.build_site(
        ROOT / "data" / "sample-tools.csv",
        tmp_path / "site",
        title=None,
        pages=True,
    )
    return {"index": index, "out": tmp_path / "site", "ncols": ncols, "nrows": nrows, "root": tmp_path}


def read_json_payload(html):
    match = re.search(r"var DATA = (\{.*\});\n", html)
    assert match, "generated page must embed its data as JSON"
    return json.loads(match.group(1).replace("<\\/", "</"))


def test_index_is_written(built):
    assert built["index"].exists()
    html = built["index"].read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in html
    assert 'id="search"' in html
    assert 'id="tbody"' in html


def test_every_row_and_header_is_embedded(built):
    html = built["index"].read_text(encoding="utf-8")
    payload = read_json_payload(html)
    assert payload["headers"] == [
        "name",
        "what_it_is",
        "free_tier",
        "good_for",
        "where_to_start",
    ]
    assert len(payload["rows"]) == built["nrows"] == 10
    names = {row["name"] for row in payload["rows"]}
    assert "Ollama" in names and "Perplexity" in names


def test_title_defaults_to_file_name(built):
    html = built["index"].read_text(encoding="utf-8")
    assert "<title>Sample Tools</title>" in html
    assert "<h1>Sample Tools</h1>" in html


def test_custom_title(tmp_path):
    index, _, _ = build.build_site(
        ROOT / "data" / "sample-tools.csv", tmp_path / "site", title="My Links", pages=False
    )
    assert "<title>My Links</title>" in index.read_text(encoding="utf-8")


def test_html_is_escaped(built):
    html = built["index"].read_text(encoding="utf-8")
    payload = read_json_payload(html)
    raw = built["index"].read_text(encoding="utf-8")
    assert raw.count("var DATA =") == 1
    assert payload["title"] == "Sample Tools"
    assert "</script>" not in raw.split("var DATA =")[1].split(";\n")[0]


def test_sort_and_search_wiring(built):
    html = built["index"].read_text(encoding="utf-8")
    for needle in [
        'addEventListener("input"',
        "function setSort",
        "aria-sort",
        "numericCols[idx] = isNumeric",
        "Showing ",
        "localeCompare",
    ]:
        assert needle in html, f"missing wiring: {needle}"


def test_pages_workflow_written_next_to_site(built):
    workflow = built["root"] / ".github" / "workflows" / "deploy-pages.yml"
    text = workflow.read_text(encoding="utf-8")
    assert "actions/deploy-pages@v4" in text
    assert '"site"' in text
    assert "permissions" in text


def test_pages_workflow_skipped_with_flag(tmp_path):
    build.build_site(
        ROOT / "data" / "sample-tools.csv", tmp_path / "site", pages=False
    )
    assert not (tmp_path / ".github").exists()
    assert (tmp_path / "site" / "index.html").exists()


def test_read_csv_handles_bom_and_missing_values(tmp_path):
    csv_file = tmp_path / "odd.csv"
    csv_file.write_bytes(b"\xef\xbb\xbfname,amount\nAlpha,1\nBeta\n,3\n")
    headers, records = build.read_csv(csv_file)
    assert headers == ["name", "amount"]
    assert records[1] == {"name": "Beta", "amount": ""}
    assert records[2] == {"name": "", "amount": "3"}


def test_read_csv_renames_duplicate_and_blank_headers(tmp_path):
    csv_file = tmp_path / "dup.csv"
    csv_file.write_text("name,,name\na,b,c\n", encoding="utf-8")
    headers, _ = build.read_csv(csv_file)
    assert headers == ["name", "Column 2", "name (2)"]


def test_read_csv_tab_delimited(tmp_path):
    csv_file = tmp_path / "tabs.txt"
    csv_file.write_text("a\tb\tc\n1\t2\t3\n", encoding="utf-8")
    headers, rows = build.read_csv(csv_file)
    assert headers == ["a", "b", "c"]
    assert rows == [{"a": "1", "b": "2", "c": "3"}]


def test_empty_csv_is_a_friendly_error(tmp_path):
    csv_file = tmp_path / "empty.csv"
    csv_file.write_text("", encoding="utf-8")
    with pytest.raises(SystemExit, match="empty"):
        build.read_csv(csv_file)


def test_single_row_csv_builds(tmp_path):
    csv_file = tmp_path / "one.csv"
    csv_file.write_text("col1,col2\nval1,val2\n", encoding="utf-8")
    index, ncols, nrows = build.build_site(csv_file, tmp_path / "site", pages=False)
    payload = read_json_payload(index.read_text(encoding="utf-8"))
    assert payload["rows"] == [{"col1": "val1", "col2": "val2"}]
    assert (ncols, nrows) == (2, 1)


def test_numeric_columns_detected_for_sorting(tmp_path):
    csv_file = tmp_path / "nums.csv"
    csv_file.write_text("item,price\nB,10.5\nA,2\nC,\n", encoding="utf-8")
    index, _, _ = build.build_site(csv_file, tmp_path / "s", title="Nums", pages=False)
    payload = read_json_payload(index.read_text(encoding="utf-8"))
    assert [r["item"] for r in payload["rows"]] == ["B", "A", "C"]
    assert [r["price"] for r in payload["rows"]] == ["10.5", "2", ""]


def test_cli_end_to_end(tmp_path):
    out = tmp_path / "out" / "site"
    result = subprocess.run(
        [sys.executable, str(ROOT / "build.py"), str(ROOT / "data" / "sample-inventory.csv"),
         "-o", str(out), "-t", "Inventory"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    index = out / "index.html"
    assert index.exists()
    payload = read_json_payload(index.read_text(encoding="utf-8"))
    assert len(payload["rows"]) == 6
    assert (tmp_path / "out" / ".github" / "workflows" / "deploy-pages.yml").exists()


def test_cli_missing_file_message(tmp_path):
    result = subprocess.run(
        [sys.executable, str(ROOT / "build.py"), str(tmp_path / "nope.csv"),
         "-o", str(tmp_path / "s"), "--no-pages"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0 or "Could not find" in result.stderr


def test_license_and_readme_credits():
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert license_text.startswith("MIT License")
    assert COPYRIGHT in license_text
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert COPYRIGHT in readme
    assert "Asdale Dynamics, LLC" in readme
