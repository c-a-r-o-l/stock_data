# Data Inventory — Stock Project

Current as of 2026-07-29.  Total: ~3.3 GB across 17 folders, 3,400+ files.

---

## Folder Map

```
data/
├── History_0_MKT/              Market internals — 1 daily file
├── History_1_D/                Raw daily technical — 329 files (119 cols, CYYMMDD dates)
├── History_1_D_clean/          Clean daily technical — 313 files (43 cols, YYYYMMDD)
├── History_2_W/                Raw weekly technical — 332 files (101 cols, CYYMMDD)
├── History_2_W_clean/          Clean weekly technical — 313 files (41 cols, YYYYMMDD)
├── History_3_M/                Raw monthly technical — 332 files (81 cols, CYYMMDD)
├── History_3_M_clean/          Clean monthly technical — 313 files (40 cols, YYYYMMDD)
├── History_4_E_Alfred/         FRED/ALFRED raw downloads — 140 files
├── History_4_E_Alfred_Release/ FRED with computed release dates — 140 files
├── History_4_F/                Raw quarterly fundamentals — 361 files (46 cols)
├── History_4_F_2/              Expanded fundamentals — 624 files (47 cols)
├── History_4_F_Dividend/       Dividend schedule — 569 files (3 cols, daily)
├── History_4_F_Dividend_Correct/ Fundamentals + dividend corrections — 624 files (51 cols)
├── History_4_F_clean/          Cleaned quarterly fundamentals — 277 files (46 cols, YYYYMMDD)
├── History_6_merge/            Final merged outputs — CSVs + parquets + JSON model
├── ETF_real.csv                ETF flag for all 359 History symbols (from gold ETF.csv)
├── ETF.csv                     Gold-standard ETF classifications (5,994 symbols)
├── _ALFRED_MANIFEST.csv        Master index of 140 FRED macro series
└── DATA_INVENTORY.md           This file
```

---

## 1. History_0_MKT — Market Internals

| | |
|---|---|
| **Files** | 1 (`MKT.txt`) |
| **Rows** | 8,208 |
| **Columns** | 44 (1 blank header at position 43 — trailing comma) |
| **Date range** | 1993-11-15 → 2026-07-01 (CYYMMDD) |
| **Content** | Growth-vs-Value ratios, VIX term structure, breadth indicators for SPY/QQQ/RSL/NYSE |

⚠ **Known issue:** Column 43 is a trailing empty column from a trailing comma in the CSV header. Handled by all merge scripts (filtered out).

---

## 2. History_1_D, History_2_W, History_3_M — Raw Technical Data

One `.txt` file per symbol, CSV-format, CYYMMDD dates. Each folder also contains `SPY.txt` and `QQQ.txt` benchmark files.

| | Daily (1_D) | Weekly (2_W) | Monthly (3_M) |
|---|---|---|---|
| **Files** | 329 | 332 | 332 |
| **Columns** | 119 | 101 | 81 |
| **Est. total rows** | ~1.83M | ~419K | ~102K |
| **Row range** | 2 (FIGR) → 10,001 (AAPL) | 1 (ALAB) → 2,853 (ADM) | 1 (ALAB) → 674 (ADM) |
| **Most common start** | 1997-04-21 (22 files) | 1971-10-29 (25 files) | 1970-05-29 (25 files) |
| **Most common end** | 2026-07-02 (196 files) | 2026-06-26 (190 files) | 2026-06-30 (193 files) |

⚠ **Trailing blank headers:** Weekly has 1 blank column (position 100), Monthly has 1 blank column (position 80). Both from trailing commas.

⚠ **Single-row files (weekly/monthly):** ALAB (1 row) — these are new listings with insufficient history.

---

## 3. History_1_D_clean / History_2_W_clean / History_3_M_clean — Cleaned Technical

Processed by `src/1_clean_tech.py`. All 313 files per folder, perfectly aligned across frequencies. YYYYMMDD dates, curated column subsets. Each contains `SPY.csv` and `QQQ.csv`.

| | Daily | Weekly | Monthly |
|---|---|---|---|
| **Files** | 313 | 313 | 313 |
| **Columns** | 43 | 41 | 40 |
| **Est. total rows** | ~1.77M | ~401K | ~95K |
| **Row range** | 480 (KVYO) → 9,981 (ADM) | 20 (LUNR) → 2,851 (CAT) | 5 (APP) → 672 (MRK) |
| **Most common end** | 2026-07-02 (197) | 2026-06-26 (200) | 2026-06-30 (200) |

