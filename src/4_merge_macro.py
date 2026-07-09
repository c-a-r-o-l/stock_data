"""
4_merge_macro.py — Merge all macro series into a daily forward-filled wide table.

Reads all files from History_4_E_Alfred_Release, extracts (release_date, value)
per series, forward-fills onto a master daily date grid.

Handles two formats:
  Multi-revision:  observation_date, revision_rank, revision_name, value, released_on
  Single-revision: observation_date, value, release_date

Output: data/History_6_merge/macro_merge_daily.csv
"""

import csv
import io
import re
from collections import defaultdict
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
INPUT_DIR = DATA_DIR / "History_4_E_Alfred_Release"
OUTPUT_FILE = DATA_DIR / "History_6_merge" / "macro_merge_daily.csv"


# ── Helpers ─────────────────────────────────────────────────────────────────

def detect_delimiter(sample: str) -> str:
    first_line = sample.split("\n")[0]
    tabs = first_line.count("\t")
    commas = first_line.count(",")
    return "\t" if tabs > commas else ","


def sniff_format(header: list[str]) -> str | None:
    cols = {c.strip().lower() for c in header}
    if {"released_on", "value", "observation_date"}.issubset(cols):
        return "multi"
    if {"release_date", "value", "observation_date"}.issubset(cols):
        return "single"
    return None


def process_multi(rows, header):
    """Extract (release_date, value) from multi-revision format.
    For each release_date, keep the row with highest revision_rank."""
    cols = {c.strip().lower(): i for i, c in enumerate(header)}
    rel_idx = cols.get("released_on", 0)
    val_idx = cols.get("value", 1)
    rank_idx = cols.get("revision_rank", -1)

    by_date = {}
    for i, row in enumerate(rows):
        if len(row) <= max(rel_idx, val_idx):
            continue
        rel = row[rel_idx].strip()
        val = row[val_idx].strip()
        if not rel or not val or val == ".":
            continue
        rank = int(row[rank_idx]) if rank_idx >= 0 and rank_idx < len(row) and row[rank_idx].strip().isdigit() else i
        if rel not in by_date or rank >= by_date[rel][0]:
            by_date[rel] = (rank, val)
    return sorted([(d, v) for d, (_, v) in by_date.items()], key=lambda x: x[0])


def process_single(rows, header):
    """Extract (release_date, value) from single-revision format."""
    cols = {c.strip().lower(): i for i, c in enumerate(header)}
    rel_idx = cols.get("release_date", 2)
    val_idx = cols.get("value", 1)
    by_date = {}
    for row in rows:
        if len(row) <= max(rel_idx, val_idx):
            continue
        rel = row[rel_idx].strip()
        val = row[val_idx].strip()
        if not rel or not val or val == ".":
            continue
        by_date[rel] = val
    return sorted(by_date.items(), key=lambda x: x[0])


def make_column_name(filename: str) -> str:
    """Use filename without extension, stripping known suffixes."""
    name = Path(filename).stem
    for suffix in ('_latest', '_revision_timeline', '_first_release', '_final'):
        if name.endswith(suffix):
            name = name[:-len(suffix)]
            break
    return name


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not INPUT_DIR.is_dir():
        print(f"ERROR: Input directory not found: {INPUT_DIR}")
        return

    files = sorted(
        f for f in INPUT_DIR.iterdir()
        if f.suffix.lower() in (".csv", ".tsv", ".txt")
        and not f.name.startswith("_")
    )

    series_data = {}
    skipped = []
    all_dates = set()

    for fpath in files:
        raw = fpath.read_text(encoding="utf-8", errors="replace")
        delim = detect_delimiter(raw)
        reader = csv.reader(io.StringIO(raw), delimiter=delim)
        all_rows = list(reader)
        if not all_rows:
            skipped.append(f"{fpath.name} (empty)")
            continue

        header = all_rows[0]
        data_rows = all_rows[1:]
        fmt = sniff_format(header)

        if fmt == "multi":
            pairs = process_multi(data_rows, header)
        elif fmt == "single":
            pairs = process_single(data_rows, header)
        else:
            skipped.append(f"{fpath.name} (unrecognized format)")
            continue

        if not pairs:
            skipped.append(f"{fpath.name} (no valid data)")
            continue

        col_name = make_column_name(fpath.name)
        series_data[col_name] = pairs
        all_dates.update(d for d, _ in pairs)

    # Build a DAILY date grid from min to max release date
    from datetime import datetime, timedelta
    min_date = datetime.strptime(min(all_dates), '%Y-%m-%d')
    max_date = datetime.strptime(max(all_dates), '%Y-%m-%d')
    master_dates = []
    d = min_date
    while d <= max_date:
        master_dates.append(d.strftime('%Y-%m-%d'))
        d += timedelta(days=1)

    col_names = sorted(series_data.keys())

    # Forward-fill onto master grid
    series_next = {}
    series_current = {}
    for col in col_names:
        pairs = series_data[col]
        it = iter(pairs)
        series_current[col] = None
        try:
            series_next[col] = next(it)
        except StopIteration:
            series_next[col] = None
        series_data[col] = it  # replace pairs list with iterator

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["date"] + col_names)

        for date in master_dates:
            row = [date]
            for col in col_names:
                while series_next[col] is not None and series_next[col][0] <= date:
                    series_current[col] = series_next[col][1]
                    try:
                        series_next[col] = next(series_data[col])
                    except StopIteration:
                        series_next[col] = None
                row.append(series_current[col] if series_current[col] is not None else "")
            writer.writerow(row)

    date_range = f"{master_dates[0]} to {master_dates[-1]}" if master_dates else "N/A"
    print(f"4_merge_macro.py — complete")
    print(f"  Files processed:  {len(series_data)}")
    print(f"  Columns:          {len(col_names)}")
    print(f"  Date range:       {date_range}")
    print(f"  Rows:             {len(master_dates)}")
    if skipped:
        print(f"  Skipped ({len(skipped)}):")
        for s in skipped[:10]:
            print(f"    - {s}")
        if len(skipped) > 10:
            print(f"    ... and {len(skipped) - 10} more")
    print(f"  Output:           {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
