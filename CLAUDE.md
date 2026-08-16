# CLAUDE.md — Stock Project

Exploratory, interpretable research — not a prediction machine, not a trading
system.  The question:

  Under which market regimes, for companies in which financial states, showing
  which price structures, do stocks tend to perform well relative to their
  peers — and is that regularity real, measurable, and stable enough to be
  trusted out of sample?

Three independent, crossed condition axes:
  1. price series  → personal indicator → structure state  (hand-encoded, deferred)
  2. market data   → k-means clustering  → regime state     (k ∈ {4,5,6})
  3. fundamentals  → k-means clustering  → financial state  (k ∈ {3,4,5})

Measurement: two-layer Fama-MacBeth on regime × financial-state × structure
interactions against a beta-residualized forward cross-sectional rank label
(63-day horizon).  Progressive baselines B0→B1→B2→B3.  Joint pipeline block
bootstrap for inference (500 resamples).  No neural nets, no FAISS, no RL.

Canonical specification: doc/Plan4_Implementation_Guide.html — that document
wins wherever it conflicts with earlier notes, CLAUDE.md, or memory.

**Source hierarchy:** The guide wins on design and reasoning (why we chose X,
the D1–D15 ledger, the interview defense).  CLAUDE.md and the phase reports
win on current state (what's built, what's pending, what data exists).  If
they disagree on a decision, the guide is canonical; if they disagree on
status, the markdowns are.

## Key design decisions (D1–D15)

- **D1 Framing**: exploratory study, not prediction machine. A null finding is a defensible result.
- **D2 Label**: beta-residualized cross-sectional rank (r_i − β*_i·r_m, ranked per day). β estimated point-in-time (trailing 252d, winsorized 1st/99th, Blume-shrunk toward 1). Forward horizon = 63 trading days.
- **D3 Universe**: 280 symbols (206 dividend-corrected stocks + 38 negligible-exposure stocks + 36 ETFs), per D3 amendment 2026-07-26. 33 materially-affected stocks dropped. Survivorship bias deliberately accepted and signed; the drop skews away from precious-metals miners and small-cap cyclicals.
- **D4 Discrete states**: coarse buckets (4–6 regimes, 3–4 financial states, 3 structure states) — primary. Continuous interactions run as robustness check.
- **D5 Two-layer Fama-MacBeth**: layer 1 = per-day cross-sections (regime absorbed into intercept); layer 2 = group days by regime, NW errors, era slices.
- **D6 Effective sample size**: count in independent episodes, not days. Minimum 4 episodes spanning 3 years per claim. Newey-West ~63 lags.
- **D7 Two-way primary, three-way exploratory**: regime × fundamentals is the spine. Full three-way cross is exploratory + ≤5 pre-registered hypotheses.
- **D8 Validation**: expanding-window hybrid — iterate on 2012–2019 validation folds; seal 2020→present for one final run. Embargo 63 days at every boundary.
- **D9 Unclassified state**: distance percentile threshold (95th) frozen from training window. Novel days → "unclassified."
- **D10 Joint pipeline block bootstrap**: 500 resamples × (block-resample 126d → refit clusters → Hungarian centroid matching → rerun stats).
- **D11 Clustering**: k-means, stability by adjusted Rand, nameability required. Regime and financial-state clusterings kept separate and crossed.
- **D12 Indicator**: deferred (not load-bearing). Spec frozen in writing before exploration. Perturbation-checked. Allowed to fail (B3 ≈ B2).
- **D13 Rejected**: RL (two reasons), autoencoder discovery, FAISS/XGBoost prediction spine.
- **D14 Point-in-time**: relative features for Drift A; era slicing for Drift B. Macro release dates are calculated approximations.
- **D15 Engineering hygiene**: config file + fixed seeds, leakage tests in CI, results log, gated build order.

## Build phases (from Plan 4)