---

## 4. History_4_E_Alfred — FRED/ALFRED Raw Downloads

| | |
|---|---|
| **Files** | 140 (matching _ALFRED_MANIFEST.csv) |
| **Formats** | 2-column (`observation_date,value`) for single-revision; 5-column for multi-revision timeline |
| **Est. total rows** | ~910K |
| **Row range** | 205 → 100,000 (NFCI leverage, 348 revision levels) |

⚠ **Not for direct use** — raw ALFRED vintages bunch all pre-2016 release dates at 2016-01-01. Use History_4_E_Alfred_Release instead.

---

## 5. History_4_E_Alfred_Release — FRED With Release Dates

| | |
|---|---|
| **Files** | 140 |
| **Formats** | Single-revision: `observation_date, value, release_date`; Multi-revision: `observation_date, revision_rank, revision_name, value, released_on` |
| **Est. total rows** | ~910K |

**Release dates are calculated** (observation_date + period length + documented delay from _ALFRED_MANIFEST.csv). T+1 for daily series, W+1 for weekly, M+1~2 for monthly, etc. These are approximate but span the full history (1919–2026), unlike the raw ALFRED vintages.

⚠ **Calendar grid artifact:** `macro_merge_daily.csv` is a CALENDAR daily grid (Mon–Sun, 39K rows), not trading-day grid. When joined to trading-day data, weekend/holiday dates drop naturally, and forward-fill across non-trading days is harmless. The SP500 series is T+1 aligned — confirmed by direct probe (see merge_decisions.md).

---

## 6. History_4_F — Raw Quarterly Fundamentals

| | |
|---|---|
| **Files** | 361 (CSV format, CYYMMDD dates, 46 columns) |
| **Est. total rows** | ~1.93M |
| **Row range** | 195 (FIGR) → 8,014 (ADI) |
| **Most common start** | 1994-09-20 (62 files) |
| **Most common end** | 2026-07-09 (200 files) |

**Columns (46):** SYMBOL, DATE, 19 MRQ_* (Most Recent Quarter), 19 TTM_* (Trailing Twelve Months), PE, ROE, LT_DE, EPS_Growth, Revenue_Growth

**Release alignment:** T+1 or T+2 from actual earnings announcement date. Confirmed for AAPL (12 quarters), WMT (2 quarters), JPM (2 quarters). No month-end batch stamping — this is the *replaced* data (post-2026-07-09 export).

**Coverage vs. clean tech:** 277 of 313 symbols overlap. The 36 missing are all ETFs (SPY, QQQ, IWM, GLD, sector ETFs, etc.) — expected, ETFs don't report quarterly fundamentals.

⚠ **84 extra symbols** not in the 313 clean tech set — stocks filtered during cleaning or excluded from the final universe.

⚠ **Bank P&L structure:** Banks (JPM, BAC, C, WFC, etc.) have zero MRQ_Revenue, MRQ_Gross_Profit, MRQ_Operating_Income. Use MRQ_Net_Income and MRQ_EPS instead.

⚠ **Banks:** MRQ_Net_Interest is non-zero for banks (7 symbols) but zero for all others.

---

## 7. History_4_F_clean — Cleaned Fundamentals

Processed by `src/3_clean_fundamentals.py`. Regenerated 2026-07-10 after History_4_F replacement.

| | |
|---|---|
| **Files** | 277 (aligned to 313-symbol clean tech set minus 36 ETFs) |
| **Columns** | 46 (19 MRQ_*, 19 TTM_*, PE, ROE, LT_DE, EPS_Growth, Revenue_Growth, plus SYMBOL, DATE) |
| **Est. total rows** | ~2.2M |
| **Date range** | 1994-09-20 → 2026-07-09 (YYYYMMDD) |
| **Row range** | 1,976 (FIGR) → 8,001 (AAPL) |

**Cleaning rules applied:**
1. Keep only symbols in the 313-symbol clean tech set (drops 84 symbols)
2. Convert DATE from CYYMMDD to YYYYMMDD, deduplicate, strip leading/trailing all-zero rows

⚠ **Correction (2026-07-26):** MRQ_Net_Interest and TTM_Net_Interest were NOT dropped from F_clean. Both columns are present in all 277 files on disk. They are nonzero for 7 bank symbols and zero for all others. This is favorable for OQ4 — Net_Interest data is available in the clean set without restoration.

