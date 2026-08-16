# Data issues log

This log records data-quality issues found and their disposition.
Diagnostic method throughout: verify a column behaves the way the underlying
reality must (e.g., breadth must move in 2008, beta obeys an identity bound)
rather than trusting it looks populated.

---

### 1. Subtractive dividend adjustment in stock prices

- **Symptom:** COST beta = 28 against SPY (identity-checked: |β| ≤ σ_stock/σ_market
  bound violated).  Sub-$1 prices for large caps (CME at $0.47, COST at $2.32
  in the 2000s when actual prices were $40+).
- **Diagnosis:** Platform prices = actual − cumulative future dividends.
  Confirmed via reconstruction identity (β = ρ × σ_stock / σ_market),
  anchor-level gap analysis (gap_frac monotonic declining toward zero),
  realized-vol inflation in early windows.
- **Root cause:** Platform subtracts dividends from price series.  Same
  mechanism affects COST, CME, and ~60 other symbols.  SPY is unaffected
  (method inconsistent across symbols).
- **Scope:** 34 definitive (min_close ≤ $0.50) + 32 likely (near-zero early
  prices) = 66 symbols flagged.  Heavy long-time payers (KO, PG, JNJ, IBM,
  XOM) are also affected but harder to detect without dividend schedule
  (prices stayed above detection threshold).  Full audit at
  `docs/adjustment_audit.csv`.
- **Disposition:** RESOLVED (2026-07-26).
  - **Diagnosis confirmed:** close_unadj from `History_4_F_Dividend/` and
    `History_4_F_Dividend_Correct/` restores COST β 24.6→0.815 with identity
    bound restored (see `docs/new_folders_verification.md` V5).  close_unadj
    is bit-identical across both folders (V4).  The fix is real.
  - **Scope:** 206 symbols corrected via close_unadj reconstruction; 38
    NEGLIGIBLE (post-2021 IPOs, immaterial exposure) retained uncorrected;
    33 AFFECTED (materially corrupt, no dividend schedule) dropped per D3
    amendment (see `docs/decision_log.md` 2026-07-26 and
    `docs/coverage_amendment_analysis.md`).
  - **Reconstruction applied 2026-07-26:** `betas.parquet` rebuilt on
    reconstructed prices (COST β 2.00→0.73, identity bound holds);
    `all_merged.parquet` CLOSE patched; 33 AFFECTED symbols dropped.
    `labels.parquet` built on reconstructed prices (T2.2).
  - **Issue closed.** No remaining action items — the fix is in production
    and all downstream outputs reflect corrected prices.
- **Interview one-liner:** "Diagnosis confirmed and fix fully applied —
  the unadjusted close series from the dividend folders restored COST beta
  from 28 to 0.8.  206 symbols corrected, 38 recent IPOs kept (negligible
  exposure), 33 long-corrupt names dropped.  Betas, all_merged CLOSE, and
  labels were all rebuilt on corrected prices.  Issue closed."

---

### 2. HY OAS series truncated (BAML* family, 2023+ only)

- **Symptom:** `F_BAMLH0A0HYM2_High_Yield_OAS` only 751 non-null rows
  starting 2023-07-05 in the macro grid.  Regime features built from it
  had <13% coverage.
- **Diagnosis:** Checked against manifest; confirmed start date.  All three
  BAML* series (`BAMLH0A0HYM2`, `BAMLC0A0CM`, `BAMLC0A4CBBBEY`) share the
  same 2023-07-05 start.
- **Root cause:** ICE BofA licensing restriction on FRED redistribution.
  Not a pipeline bug — the data simply isn't available before 2023 via FRED.
- **Scope:** 3 macro series.  Affects any feature built from BAML* columns.
- **Disposition:** Replaced with `F_BAA10Y_Baa_10Y_Spread` (Moody's-sourced,
  full history from 1986-01-03, 14,808 rows).  Baa−Aaa spread is slightly
  less volatile than HY OAS but carries the same credit-stress signal with
  full coverage.  BAML* columns remain in macro_merge_daily but are NOT
  used in regime features.
- **Interview one-liner:** "ICE BofA restricts FRED redistribution to the
  last ~3 years. We swapped to Moody's Baa10Y spread which starts in 1986
  and captures credit stress equally well across the full study window."

---

### 3. TEDRATE zombie (flat since LIBOR discontinuation)

- **Symptom:** `F_TEDRATE_TED_Spread` last changed 2022-01-24; forward-filled
  silently for 4+ years to present.  Appeared "live" in the grid with
  non-null values on every row.
- **Diagnosis:** Caught by macro staleness audit (`docs/macro_coverage_audit.csv`):
  `flat_trailing_days > 30` with `frequency = daily`.  TEDRATE = 3M LIBOR −
  3M T-bill; LIBOR was discontinued in early 2022.
- **Root cause:** LIBOR cessation (the underlying rate stopped publishing).
  FRED carries the last value forward rather than nulling it.
