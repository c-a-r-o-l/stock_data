# Phase 3 — T3.1 regime features (final)

2026-07-24.  Output: `data/History_6_merge/regime_features.parquet`
(6,540 rows × 12 cols: DATE + 11 features).  Extras: `data/History_6_merge/regime_features_extras.parquet`.
Extras: `data/History_6_merge/regime_features_extras.parquet`.
Report: `docs/data_issues_log.md` items 4–6.

## Final 11 features

| # | Feature | Source raw column | Transform | Window |
|---|---------|------------------|-----------|--------|
| 1 | `spy_ret_21` | MKT_SPY_CLOSE | 21d trailing return | 21d |
| 2 | `spy_ret_63` | MKT_SPY_CLOSE | 63d trailing return | 63d |
| 3 | `spy_rvol_21` | MKT_SPY_CLOSE | ann. std of daily ret × √252 | 21d |
| 4 | `vix_pct_2y` | L_VIXCLS_VIX (macro, clean) | trailing percentile rank | 504d |
| 5 | `vix_front_slope_pct` | VIX_Front_Slope (MKT) | trailing percentile rank | 252d |
| 6 | `gv_z` | Growth_vs_Value | trailing z-score | 252d |
| 7 | `trin_nyse_pct` | TRIN_Z_NYSE | trailing percentile rank | 252d |
| 8 | `nhnl_nyse_pct` | NHNL_Ratio_NYSE | trailing percentile rank | 252d |
| 9 | `baa10y_z_1y` | F_BAA10Y_Baa_10Y_Spread (macro) | trailing z-score | 252d |
| 10 | `baa10y_chg_21` | F_BAA10Y_Baa_10Y_Spread | 21d change | 21d |
| 11 | `curve_z_1y` | M_T10Y2Y_10Y_2Y_Spread (macro) | trailing z-score | 252d |
| 12 | `curve_chg_21` | M_T10Y2Y_10Y_2Y_Spread | 21d change | 21d |
| 13 | `dgs10_z_1y` | M_DGS10_10Y_Treasury (macro) | trailing z-score | 252d |
| 14 | `dgs10_chg_21` | M_DGS10_10Y_Treasury | 21d change | 21d |
| 15 | `nfci_z_1y` | E_NFCI_Financial_Conditions (macro) | trailing z-score | 252d |

## Dropped features (with reasons)

| Feature | Reason | Decision log |
|---------|--------|-------------|
| `sp_above_200_z` | Source column dead until 2010-03-08 (broken for >90% of training window) | data_issues_log #4 |
| `sp_above_200_pct` | Same broken source; percentile conversion didn't help | data_issues_log #4 |
| `vix_back_slope_z` | 48% exact zeros from zero-variance stretches; raw source dead-started 2013-11-29 | data_issues_log #6 |
| `partic_nyse_z` | r=0.68 with nhnl_nyse_z; third short-term breadth measure of one concept | decision_log |
| `sp_above_050_z` | r=0.76 with sp_above_200_z; judgment override (below 0.85 threshold, dimension-budget call) | decision_log |
| `hy_z_1y`, `hy_chg_21` | Source truncated (BAML*, 2023+); swapped for BAA10Y | data_issues_log #2 |

## Credit swap

`F_BAMLH0A0HYM2_High_Yield_OAS` → `F_BAA10Y_Baa_10Y_Spread` (Moody's,
1986-01-03 → present, 14,808 rows).  Baa−Aaa spread is slightly less
volatile than HY OAS but has full history and the correct stress-direction
(widens in crisis).  BAML* family is ICE-licensing-truncated on FRED
(2023+ only).

## Degeneracy & dead-start audit

Z-score guard (returning 0.0 when trailing std < 1e-10) was initially
blamed for feature degeneracy.  Root cause proved to be vendor dead-start:
the raw MKT-derived columns are exact 0.0 for years before springing to
life.  Percentile-rank conversion didn't change degeneracy rates because
the raw values themselves don't vary.  See `docs/data_issues_log.md` #4–6
and `docs/raw_flagged_2002_2011.png`.

| Column family | First live | Training window impact |
|--------------|-----------|----------------------|
| Price, GVR, all macro | 2000-06-28 | Full coverage |
| VIX_3M (MKT) | 2007-11-12 | Live from 2007 |
| NYSE breadth (6 cols) | 2007-09-10 | Live from 2007, includes 2008 |
| SP/ND above-MA (4 cols) | 2010-03-08 | >90% dead — DROPPED |
| VIX_9D / Front_Slope (MKT) | 2011-01-04 | Dead pre-2011; carries −VIX_3M signal 2007–2011 |
| VIX_6M / Back_Slope (MKT) | 2013-11-29 | Dead through entire training window — DROPPED |

## Correlation screen (train ≤ 2011-12, 2,393 complete cases)

Zero pairs ≥ |r| = 0.85.  Top pair: `vix_pct_2y` ↔ `baa10y_z_1y` at r=0.71.
`dgs10_chg_21` ↔ `curve_chg_21` at r=0.51.  All within range.

## Leakage assertions — ALL PASS

- 4a: 3+ manual recomputes match exactly
- 4b: Future-corruption test on 4 features — all pre-t0 values bit-identical
- 4c: No full-series `.mean()`/`.std()`/`.quantile()` in feature code
- Spot checks on percentile and z-score features all match to machine precision

## Effective start

**2002-07-03** (6,037 complete cases).  VIX 504d percentile is the bottleneck.

## Output files

| File | Content |
|------|---------|
| `regime_features.parquet` | DATE + 11 features, 6,540 rows |
| `regime_features_extras.parquet` | Rejected features (vix_back_slope_z) |
| `regime_raw_inputs.parquet` | Whitelisted raw columns before transforms |
