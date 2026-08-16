"""
6_merge_aapl.py
===============
Merge all data files into one daily table for AAPL only.

Sources (data/History_6_merge/):
  tech_daily.csv          — spine (SYMBOL == "AAPL"), suffix _D
  tech_weekly.csv         — asof join backward, suffix _W, keep DATE_W
  tech_monthly.csv        — asof join backward, suffix _M, keep DATE_M
  market_merge_daily.csv  — left join on DATE, suffix _MKT
  market_merge_weekly.csv — asof join backward, suffix _MKTW, keep DATE_MKTW
  market_merge_monthly.csv— asof join backward, suffix _MKTM, keep DATE_MKTM
  macro_merge_daily.csv   — left join on DATE (rename 'date'→DATE), suffix _MAC
  History_4_F_clean/AAPL.csv — asof join backward, suffix _F, keep DATE_F
  ETF_real.csv            — left join on SYMBOL, add isETF column

Output: data/History_6_merge/AAPL_merged.parquet
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent.parent / "data" / "History_6_merge"


# ── Helpers ────────────────────────────────────────────────────────────────

def read_csv_sorted(path, check_dupes=True, **kwargs) -> pd.DataFrame:
    """Read CSV, parse dates, sort by DATE, optionally assert no duplicate dates."""
    df = pd.read_csv(path, **kwargs)
    if "DATE" not in df.columns and "date" in df.columns:
        df.rename(columns={"date": "DATE"}, inplace=True)

    # Handle both YYYYMMDD (tech/market) and YYYY-MM-DD (macro) formats
    sample = str(df["DATE"].iloc[0]) if len(df) > 0 else ""
    fmt = "%Y-%m-%d" if "-" in sample else "%Y%m%d"
    df["DATE"] = pd.to_datetime(df["DATE"], format=fmt, errors="coerce")

    assert df["DATE"].notna().all(), f"Null dates in {path}"
    df = df.sort_values("DATE").reset_index(drop=True)
    if check_dupes:
        assert not df["DATE"].duplicated().any(), f"Duplicate dates in {path}"
    return df


def assert_row_count(df: pd.DataFrame, expected: int, label: str):
    if len(df) != expected:
        print(f"ERROR: {label} — expected {expected} rows, got {len(df)}")
        sys.exit(1)


def suffix_columns(df: pd.DataFrame, suffix: str, keep: set = None) -> pd.DataFrame:
    """Add suffix to all columns except DATE and SYMBOL."""
    rename = {}
    for c in df.columns:
        if c in ("DATE", "SYMBOL"):
            continue
        if keep and c in keep:
            continue
        rename[c] = f"{c}{suffix}"
    return df.rename(columns=rename)


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("6_merge_aapl.py — AAPL daily merge")
    print("=" * 60)

    # ── 1. Read spine: tech_daily for AAPL ─────────────────────────────────
    print("\n[1/7] Reading tech_daily (spine)...")
    spine = read_csv_sorted(BASE / "tech_daily.csv", check_dupes=False)
    spine = spine[spine["SYMBOL"] == "AAPL"].copy()
    spine = spine.drop(columns=["SYMBOL"])
    spine = suffix_columns(spine, "_D")
    spine = spine.rename(columns={"DATE_D": "DATE"})  # keep spine date as DATE
    spine = spine.sort_values("DATE").reset_index(drop=True)
    assert not spine["DATE"].duplicated().any(), "Duplicate dates in AAPL spine"

    # Trim spine to min(last AAPL date, last market date, last macro date)
    aapl_last = spine["DATE"].max()
    mkt_last = pd.to_datetime(
        pd.read_csv(BASE / "market_merge_daily.csv", usecols=["DATE"], dtype={"DATE": str})
        ["DATE"].max(), format="%Y%m%d"
    )
    macro_last_raw = pd.read_csv(
        BASE / "macro_merge_daily.csv", usecols=["date"], dtype={"date": str}
    )["date"].max()
    macro_last = pd.to_datetime(macro_last_raw, format="%Y-%m-%d")
    trim_last = min(aapl_last, mkt_last, macro_last)
    spine = spine[spine["DATE"] <= trim_last].copy()
    spine = spine.sort_values("DATE").reset_index(drop=True)
    print(f"  Trimmed spine to {trim_last.date()} (AAPL={aapl_last.date()}, "
          f"MKT={mkt_last.date()}, MAC={macro_last.date()})")

    n_rows = len(spine)
    print(f"  {n_rows} rows, {len(spine.columns)} cols")
    print(f"  Range: {spine['DATE'].iloc[0].date()} → {spine['DATE'].iloc[-1].date()}")

    # ── 2. tech_weekly — asof join ─────────────────────────────────────────
    print("\n[2/7] Joining tech_weekly (asof backward)...")
    weekly = read_csv_sorted(BASE / "tech_weekly.csv", check_dupes=False)
    weekly = weekly[weekly["SYMBOL"] == "AAPL"].copy()
    assert not weekly["DATE"].duplicated().any(), "Duplicate dates in AAPL weekly"
    weekly = weekly.drop(columns=["SYMBOL"])
    weekly = suffix_columns(weekly, "_W", keep={"DATE"})
    weekly = weekly.rename(columns={"DATE": "DATE_W"})
    weekly["DATE_join"] = weekly["DATE_W"]  # merge_asof needs the key column
    weekly = weekly.sort_values("DATE_join").reset_index(drop=True)

    spine = pd.merge_asof(
        spine, weekly,
        left_on="DATE", right_on="DATE_join",
        direction="backward", allow_exact_matches=True,
    )
    spine = spine.drop(columns=["DATE_join"])
    assert_row_count(spine, n_rows, "after tech_weekly join")
    print(f"  {len(spine.columns)} cols total")

    # ── 3. tech_monthly — asof join ────────────────────────────────────────
    print("\n[3/7] Joining tech_monthly (asof backward)...")
    monthly = read_csv_sorted(BASE / "tech_monthly.csv", check_dupes=False)
    monthly = monthly[monthly["SYMBOL"] == "AAPL"].copy()
    assert not monthly["DATE"].duplicated().any(), "Duplicate dates in AAPL monthly"
    monthly = monthly.drop(columns=["SYMBOL"])
    monthly = suffix_columns(monthly, "_M", keep={"DATE"})
    monthly = monthly.rename(columns={"DATE": "DATE_M"})
    monthly["DATE_join"] = monthly["DATE_M"]
    monthly = monthly.sort_values("DATE_join").reset_index(drop=True)

    spine = pd.merge_asof(
        spine, monthly,
        left_on="DATE", right_on="DATE_join",
        direction="backward", allow_exact_matches=True,
    )
    spine = spine.drop(columns=["DATE_join"])
    assert_row_count(spine, n_rows, "after tech_monthly join")
    print(f"  {len(spine.columns)} cols total")

    # ── 4. market_merge_daily — plain left join ────────────────────────────
    print("\n[4/7] Joining market_merge_daily (left join)...")
    mkt_d = read_csv_sorted(BASE / "market_merge_daily.csv")
    mkt_d = suffix_columns(mkt_d, "_MKT")
    mkt_d = mkt_d.rename(columns={"DATE_MKT": "DATE"})  # back to DATE for join

    spine = spine.merge(mkt_d, on="DATE", how="left")
    assert_row_count(spine, n_rows, "after market_merge_daily join")
    print(f"  {len(spine.columns)} cols total")

    # ── 5. market_merge_weekly — asof join ─────────────────────────────────
    print("\n[5/7] Joining market_merge_weekly (asof backward)...")
    mkt_w = read_csv_sorted(BASE / "market_merge_weekly.csv")
    mkt_w = suffix_columns(mkt_w, "_MKTW", keep={"DATE"})
    mkt_w = mkt_w.rename(columns={"DATE": "DATE_MKTW"})
    mkt_w["DATE_join"] = mkt_w["DATE_MKTW"]
    mkt_w = mkt_w.sort_values("DATE_join").reset_index(drop=True)

    spine = pd.merge_asof(
        spine, mkt_w,
        left_on="DATE", right_on="DATE_join",
        direction="backward", allow_exact_matches=True,
    )
    spine = spine.drop(columns=["DATE_join"])
    assert_row_count(spine, n_rows, "after market_merge_weekly join")
    print(f"  {len(spine.columns)} cols total")

    # ── 6. market_merge_monthly — asof join ────────────────────────────────
    print("\n[6/7] Joining market_merge_monthly (asof backward)...")
    mkt_m = read_csv_sorted(BASE / "market_merge_monthly.csv")
    mkt_m = suffix_columns(mkt_m, "_MKTM", keep={"DATE"})
    mkt_m = mkt_m.rename(columns={"DATE": "DATE_MKTM"})
    mkt_m["DATE_join"] = mkt_m["DATE_MKTM"]
    mkt_m = mkt_m.sort_values("DATE_join").reset_index(drop=True)

    spine = pd.merge_asof(
        spine, mkt_m,
        left_on="DATE", right_on="DATE_join",
        direction="backward", allow_exact_matches=True,
    )
    spine = spine.drop(columns=["DATE_join"])
    assert_row_count(spine, n_rows, "after market_merge_monthly join")
    print(f"  {len(spine.columns)} cols total")

    # ── 7. macro_merge_daily — plain left join ────────────────────────────
    print("\n[7/7] Joining macro_merge_daily (left join)...")
    macro = read_csv_sorted(BASE / "macro_merge_daily.csv")
    macro = suffix_columns(macro, "_MAC")
    macro = macro.rename(columns={"DATE_MAC": "DATE"})

    spine = spine.merge(macro, on="DATE", how="left")
    assert_row_count(spine, n_rows, "after macro join")
    print(f"  {len(spine.columns)} cols total")

    # ── 8. fundamentals (History_4_F_clean) — asof join ──────────────────
    print("\n[8/9] Joining fundamentals (asof backward)...")
    fund_path = BASE.parent / "History_4_F_clean/AAPL.csv"  # BASE = History_6_merge, go up one
    fund = read_csv_sorted(fund_path, check_dupes=True)  # per-symbol, dupes should be cleaned
    fund = fund.drop(columns=["SYMBOL"], errors="ignore")
    fund = suffix_columns(fund, "_F", keep={"DATE"})
    fund = fund.rename(columns={"DATE": "DATE_F"})
    fund["DATE_join"] = fund["DATE_F"]
    fund = fund.sort_values("DATE_join").reset_index(drop=True)

    spine = pd.merge_asof(
        spine, fund,
        left_on="DATE", right_on="DATE_join",
        direction="backward", allow_exact_matches=True,
    )
    spine = spine.drop(columns=["DATE_join"])
    assert_row_count(spine, n_rows, "after fundamentals join")
    print(f"  {len(spine.columns)} cols total")

    # ── 9. isETF lookup ──────────────────────────────────────────────────
    print("\n[9/9] Adding isETF from ETF_real.csv...")
    etf_df = pd.read_csv(BASE.parent / "ETF_real.csv", dtype={"symbol": str, "isETF": int})
    etf_val = int(etf_df[etf_df["symbol"] == "AAPL"]["isETF"].values[0]) if "AAPL" in etf_df["symbol"].values else 0
    spine["isETF"] = etf_val
    print(f"  isETF = {etf_val}")

    # ── Final: sort, verify, write ─────────────────────────────────────────
    print("\n" + "=" * 60)
    print("FINAL OUTPUT")
    print("=" * 60)

    spine = spine.sort_values("DATE").reset_index(drop=True)

    # Column counts by suffix
    suffixes = ["_D", "_W", "_M", "_F", "_MKT", "_MKTW", "_MKTM", "_MAC"]
    date_cols = [c for c in spine.columns if c.startswith("DATE_")]
    for s in suffixes + ["date cols"]:
        if s == "date cols":
            count = len(date_cols)
            cols = date_cols
        else:
            cols = [c for c in spine.columns if c.endswith(s) and c != "DATE"]
            count = len(cols)
        print(f"  {s:>8s}: {count:>4}")

    print(f"\n  Total cols:  {len(spine.columns)}")
    print(f"  Total rows:  {len(spine):,}")
    print(f"  Date range:  {spine['DATE'].iloc[0].date()} → {spine['DATE'].iloc[-1].date()}")

    # Check for unexpected nulls in the spine (DATE should never be null)
    assert spine["DATE"].notna().all()

    out = BASE / "AAPL_merged.parquet"
    spine.to_parquet(out, index=False)
    print(f"\n  Output: {out}")


if __name__ == "__main__":
    main()