- **Scope:** 1 series.  Not used in any feature.
- **Disposition:** Flagged as zombie — do not use.  Remaining 18 "stale"
  flags in the audit are just data-lag (~90 days since latest release),
  not true zombies.
- **Interview one-liner:** "TEDRATE died with LIBOR in January 2022. Our
  staleness audit flagged it automatically — trapped in the 'every series
  that's flat for more than 30 days when it should move daily' check.
  Never entered any feature."

---

### 4. SP/ND above-MA breadth block dead until 2010-03-08

- **Symptom:** `SP_Above_200` showed 0.0000 through the entire 2008 crash
  despite the S&P 500 losing >50% — physically impossible for % of
  components above 200-day MA to be zero during a bull market.
- **Diagnosis:** Direct probe of raw column values 2002–2011: 2,058/2,519
  days = exact 0.0000.  Pre-crash "max" in 2007–2008 was 0.0000.  Crash
  "low" in 2008–2009 was 0.0000.  First non-zero value: 2010-03-08.
  After that: works normally (range 2.8%–95.8%).
- **Root cause:** Vendor/platform did not compute these columns before
  March 2010.  All four SP/ND_Above columns share the exact same
  springs-to-life date (2010-03-08).
- **Scope:** 4 columns: `SP_Above_050`, `SP_Above_200`, `ND_Above_050`,
  `ND_Above_200`.  2,435 consecutive dead days (2000-06-28 → 2010-03-05).
  Entire training window (→2011-12) has only ~21 months of live data.
- **Disposition:** `sp_above_200_pct` feature dropped as broken source column.
  Logged as reconstruction candidate: can potentially be rebuilt from
  per-stock CLOSE vs own 200d MA if constituent data is available.
- **Interview one-liner:** "The vendor didn't compute these before 2010 —
  they read 0.0 through the 2008 crash, which is how we caught it. We
  dropped the feature and flagged it as a reconstruction candidate."

---

### 5. NYSE breadth block dead until 2007-09-10

- **Symptom:** `nhnl_nyse_pct` and `trin_nyse_pct` flagged degenerate
  (f_modal = 0.55) during the degeneracy screen.  VIX front slope was
  initially blamed as "genuinely calm" but the same diagnostic found this
  block had the SAME dead-start pattern.
- **Diagnosis:** 2002-01 → 2007-09-09: 1,431/1,431 days = exact 0.0000
  (n_distinct = 1, std = 0.0000).  First movement: 2007-09-10.  After that:
  works normally (TRIN spikes to 14.1 in 2008, NHNL crashes toward 0 in
  crashes).  All 6 NYSE breadth columns (`TRIN_Z_NYSE`, `NHNL_Ratio_NYSE`,
  `Participation_NYSE`, `Fosback_NYSE`, `Advance_NYSE`, `UpVolume_NYSE`)
  share the exact same 2007-09-10 springs-to-life date.
- **Root cause:** Same vendor dead-start as the SP/ND block, with an
  earlier start date (~2007 vs ~2010).  The breadth computation was added
  to the platform in stages.
- **Scope:** 6 columns.  1,808 consecutive dead days (2000-06-28 →
  2007-09-07).  Training window has live data from 2007-09-10 onward
  (~4.3 years of the ~9.5 year window).
- **Disposition:** `trin_nyse_pct` and `nhnl_nyse_pct` KEPT.  These are
  dead pre-2007 but live through the 2008 crash and beyond — the
  clustering training window (2002→2011) includes 4+ years of genuine
  breadth signal including the single most important stress episode.
  The early-fold dead period is documented; it means breadth features
  contribute zero signal to the earliest fold years (2002–2007).
- **Interview one-liner:** "NYSE breadth starts mid-2007 in this dataset —
  another vendor coverage gap. It's live through 2008 and the rest of the
  study window, so we kept it, but the earliest training years get no
  breadth signal. Documented limitation."

---

### 6. VIX term structure columns dead-started in market_merge_daily

- **Symptom:** `vix_front_slope_pct` flagged degenerate (f_modal=0.90 in
  training window), initially misdiagnosed as "genuinely calm."  Dead-start
  sweep found all 7 MKT VIX columns dead-started: VIX_9D until 2011-01-04,
  VIX_3M until 2007-11-12, VIX_6M until 2013-11-29.
- **Diagnosis:** Same vendor dead-start pattern as breadth blocks.
  `L_VIXCLS_VIX` (macro, FRED-sourced) is clean from 2000-06-29 — only
  the MKT-derived VIX columns are affected.
- **Root cause:** Vendor/platform added VIX term structure computation in
  stages (3M ~2007, 9D ~2011, 6M ~2013).
- **Scope:** 7 columns.  `vix_front_slope_pct` was reading dead data for
  ~90% of the training window; kept because from 2007-11 it carries −VIX_3M
  signal and from 2011 genuine 9D−3M slope.  `vix_back_slope_z` excluded
  (dead through entire training window).
