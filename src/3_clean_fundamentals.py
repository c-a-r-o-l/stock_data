"""
clean_fundamentals.py
=====================
Cleans History_4_F fundamental data and outputs CSV files to History_4_F_clean.

Cleaning rules:
  1. Keep only symbols present in the 313-symbol clean price set
  2. Convert DATE from CYYMMDD to YYYYMMDD
  3. Drop duplicate DATE rows (keep first)
  4. Strip leading and trailing all-zero rows
  5. Drop MRQ_Net_Interest and TTM_Net_Interest columns
"""

import csv
import shutil
from pathlib import Path

# ── Columns to drop ───────────────────────────────────────────────────────
DROP_COLS = {"MRQ_Net_Interest", "TTM_Net_Interest"}

# ── Helpers ────────────────────────────────────────────────────────────────

def convert_date(raw: str) -> str:
    """Convert CYYMMDD (e.g. 891130) to YYYYMMDD (19891130)."""
    s = raw.strip().zfill(7)
    century = int(s[0])
    yy = int(s[1:3])
    mm = int(s[3:5])
    dd = int(s[5:7])
    full_year = 1900 + century * 100 + yy
    return f"{full_year:04d}{mm:02d}{dd:02d}"


def is_all_zero(row: dict, numeric_cols: list) -> bool:
    """True if every numeric column in the row is zero (or empty)."""
    for c in numeric_cols:
        v = row.get(c, "").strip()
        if v and v not in (".", "-"):
            try:
                if float(v) != 0.0:
                    return False
            except ValueError:
                return False
    return True


def clean_file(input_path: Path, output_path: Path,
               keep_cols: list, numeric_cols: list) -> int:
    """Clean one file.  Returns number of rows written."""
    with open(input_path, "r", newline="") as fin:
        reader = csv.DictReader(fin)
        rows = list(reader)

    if not rows:
        return 0

    # 1. Strip leading / trailing all-zero rows
    start = 0
    while start < len(rows) and is_all_zero(rows[start], numeric_cols):
        start += 1
    end = len(rows) - 1
    while end >= start and is_all_zero(rows[end], numeric_cols):
        end -= 1

    if start > end:
        return 0  # all rows were zero

    rows = rows[start:end + 1]

    # 2. Convert DATE + deduplicate (keep first)
    seen_dates = set()
    deduped = []
    for row in rows:
        raw_date = row.get("DATE", "").strip()
        if not raw_date:
            continue
        new_date = convert_date(raw_date)
        if new_date in seen_dates:
            continue
        seen_dates.add(new_date)
        row["DATE"] = new_date
        deduped.append(row)

    if not deduped:
        return 0

    # 3. Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="") as fout:
        writer = csv.DictWriter(fout, fieldnames=keep_cols, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(deduped)

    return len(deduped)


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    project_root = Path(__file__).resolve().parent.parent

    # Get the 313 symbols from the clean daily price data
    clean_syms = {f.stem for f in
                  (project_root / "data/History_1_D_clean").glob("*.csv")}
    print(f"Clean symbol set: {len(clean_syms)} symbols")

    input_dir = project_root / "data/History_4_F"
    output_dir = project_root / "data/History_4_F_clean"

    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Determine output columns (all input columns minus DROP_COLS)
    with open(input_dir / "AAPL.txt") as f:
        all_cols = f.readline().strip().split(",")
    keep_cols = [c for c in all_cols if c not in DROP_COLS]
    numeric_cols = [c for c in keep_cols if c not in ("SYMBOL", "DATE")]
    dropped_cols = [c for c in all_cols if c in DROP_COLS]
    print(f"Columns: {len(all_cols)} total, dropping {dropped_cols}, keeping {len(keep_cols)}")
    print(f"Output: {output_dir}")

    txt_files = sorted(input_dir.glob("*.txt"))
    total_in = 0
    total_out = 0
    skipped = 0
    empty_after = 0

    for txt_file in txt_files:
        sym = txt_file.stem

        if sym not in clean_syms:
            skipped += 1
            continue

        csv_file = output_dir / f"{sym}.csv"
        rows_in = sum(1 for _ in open(txt_file)) - 1  # minus header

        rows_out = clean_file(txt_file, csv_file, keep_cols, numeric_cols)
        total_in += rows_in
        total_out += rows_out

        if rows_out == 0:
            empty_after += 1

    print(f"\n{'='*50}")
    print(f"Processed:  {len(txt_files)} input files")
    print(f"Skipped (not in 313 set): {skipped}")
    print(f"Kept:       {len(txt_files) - skipped} symbols")
    print(f"Empty after cleaning:     {empty_after}")
    print(f"Rows in:    {total_in:,}")
    print(f"Rows out:   {total_out:,}")
    print(f"Dropped:    {total_in - total_out:,}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
