# Phase 1 — data layer sanity report

2026-07-19.  Checked against `all_merged.parquet` (1,664,246 rows × 567 cols).

## §1 Row & symbol reconciliation — ALL PASS

- Row count: 1,664,246 = `tech_daily.csv` → PASS
- Symbols: 313 → PASS
- ETFs: 36/36 present, all with null fundamentals → PASS
- Duplicate (SYMBOL, DATE): 0 → PASS
- DATE format: YYYYMMDD integer, 1986-11-07 → 2026-07-10, all 8-char → PASS

## §2 Per-symbol end-date sanity — PASS

- Modal (common) end date: **2026-07-02** (308/313 symbols)
- 5 symbols extend to **2026-07-10**: COHR, IBM, JPM, PG, CMCSA
  (These had stale truncated data in an earlier export; the replacement
  raw files go 5 trading days further. Not an issue.)
- Zero symbols have truncated data before the modal end date
- 2 newly-listed symbols with short history: SHAZ (150 rows), KVYO (480 rows)

## §3 Price adjustment — ALL ADJUSTED

| Symbol | Split date | Ratio | Pre-split close → split close | Verdict |
|--------|-----------|-------|-------------------------------|---------|
| AAPL | 2020-08-31 (4:1) | 0.967 | $124.81 → $129.04 | ADJUSTED |
| AAPL | 2014-06-09 (7:1) | 0.984 | $23.06 → $23.43 | ADJUSTED |
| NVDA | 2021-07-20 (4:1) | 1.009 | $18.78 → $18.61 | ADJUSTED |
| NVDA | 2024-06-10 (10:1) | 0.993 | $120.89 → $121.79 | ADJUSTED |

All ratios near 1.0 — no split-sized jumps.  Prices are split-adjusted.
Phase 2 label construction is NOT blocked.

## §4 Coverage profile

File: `docs/coverage_by_day.parquet` (9,986 trading days, n_symbols + n_fund per day).
Plot: `docs/coverage_by_day.png`.

### Core study window (2000-07-01 → 2026-07-02)

| Metric | n_symbols | n_with_fundamentals |
|--------|-----------|---------------------|
| Min | 123 | 106 |
| p01 | 134 | 117 |
| p05 | 142 | 125 |
| Median | 217 | 184 |
| Max | 313 | 276 |

### Tail dates excluded (2026-07-06 → 2026-07-10)

These 5 dates have only the 5 extended-export symbols (COHR, IBM, JPM, PG,
CMCSA).  n_symbols = 5, n_fund = 4.  Excluded from the core window above;
the effective common end date is 2026-07-02.

### First dates

- n_symbols ≥ 100: 1997-05-27
- n_fund ≥ 100: 1997-12-09
- (Both comfortably before the 2000-07 study window start)

## §5 min_cross_section recommendation

**Recommend: 100** (matches Plan4 default).

Core window min n_fund = 106, p01 = 117.  100 is safe — zero days cross
below it in the core study window.  No downward adjustment needed.