- **Disposition:** `vix_pct_2y` uses clean `L_VIXCLS_VIX` (unaffected).
  `vix_front_slope_pct` kept but with documented dead-start caveat.
  Feature was later dropped in the 15→11 trim (not a regime-clustering input).
- **Interview one-liner:** "The MKT-derived VIX columns start late — 9-day
  VIX in 2011, 3-month in 2007 — another vendor coverage pattern. The
  canonical 30-day VIX from FRED is clean, so our main VIX feature is solid."

---

### 7. Unclassified-threshold "stored as max" scare — measurement artifact

- **Symptom:** Recomputed panic-cluster p95 on `regime_labels.parquet` (5.81)
  ≠ frozen threshold (6.48).  Looked like the freeze step had stored max
  instead of p95.
- **Diagnosis:** `regime_labels.parquet` contains FORWARD-APPLY labels — the
  unclassified filter has already relabeled the >p95 tail as "unclassified."
  Recomputed p95 on this trimmed population (255 surviving panic days of 269
  original) is systematically lower than the correct freeze-step p95
  (computed on all 269 days).  The frozen thresholds were correct p95s all
  along (c0=3.5921, c1=6.4821, c2=3.8895, c3=2.7723).
- **Root cause:** Cluster-distribution statistics must be computed on
  pre-filter freeze-step labels (`regime_train_distances.parquet`), never on
  the threshold-filtered forward-apply labels (`regime_labels.parquet`).
- **Disposition:** No model change.  Pre-filter training distances persisted
  to `regime_train_distances.parquet`; CI assertion added against freeze-step
  p95 (not forward-apply labels); docs annotated with the distinction.
- **Interview one-liner:** "The unclassified filter trims its own tail —
  recomputing a cluster's p95 on post-filter labels understates it by
  construction. The thresholds were correct; the diagnostic was reading the
  wrong file."

- **Symptom:** `VIX_9D` pinned at 0.0 until 2011-01-04 (2,645 days).
  `VIX_3M` pinned until 2007-11-12 (1,853 days).  `VIX_6M` pinned until
  2013-11-29 (3,376 days).  `VIX_Front_Slope` (= VIX_9D − VIX_3M) showed
  exact 0.0 for 90% of training window days — initially misdiagnosed as
  "genuinely calm."
- **Diagnosis:** Dead-start sweep (Part 2 of T3.1 finalization) caught
  `lead_dead > 60` on all 7 VIX columns from MKT internals.
- **Root cause:** Same vendor dead-start pattern as breadth.
  `L_VIXCLS_VIX` (macro, FRED-sourced) is clean from 2000-06-29 — only
  the MKT-derived VIX columns are affected.
- **Scope:** 7 columns: `VIX_9D`, `VIX_3M`, `VIX_6M`, `VIX_Front_Slope`,
  `VIX_Back_Slope`, `VIX_9D_Z`, `VIX_3M_Z`.  VIX_3M is the earliest live
  (2007-11-12); VIX_9D and front slope are dead through most of the
  training window.
- **Disposition:** `vix_front_slope_pct` KEPT.  From 2007-11 to 2011-01:
  front_slope = 0 − VIX_3M = −VIX_3M (informative — captures the VIX 3M
  level with inverted sign during the 2008 crash).  After 2011-01: both
  9D and 3M are live, front slope measures the genuine term-structure
  slope.  `vix_pct_2y` uses `L_VIXCLS_VIX` (clean) and is unaffected.
- **Interview one-liner:** "The MKT-derived VIX columns start late — 9-day
  VIX in 2011, 3-month in 2007 — another vendor coverage pattern. The
  canonical 30-day VIX from FRED is clean, so our main VIX feature
  (trailing percentile) is solid. The front-slope feature captures the
  3-month VIX level from 2007 and the genuine 9D−3M slope from 2011."

---

## Coverage timeline summary

| Dimension | First live date | Dead days | Training window coverage |
|-----------|----------------|-----------|--------------------------|
| Price (MKT_SPY_CLOSE) | 2000-06-28 | 0 | Full |
| Growth/Value, GVR | 2000-06-28 | 0 | Full |
| Macro (BAA10Y, T10Y2Y, DGS10, NFCI, VIXCLS) | 2000-06-28 | 0–4 | Full |
| VIX_3M from MKT | 2007-11-12 | 1,853 | ~4.3 years |
| NYSE breadth (6 cols) | 2007-09-10 | 1,808 | ~4.3 years |
| VIX_9D / Front_Slope from MKT | 2011-01-04 | 2,645 | ~1 year |
| SP/ND above-MA (4 cols) | 2010-03-08 | 2,435 | ~1.8 years |
| VIX_6M / Back_Slope from MKT | 2013-11-29 | 3,376 | 0 (starts after train window) |

Columns with lead_dead ≤ 1 and verified live from day 1: `MKT_SPY_CLOSE`,
all GVR/Growth_vs_Value, all 5 macro series used in features.