⚠ **Bank P&L structure:** Banks (JPM, BAC, C, WFC, etc.) have zero MRQ_Revenue, MRQ_Gross_Profit, MRQ_Operating_Income. Use MRQ_Net_Income and MRQ_EPS instead.

---

## 7b. History_4_F_2 — Expanded Fundamentals

| | |
|---|---|
| **Files** | 624 (CSV format, 47 columns) |
| **Date format** | ⚠ **CYYMMDD/YYMMDD** (NOT YYYYMMDD). Pre-2000: 6-digit YYMMDD (e.g. `991118`→1999-11-18). 2000+: 7-digit CYYMMDD (e.g. `1050927`→2005-09-27). Merge scripts must convert to YYYYMMDD before joining. |
| **Est. total rows** | ~5M |
| **Symbols** | 624 (broader universe than original 361) |

**vs. History_4_F (original):**
- Drops 8 columns: MRQ_Revenue, TTM_Revenue, MRQ_Net_Interest, TTM_Net_Interest,
  TTM_Total_Debt, TTM_Total_Equity, TTM_Cash_Equivalents, TTM_SharesOutstanding
- Adds 9 columns: EPS_Turnaround, EPS_LossRecovery, EPS_Acceleration,
  Economic_Revenue_Growth, FreeCashFlow, CurrentRatio, ShareCountGrowth,
  MRQ_Economic_Revenue, TTM_Economic_Revenue
- 263 additional symbols (624 vs 361)

## 7c. History_4_F_Dividend — Dividend Schedule

| | |
|---|---|
| **Files** | 569 (CSV format, YYYYMMDD dates, 3 columns) |
| **Columns** | `DATE`, `dividend_per_share`, `close_unadj` |
| **Frequency** | Daily (includes zero-dividend days) |
| **Example** | AAPL: 11,494 rows from 1980-12-12 to 2026-07-23 |

This is the per-symbol dividend payment history needed for price
reconstruction (undoing the subtractive dividend adjustment discovered
in the Phase 1 audit).  `close_unadj` is the unadjusted close price
before any dividend subtraction.

## 7d. History_4_F_Dividend_Correct — Fundamentals + Dividend Corrections

| | |
|---|---|
| **Files** | 624 (CSV format, 51 columns) |
| **Symbols** | 624 (same universe as History_4_F_2) |

Full fundamentals (same columns as History_4_F_2) PLUS:
- `Close_unadj` — unadjusted close price (pre-dividend-subtraction)
- `MRQ_DivPerShare` — quarterly dividend per share
- `Special_Dividend` — flag for special/one-time dividends
- `PE_corrected` — PE ratio corrected for dividend adjustment

---

## 8. History_6_merge — Final Merged Outputs

| File | Rows | Cols | Size | Source Script |
|------|------|:---:|-----:|---------------|
| `tech_daily.csv` | 1,664,246 | 43 | 464 MB | `1_merge_tech.py` |
| `tech_weekly.csv` | 375,693 | 41 | 98 MB | `1_merge_tech.py` |
| `tech_monthly.csv` | 89,159 | 40 | 22.5 MB | `1_merge_tech.py` |
| `market_merge_daily.csv` | 6,540 | 115 | 5.1 MB | `2_merge_market_daily.py` |
| `market_merge_weekly.csv` | 1,526 | 75 | 0.7 MB | `2_merge_market_weekly.py` |
| `market_merge_monthly.csv` | 335 | 75 | 0.15 MB | `2_merge_market_monthly.py` |
| `fundamentals.csv` | 1,479,677 | 46 | 452 MB | `3_merge_fundamentals.py` |
| `macro_merge_daily.csv` | 39,251 | 141 | 17.6 MB | `4_merge_macro.py` |
| `betas.parquet` | 1,403,427 | 4 | 24 MB | T2.1 (rebuilt 2026-07-26 on reconstructed close_unadj) |
| `labels.parquet` | 1,191,508 | 6 | 25 MB | T2.2 (beta-residualized rank label, H=63d) |
| `regime_features.parquet` | 6,540 | 12 | 0.5 MB | T3.1 (manual) |
| `regime_features_extras.parquet` | 6,540 | 2 | 32 KB | T3.1 (manual) |
| `regime_raw_inputs.parquet` | 6,540 | 29 | 0.4 MB | T3.1 (manual) |
| `regime_model_frozen.json` | — | — | ~3 KB | T3.2b (k=4, frozen centroids, scaler, p95 thresholds) |
| `regime_labels.parquet` | 6,037 | 3 | 0.1 MB | T3.2b (daily regime 0-3 or 'unclassified') |
| `regime_train_distances.parquet` | 2,393 | 3 | 0.1 MB | T3.2b (pre-filter freeze-step distances) |
| `regime_scaler_stats_T3.2a.parquet` | 11 | 3 | <1 KB | T3.2a |
| `regime_kmeans_diagnostics_T3.2a.parquet` | 165 | 7 | <1 KB | T3.2a |
| `AAPL_merged.parquet` | 9,909 | 569 | 8.5 MB | `6_merge_aapl.py` |
| `all_merged.parquet` | 1,500,309 | 567 | 412 MB | `6_merge_all.py` (rebuilt 2026-07-26: CLOSE patched, 33 AFFECTED dropped) |
| `zero_audit.csv` | 34 | 5 | 5 KB | `8_zero_audit.py` |

