# Indicator specification — partial, pending formula

Committed 2026-07-19 by carol. Formula held by partner.
This document will be **extended, not rewritten**, when the formula is
transcribed. See `docs/decision_log.md` entry for context.

## 1. Exports received

Three CSV/TXT export sets, one per frequency (daily, weekly, monthly),
covering the project universe. Per-file hashes are in
`indicator/hashes/pv_<freq>_files.sha256`; aggregate hashes below.

| Frequency | Source folder | Aggregate sha256 |
|-----------|---------------|------------------|
| Daily     | `data/History_1_D` | `fd262fcb1b1b3de70fca4c94f1857ad06eb5b6994297d7fd4bb36db9ff325b6e` |
| Weekly    | `data/History_2_W` | `c56c850a159ffea960e059121e4fb9829c6bdb2afdd42860e87cb96ebec94f1e` |
| Monthly   | `data/History_3_M` | `cb343a25c86f15cb32aebe6e6aa53b9892cf0b931fc85d3a33510b11390506d6` |

Each raw file contains 13 PV columns (the clean pass drops `PV_BULL` and
`PV_BEAR` sentinel columns, keeping 11).  The files also appear in the
`_clean` folders and in `all_merged.parquet`; the raw folders are the
authoritative export sets.

## 2. Columns present (11 per row after cleaning)

- `Trend_PV` — signed integer. Sign indicates trend direction (positive =
  bull, negative = bear); magnitude indexes the leg number within the
  current trend. Observed range in the daily sample across AAPL, JPM,
  NVDA, COHR: −11 to +17.
- Bull-side (active during bull trends; zero-sentinels during bear trends):
  `PV_BULL_STEP`, `PV_BULL_START`, `PV_BULL_STOP`, `PV_BULL_CNT`, `PV_BULL_H`
- Bear-side (active during bear trends; zero-sentinels during bull trends):
  `PV_BEAR_STEP`, `PV_BEAR_START`, `PV_BEAR_STOP`, `PV_BEAR_CNT`, `PV_BEAR_L`

Apparent semantics, **inferred from column values, not confirmed against the
formula**:
- `START` — trend-origin price, fixed within a trend
- `STOP` — trailing invalidation level, stepping on leg increments
- `H` / `L` — trend extreme so far
- `CNT` — bar count within the trend
- `STEP` — bar count within the current leg

Raw files additionally contain bare `PV_BULL` and `PV_BEAR` sentinel columns
(13 total); these are dropped by `src/1_clean_tech.py` during cleaning.

## 3. Known gaps — to be resolved when formula is available

- Exact rule defining a leg, a leg increment, and a trend flip
- Origin-selection rule (open puzzle: in the sample, some trend origins equal
  the prior trend's extreme and others don't — e.g., bull `START=17.85` equals
  prior bear low, but next bull `START=19.04` does not equal prior bear low
  16.83; likewise bear `START=22.26` equals prior bull `H` but bear
  `START=19.68` does not equal prior bull `H` 20.13)
- Any numerical thresholds inside the formula (needed for perturbation checks
  per Phase 8 / T8.2)
- Repaint behavior — whether the state assigned at bar t uses information
  from bars later than t
- Which of daily / weekly / monthly is the study frequency (OQ2)
- Encoding rules for the structure state axis: intact vs. broken definition,
  leg bucketing, distance-from-origin normalization (percent vs. absolute),
  completed-bar alignment rule for non-daily frequencies
- Provenance: whether the indicator was implemented as a vendor built-in or
  as a user script on the charting platform

## 4. What has NOT been done as of this commit

- No PV column has been joined to any forward return, label, or
  return-derived quantity
- No frequency has been chosen (OQ2 open)
- No encoding has been applied
- No repaint test has been performed
- No perturbation checks have been performed (impossible without the formula)

## 5. Extension protocol

When the formula is transcribed, append a new section `## 6. Formula (added
<date>)` to this file rather than editing sections 1–4. Add a new decision-log
entry citing the git commit that adds the formula. The intent is that the
file's git history serves as the audit trail for what was known when.
