"""
merge_market.py
===============
Merges market data (MKT), SPY technicals, and QQQ technicals on DATE.

Inputs:
  data/History_0_MKT/MKT.txt       — market internals
  data/History_1_D_clean/SPY.csv   — SPY daily technicals (cleaned)
  data/History_1_D_clean/QQQ.csv   — QQQ daily technicals (cleaned)

Output:
  data/History_6_merge/market_merge_daily.csv
"""

import csv
from pathlib import Path

# ── Column mappings ────────────────────────────────────────────────────────
SPY_RENAME = {
    "VOLUME": "MKT_SPY_VOLUME", "OPEN": "MKT_SPY_OPEN", "HIGH": "MKT_SPY_HIGH",
    "LOW": "MKT_SPY_LOW", "CLOSE": "MKT_SPY_CLOSE",
    "SMA_020": "MKT_SPY_SMA_020", "SMA_050": "MKT_SPY_SMA_050", "SMA_200": "MKT_SPY_SMA_200",
    "PFE_010": "MKT_SPY_PFE_010", "PFE_020": "MKT_SPY_PFE_020",
    "Fit": "MKT_SPY_Fit", "Trigger": "MKT_SPY_Trigger", "Itrend": "MKT_SPY_Itrend",
    "STD_20": "MKT_SPY_STD_20", "ATR": "MKT_SPY_ATR", "Trend_PV": "MKT_SPY_Trend_PV",
    "PV_BULL_STEP": "MKT_SPY_PV_BULL_STEP", "PV_BULL_START": "MKT_SPY_PV_BULL_START",
    "PV_BULL_STOP": "MKT_SPY_PV_BULL_STOP", "PV_BULL_CNT": "MKT_SPY_PV_BULL_CNT",
    "PV_BULL_H": "MKT_SPY_PV_BULL_H",
    "PV_BEAR_STEP": "MKT_SPY_PV_BEAR_STEP", "PV_BEAR_START": "MKT_SPY_PV_BEAR_START",
    "PV_BEAR_STOP": "MKT_SPY_PV_BEAR_STOP", "PV_BEAR_CNT": "MKT_SPY_PV_BEAR_CNT",
    "PV_BEAR_L": "MKT_SPY_PV_BEAR_L",
    "Push_Diff": "MKT_SPY_Push_Diff",
    "MACD_C": "MKT_SPY_MACD_C", "MACD_H": "MKT_SPY_MACD_H",
    "MACD_L": "MKT_SPY_MACD_L", "MACD_DIFF": "MKT_SPY_MACD_DIFF",
    "oSlowK": "MKT_SPY_oSlowK", "RSI_03": "MKT_SPY_RSI_03",
}

QQQ_RENAME = {
    "VOLUME": "MKT_QQQ_VOLUME", "OPEN": "MKT_QQQ_OPEN", "HIGH": "MKT_QQQ_HIGH",
    "LOW": "MKT_QQQ_LOW", "CLOSE": "MKT_QQQ_CLOSE",
    "SMA_020": "MKT_QQQ_SMA_020", "SMA_050": "MKT_QQQ_SMA_050", "SMA_200": "MKT_QQQ_SMA_200",
    "SPY_C": "MKT_QQQ_SPY_C", "SPY_020": "MKT_QQQ_SPY_020",
    "SPY_050": "MKT_QQQ_SPY_050", "SPY_200": "MKT_QQQ_SPY_200",
    "PFE_010": "MKT_QQQ_PFE_010", "PFE_020": "MKT_QQQ_PFE_020",
    "Fit": "MKT_QQQ_Fit", "Trigger": "MKT_QQQ_Trigger", "Itrend": "MKT_QQQ_Itrend",
    "Fit_SPY": "MKT_QQQ_Fit_SPY", "Trigger_SPY": "MKT_QQQ_Trigger_SPY",
    "Itrend_SPY": "MKT_QQQ_Itrend_SPY",
    "STD_20": "MKT_QQQ_STD_20", "ATR": "MKT_QQQ_ATR", "Trend_PV": "MKT_QQQ_Trend_PV",
    "PV_BULL_STEP": "MKT_QQQ_PV_BULL_STEP", "PV_BULL_START": "MKT_QQQ_PV_BULL_START",
    "PV_BULL_STOP": "MKT_QQQ_PV_BULL_STOP", "PV_BULL_CNT": "MKT_QQQ_PV_BULL_CNT",
    "PV_BULL_H": "MKT_QQQ_PV_BULL_H",
    "PV_BEAR_STEP": "MKT_QQQ_PV_BEAR_STEP", "PV_BEAR_START": "MKT_QQQ_PV_BEAR_START",
    "PV_BEAR_STOP": "MKT_QQQ_PV_BEAR_STOP", "PV_BEAR_CNT": "MKT_QQQ_PV_BEAR_CNT",
    "PV_BEAR_L": "MKT_QQQ_PV_BEAR_L",
    "Push_Diff": "MKT_QQQ_Push_Diff", "Push_Diff_SPY": "MKT_QQQ_Push_Diff_SPY",
    "MACD_C": "MKT_QQQ_MACD_C", "MACD_H": "MKT_QQQ_MACD_H",
    "MACD_L": "MKT_QQQ_MACD_L", "MACD_DIFF": "MKT_QQQ_MACD_DIFF",
    "oSlowK": "MKT_QQQ_oSlowK", "RSI_03": "MKT_QQQ_RSI_03",
}


