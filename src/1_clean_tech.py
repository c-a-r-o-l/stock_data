"""
clean_history.py
================
Cleans raw history .txt files and outputs trimmed .csv files.

Inputs:
  data/History_1_D/*.txt   →  data/History_1_D_clean/*.csv  (daily)
  data/History_2_W/*.txt   →  data/History_2_W_clean/*.csv  (weekly)
  data/History_3_M/*.txt   →  data/History_3_M_clean/*.csv  (monthly)

Cleaning rules (applied in order):
  1. Drop rows where SPY_C == 0
  2. Drop rows where OPEN, HIGH, LOW, or CLOSE <= 0
  3. Drop rows where PV_BULL_CNT == 0 or PV_BEAR_CNT == 0  (raw values, before zeroing)
  4. Drop rows where all MACD columns (MACD_C, MACD_H, MACD_L, MACD_DIFF) are 0
  5. If PV_BULL_STEP == 0, zero out all PV_BULL_* columns
  6. If PV_BEAR_STEP == 0, zero out all PV_BEAR_* columns
  7. Convert DATE from source format (CYYMMDD) to YYYYMMDD
  8. Keep only the columns listed in COLUMNS_DAILY / COLUMNS_WEEKLY / COLUMNS_MONTHLY
  9. Output folder is deleted and recreated before writing
 10. Post-processing: symbols with empty output in ANY frequency are removed from ALL
     three output folders, keeping the datasets perfectly aligned
"""

import csv
import shutil
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Per-filetype column definitions (order as they should appear in output CSV)
# ---------------------------------------------------------------------------

COLUMNS_DAILY = [
    "SYMBOL",
    "DATE",
    "VOLUME",
    "OPEN",
    "HIGH",
    "LOW",
    "CLOSE",
    "SMA_020",
    "SMA_050",
    "SMA_200",
    "SPY_C",
    "SPY_020",
    "SPY_050",
    "SPY_200",
    "PFE_010",
    "PFE_020",
    "Fit",
    "Trigger",
    "Itrend",
    "Fit_SPY",
    "Trigger_SPY",
    "Itrend_SPY",
    "STD_20",
    "ATR",
    "Trend_PV",
    "PV_BULL_STEP",
    "PV_BULL_START",
    "PV_BULL_STOP",
    "PV_BULL_CNT",
    "PV_BULL_H",
    "PV_BEAR_STEP",
    "PV_BEAR_START",
    "PV_BEAR_STOP",
    "PV_BEAR_CNT",
    "PV_BEAR_L",
    "Push_Diff",
    "Push_Diff_SPY",
    "MACD_C",
    "MACD_H",
    "MACD_L",
    "MACD_DIFF",
    "oSlowK",
    "RSI_03",
]

COLUMNS_WEEKLY = [
    "SYMBOL",
    "DATE",
    "VOLUME",
    "OPEN",
    "HIGH",
    "LOW",
    "CLOSE",
    "SMA_020",
    "SMA_050",
    "SPY_C",
    "SPY_020",
    "SPY_050",
    "PFE_010",
    "PFE_020",
    "Fit",
    "Trigger",
    "Itrend",
    "Fit_SPY",
    "Trigger_SPY",
    "Itrend_SPY",
    "STD_20",
    "ATR",
    "Trend_PV",
    "PV_BULL_STEP",
    "PV_BULL_START",
    "PV_BULL_STOP",
    "PV_BULL_CNT",
    "PV_BULL_H",
    "PV_BEAR_STEP",
    "PV_BEAR_START",
    "PV_BEAR_STOP",
    "PV_BEAR_CNT",
    "PV_BEAR_L",
    "Push_Diff",
    "Push_Diff_SPY",
    "MACD_C",
    "MACD_H",
    "MACD_L",
    "MACD_DIFF",
    "oSlowK",
    "RSI_03",
]

