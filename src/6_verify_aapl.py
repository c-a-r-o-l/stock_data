"""
6_verify_aapl.py
================
Verify AAPL_merged.parquet against its source CSVs.
Reports PASS/FAIL for each check with specific numbers.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent.parent / "data" / "History_6_merge"
PARQUET = BASE / "AAPL_merged.parquet"

# ── Load merged data ───────────────────────────────────────────────────────
print("=" * 70)
print("LOADING AAPL_merged.parquet ...")
df = pd.read_parquet(PARQUET)
print(f"  {len(df)} rows × {len(df.columns)} cols")
print(f"  {df['DATE'].min().date()} → {df['DATE'].max().date()}")

all_pass = True

def check(label, passed, detail=""):
    global all_pass
    status = "PASS" if passed else "FAIL"
    if not passed:
        all_pass = False
    print(f"[{status}] {label}")
    if detail:
        print(f"       {detail}")


# ── 1. Spine: row count + DATE monotonic ───────────────────────────────────
print("\n" + "=" * 70)
print("1. SPINE CHECKS")

src_daily = pd.read_csv(
    BASE / "tech_daily.csv",
    usecols=["SYMBOL", "DATE"],
    dtype={"DATE": str}
)
aapl_dates = sorted(src_daily[src_daily["SYMBOL"] == "AAPL"]["DATE"].tolist())
n_expected = len(aapl_dates)
check(f"Row count matches AAPL in tech_daily ({n_expected})", len(df) == n_expected,
      f"got {len(df)}")

dates = df["DATE"]
check("DATE unique", dates.is_unique, f"{dates.duplicated().sum()} dupes")
check("DATE strictly increasing", dates.is_monotonic_increasing)


# ── 2. Lookahead: DATE_W <= DATE etc. ──────────────────────────────────────
print("\n" + "=" * 70)
print("2. LOOKAHEAD CHECKS (source date <= spine DATE)")

for col in ["DATE_W", "DATE_M", "DATE_MKTW", "DATE_MKTM"]:
    if col in df.columns:
        violations = (df[col] > df["DATE"]).sum()
        check(f"{col} <= DATE always", violations == 0,
              f"{violations} rows where {col} > DATE" if violations else "")


# ── 3. Cadence: median run length of repeated values ──────────────────────
print("\n" + "=" * 70)
print("3. CADENCE (median run-length of consecutive equal values)")

def cadence(series):
    """Median length of consecutive runs of identical values (ignoring NaN)."""
    s = series.dropna()
    if len(s) < 2:
        return np.nan
    runs = []
    run_len = 1
    for i in range(1, len(s)):
        if s.iloc[i] == s.iloc[i-1]:
            run_len += 1
        else:
            runs.append(run_len)
            run_len = 1
    runs.append(run_len)
    return np.median(runs)

def cadence_summary(df, suffix, expected, group_label, max_show=5):
    """Print median cadence for columns with given suffix, flag outliers."""
    cols = [c for c in df.columns if c.endswith(suffix)]
    results = {}
    for c in cols:
        med = cadence(df[c])
        if not np.isnan(med):
            results[c] = med

    if not results:
        print(f"  {group_label}: no numeric columns")
        return

    medians = list(results.values())
    overall = np.median(medians)
    print(f"  {group_label} ({len(results)} cols): expected ~{expected}, actual median={overall:.1f}")

    # Find off-target
    off = []
    for c, med in results.items():
        if expected == 1:
            if med > 1.5:
                off.append((c, med, med - expected))
        elif expected == 5:
            if abs(med - 5) > 2.5:
                off.append((c, med, med - expected))
        elif expected == 21:
            if abs(med - 21) > 8:
                off.append((c, med, med - expected))

    if off:
        off.sort(key=lambda x: -abs(x[2]))
        print(f"       Most off-target ({min(max_show, len(off))} of {len(off)}):")
        for c, med, diff in off[:max_show]:
            print(f"         {c}: {med:.1f} (diff={diff:+.1f})")


cadence_summary(df, "_D", 1, "_D")
cadence_summary(df, "_W", 5, "_W")
cadence_summary(df, "_MKTW", 5, "_MKTW (market weekly)")
cadence_summary(df, "_M", 21, "_M")
cadence_summary(df, "_MKTM", 21, "_MKTM (market monthly)")
cadence_summary(df, "_MKT", 1, "_MKT")

# _MAC: just report distribution
mac_cols = [c for c in df.columns if c.endswith("_MAC")]
mac_cadences = {}
for c in mac_cols:
    med = cadence(df[c])
    if not np.isnan(med):
        mac_cadences[c] = med

if mac_cadences:
    vals = list(mac_cadences.values())
    print(f"  _MAC ({len(mac_cadences)} cols): median={np.median(vals):.1f}, "
          f"min={min(vals):.0f}, max={max(vals):.0f}, "
          f"~daily={sum(1 for v in vals if v < 2)}, "
          f"~monthly={sum(1 for v in vals if 15 < v < 35)}, "
          f"~quarterly={sum(1 for v in vals if 55 < v < 75)}")


# ── 4. Staleness: DATE - source_date ───────────────────────────────────────
print("\n" + "=" * 70)
print("4. STALENESS (days since last source bar)")

staleness_checks = {
    "DATE - DATE_W":      ("DATE_W",      9),
    "DATE - DATE_MKTW":   ("DATE_MKTW",   9),
    "DATE - DATE_M":      ("DATE_M",     35),
    "DATE - DATE_MKTM":   ("DATE_MKTM",  35),
}

for label, (col, bound) in staleness_checks.items():
    if col not in df.columns:
        check(f"{label} — column not found", False, f"missing {col}")
        continue
    diff = (df["DATE"] - df[col]).dt.days
    max_val = diff.max()
    p99 = diff.quantile(0.99)
    violations = diff[diff > bound]
    n_viol = len(violations)

    detail = f"max={max_val:.0f}d, p99={p99:.0f}d"
    if n_viol > 0:
        detail += f", {n_viol} rows > {bound}d"
        worst = violations.nlargest(3)
        for idx in worst.index:
            detail += f"\n         {df.loc[idx, 'DATE'].date()}: lag={diff.loc[idx]:.0f}d"

    check(f"{label} ≤ {bound}d  (p99={p99:.0f}, max={max_val:.0f})",
          n_viol == 0, detail)


# ── 5. No duplicate column names ──────────────────────────────────────────
print("\n" + "=" * 70)
print("5. DUPLICATE COLUMNS")

dupes = df.columns[df.columns.duplicated()].tolist()
check("No duplicate column names", len(dupes) == 0,
      f"{dupes}" if dupes else "")


# ── 6. Per-column first-valid-date audit ───────────────────────────────────
print("\n" + "=" * 70)
print("6. FIRST-VALID-DATE AUDIT")

def first_valid_date(series):
    """First index where series is not null and not zero-ish (for numeric)."""
    valid = series.notna()
    if pd.api.types.is_numeric_dtype(series):
        valid = valid & (series != 0)
    idx = valid.idxmax() if valid.any() else None
    return idx

def last_null_date(series):
    """Last index where series IS null."""
    nulls = series.isna()
    if not nulls.any():
        return None
    return nulls[nulls].index[-1]

suffix_groups = {
    "_W": "Weekly tech — expect zero leading nulls",
    "_M": "Monthly tech — expect zero leading nulls",
    "_MKT": "Market daily",
    "_MKTW": "Market weekly",
    "_MKTM": "Market monthly",
    "_MAC": "Macro",
}

for suffix, desc in suffix_groups.items():
    cols = [c for c in df.columns if c.endswith(suffix)]
    starts = {}
    late_nulls = []

    for c in cols:
        fv = first_valid_date(df[c])
        if fv is not None:
            starts[c] = fv
            # Check for nulls after first valid date
            after_first = df.loc[fv:, c]
            null_after = after_first.isna().sum()
            if null_after > 0:
                last_null = df.loc[fv:, c][after_first.isna()].index[-1]
                late_nulls.append((c, fv, null_after, df.loc[last_null, "DATE"]))

    if not starts:
        print(f"  {suffix}: no columns found")
        continue

    start_vals = list(starts.values())
    spine_start = df["DATE"].iloc[0]
    print(f"\n  {suffix} ({len(cols)} cols): {desc}")
    print(f"    Earliest start: {df.loc[min(start_vals), 'DATE'].date()}")
    print(f"    Latest start:   {df.loc[max(start_vals), 'DATE'].date()}")

    # Flag any that start at spine_start (meaning no leading nulls)
    at_spine = sum(1 for v in start_vals if v == 0)
    after_spine = sum(1 for v in start_vals if v > 0)
    print(f"    At spine start: {at_spine}, after spine start: {after_spine}")

    if late_nulls:
        print(f"    ⚠ Columns with nulls AFTER first valid ({len(late_nulls)}):")
        for c, fv, n, last_d in late_nulls[:5]:
            print(f"      {c}: first_valid={df.loc[fv,'DATE'].date()}, "
                  f"then {n} nulls, last_null={last_d.date()}")
        check(f"{suffix}: no mid-history null blocks", False,
              f"{len(late_nulls)} columns have mid-history nulls")
    else:
        check(f"{suffix}: no mid-history null blocks", True)


# ── 7. Cross-frequency spot checks ─────────────────────────────────────────
print("\n" + "=" * 70)
print("7. CROSS-FREQUENCY SPOT CHECKS")

# 7a: 5 random months — CLOSE_M should equal CLOSE_D on the month's last trading day
monthly_dates = df["DATE_M"].dropna().unique()
np.random.seed(42)
sample_months = np.random.choice(monthly_dates, min(5, len(monthly_dates)), replace=False)

m_pass = 0
for mdate in sample_months:
    row = df[df["DATE"] == mdate]
    if len(row) == 0:
        continue
    close_d = row["CLOSE_D"].values[0]
    close_m = row["CLOSE_M"].values[0]
    match = abs(close_d - close_m) < 0.01
    if match:
        m_pass += 1
    else:
        print(f"  MONTH {pd.Timestamp(mdate).date()}: CLOSE_D={close_d:.2f}, "
              f"CLOSE_M={close_m:.2f} — MISMATCH")

check(f"Monthly CLOSE_M == daily CLOSE_D on month-end: {m_pass}/5", m_pass == 5)

# 7b: 5 random weeks
weekly_dates = df["DATE_W"].dropna().unique()
sample_weeks = np.random.choice(weekly_dates, min(5, len(weekly_dates)), replace=False)

w_pass = 0
for wdate in sample_weeks:
    row = df[df["DATE"] == wdate]
    if len(row) == 0:
        continue
    close_d = row["CLOSE_D"].values[0]
    close_w = row["CLOSE_W"].values[0]
    match = abs(close_d - close_w) < 0.01
    if match:
        w_pass += 1
    else:
        print(f"  WEEK {pd.Timestamp(wdate).date()}: CLOSE_D={close_d:.2f}, "
              f"CLOSE_W={close_w:.2f} — MISMATCH")

check(f"Weekly CLOSE_W == daily CLOSE_D on week-end: {w_pass}/5", w_pass == 5)


# ── 8. Macro alignment ─────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("8. MACRO ALIGNMENT SPOT CHECK")

# Load original macro
macro_src = pd.read_csv(
    BASE / "macro_merge_daily.csv",
    dtype={"date": str}
)
macro_src["date"] = pd.to_datetime(macro_src["date"], format="%Y-%m-%d")

# Pick 2 columns that have data in the AAPL range
macro_cols = [c for c in df.columns if c.endswith("_MAC")]
# Look for columns with actual data (not all NaN)
valid_macro = []
for c in macro_cols[:20]:
    if df[c].notna().sum() > 1000:
        valid_macro.append(c)

spot_cols = valid_macro[:2] if len(valid_macro) >= 2 else valid_macro
if len(spot_cols) >= 1:
    for mc in spot_cols:
        src_col = mc.replace("_MAC", "")
        if src_col not in macro_src.columns:
            print(f"  {mc}: source column '{src_col}' not found in macro_merge_daily.csv")
            continue

        # Find 5 dates where the value changes in the merged df
        changed = df[mc].dropna()
        if len(changed) < 2:
            continue
        change_mask = changed.diff().abs() > 1e-6
        change_dates = changed.index[change_mask][:5]

        matches = 0
        for idx in change_dates:
            d = df.loc[idx, "DATE"]
            merged_val = df.loc[idx, mc]
            src_row = macro_src[macro_src["date"] == d]
            if len(src_row) > 0:
                src_val = src_row[src_col].values[0]
                try:
                    match = abs(float(merged_val) - float(src_val)) < 1e-4
                except (ValueError, TypeError):
                    match = str(merged_val) == str(src_val)
                if match:
                    matches += 1
                else:
                    print(f"    MISMATCH {d.date()} / {mc}: merged={merged_val}, src={src_val}")

        check(f"{mc}: {matches}/{min(5, len(change_dates))} change-point values match source",
              matches >= min(3, len(change_dates)))


# ── 9. SPY_C formula verification ──────────────────────────────────────
# SPY_C formula (Column_Description.txt line 119):
#   SPY_C = 1,000,000 × stock_close / SPX_index
# SPY ETF ≈ SPX/10, so:  SPY_C ≈ 100,000 × stock_close / SPY_ETF_close
#
# The SPY ETF check is PRIMARY (same-day, ±1.5% for SPY/SPX tracking drift).
# The FRED SP500 macro check is a STALENESS PROBE — the macro series is T+1 aligned
# (release-date convention), so K should deviate by roughly −(day's return) on big-move
# days. A perfect K=1e6 on a ≥0.5% SPY-move day would mean the macro series is
# same-day aligned — which would be a lookahead leak.
print("\n" + "=" * 70)
print("9. SPY_C FORMULA VERIFICATION")
print("   Documented: SPY_C = 1,000,000 × CLOSE / SPX")
print("   Primary:     SPY_C ≈ 100,000 × CLOSE / SPY_ETF  (same-day, ±1.5%)")
print("   Macro probe: SPY_C ≈ 1,000,000 × CLOSE / SPX    (T+1 aligned, expects dips)")

if "CLOSE_D" not in df.columns or "SPY_C_D" not in df.columns:
    check("SPY_C formula: CLOSE_D or SPY_C_D missing", False)
else:
    sp500_col = None
    for c in df.columns:
        if c.endswith("_MAC") and ("SP500" in c or "sp500" in c.lower()):
            sp500_col = c
            break

    spy_close_col = None
    for c in df.columns:
        if "SPY_CLOSE_MKT" in c:
            spy_close_col = c
            break

    np.random.seed(42)

    # ── Primary: against SPY ETF close (same-day, ±1.5%) ────────────────
    if spy_close_col:
        valid = df["SPY_C_D"].notna() & df[spy_close_col].notna() & (df["SPY_C_D"] > 0) & (df[spy_close_col] > 0)
        if valid.sum() >= 10:
            sample = df[valid].sample(min(10, valid.sum()), random_state=42)
            spy_ok = 0; spy_total = 0
            for idx in sample.index:
                cd = df.loc[idx, "CLOSE_D"]
                sc = df.loc[idx, "SPY_C_D"]
                spy = df.loc[idx, spy_close_col]
                K = sc * spy / cd
                pct = abs(K - 100_000) / 100_000 * 100
                ok = pct < 1.5
                spy_total += 1
                if ok: spy_ok += 1
                marker = "✓" if ok else "✗"
                print(f"    {marker} {df.loc[idx,'DATE'].date()}: CLOSE={cd:.2f}, "
                      f"SPY_C={sc:.1f}, SPY_ETF={spy:.1f} → K={K:.0f} ({pct:+.2f}%)")
            if spy_ok == spy_total:
                check(f"Primary (vs SPY ETF): {spy_ok}/{spy_total} within 1.5% of 100,000", True)
            else:
                check(f"Primary (vs SPY ETF): {spy_ok}/{spy_total} within 1.5% of 100,000", False)
        else:
            check("Primary (vs SPY ETF): insufficient data", False)

    # ── Macro staleness probe: K should deviate ≈ −return on big-move days ─
    if sp500_col and spy_close_col:
        valid2 = (df["SPY_C_D"].notna() & df[sp500_col].notna() & df[spy_close_col].notna() &
                  (df["SPY_C_D"] > 0) & (df[sp500_col] > 0) & (df[spy_close_col] > 0))
        if valid2.sum() >= 10:
            # Find big-move days (>|0.5%| SPY return)
            spy_ret = df.loc[valid2, spy_close_col].pct_change().abs()
            big_move_idx = spy_ret[spy_ret > 0.005].index
            if len(big_move_idx) >= 2:
                sample_m = np.random.RandomState(99).choice(big_move_idx, min(5, len(big_move_idx)), replace=False)
                probe_ok = 0; probe_total = 0
                for idx in sorted(sample_m):
                    cd = df.loc[idx, "CLOSE_D"]
                    sc = df.loc[idx, "SPY_C_D"]
                    spx = df.loc[idx, sp500_col]
                    spy_today = df.loc[idx, spy_close_col]
                    spy_prior = df.loc[idx - 1, spy_close_col]  # prior row
                    ret = (spy_today - spy_prior) / spy_prior * 100
                    K_macro = sc * spx / cd
                    pct = (K_macro - 1_000_000) / 1_000_000 * 100
                    # Expected deviation if macro is T+1: K_dev ≈ −return
                    expected = -ret
                    residual = pct - expected
                    ok = abs(residual) < 0.3  # within 0.3pp of expected
                    probe_total += 1
                    if ok: probe_ok += 1
                    marker = "✓" if ok else "✗"
                    print(f"    {marker} {df.loc[idx,'DATE'].date()}: SPY_ret={ret:+.2f}%, "
                          f"K_dev={pct:+.2f}%, expected={expected:+.2f}%, residual={residual:+.2f}pp"
                          f"{' — T+1 alignment confirmed' if ok else ''}")
                if probe_ok >= probe_total * 0.7:
                    check(f"Macro staleness probe: {probe_ok}/{probe_total} big-move days "
                          f"show T+1 alignment (K_dev ≈ −return)", True)
                else:
                    check(f"Macro staleness probe: only {probe_ok}/{probe_total} show "
                          f"T+1 alignment — investigate", False)


# ── Final ──────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
if all_pass:
    print("OVERALL: PASS ✓")
else:
    print("OVERALL: FAIL ✗  (see failures above)")
print("=" * 70)
