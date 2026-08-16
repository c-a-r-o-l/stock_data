"""
2_merge_market_monthly.py
=========================
Merges monthly SPY and QQQ technicals on DATE.  No MKT data — market
internals are daily-only and don't make sense at monthly grain.

Inputs:
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


def main():
    project_root = Path(__file__).resolve().parent.parent

    spy_path = project_root / "data/History_3_M_clean/SPY.csv"
    qqq_path = project_root / "data/History_3_M_clean/QQQ.csv"
    out_path = project_root / "data/History_6_merge/market_merge_monthly.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    spy_data = load_indexed(spy_path, SPY_RENAME)
    qqq_data = load_indexed(qqq_path, QQQ_RENAME)
    spy_cols = list(SPY_RENAME.values())
    qqq_cols = list(QQQ_RENAME.values())
    print(f"SPY (monthly): {len(spy_data)} dates, QQQ (monthly): {len(qqq_data)} dates")

    all_cols = ["DATE"] + spy_cols + qqq_cols
    all_dates = sorted(set(spy_data.keys()))

    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=all_cols)
        writer.writeheader()

        written = 0
        for d in all_dates:
            out = {"DATE": d}
            for c in spy_cols:
                out[c] = fill_zero(spy_data.get(d, {}).get(c, ""))
            for c in qqq_cols:
                out[c] = fill_zero(qqq_data.get(d, {}).get(c, ""))
            writer.writerow(out)
            written += 1

    print(f"Output: {out_path}")
    print(f"Rows: {written:,}  |  Columns: {len(all_cols)}")
    print(f"Range: {all_dates[0]} → {all_dates[-1]}")


if __name__ == "__main__":
    main()