| Phase | What | Status |
|-------|------|--------|
| 0 | Engineering scaffold (config, modules, leakage tests, spec freeze) | **Done** |
| 1 | Data layer finalization (checklist, adjustment verification, coverage profile) | **Done** |
| 2 | Label construction — T2.1 betas.parquet rebuilt 2026-07-26 on reconstructed close_unadj (COST β 2.00→0.73, identity bound holds); T2.2 beta-residualized rank label done (labels.parquet, 1.19M rows, 243 stocks) | **Done** |
| 3 | Regime features — T3.1 done (11 features, leakage-passed, dead-start audited). ⚠ T3.1 is NOT invalidated by the stock-price bug: regime features are market-level (SPY CLOSE + macro), confirmed clean per data_issues_log #1. T3.2 clustering done (k=4, frozen, unclassified threshold applied, forward labels saved). | **Done** |
| 4 | Financial-state clustering (resolve OQ3/OQ4, fit/freeze) | Pending |
| 5 | Two-layer Fama-MacBeth | Pending |
| 6 | Progressive baselines B0→B1→B2→B3 | Pending |
| 7 | Validation protocol (expanding-window hybrid, pre-registration) | Pending |
| 8 | Rigor suite (joint bootstrap, perturbation checks) | Pending |
| 9 | Write-up | Pending |
| Rec | Indicator implementation + B3, continuous-interaction check, sector mapping | Pending |
| Opt | Similarity retrieval, multiple horizons, partial pooling | Pending |

### What's built and where

| Output | File | Phase |
|--------|------|-------|
| PIT betas (β̂_winsor + β*) | `data/History_6_merge/betas.parquet` | T2.1 ✅ rebuilt 2026-07-26 on reconstructed close_unadj; COST β 2.00→0.73 |
| Beta-residualized rank labels | `data/History_6_merge/labels.parquet` | T2.2 ✅ 1.19M rows, 243 stocks, 1994→2026, H=63d |
| Regime features (11 cols) | `data/History_6_merge/regime_features.parquet` | T3.1 |
| Regime feature extras (rejects) | `data/History_6_merge/regime_features_extras.parquet` | T3.1 |
| Regime model (k=4, frozen) | `data/History_6_merge/regime_model_frozen.json` | T3.2b |
| Regime labels (daily, 2002-07→2026-07) | `data/History_6_merge/regime_labels.parquet` | T3.2b |
| Regime train distances (pre-filter) | `data/History_6_merge/regime_train_distances.parquet` | T3.2b |
| Raw assembled inputs | `data/History_6_merge/regime_raw_inputs.parquet` | T3.1 |
| Coverage profile | `docs/coverage_by_day.parquet` + `.png` | Phase 1 |
| Adjustment audit (66 flags) | `docs/adjustment_audit.csv` | Phase 1 |
| Macro coverage audit (140 series) | `docs/macro_coverage_audit.csv` | T3.1 |
| Data issues log | `docs/data_issues_log.md` | ongoing |
| Decision log | `docs/decision_log.md` | ongoing |

### Data issues discovered (see `docs/data_issues_log.md` for details)

