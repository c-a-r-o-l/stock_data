"""
merge_market_monthly.py
=======================
Merges daily market data (MKT) with monthly SPY and QQQ technicals on DATE.

Inputs:
  data/History_0_MKT/MKT.txt       — market internals (daily)
  data/History_3_M_clean/SPY.csv   — SPY monthly technicals (cleaned)
  data/History_3_M_clean/QQQ.csv   — QQQ monthly technicals (cleaned)

Output:
  data/History_6_merge/market_merge_monthly.csv
"""

import csv
import importlib
from pathlib import Path

_daily = importlib.import_module("2_merge_market_daily")
SPY_RENAME = _daily.SPY_RENAME
QQQ_RENAME = _daily.QQQ_RENAME
convert_date = _daily.convert_date
load_indexed = _daily.load_indexed
fill_zero = _daily.fill_zero
is_zero = _daily.is_zero


def main():
    project_root = Path(__file__).resolve().parent.parent

    mkt_path = project_root / "data/History_0_MKT/MKT.txt"
    spy_path = project_root / "data/History_3_M_clean/SPY.csv"
    qqq_path = project_root / "data/History_3_M_clean/QQQ.csv"
    out_path = project_root / "data/History_6_merge/market_merge_monthly.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Load SPY and QQQ (monthly)
    spy_data = load_indexed(spy_path, SPY_RENAME)
    qqq_data = load_indexed(qqq_path, QQQ_RENAME)
    spy_cols = list(SPY_RENAME.values())
    qqq_cols = list(QQQ_RENAME.values())
    print(f"SPY (monthly): {len(spy_data)} dates, QQQ (monthly): {len(qqq_data)} dates")

    # Load MKT into lookup by date
    with open(mkt_path, newline="") as f:
        reader = csv.DictReader(f)
        mkt_data_cols = [c for c in reader.fieldnames
                         if c not in ("SYMBOL", "BarNumber", "DATE", "")
                         and c is not None]
        all_cols = ["DATE"] + mkt_data_cols + spy_cols + qqq_cols
        mkt_index = {}
        for row in reader:
            d = convert_date(row.get("DATE", ""))
            mkt_index[d] = {c: row.get(c, "") for c in mkt_data_cols}

    # Get all unique dates from SPY (leading), sorted
    all_dates = sorted(set(spy_data.keys()))

    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=all_cols)
        writer.writeheader()

        written = 0
        started = False
        for d in all_dates:
            out = {"DATE": d}

            mkt_vals = {}
            for c in mkt_data_cols:
                mkt_vals[c] = fill_zero(mkt_index.get(d, {}).get(c, ""))
            for c in spy_cols:
                out[c] = fill_zero(spy_data.get(d, {}).get(c, ""))
            for c in qqq_cols:
                out[c] = fill_zero(qqq_data.get(d, {}).get(c, ""))

            # Strip leading all-zero rows (check MKT columns only)
            if not started:
                if all(is_zero(v) for v in mkt_vals.values()):
                    continue
                started = True

            out.update(mkt_vals)
            writer.writerow(out)
            written += 1

    print(f"Output: {out_path}")
    print(f"Rows: {written:,}  |  Columns: {len(all_cols)}")
    print(f"Range: {all_dates[0]} → {all_dates[-1]}")


if __name__ == "__main__":
    main()
