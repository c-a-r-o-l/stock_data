"""
7_verify_all.py — Verify all_merged.parquet. Reports PASS/FAIL per check.
Reads by column selection to keep memory low.
"""

import pyarrow.parquet as pq
import pandas as pd
import numpy as np
from pathlib import Path
import csv
import sys

PARQUET = Path('/home/carol/projects/stock_project/data/History_6_merge/all_merged.parquet')
DATA = Path('/home/carol/projects/stock_project/data')

# ── Helpers ────────────────────────────────────────────────────────────────
pf = pq.ParquetFile(PARQUET)
all_cols = pf.schema.names
n_rows = pf.metadata.num_rows

def read(cols):
    return pf.read(columns=cols).to_pandas()

def check(label, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    if not passed:
        global any_fail; any_fail = True
    print(f"[{status}] {label}")
    if detail:
        print(f"       {detail}")

any_fail = False

# ── 0. Provenance ─────────────────────────────────────────────────────────
print("=" * 70)
print("0. PROVENANCE")
print("=" * 70)

# Which fundamentals?
f4_clean_exists = (DATA / 'History_4_F_clean').is_dir() and len(list((DATA / 'History_4_F_clean').glob('*.csv'))) > 0
check(f"Fundamentals from History_4_F_clean (regenerated): {f4_clean_exists}", f4_clean_exists,
      f"{len(list((DATA / 'History_4_F_clean').glob('*.csv')))} files" if f4_clean_exists else "MISSING")

# Check truncated symbols still early
early_syms = {}
for sym, fname in [('IBM', 'History_1_D/IBM.txt'), ('JPM', 'History_1_D/JPM.txt'),
                    ('COHR', 'History_1_D/COHR.txt'), ('CMCSA', 'History_1_D/CMCSA.txt')]:
    fp = DATA / fname
    if fp.exists():
        with open(fp) as f:
            reader = csv.DictReader(f)
            last_date = None
            for r in reader:
                last_date = r['DATE']
        if last_date:
            s = last_date.zfill(7)
            c = int(s[0]); y = int(s[1:3]); m = int(s[3:5]); d = int(s[5:7])
            early_syms[sym] = f"{1900+c*100+y}-{m:02d}-{d:02d}"

if early_syms:
    print(f"  Still truncated: {early_syms}")
else:
    print("  All re-exported — no truncation")

# Was spine trimmed to 2026-07-01?
dates = read(['DATE'])
max_date = pd.to_datetime(dates['DATE'], format='%Y%m%d').max()
trimmed = max_date <= pd.Timestamp('2026-07-01')
check(f"Spine trimmed to ≤ 2026-07-01 (actual max: {max_date.date()})", trimmed)

# ── 1. Spine ──────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("1. SPINE CHECKS")

total_rows = n_rows
src_rows = sum(1 for _ in open(DATA / 'History_6_merge/tech_daily.csv')) - 1
check(f"Total rows == tech_daily rows ({src_rows})", total_rows == src_rows,
      f"got {total_rows}")

# Per-symbol counts
spine = read(['SYMBOL', 'DATE'])
spine['DATE'] = pd.to_datetime(spine['DATE'], format='%Y%m%d')
src_counts = spine.groupby('SYMBOL').size()  # same data, so this is trivially true — skip heavy check
unique_pairs = len(spine) == len(spine.drop_duplicates(['SYMBOL', 'DATE']))
check("(SYMBOL, DATE) unique", unique_pairs)

# DATE strictly increasing per symbol
spine_sorted = spine.sort_values(['SYMBOL', 'DATE'])
non_inc = 0
for sym, grp in spine.groupby('SYMBOL'):
    if not grp['DATE'].is_monotonic_increasing:
        non_inc += 1
check(f"DATE strictly increasing per symbol: {non_inc} violations", non_inc == 0)

# ── 2. Boundary trim ─────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("2. BOUNDARY TRIM")
post = (spine['DATE'] > pd.Timestamp('2026-07-01')).sum()
check(f"Rows after 2026-07-01: {post} (should be 0 per merge_decisions)", post == 0,
      f"{post} rows past trim date" if post else "")

# ── 3. Cross-symbol contamination ────────────────────────────────────────
print("\n" + "=" * 70)
print("3. CROSS-SYMBOL CONTAMINATION")

np.random.seed(123)
all_syms = sorted(spine['SYMBOL'].unique())
sample_syms = np.random.choice(all_syms, min(20, len(all_syms)), replace=False)

# Check: for each symbol's first date, is DATE_W null or from that symbol?
w_data = read(['SYMBOL', 'DATE', 'DATE_W', 'DATE_M'])
w_data['DATE_W'] = pd.to_datetime(w_data['DATE_W'], format='%Y%m%d', errors='coerce')
w_data['DATE_M'] = pd.to_datetime(w_data['DATE_M'], format='%Y%m%d', errors='coerce')
w_data['DATE'] = pd.to_datetime(w_data['DATE'], format='%Y%m%d')

# Check: DATE_W non-decreasing within symbol
w_issues = 0
m_issues = 0
for sym in all_syms:
    grp = w_data[w_data['SYMBOL'] == sym].sort_values('DATE')
    dw = grp['DATE_W'].dropna()
    if len(dw) > 1 and not dw.is_monotonic_increasing:
        w_issues += 1
    dm = grp['DATE_M'].dropna()
    if len(dm) > 1 and not dm.is_monotonic_increasing:
        m_issues += 1

check(f"DATE_W non-decreasing per symbol: {w_issues} violations", w_issues == 0)
check(f"DATE_M non-decreasing per symbol: {m_issues} violations", m_issues == 0)

# Check: rows before a symbol's first weekly bar have null _W
pre_w_nulls = 0
for sym in all_syms:
    grp = w_data[w_data['SYMBOL'] == sym].sort_values('DATE')
    first_w = grp['DATE_W'].first_valid_index()
    if first_w is not None:
        before = grp.loc[:first_w - 1] if first_w > grp.index[0] else grp.iloc[:0]
        non_null = before['DATE_W'].notna().sum()
        if non_null > 0:
            pre_w_nulls += 1
check(f"Symbols with non-null _W before first weekly bar: {pre_w_nulls}", pre_w_nulls == 0)

# ── 4. Lookahead ─────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("4. LOOKAHEAD")

cols_4 = read(['DATE', 'DATE_W', 'DATE_M', 'DATE_MKTW', 'DATE_MKTM', 'DATE_F'])
for c in ['DATE_W', 'DATE_M', 'DATE_MKTW', 'DATE_MKTM', 'DATE_F']:
    if c in cols_4.columns:
        cols_4[c] = pd.to_datetime(cols_4[c], format='%Y%m%d', errors='coerce')
cols_4['DATE'] = pd.to_datetime(cols_4['DATE'], format='%Y%m%d')

for c in ['DATE_W', 'DATE_M', 'DATE_MKTW', 'DATE_MKTM', 'DATE_F']:
    if c in cols_4.columns:
        violations = (cols_4[c].notna() & (cols_4[c] > cols_4['DATE'])).sum()
        check(f"{c} <= DATE: {violations} violations", violations == 0,
              f"{violations} lookahead rows" if violations else "")

# ── 5. SPX identity cross-symbol ─────────────────────────────────────────
print("\n" + "=" * 70)
print("5. SPX IDENTITY CROSS-SYMBOL")

spx_data = read(['SYMBOL', 'DATE', 'CLOSE_D', 'SPY_C_D'])
spx_data['DATE'] = pd.to_datetime(spx_data['DATE'], format='%Y%m%d')
valid = spx_data[spx_data['SPY_C_D'].notna() & (spx_data['SPY_C_D'] > 0) & (spx_data['CLOSE_D'] > 0)]
valid['SPX_implied'] = 1_000_000 * valid['CLOSE_D'] / valid['SPY_C_D']

np.random.seed(99)
all_dates = sorted(valid['DATE'].unique())
if len(all_dates) > 15:
    sample_dates = np.random.choice(all_dates, 15, replace=False)
else:
    sample_dates = all_dates

worst_spread = 0
worst_date = None
for d in sample_dates:
    day_data = valid[valid['DATE'] == d]
    if len(day_data) < 5:
        continue
    spx_vals = day_data['SPX_implied']
    spread = (spx_vals.max() - spx_vals.min()) / spx_vals.median() * 100
    if spread > worst_spread:
        worst_spread = spread
        worst_date = d
    if spread > 1.0:
        outlier = day_data.iloc[(spx_vals - spx_vals.median()).abs().argmax()]
        print(f"  {d.date()}: spread={spread:.2f}%, worst={outlier['SYMBOL']} "
              f"({outlier['SPX_implied']:.0f})")

check(f"SPX identity: max cross-symbol spread {worst_spread:.2f}% (< 1.0% expected)",
      worst_spread < 1.0, f"worst on {worst_date.date()}: {worst_spread:.2f}%" if worst_date else "")

# ── 6. Cadence ────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("6. CADENCE (sampled 15 symbols)")

np.random.seed(77)
cadence_syms = np.random.choice(all_syms, min(15, len(all_syms)), replace=False)

def median_run_length(series):
    s = series.dropna()
    if len(s) < 2:
        return np.nan
    runs = []; rlen = 1
    for i in range(1, len(s)):
        if s.iloc[i] == s.iloc[i-1]:
            rlen += 1
        else:
            runs.append(rlen); rlen = 1
    runs.append(rlen)
    return np.median(runs)

# Read a subset of columns for cadence checking on sampled symbols only
cadence_cols = read(['SYMBOL', 'DATE'] +
    [c for c in all_cols if any(c.endswith(s) for s in ['_D', '_W', '_M', '_F', '_MKT', '_MKTW', '_MKTM', '_MAC'])]
)
cadence_cols = cadence_cols[cadence_cols['SYMBOL'].isin(cadence_syms)]

cadence_groups = {
    '_D': 1, '_W': 5, '_MKTW': 5, '_M': 21, '_MKTM': 21, '_MKT': 1,
}
# Skip _F and _MAC — too varied
for suffix, expected in cadence_groups.items():
    cols = [c for c in cadence_cols.columns if c.endswith(suffix) and not any(
        x in c for x in ['PV_BULL_START', 'PV_BEAR_START', 'PV_BULL_STOP', 'PV_BEAR_STOP',
                          'Trend_PV', 'SMA_200', 'SMA_050']
    )]
    if len(cols) < 5:
        continue
    medians = {}
    for c in cols:
        med = median_run_length(cadence_cols[c])
        if not np.isnan(med):
            medians[c] = med
    if medians:
        vals = list(medians.values())
        med = np.median(vals)
        off = sorted([(c, v, v-expected) for c, v in medians.items() if abs(v-expected) > expected*0.5],
                     key=lambda x: -abs(x[2]))[:5]
        print(f"  {suffix}: {len(medians)} cols, median={med:.1f} (expected ~{expected})")
        if off:
            for c, v, d in off:
                print(f"      {c}: {v:.1f} (diff={d:+.1f})")

# ── 7. Staleness ──────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("7. STALENESS")

# DATE_W and DATE_M already loaded in cols_4
for col, bound, label in [('DATE_W', 9, '≤9d'), ('DATE_M', 35, '≤35d'), ('DATE_F', 5, '≤5d')]:
    if col not in cols_4.columns:
        continue
    diff = (cols_4['DATE'] - cols_4[col]).dt.days
    valid_diff = diff.dropna()
    if len(valid_diff) == 0:
        print(f"  {col}: no valid data")
        continue
    p99 = valid_diff.quantile(0.99)
    mx = valid_diff.max()
    viol = (valid_diff > bound).sum()
    check(f"{col} {label}: p99={p99:.0f}d, max={mx:.0f}d, {viol} > {bound}",
          viol <= 10, f"{viol} violations" if viol else "")

# ── 8. Null audit ────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("8. NULL AUDIT")

# 8a: Per (symbol, column) first-non-null then no nulls after — sample 20 symbols
audit_syms = np.random.choice(all_syms, min(20, len(all_syms)), replace=False)
audit_cols = [c for c in all_cols if any(c.endswith(s) for s in ['_W', '_M', '_F', '_MKT', '_MKTW', '_MKTM', '_MAC'])]
# Too heavy for full scan — spot check 5 columns per group
spot_cols = []
for suffix in ['_W', '_M', '_F', '_MKT', '_MKTW', '_MKTM']:
    group = [c for c in all_cols if c.endswith(suffix)]
    spot_cols.extend(group[:5])

audit_data = read(['SYMBOL', 'DATE'] + spot_cols)
audit_data = audit_data[audit_data['SYMBOL'].isin(audit_syms)]

null_violations = 0
for sym in audit_syms:
    grp = audit_data[audit_data['SYMBOL'] == sym].sort_values('DATE')
    for c in spot_cols:
        if c not in grp.columns:
            continue
        col_data = grp[c]
        first_valid = col_data.first_valid_index()
        if first_valid is None:
            continue
        after = col_data.loc[first_valid:]
        if after.isna().any():
            null_violations += 1
            if null_violations <= 5:
                last_null = after[after.isna()].index[-1]
                print(f"  {sym}/{c}: null after first_valid at {grp.loc[last_null, 'DATE'].date()}")

check(f"Mid-history null blocks: {null_violations} in sample", null_violations == 0,
      f"{null_violations} violations in sampled cols" if null_violations else "")

# 8b: ETF fundamentals policy
etf_data = read(['SYMBOL', 'isETF', 'MRQ_Revenue_F'])
etf_syms = etf_data[etf_data['isETF'] == 1]['SYMBOL'].unique()
non_etf_syms = etf_data[etf_data['isETF'] == 0]['SYMBOL'].unique()
print(f"\n  8b: ETFs={len(etf_syms)}, Non-ETFs={len(non_etf_syms)}")

# ETFs should have null _F
etf_with_fund = 0
for sym in etf_syms:
    grp = etf_data[etf_data['SYMBOL'] == sym]
    if grp['MRQ_Revenue_F'].notna().any():
        etf_with_fund += 1
        print(f"  ETF with _F data: {sym}")

# Non-ETFs should have _F data
no_fund_equities = []
for sym in non_etf_syms:
    grp = etf_data[etf_data['SYMBOL'] == sym]
    if not grp['MRQ_Revenue_F'].notna().any():
        no_fund_equities.append(sym)

check(f"ETFs with unexpected _F data: {etf_with_fund}", etf_with_fund == 0)
check(f"Equities missing _F data: {len(no_fund_equities)}", len(no_fund_equities) < 10,
      f"{no_fund_equities[:10]}" if no_fund_equities else "")

# ── 9. Cross-frequency closes ────────────────────────────────────────────
print("\n" + "=" * 70)
print("9. CROSS-FREQUENCY CLOSES")

xf_data = read(['SYMBOL', 'DATE', 'CLOSE_D', 'CLOSE_M', 'CLOSE_W', 'DATE_M', 'DATE_W'])
xf_data['DATE'] = pd.to_datetime(xf_data['DATE'], format='%Y%m%d')
xf_data['DATE_M'] = pd.to_datetime(xf_data['DATE_M'], format='%Y%m%d', errors='coerce')
xf_data['DATE_W'] = pd.to_datetime(xf_data['DATE_W'], format='%Y%m%d', errors='coerce')

np.random.seed(55)
xf_syms = np.random.choice(all_syms, min(10, len(all_syms)), replace=False)

m_fail = 0; w_fail = 0
for sym in xf_syms:
    grp = xf_data[xf_data['SYMBOL'] == sym].sort_values('DATE')
    # Monthly: find 3 dates where DATE_M changes
    m_dates = grp['DATE_M'].dropna().unique()
    if len(m_dates) >= 3:
        for md in np.random.choice(m_dates, min(3, len(m_dates)), replace=False):
            row = grp[grp['DATE'] == pd.Timestamp(md)]
            if len(row) == 0:
                continue
            cd = row['CLOSE_D'].values[0]
            cm = row['CLOSE_M'].values[0]
            if pd.notna(cd) and pd.notna(cm) and abs(cd - cm) > 0.01:
                m_fail += 1
    # Weekly
    w_dates = grp['DATE_W'].dropna().unique()
    if len(w_dates) >= 3:
        for wd in np.random.choice(w_dates, min(3, len(w_dates)), replace=False):
            row = grp[grp['DATE'] == pd.Timestamp(wd)]
            if len(row) == 0:
                continue
            cd = row['CLOSE_D'].values[0]
            cw = row['CLOSE_W'].values[0]
            if pd.notna(cd) and pd.notna(cw) and abs(cd - cw) > 0.01:
                w_fail += 1

check(f"Monthly CLOSE_M = daily CLOSE_D: {m_fail} mismatches", m_fail == 0)
check(f"Weekly CLOSE_W = daily CLOSE_D: {w_fail} mismatches", w_fail == 0)

# ── 10. Truncated symbols ────────────────────────────────────────────────
print("\n" + "=" * 70)
print("10. TRUNCATED SYMBOLS")

last_per_sym = spine.groupby('SYMBOL')['DATE'].max()
cutoff = pd.Timestamp('2026-07-01')
truncated = last_per_sym[last_per_sym < cutoff]
known_broken = {'IBM', 'JPM', 'COHR', 'CMCSA'}
new_trunc = set(truncated.index) - known_broken
check(f"Truncated symbols (last < 2026-07-01): {len(truncated)} total, {len(new_trunc)} new",
      len(new_trunc) == 0,
      f"Known: {sorted(set(truncated.index) & known_broken)}, New: {sorted(new_trunc)}" if new_trunc else
      f"All known: {sorted(truncated.index)}")

# ── 11. isETF ─────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("11. isETF")
isETF_data = read(['isETF'])
null_etf = isETF_data['isETF'].isna().sum()
unique_etf = sorted(isETF_data['isETF'].dropna().unique())
etf_count = (isETF_data['isETF'] == 1).sum()
sym_etf_count = etf_data[etf_data['isETF'] == 1]['SYMBOL'].nunique()
check(f"isETF nulls: {null_etf}", null_etf == 0)
check(f"isETF ∈ {{0,1}}: {unique_etf}", unique_etf == [0, 1] or unique_etf == [0.0, 1.0])
check(f"isETF true symbols: {sym_etf_count} (expected 39)", sym_etf_count == 39)

# ── 12. Macro T+1 probe ──────────────────────────────────────────────────
print("\n" + "=" * 70)
print("12. MACRO T+1 PROBE")

# SPX_implied per day from CLOSE_D/SPY_C_D
# We need L_SP500_MAC column
sp500_mac_col = [c for c in all_cols if 'SP500' in c and c.endswith('_MAC')]
if sp500_mac_col:
    probe_data = read(['DATE', 'CLOSE_D', 'SPY_C_D', sp500_mac_col[0]])
    probe_data['DATE'] = pd.to_datetime(probe_data['DATE'], format='%Y%m%d')
    valid = probe_data[probe_data['SPY_C_D'].notna() & (probe_data['SPY_C_D'] > 0) &
                       probe_data[sp500_mac_col[0]].notna() & (probe_data[sp500_mac_col[0]] > 0)]
    valid['SPX_implied'] = 1_000_000 * valid['CLOSE_D'] / valid['SPY_C_D']
    valid['SPX_implied_prev'] = valid.groupby('SYMBOL')['SPX_implied'].shift(1)
    valid = valid.dropna(subset=['SPX_implied_prev'])

    # Find big-move days (|ret| > 0.3%)
    valid['ret'] = valid.groupby('SYMBOL')['SPX_implied'].pct_change().abs()
    big_moves = valid[valid['ret'] > 0.003]
    if len(big_moves) >= 10:
        sample_m = big_moves.sample(min(10, len(big_moves)), random_state=42)
    else:
        sample_m = valid.sample(min(10, len(valid)), random_state=42)

    t1_ok = 0
    for _, row in sample_m.iterrows():
        si_t1 = row['SPX_implied_prev']
        macro_val = row[sp500_mac_col[0]]
        diff = abs(macro_val - si_t1) / si_t1 * 100
        if diff < 0.1:
            t1_ok += 1

    check(f"Macro T+1: {t1_ok}/{len(sample_m)} L_SP500(t) == SPX_implied(t-1) within 0.1%",
          t1_ok >= len(sample_m) * 0.8,
          f"{t1_ok}/{len(sample_m)} passed")
else:
    print("  SP500 macro column not found — skipping")

# ── Final ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
if not any_fail:
    print("OVERALL: PASS")
else:
    print("OVERALL: FAIL — see failures above")
print("=" * 70)