1. **Subtractive dividend adjustment** — 66 symbols' prices are actual − future dividends. **Diagnosis resolved (2026-07-26):** close_unadj from `History_4_F_Dividend/` verified (COST β 24.6→0.815, identity bound restored). 206 symbols correctable; 38 negligible (retained); 33 dropped (D3 amendment). **Reconstruction applied to pipeline 2026-07-26** — betas.parquet rebuilt, all_merged.parquet CLOSE patched. T2.2 unblocked.
2. **BAML* series truncated** — ICE BofA licensing; HY OAS starts 2023. Swapped to BAA10Y (Moody's, 1986→).
3. **TEDRATE zombie** — flat since LIBOR discontinuation (2022-01-24). Not used.
4. **Vendor dead-start in market_merge_daily**: NYSE breadth dead until 2007-09-10, SP/ND above-MA dead until 2010-03-08, VIX term structure columns dead-started in tiers (2007/2011/2013). All macro+price columns verified clean from day 1.
5. **Price adjustment confirmed** — SPY and all stocks split-adjusted (Phase 1); dividend subtraction is a separate issue (item 1).

## Open questions (OQ1–OQ7)

Decide on purpose, in writing. Defaults in Plan4 §5. Currently unresolved:
- OQ1: Indicator × sealed fold sequencing
- OQ2: Indicator bar frequency (default: weekly)
- OQ3: Financial clustering staleness & sector treatment
- OQ4: Banks (7 symbols — default: exclude from financial-state axis)
- OQ5: Price adjustment status (verify split dates)
- OQ6: Fold boundaries (default committed in config.yaml)
- OQ7: Exploration triage threshold

## Project structure

```
/home/carol/projects/stock_project/
├── src/                           Pipeline scripts + analysis package
│   ├── 1_clean_tech.py            (etc. — numbered ETL scripts 1–8)
│   ├── 6_merge_all.py             Produces all_merged.parquet
│   └── analysis/                  Downstream research package (new code)
│       ├── data/                  PIT loaders (visibility-date enforcement)
│       ├── features/              Beta estimation, regime-relative features
│       ├── clustering/            k-means (regimes/financial-states), episodes
│       ├── stats/                 Two-layer Fama-MacBeth
│       ├── rigor/                 Block bootstrap, perturbation, FDR
│       └── report/                Results log, tables/figures
├── config.yaml                    All analysis constants (single source of truth)
├── tests/                         Leakage tests (T0.3 a–d, xfail stubs)
├── pyproject.toml                 Pytest config
├── data/                          All data (see DATA_INVENTORY.md for details)
│   ├── History_0_MKT/             Market internals (1 file)
│   ├── History_1_D/               Raw daily price/technical (329 files)
│   ├── History_1_D_clean/         Cleaned daily (313 files)
│   ├── History_2_W/               Raw weekly price/technical (332 files)
│   ├── History_2_W_clean/         Cleaned weekly (313 files)
│   ├── History_3_M/               Raw monthly price/technical (332 files)
│   ├── History_3_M_clean/         Cleaned monthly (313 files)
│   ├── History_4_E_Alfred/        FRED macro raw downloads (140 series)
│   ├── History_4_E_Alfred_Release/ FRED macro with release dates (140)
│   ├── History_4_F/               Raw quarterly fundamentals (361 symbols, 46 cols)
│   ├── History_4_F_2/             Expanded fundamentals (624 symbols, 47 cols)
│   ├── History_4_F_Dividend/      Dividend schedule (569 symbols, daily)
│   ├── History_4_F_Dividend_Correct/ Fundamentals + dividend + corrections (624)
│   ├── History_4_F_clean/         Cleaned fundamentals (277 symbols)
│   └── History_6_merge/           Final merged outputs (CSVs + parquets)
├── config.yaml                    All analysis constants (single source of truth)
├── tests/                         Leakage tests (T0.3 a–d, xfail stubs)
├── pyproject.toml                 Pytest config
├── indicator_notes.md             PV indicator notes (formula pending)
├── hypotheses.md                  Pre-registration placeholder (T7.2)
├── CLAUDE.md                      This file
├── DATA_INVENTORY.md              Comprehensive data catalog
├── doc/                           Plan4 guide + breakdown docs
└── docs/                          Reports, audit CSVs, decision log
```

## Key conventions

### Date formats
- **Raw files (CYYMMDD)**: `1180716` = century 1, year 18, month 07, day 16 = 2018-07-16
- **Cleaned files (YYYYMMDD)**: `20180716`
- All merge outputs use YYYYMMDD

### Symbol universe
- **313 symbols** aligned across daily/weekly/monthly after cleaning
- **277 symbols** have fundamental data (36 missing from History_4_F)
- SPY and QQQ are benchmark files, not in the 313 stock set

### Column naming in merge outputs
- Tech: original names (OPEN, HIGH, SMA_020, PV_BULL_STEP, etc.)
- Market: `MKT_SPY_*` prefix for SPY data, `MKT_QQQ_*` prefix for QQQ data
- Macro: original filenames with `_latest`/`_revision_timeline` suffixes stripped
- Fundamentals: MRQ_* and TTM_* prefixes for quarterly/annual views

### The .venv
All Python scripts run under `/home/carol/projects/stock_project/.venv/`.
Activate: `source .venv/bin/activate`. Key packages: duckdb, pandas, requests.

## Pipeline scripts (src/)

Numbered by execution order:

| # | Script | What it does |
|---|--------|--------------|
| 1 | `1_clean_tech.py` | Clean raw price/technical .txt → clean .csv |
| 1 | `1_merge_tech.py` | Stack clean CSVs → `tech_daily/weekly/monthly.csv` |
| 2 | `2_merge_market_daily.py` | Merge MKT + SPY + QQQ daily → `market_merge_daily.csv` |
| 2 | `2_merge_market_weekly.py` | Same for weekly |
| 2 | `2_merge_market_monthly.py` | Same for monthly |
| 3 | `3_clean_fundamentals.py` | Clean raw fundamentals → `History_4_F_clean/` |
| 3 | `3_merge_fundamentals.py` | Merge clean fundamentals → daily grid → `fundamentals.csv` |
| 4 | `4_download_macro.py` | Download FRED+ALFRED → `History_4_E_Alfred/` |
| 4 | `4_download_macro_release.py` | Add release dates → `History_4_E_Alfred_Release/` |
| 4 | `4_merge_macro.py` | Merge macro to daily grid → `macro_merge_daily.csv` |
| 6 | `6_merge_aapl.py` | Single-symbol merge (AAPL POC) → `AAPL_merged.parquet` |
| 6 | `6_merge_all.py` | Full 313-symbol merge → `all_merged.parquet` |
| 6 | `6_verify_aapl.py` | Verify AAPL merge correctness |
| 7 | `7_verify_all.py` | Verify all-symbol merge correctness |
| 8 | `8_zero_audit.py` | Audit zero-value patterns → `zero_audit.csv` |
| — | `merge_wide.py` | (Legacy) Merge tech+fundamentals → parquet |

### Running the full pipeline
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

## Data cleaning rules

### Technical data (1_clean_tech.py)
1. Drop rows where SPY_C == 0
2. Drop rows where OPEN, HIGH, LOW, or CLOSE <= 0
3. Drop rows where PV_BULL_CNT == 0 or PV_BEAR_CNT == 0 (raw values, before zeroing)
4. Drop rows where all MACD columns are 0
5. Zero out PV_BULL_* if PV_BULL_STEP == 0; same for PV_BEAR
6. Convert DATE from CYYMMDD to YYYYMMDD
7. Keep only curated column subsets (42/39/38 for daily/weekly/monthly)
8. Post-process: remove any symbol empty in ANY frequency from ALL three

### Fundamentals (3_clean_fundamentals.py)
1. Keep only 313-symbol clean set (drops 84 symbols)
2. Convert DATE, deduplicate, strip leading/trailing all-zero rows
3. ⚠ Correction (2026-07-26): MRQ_Net_Interest and TTM_Net_Interest were NOT dropped. Both columns are present in all F_clean files. They are nonzero for 7 bank symbols and zero for all others.

## Macro data notes

- 140 FRED series documented in `_ALFRED_MANIFEST.csv`
- Use `History_4_E_Alfred_Release/` NOT `History_4_E_Alfred/` — the Release
  folder has calculated release dates that span the full history (1919–2026).
  The raw ALFRED vintages bunch all pre-2016 data at 2016-01-01.
- `macro_merge_daily.csv` is a daily forward-filled grid — use this for
  release-date-aligned macro features

## Merged outputs (History_6_merge/)

| File | Rows | Cols | Content |
|------|------|:---:|---------|
| `tech_daily.csv` | 1.66M | 43 | Per-symbol daily price/technicals |
| `tech_weekly.csv` | 376K | 41 | Per-symbol weekly |
| `tech_monthly.csv` | 89K | 40 | Per-symbol monthly |
| `market_merge_daily.csv` | 6.5K | 115 | MKT + SPY + QQQ daily |
| `market_merge_weekly.csv` | 1.5K | 75 | Same, weekly |
| `market_merge_monthly.csv` | 336 | 75 | Same, monthly |
| `fundamentals.csv` | 1.48M | 46 | Daily forward-filled quarterly fundamentals (277 symbols) |
| `macro_merge_daily.csv` | 39K | 141 | All macro series, daily grid |
| `betas.parquet` | 1.66M | 4 | PIT betas: SYMBOL, DATE, beta_raw (β̂_winsor), beta_star (β*) |
| `regime_features.parquet` | 6.5K | 17 | 15 regime features + DATE, 2002-07→2026-07 |
| `regime_features_extras.parquet` | 6.5K | 2 | Rejected/candidate features (vix_back_slope_z) |
| `regime_raw_inputs.parquet` | 6.5K | 29 | Whitelisted MKT + macro columns, joined |
| `AAPL_merged.parquet` | 9.9K | 569 | Single-symbol merge (AAPL proof of concept) |
| `all_merged.parquet` | 1.66M | 567 | Full 313-symbol merge (tech+market+macro+fundamentals+isETF) |
| `zero_audit.csv` | 34 | 5 | Zero-value audit across all merged data |

## FRED API

- API key: in `.env` as `FRED_API_KEY` (free tier, 120 req/min)
- Base URL: `https://api.stlouisfed.org/fred/`
- ALFRED: query in ≤3-month realtime windows to avoid 0-result responses

## Project memory

Persistent memory at `/home/carol/.claude/projects/-home-carol-projects-stock-project/memory/`
- `MEMORY.md` — index
- `project-knowledge.md` — full technical details on all 140 FRED series,
  revision schedules, vintage data, cleaning rules, and pipeline architecture
- `track-all-prompts.md` — prompt logging preference