def convert_date(raw: str) -> str:
    """Convert date to YYYYMMDD.  Handles both CYYMMDD (e.g. 931116 → 19931116)
    and already-converted YYYYMMDD (passes through unchanged)."""
    s = raw.strip()
    if len(s) == 8 and s.isdigit():
        return s  # already YYYYMMDD
    s = s.zfill(7)
    c = int(s[0]); y = int(s[1:3]); m = int(s[3:5]); d = int(s[5:7])
    return f"{1900 + c * 100 + y:04d}{m:02d}{d:02d}"


def fill_zero(val: str) -> str:
    v = val.strip()
    return v if v != "" else "0"


def is_zero(val: str) -> bool:
    """True if val is numerically zero (handles non-numeric gracefully)."""
    try:
        return float(val.strip()) == 0.0
    except (ValueError, TypeError):
        return False


def load_indexed(path: Path, rename_map: dict) -> dict:
    """Read a file, rename columns, key by converted DATE.  Returns {date: {col: val}}."""
    indexed = {}
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            d = convert_date(row.get("DATE", ""))
            indexed[d] = {new: row.get(old, "") for old, new in rename_map.items()}
    return indexed


def main():
    project_root = Path(__file__).resolve().parent.parent

    mkt_path = project_root / "data/History_0_MKT/MKT.txt"
    spy_path = project_root / "data/History_1_D_clean/SPY.csv"
    qqq_path = project_root / "data/History_1_D_clean/QQQ.csv"
    out_path = project_root / "data/History_6_merge/market_merge_daily.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # ── Load SPY and QQQ into lookup dicts ─────────────────────────────────
    spy_data = load_indexed(spy_path, SPY_RENAME)
    qqq_data = load_indexed(qqq_path, QQQ_RENAME)
    print(f"SPY: {len(spy_data)} dates, QQQ: {len(qqq_data)} dates")

    # ── Read MKT and build merged output ───────────────────────────────────
    spy_cols = list(SPY_RENAME.values())
    qqq_cols = list(QQQ_RENAME.values())

    with open(mkt_path, newline="") as f:
        reader = csv.DictReader(f)
        # Filter out unwanted columns
        mkt_data_cols = [c for c in reader.fieldnames
                         if c not in ("SYMBOL", "BarNumber", "DATE", "")
                         and c is not None]
        all_cols = ["DATE"] + mkt_data_cols + spy_cols + qqq_cols

        rows = list(reader)

    print(f"MKT: {len(rows)} rows, {len(mkt_data_cols)} data columns")

    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=all_cols)
        writer.writeheader()

        written = 0
        started = False
        for row in rows:
            d = convert_date(row.get("DATE", ""))
            out = {"DATE": d}

            # Build MKT data first to check for all-zero
            mkt_vals = {}
            for c in mkt_data_cols:
                mkt_vals[c] = fill_zero(row.get(c, ""))

            # Strip leading all-zero rows (check MKT columns only)
            if not started:
                if all(is_zero(v) for v in mkt_vals.values()):
                    continue
                started = True

            out.update(mkt_vals)
            for c in spy_cols:
                out[c] = fill_zero(spy_data.get(d, {}).get(c, ""))
            for c in qqq_cols:
                out[c] = fill_zero(qqq_data.get(d, {}).get(c, ""))
            writer.writerow(out)
            written += 1

    print(f"Output: {out_path}")
    print(f"Rows: {written:,}  |  Columns: {len(all_cols)}")
    # Read back first/last dates from output for accurate range
    with open(out_path, newline="") as f:
        reader = csv.DictReader(f)
        out_rows = list(reader)
    if out_rows:
        print(f"Range: {out_rows[0]['DATE']} → {out_rows[-1]['DATE']}")


if __name__ == "__main__":
    main()