**Key dates per file:**
| File | Start | End |
|------|-------|-----|
| `tech_daily` | 1986-11-07 | 2026-07-02 |
| `tech_weekly` | 1971-11-12 | 2026-06-26 |
| `tech_monthly` | 1970-05-29 | 2026-06-30 |
| `market_merge_daily` | 2000-06-28 | 2026-07-01 |
| `market_merge_weekly` | 1997-04-04 | 2026-06-26 |
| `market_merge_monthly` | 1998-08-31 | 2026-06-30 |
| `fundamentals` | 1991-07-17 | 2026-07-09 |
| `macro_merge_daily` | 1919-02-01 | 2026-07-19 |
| `betas` | 1994-06-20 | 2026-07-02 |
| `labels` | 1994-06-20 | 2026-04-01 |
| `regime_features` | 2000-06-28 | 2026-07-01 |
| `regime_labels` | 2002-07-03 | 2026-07-01 |
| `all_merged` | 1986-11-07 | 2026-07-10 |
| `AAPL_merged` | 1986-11-07 | 2026-07-02 |

### File descriptions

**tech_daily/weekly/monthly.csv** — Stacked clean technical data. One row per symbol per date. Date column is `DATE` (YYYYMMDD int). All 313 symbols aligned across frequencies.

**market_merge_daily/weekly/monthly.csv** — MKT internals merged with SPY and QQQ price/technicals. `MKT_SPY_*` and `MKT_QQQ_*` column prefixes. The 75-column weekly/monthly files exclude some daily-only indicators.

**fundamentals.csv** — Cleaned quarterly fundamentals forward-filled to a daily grid, then merged with the daily tech date index. 277 symbols (313 minus 36 ETFs). 46 columns: SYMBOL, DATE, 19 MRQ_*, 19 TTM_*, PE, ROE, LT_DE, EPS_Growth, Revenue_Growth. Daily forward-fill ensures fundamentals are available on every trading day with the most recent quarter's data. Generated by `src/3_merge_fundamentals.py`.

**macro_merge_daily.csv** — All 140 FRED macro series on a calendar daily grid (Mon–Sun). Forward-filled — each day carries the latest released value. Weekend/holiday dates drop naturally when joined to trading-day data.

**AAPL_merged.parquet** — Single-symbol proof-of-concept merge: AAPL daily tech + market + macro + fundamentals + isETF flag. 569 columns with source-specific suffixes (`_D` for daily, `_MKT` for market, `_M` for macro, `_F` for fundamentals). Columns: DATE (no SYMBOL — single stock). Generated by `src/6_merge_aapl.py`.

**all_merged.parquet** — Full multi-symbol merge: all 313 symbols × daily tech + market + macro + fundamentals + isETF. 567 columns, 1.66M rows. Columns include SYMBOL and DATE. This is the primary modeling-ready dataset. Column suffixes match AAPL_merged conventions. Generated by `src/6_merge_all.py`.

**betas.parquet** — Point-in-time market betas computed in T2.1.  4 columns:
`SYMBOL`, `DATE`, `beta_raw` (β̂_winsor, used as layer-1 control regressor),
`beta_star` (β* = 0.67·β̂_winsor + 0.33, Blume-shrunk, used for the
beta-residualized label).  252d trailing OLS, shift-1 (excludes t's own
return), winsorized cross-sectionally at 1st/99th daily.  Rebuilt
2026-07-26 on reconstructed close_unadj from `History_4_F_Dividend/`;
amended universe (280 symbols, 33 AFFECTED dropped per D3 amendment).

