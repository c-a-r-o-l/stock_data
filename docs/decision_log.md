# Decision log

Chronological record of design decisions.  Each entry links the commit
that implemented it.  See also `doc/Plan4_Implementation_Guide.html` §1
for the canonical decision ledger (D1–D15).

---

## 2026-07-29 — T3.2c episode reconciliation + Phase 3 close

### c0/c2 gate discrepancy resolved — population difference, not a segmentation bug

- T3.2c reported c0=6 and c2=11 on forward-apply labels vs gate's 8 and 14.
  Re-segmented on freeze-step labels (`regime_train_distances.parquet`) using
  the identical T3.2c code path → 8/9/14/6 reproduced exactly.
- **Cause:** The unclassified filter relocated 35 c0 days and 33 c2 days to
  'unclassified' (none to other clusters).  These days broke contiguous
  freeze-step runs, and some remnants fell below the 10-day floor (dropped as
  transitions).  Total days across all categories still sums to 6,037.
- **Verdict:** Legitimate D9 behavior — the p95 threshold trims the tail,
  fragmenting some episodes.  Not a bug.  Phase 3 episode logic is sound.

### Robustness: COVID panic episode near the 10-day floor

- The 2020 COVID panic episode is 12 trading days (2020-02-27 → 2020-03-13),
  just above `episode_min_len`=10.  Raising the floor to 15 drops it,
  reducing sealed-window panic episodes from 3 to 2.
- **Flagged for Phase 8**: the perturbation of `episode_min_len` in the
  robustness suite must check whether this changes the sealed panic
  sufficiency verdict (D6/D8).  A 3→2 drop is material.

### Unclassified merge choice safe for stress regimes

- Default (merge same-regime unclassified blips) vs strict (never merge)
  changes panic episode count by +1 (13→14) but non-stress regimes by
  +7–8.  Stress regimes are near-invariant to the choice — the decision
  primarily affects calm-regime episode counts.

### Phase 3 closed

- T3.1 (features), T3.2a (k-selection), T3.2b (freeze + forward apply),
  T3.2c (episodes + D6 sufficiency) all complete.  Regime labels at
  `regime_labels.parquet`, episodes at `regime_episodes.parquet`.
  Phase 4 (financial-state clustering) is next.

---

## 2026-07-26 — D3 universe amendment (dividend-correction coverage)

### Finding

- **Dividend fix verified** (`docs/new_folders_verification.md` V5):
  close_unadj from `History_4_F_Dividend/` restores COST β 24.6→0.815;
  identity bound |β| ≤ σ_stock/σ_market now holds.  close_unadj is
  bit-identical across Dividend / Dividend_Correct folders (V4).
- **Coverage gap:** 71 of 277 clean-universe symbols have no dividend
  schedule and cannot be corrected (`docs/coverage_amendment_analysis.md`).
  Of these, only **33 are genuinely affected** (min_close < $5 with pre-2021
  history — the subtractive-dividend bug has materially corrupted their
  CLOSE).  The remaining **38 are NEGLIGIBLE**: post-2021 IPOs whose entire
  price history falls in the period where the bug has ≤2.6% impact
  (the gap signature confirmed in V4 shrinks toward zero by 2020+).

### Decision (D3 amendment)

The Phase 2 universe is amended from 277 clean-fundamentals symbols to:

- **206 fully corrected** — symbols with dividend schedules; CLOSE will be
  reconstructed from close_unadj before T2.1 rerun.
- **38 NEGLIGIBLE retained** — no dividend schedule, but bug exposure is
  immaterial for post-2021-starting histories; CLOSE used as-is with
  documented caveat.
- **33 AFFECTED dropped** — no dividend schedule AND materially corrupt
  CLOSE in pre-2021 history.  Analysis on knowingly-corrupt prices is the
  thing being avoided.
- **36 ETFs retained** — no fundamentals, no dividend needed; price data
  is clean (split-adjusted only, confirmed in Phase 1).
- **Total: 280 symbols** (206 + 38 + 36), down from the original 280 effective
  (277 stocks + 36 ETFs = 313 minus 33 dropped = 280).

The 33 AFFECTED symbols dropped:
`APLD BBBY BMNR CELH CLSK CROX CYTK DKS EGO EQX ET FTAI GFI GLXY HUT IAG
KGC MXL PAAS PACB PEP POET QXO RGLD RIG SAIA SEI SGI SIMO SSRM TE TGTX WPM`

### Signed skew

The drop is NOT random — it skews away from precious-metals miners (9/33:
KGC, PAAS, WPM, RGLD, GFI, IAG, EGO, SSRM, EQX), crypto-adjacent names
(CLSK, HUT, GLXY), and small-cap cyclicals.  The restricted universe
under-represents inflation-sensitive and risk-off signals.  This is
a known survivor bias within the already-admitted survivorship-bias
universe (D3) and must be signed in the write-up.

### Cross-section viability