COLUMNS_MONTHLY = [
    "SYMBOL",
    "DATE",
    "VOLUME",
    "OPEN",
    "HIGH",
    "LOW",
    "CLOSE",
    "SMA_010",
    "SMA_020",
    "SPY_C",
    "SPY_020",
    "PFE_010",
    "PFE_020",
    "Fit",
    "Trigger",
    "Itrend",
    "Fit_SPY",
    "Trigger_SPY",
    "Itrend_SPY",
    "STD_20",
    "ATR",
    "Trend_PV",
    "PV_BULL_STEP",
    "PV_BULL_START",
    "PV_BULL_STOP",
    "PV_BULL_CNT",
    "PV_BULL_H",
    "PV_BEAR_STEP",
    "PV_BEAR_START",
    "PV_BEAR_STOP",
    "PV_BEAR_CNT",
    "PV_BEAR_L",
    "Push_Diff",
    "Push_Diff_SPY",
    "MACD_C",
    "MACD_H",
    "MACD_L",
    "MACD_DIFF",
    "oSlowK",
    "RSI_03",
]

# ---------------------------------------------------------------------------
# Column groupings for cleaning rules
# ---------------------------------------------------------------------------

OHLC_COLS = {"OPEN", "HIGH", "LOW", "CLOSE"}

PV_BULL_COLS = {"PV_BULL_STEP", "PV_BULL_START", "PV_BULL_STOP",
                "PV_BULL_CNT", "PV_BULL_H"}

PV_BEAR_COLS = {"PV_BEAR_STEP", "PV_BEAR_START", "PV_BEAR_STOP",
                "PV_BEAR_CNT", "PV_BEAR_L"}

MACD_COLS = {"MACD_C", "MACD_H", "MACD_L", "MACD_DIFF"}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def safe_float(value: str) -> float:
    """Convert string to float, returning 0.0 on empty / non-numeric."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def convert_date(raw: str) -> str:
    """Convert source DATE format (CYYMMDD integer) to 'YYYYMMDD' string.

    C = century indicator (0 → 19xx, 1 → 20xx).
    Example: 1180716 → 20180716
    """
    s = raw.strip().zfill(7)        # ensure 7 digits
    century = int(s[0])
    yy = int(s[1:3])
    mm = int(s[3:5])
    dd = int(s[5:7])
    full_year = 1900 + century * 100 + yy
    return f"{full_year:04d}{mm:02d}{dd:02d}"


def clean_file(
    input_path: Path,
    output_path: Path,
    keep_columns: list[str],
) -> tuple[int, int]:
    """Clean a single input .txt file and write a .csv.

    Returns (rows_in, rows_out).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows_in = 0
    rows_out = 0

    with open(input_path, "r", newline="") as fin, \
         open(output_path, "w", newline="") as fout:

        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=keep_columns, extrasaction="ignore")
        writer.writeheader()

        for row in reader:
            rows_in += 1

            # -- Rule 1: drop if SPY_C == 0 -----------------------------------
            if safe_float(row.get("SPY_C", "")) == 0.0:
                continue

            # -- Rule 2: drop if OPEN, HIGH, LOW, or CLOSE <= 0 ---------------
            if any(safe_float(row.get(c, "")) <= 0.0 for c in OHLC_COLS):
                continue

            # -- Rule 6: drop if PV_BULL_CNT == 0 or PV_BEAR_CNT == 0 -----------
            if safe_float(row.get("PV_BULL_CNT", "")) == 0.0:
                continue
            if safe_float(row.get("PV_BEAR_CNT", "")) == 0.0:
                continue

            # -- Rule 7: drop if all MACD columns are 0 -----------------------
            if all(safe_float(row.get(c, "")) == 0.0 for c in MACD_COLS):
                continue

            # -- Rule 3: zero out PV_BULL_* if PV_BULL_STEP == 0 --------------
            if safe_float(row.get("PV_BULL_STEP", "")) == 0.0:
                for c in PV_BULL_COLS:
                    row[c] = "0"

            # -- Rule 4: zero out PV_BEAR_* if PV_BEAR_STEP == 0 --------------
            if safe_float(row.get("PV_BEAR_STEP", "")) == 0.0:
                for c in PV_BEAR_COLS:
                    row[c] = "0"

            # -- Rule 5: convert DATE to YYYYMMDD -----------------------------
            raw_date = row.get("DATE", "")
            row["DATE"] = convert_date(raw_date) if raw_date else ""

            # -- Build output row from keep_columns only ----------------------
            out_row = {col: row.get(col, "") for col in keep_columns}
            writer.writerow(out_row)
            rows_out += 1

    return rows_in, rows_out