**labels.parquet** — Beta-residualized forward cross-sectional rank
labels, computed in T2.2.  6 columns: `SYMBOL`, `DATE`, `r_fwd`
(forward 63-trading-day return), `r_m` (SPY forward return), `resid`
(r_fwd − β*·r_m), `label` (daily cross-sectional percentile rank of
resid, ∈ [0,1]).  1,191,508 rows, 243 stocks, 1994-06-20 →
2026-04-01.  Rank uses average-rank for ties; days with <100 stocks
(min_cross_section) are null.  **The label column is a
FORWARD-LOOKING target — never feed it as a predictor.**

**regime_features.parquet** — 11 regime features + DATE on the
market_merge_daily trading-day grid (6,540 rows, 2000-06→2026-07).
Effective start 2002-07-03 (504d VIX percentile warmup).  3 SPY
(ret/vol), 1 VIX (30d percentile), 1 Growth/Value (z), 2 credit
(Baa10Y z + chg), 2 curve (z + chg), 1 rates (z), 1 NFCI (z).
Breadth and VIX term-structure features excluded (vendor dead-start
pre-2007).  All trailing-window transforms, leakage-verified.  See
`docs/phase3_features_report.md` for full build details.

**regime_features_extras.parquet** — Rejected/candidate features kept
for the record: `vix_back_slope_z` (excluded as degenerate).
`sp_above_200_z` was also excluded (broken source column, dead until
2010-03-08) and is NOT in this file — see `docs/data_issues_log.md`.

**regime_raw_inputs.parquet** — Whitelisted MKT columns + 5 macro series
joined on DATE, before any transform.  Used as the input to the feature
transforms; kept for audit/rebuild.

**regime_model_frozen.json** — Frozen k=4 regime model (T3.2b).  Contains:
feature names + order (11), scaler mean/std, 4 centroids in standardized
space, per-cluster unclassified thresholds (c0=3.59, c1=6.48, c2=3.89,
c3=2.77 — 95th percentile of within-cluster training distances), train
window bounds, training-matrix hash, git commit, seed=42.  See
`docs/regime_model_frozen_manifest.md`.

**regime_labels.parquet** — Daily regime series, 2002-07-03 → 2026-07-01
(6,037 trading days).  Columns: `DATE`, `regime` (0–3 or 'unclassified'),
`dist_to_centroid`.  FORWARD-APPLY labels — the unclassified threshold has
already been applied.  For per-cluster distribution stats (e.g.,
recomputing p95), use `regime_train_distances.parquet` instead — the
unclassified filter trims its own >p95 tail, shifting any recomputed
percentile downward.  See data_issues_log.md item 7.

**regime_train_distances.parquet** — PRE-FILTER training-window distances
(2,393 days, 2002-07-03 → 2011-12-30).  Columns: `DATE`, `cluster`
(0–3, freeze-step assignment), `dist_to_centroid`.  Every training day is
present — the unclassified threshold has NOT been applied.  Use this file
(never `regime_labels.parquet`) when computing cluster-distribution
statistics on the training window.  The frozen thresholds are exactly the
p95 of these per-cluster distances.

**regime_kmeans_diagnostics_T3.2a.parquet** — Tidy long table from the
k-selection diagnostics (k=4,5,6): k, cluster_id, feature, raw_mean,
std_mean, size, pct.  165 rows (3k × 5clusters × 11features).

**zero_audit.csv** — Zero-value audit across all merged data sources. 34 rows × 5 columns (`source`, `column`, `pattern`, `proposed_action`, `reason`). Documents which columns are zero for which symbols and recommends handling (keep, drop, or flag). Generated by `src/8_zero_audit.py`.

⚠ **Data refresh note:** Tech CSVs, fundamentals.csv, and AAPL_merged.parquet regenerated 2026-07-10. `macro_merge_daily.csv` regenerated 2026-07-19. `all_merged.parquet` rebuilt 2026-07-26 (CLOSE patched from close_unadj, 33 AFFECTED symbols dropped per D3 amendment). `betas.parquet` rebuilt 2026-07-26 on reconstructed prices. `labels.parquet` generated 2026-07-26. Regime features (T3.1) and model (T3.2) built 2026-07-29. Re-run the pipeline if raw data has been updated since.