The restricted universe (280 symbols) stays above min_cross_section=100
(T1.3 default) for all years from 1999 onward — the entire Phase 2 study
window (2002+).  Pre-1999 years were already below 100 in the full universe
and are outside the regime-feature coverage window.  No fold-boundary
interaction (losses are smoothly distributed across years).

### Implementation requirement

The D3 amendment requires a config universe-list update (`config.yaml`)
before Phase 4 (financial-state clustering).  **Do NOT make that config
change here — this is a decision entry, not a config edit.**  The
reconstruction itself (rebuilding CLOSE from close_unadj) must be applied
to the pipeline before T2.1 is rerun; betas.parquet and all_merged.parquet
currently carry buggy prices.

### Cross-references

- `doc/Plan4_Implementation_Guide.html` §D3 (canonical universe definition)
- `docs/coverage_amendment_analysis.md` (full classification, A1–A3)
- `docs/new_folders_verification.md` (dividend fix verification, V1–V6)
- `docs/data_issues_log.md` issue #1 (subtractive dividend adjustment)

---

## 2026-07-24 — T3.1 feature finalization decisions

### sp_above_050_z rejected (judgment call, r=0.76 < 0.85 threshold)

- Correlation with `sp_above_200_z` was r=0.76 — below the pre-set 0.85
  automatic-drop threshold.
- **Override reason:** Dimension-budget judgment.  SP_Above_200_z already
  represents the trend-breadth concept; adding SP_Above_050_z would give
  trend breadth 2 of 16 feature slots (~12.5%) for two versions of the same
  underlying construct.
- **Decision:** Rejected as a dimension-budget override, not by the
  automatic correlation rule.  Noted for transparency — a different
  analyst could reasonably keep it.
- **Follow-up:** `sp_above_200` was later found to be BROKEN-RAW (dead until
  2010-03-08), making the override moot for the current dataset.  If
  reconstructed, the same judgment should be revisited.

### vix_back_slope_z excluded as degenerate (distributional grounds)

- Promoted on r=0.57 vs front slope, but rebuilt feature was 48% exact
  zeros from zero-variance stretches in raw VIX_Back_Slope (3M−6M spread).
- Correlation screen returned NaN (could not evaluate), masking the
  degeneracy.
- **Decision:** Excluded on degeneracy grounds, NOT on correlation grounds.
  The raw column was later found to be dead-started (first live 2013-11-29),
  confirming the exclusion.

### dgs10_chg_21 restored; partic_nyse_z dropped

- `dgs10_chg_21` re-added as the swap counterpart to `vix_back_slope_z`,
  balancing rates at 4 features for 2 concepts (level + shape × z + chg).
  Credit balanced at 2 features (BAA10Y z + chg).
- `partic_nyse_z` dropped: r=0.68 with `nhnl_nyse_z`, third short-term
  breadth measure of one concept.  TRIN + NHNL adequately represent NYSE
  breadth.

### Breadth/trend coverage → OQ6 training-window tension

- **Finding:** All breadth and VIX-term-structure columns in
  market_merge_daily are dead-started:
  - NYSE breadth (6 cols): dead until 2007-09-10 (first 1,808 days)
  - VIX_3M from MKT: dead until 2007-11-12
  - SP/ND above-MA (4 cols): dead until 2010-03-08 (first 2,435 days)
  - VIX_9D / Front_Slope: dead until 2011-01-04
  - VIX_6M / Back_Slope: dead until 2013-11-29
- **Impact on training window (2000-07 → 2011-12):** NYSE breadth is live
  for ~4.3 years (including 2008 crash).  SP/ND trend breadth is live for
  ~1.8 years.  VIX front slope is ~dead/stub (0 − VIX_3M) until 2011.
  Price, macro, and GVR features are live from day 1.
- **This is an OQ6 tension, not a bug.** Two options:
  - (A) Keep the window; early-fold regimes defined mainly by macro/price/
    vol features (all live).  Breadth enters from ~2007, trend from ~2010.
    The oldest clusters may be under-informed on breadth dimensions.
  - (B) Move training start to ~2007–2008 so all features are live, at the
    cost of shorter pre-validation history.
- **Decision:** NOT settled here.  Partner decision tied to OQ2/OQ6.
  Documented; window boundary unchanged.
- **See:** `docs/data_issues_log.md` items 4–6.

### Feature matrix frozen at 15 (one rebuild pending)

- `sp_above_200_pct` dropped — broken source column.
- `trin_nyse_pct` and `nhnl_nyse_pct` kept — live from 2007-09-10,
  including the 2008 crash episode.
- `vix_front_slope_pct` kept — carries −VIX_3M signal from 2007, genuine
  front-slope signal from 2011.
- Final 15: spy_ret_21, spy_ret_63, spy_rvol_21, vix_pct_2y,
  vix_front_slope_pct, gv_z, trin_nyse_pct, nhnl_nyse_pct,
  baa10y_z_1y, baa10y_chg_21, curve_z_1y, curve_chg_21,
  dgs10_z_1y, dgs10_chg_21, nfci_z_1y.
- One clean rebuild to `regime_features.parquet` pending confirmation.