# ---------------------------------------------------------------------------
# Pipeline definitions
# ---------------------------------------------------------------------------

PIPELINES = {
    "History_1_D": {
        "input_dir":  "data/History_1_D",
        "output_dir": "data/History_1_D_clean",
        "columns":    COLUMNS_DAILY,
    },
    "History_2_W": {
        "input_dir":  "data/History_2_W",
        "output_dir": "data/History_2_W_clean",
        "columns":    COLUMNS_WEEKLY,
    },
    "History_3_M": {
        "input_dir":  "data/History_3_M",
        "output_dir": "data/History_3_M_clean",
        "columns":    COLUMNS_MONTHLY,
    },
}


def main():
    project_root = Path(__file__).resolve().parent.parent  # src/ → project root

    # Allow overriding project root via CLI arg
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1])

    total_in = 0
    total_out = 0

    for label, cfg in PIPELINES.items():
        input_dir = project_root / cfg["input_dir"]
        output_dir = project_root / cfg["output_dir"]
        columns = cfg["columns"]

        if not input_dir.is_dir():
            print(f"[SKIP] {label}: input dir not found ({input_dir})")
            continue

        # -- Delete output folder before writing ------------------------------
        if output_dir.exists():
            shutil.rmtree(output_dir)
            print(f"[CLEAR] deleted existing {output_dir}")

        txt_files = sorted(input_dir.glob("*.txt"))
        print(f"\n{'='*60}")
        print(f"[{label}]  {len(txt_files)} files  →  {output_dir}")
        print(f"{'='*60}")

        for txt_file in txt_files:
            csv_file = output_dir / f"{txt_file.stem}.csv"
            rows_in, rows_out = clean_file(txt_file, csv_file, columns)
            total_in += rows_in
            total_out += rows_out

            dropped = rows_in - rows_out
            print(f"  {txt_file.name:30s}  in={rows_in:>6}  out={rows_out:>6}  dropped={dropped:>6}")

    print(f"\n{'='*60}")
    print(f"TOTAL  in={total_in}  out={total_out}  dropped={total_in - total_out}")
    print(f"{'='*60}")

    # -- Post-processing: remove symbols with empty output in any frequency -----
    print(f"\n{'='*60}")
    print("[POST] removing symbols with empty output in any frequency")
    print(f"{'='*60}")

    output_dirs = [project_root / cfg["output_dir"] for cfg in PIPELINES.values()]

    # Find symbols that have an empty file (header only) in any output folder
    empty_symbols: set[str] = set()
    for out_dir in output_dirs:
        if not out_dir.is_dir():
            continue
        for csv_file in out_dir.glob("*.csv"):
            lines = csv_file.read_text().strip().split("\n")
            if len(lines) <= 1:
                empty_symbols.add(csv_file.stem)

    if empty_symbols:
        print(f"  Empty files found for {len(empty_symbols)} symbols: {sorted(empty_symbols)}")
        removed = 0
        for sym in sorted(empty_symbols):
            for out_dir in output_dirs:
                f = out_dir / f"{sym}.csv"
                if f.exists():
                    f.unlink()
                    removed += 1
        print(f"  Removed {removed} files across all folders")
        # Count remaining
        for out_dir in output_dirs:
            if out_dir.is_dir():
                print(f"  {out_dir.name}: {len(list(out_dir.glob('*.csv')))} files remaining")
    else:
        print("  No empty files found.")

    print(f"\n{'='*60}")
    print("Done.")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