⚠ **fundamentals.csv is now a daily grid** (forward-filled), not quarterly snapshots. The 1.48M rows come from forward-filling 277 symbols' quarterly data to every trading day. This matches the tech daily date index.

### Column catalogs (as of 2026-07-29)

#### tech_daily.csv — 43 columns

```
SYMBOL, DATE, VOLUME, OPEN, HIGH, LOW, CLOSE,
SMA_020, SMA_050, SMA_200,
SPY_C, SPY_020, SPY_050, SPY_200,
PFE_010, PFE_020,
Fit, Trigger, Itrend,
Fit_SPY, Trigger_SPY, Itrend_SPY,
STD_20, ATR,
Trend_PV, PV_BULL_STEP, PV_BULL_START, PV_BULL_STOP, PV_BULL_CNT, PV_BULL_H,
PV_BEAR_STEP, PV_BEAR_START, PV_BEAR_STOP, PV_BEAR_CNT, PV_BEAR_L,
Push_Diff, Push_Diff_SPY,
MACD_C, MACD_H, MACD_L, MACD_DIFF,
oSlowK, RSI_03
```

#### tech_weekly.csv — 41 columns

```
SYMBOL, DATE, VOLUME, OPEN, HIGH, LOW, CLOSE,
SMA_020, SMA_050,
SPY_C, SPY_020, SPY_050,
PFE_010, PFE_020,
Fit, Trigger, Itrend,
Fit_SPY, Trigger_SPY, Itrend_SPY,
STD_20, ATR,
Trend_PV, PV_BULL_STEP, PV_BULL_START, PV_BULL_STOP, PV_BULL_CNT, PV_BULL_H,
PV_BEAR_STEP, PV_BEAR_START, PV_BEAR_STOP, PV_BEAR_CNT, PV_BEAR_L,
Push_Diff, Push_Diff_SPY,
MACD_C, MACD_H, MACD_L, MACD_DIFF,
oSlowK, RSI_03
```
*(vs daily: drops SMA_200, SPY_200; no other structural differences)*

#### tech_monthly.csv — 40 columns

```
SYMBOL, DATE, VOLUME, OPEN, HIGH, LOW, CLOSE,
SMA_010, SMA_020,
SPY_C, SPY_020,
PFE_010, PFE_020,
Fit, Trigger, Itrend,
Fit_SPY, Trigger_SPY, Itrend_SPY,
STD_20, ATR,
Trend_PV, PV_BULL_STEP, PV_BULL_START, PV_BULL_STOP, PV_BULL_CNT, PV_BULL_H,
PV_BEAR_STEP, PV_BEAR_START, PV_BEAR_STOP, PV_BEAR_CNT, PV_BEAR_L,
Push_Diff, Push_Diff_SPY,
MACD_C, MACD_H, MACD_L, MACD_DIFF,
oSlowK, RSI_03
```
*(vs daily: drops SMA_050, SMA_200, SPY_050, SPY_200; adds SMA_010; keeps only SPY_C, SPY_020)*

#### market_merge_daily.csv — 115 columns

- **1 index:** `DATE`
- **40 MKT internals:** Growth_vs_Value, GVR_020, GVR_050, GVR_100, GVR_200, VIX_9D, VIX_3M, VIX_6M, VIX_Front_Slope, VIX_Back_Slope, VIX_9D_Z, VIX_3M_Z, SP_Above_050, SP_Above_200, ND_Above_050, ND_Above_200, TRIN_Z_{SPY,QQQ,RSL,NYSE}, NHNL_Ratio_{SPY,QQQ,RSL,NYSE}, Fosback_{SPY,QQQ,RSL,NYSE}, Participation_{SPY,QQQ,RSL,NYSE}, Advance_{SPY,QQQ,RSL,NYSE}, UpVolume_{SPY,QQQ,RSL,NYSE}
- **33 SPY technicals** (prefix `MKT_SPY_`): VOLUME, OPEN, HIGH, LOW, CLOSE, SMA_020, SMA_050, SMA_200, PFE_010, PFE_020, Fit, Trigger, Itrend, STD_20, ATR, Trend_PV, PV_BULL_*, PV_BEAR_*, Push_Diff, MACD_*, oSlowK, RSI_03
- **41 QQQ technicals** (prefix `MKT_QQQ_`): same as SPY plus SPY_C, SPY_020, SPY_050, SPY_200, Fit_SPY, Trigger_SPY, Itrend_SPY, Push_Diff_SPY

