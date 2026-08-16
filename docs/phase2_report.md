# Phase 2 — T2.1 point-in-time betas

2026-07-19.  Output: `data/History_6_merge/betas.parquet`.

## §1 Daily returns

- Source: `tech_daily.csv`, close column = `CLOSE`
- SPY non-null returns: 8,187 (full 1986→2026 history)
- 1,060 rows with |r| > 0.5 (meme-stock moves, earnings gaps — all appear
  to be real price data, not split artifacts; splits confirmed adjusted in
  Phase 1)

## §2 Rolling beta

- Method: pandas groupby rolling (polars `rolling_var` not available in
  this env; 1.4s wall time for 1.66M rows across 313 symbols)
- Window: 252 trading days ending at t−1 (shift-1 enforced)
- Fallback: β̂ = 1 if fewer than 126 valid returns in window
- Fallback rows: 107,723 (6.5% — mostly the first 252 days per symbol)

### Distribution of raw β̂

| Stat | Value |
|------|-------|
| min | −125.07 |
| p01 | −0.25 |
| p25 | 0.76 |
| median | 1.00 |
| p75 | 1.33 |
| p99 | 3.05 |
| max | 47.43 |

Heavy tails from small/illiquid names with noisy return series — winsorized in §3.

## §3 Winsorization

Cross-sectional per-day, 1st/99th percentile.

- Clipped at upper bound: 15,841 rows
- Clipped at lower bound: 15,845 rows
- Total clipped: 31,686 (1.9%)

### β̂_winsor distribution

| Stat | Value |
|------|-------|
| min | −1.40 |
| median | 1.00 |
| max | 18.77 |

## §4 Blume shrinkage

β* = 0.67 × β̂_winsor + 0.33

| Stat | Value |
|------|-------|
| min | −0.61 |
| median | 1.00 |
| max | 12.91 |

## §5 Output

`data/History_6_merge/betas.parquet` — 1,664,246 rows × 4 columns:
- `SYMBOL`, `DATE`, `beta_raw` (= β̂_winsor), `beta_star` (= β*)

## §6 Sanity checks — ALL PASS

### 6a No look-ahead

Manual β̂ recomputed for 3 random (symbol, date) rows using only returns
strictly before t.  All three match to 4 decimal places (Δ = 0.0000).
The stored beta uses no future information.

### 6b Known betas pass smell test

| Symbol | mean β* | Expected |
|--------|---------|----------|
| KO | 0.68 | Below 1 (defensive staple) |
| PG | 0.61 | Below 1 (defensive staple) |
| JNJ | 0.68 | Below 1 (defensive healthcare) |
| NVDA | 1.53 | Above 1 (high-beta tech) |
| META | 1.22 | Above 1 (tech) |
| TSLA | 1.37 | Above 1 (high-beta) |
| SPY | 1.00 | Exactly 1 (market) |

### 6c SPY beta ≡ 1

SPY mean β* = 1.0000, std = 0.0000.  Trivially correct (regressing market
on itself).

## Notes

- TSLA and META are present in the universe (large-cap Nasdaq/S&P names).
- The 1060 |r| > 0.5 moves include AMC's +301.3% (Jan 2021 meme squeeze)
  and AAPL's −52.1% (Sep 2000 dot-com crash).  These are real prices.