*(SPY source: History_1_D_clean/SPY.csv; QQQ source: History_1_D_clean/QQQ.csv; pure rename-and-join, no computation)*

#### market_merge_weekly.csv — 75 columns

`DATE` + `MKT_SPY_*` (33 cols) + `MKT_QQQ_*` (41 cols). Same structure as daily, no MKT internals block. Source: clean weekly SPY/QQQ files.

#### market_merge_monthly.csv — 75 columns

Identical column set to weekly. Source: clean monthly SPY/QQQ files.

#### fundamentals.csv — 46 columns

```
SYMBOL, DATE,
MRQ_Total_Long_Term_Debt, MRQ_Total_Equity, MRQ_Total_Debt,
MRQ_Gross_Profit, MRQ_Net_Income, MRQ_Operating_Income, MRQ_Revenue,
MRQ_EPS, MRQ_Gross_Margin, MRQ_Operating_Margin,
MRQ_Total_Asset, MRQ_Total_Liabilities, MRQ_Current_Asset, MRQ_Current_Liabilities,
MRQ_LongTerm_Asset, MRQ_LongTerm_Liabilities,
MRQ_Net_Interest, MRQ_Depreciation, MRQ_Amortization,
MRQ_CapEx, MRQ_OperatingCashFlow, MRQ_Cash_Equivalents, MRQ_SharesOutstanding,
TTM_Total_Equity, TTM_Total_Debt,
TTM_Gross_Profit, TTM_Net_Income, TTM_Net_Interest,
TTM_Operating_Income, TTM_Revenue, TTM_EPS,
TTM_Gross_Margin, TTM_Operating_Margin,
TTM_Depreciation, TTM_Amortization,
TTM_CapEx, TTM_OperatingCashFlow, TTM_Cash_Equivalents, TTM_SharesOutstanding,
PE, ROE, LT_DE, EPS_Growth, Revenue_Growth
```

#### macro_merge_daily.csv — 141 columns

1 date index (`date`) + 140 FRED macro series. Columns follow pattern `{category}_{series_id}_{description}`. Categories: A1–A4 (Fed/Flow of Funds), B (Employment), C (Inflation/GDP), D (Production), E (Financial Conditions), F (Credit/Yields), G (FX), H (Commodities), I (Sentiment), J (Housing), K (Fiscal), L (Equities), M (Rates), N (Construction), O (Money Stock), R (OECD CLI), T (NFC Accounts).

#### AAPL_merged.parquet — 569 columns (single-symbol POC)

Suffix convention: `_D` = daily, `_W` = weekly, `_M` = monthly, `_MKT` = market daily, `_MKTW` = market weekly, `_MKTM` = market monthly, `_MAC` = macro, `_F` = fundamentals.

- **42 daily tech cols** (`_D`): VOLUME_D, OPEN_D, CLOSE_D, SMA_020_D, ..., RSI_03_D
- **40 weekly tech cols** (`_W`): VOLUME_W, ..., RSI_03_W (forward-filled)
- **39 monthly tech cols** (`_M`): VOLUME_M, ..., RSI_03_M (forward-filled)
- **40 MKT internals** (`_MKT`): Growth_vs_Value_MKT, ..., UpVolume_NYSE_MKT
- **33 SPY daily** (`MKT_SPY_*_MKT`): MKT_SPY_CLOSE_MKT, ...
- **41 QQQ daily** (`MKT_QQQ_*_MKT`): MKT_QQQ_CLOSE_MKT, ...
- **34 SPY weekly** (`MKT_SPY_*_MKTW`): forward-filled
- **41 QQQ weekly** (`MKT_QQQ_*_MKTW`): forward-filled
- **34 SPY monthly** (`MKT_SPY_*_MKTM`): forward-filled
- **41 QQQ monthly** (`MKT_QQQ_*_MKTM`): forward-filled
- **140 macro** (`_MAC`): A1_RRPONTSYD_ON_RRP_Daily_MAC, ...
- **43 fundamentals** (`_F`): MRQ_Revenue_F, ..., Revenue_Growth_F
- **1 flag:** isETF

#### all_merged.parquet — 567 columns (multi-symbol)

Same structure as AAPL_merged but adds `SYMBOL` column and uses different suffix conventions: weekly cols get `_1`, monthly get `_2`; MKT weekly/monthly market caps get `_1`/`_2` suffixes; macro and fundamentals columns keep original names (no suffix). `isETF` column included.

Column groups:
- **SYMBOL, DATE** (2)
- **Daily tech** (42): VOLUME, OPEN, ..., RSI_03 (original names, no suffix)
- **MKT internals** (40): Growth_vs_Value, ..., UpVolume_NYSE
- **SPY daily** (33): MKT_SPY_VOLUME, ..., MKT_SPY_RSI_03
- **QQQ daily** (41): MKT_QQQ_VOLUME, ..., MKT_QQQ_RSI_03
- **Macro** (140): A1_RRPONTSYD_ON_RRP_Daily, ..., T_BOGZ1FA106300011Q_Capital_Consumption_NFC
- **Weekly tech** (39): VOLUME_1, OPEN_1, ..., RSI_03_1
- **Monthly tech** (37): VOLUME_2, OPEN_2, ..., RSI_03_2
- **SPY weekly** (33): MKT_SPY_VOLUME_1, ..., MKT_SPY_RSI_03_1
- **QQQ weekly** (41): MKT_QQQ_VOLUME_1, ..., MKT_QQQ_RSI_03_1
- **SPY monthly** (33): MKT_SPY_VOLUME_2, ..., MKT_SPY_RSI_03_2
- **QQQ monthly** (41): MKT_QQQ_VOLUME_2, ..., MKT_QQQ_RSI_03_2
- **Fundamentals** (44): MRQ_Total_Long_Term_Debt, ..., Revenue_Growth (original names)
- **isETF** (1)

#### zero_audit.csv — 5 columns

`source`, `column`, `pattern`, `proposed_action`, `reason`

---

## 9. Symbol Cross-Reference

| Set | Count | Notes |
|-----|:-----:|-------|
| Raw daily | 329 | Includes SPY, QQQ |
| Raw weekly | 332 | Includes SPY, QQQ |
| Raw monthly | 332 | Includes SPY, QQQ |
| **Clean tech (all 3 frequencies)** | **313** | Perfectly aligned |
| History_4_F | 361 | 277 overlap with clean tech |
| Missing from 4_F (clean tech present) | 36 | ALL ETFs — expected |
| Extra in 4_F (not in clean) | 84 | Filtered/excluded stocks |

**ETFs in clean tech (no fundamentals):** DIA, EFA, EWJ, GDX, GDXJ, GLD, HYG, IEF, INDA, ITB, IWM, KRE, KWEB, LQD, QQQ, SHY, SLV, SMH, SPY, TAN, TLT, USO, XAR, XBI, XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY, XOP

---

## 10. Files Requiring Regeneration

Most outputs were regenerated 2026-07-10. `macro_merge_daily.csv` and `all_merged.parquet` were regenerated 2026-07-19 (macro grid truncated to today, COHR/IBM/JPM stale data fixed).

To refresh after raw data updates, run in order:
```
source .venv/bin/activate
python3 src/1_clean_tech.py
python3 src/3_clean_fundamentals.py
python3 src/1_merge_tech.py
python3 src/2_merge_market_daily.py && python3 src/2_merge_market_weekly.py && python3 src/2_merge_market_monthly.py
python3 src/3_merge_fundamentals.py
python3 src/4_merge_macro.py
python3 src/6_merge_all.py
python3 src/8_zero_audit.py
```

---

## 11. Quick Error Checks

- **Blank headers:** MKT.txt (pos 43), raw weekly (pos 100), raw monthly (pos 80). Trailing commas — harmless, filtered by all scripts.
- **Duplicate column names:** None found in any file.
- **Single-row weekly/monthly files:** ALAB — insufficient history for weekly/monthly bars.
- **Zero-value columns (fundamentals):** MRQ_Net_Interest and TTM_Net_Interest are zero for 274/277 symbols. Dropped by `3_clean_fundamentals.py`. See `zero_audit.csv` for full zero-value audit across all data sources.
- **Bank P&L:** Banks have zero MRQ_Revenue, MRQ_Gross_Profit, MRQ_Operating_Income. Use MRQ_Net_Income and MRQ_EPS instead. Also affects ~8 symbols' MRQ_Gross_Profit and MRQ_Operating_Income.
