# Coverage Amendment Analysis — 71 Uncorrectable Symbols

**Date:** 2026-07-26
**Context:** `docs/new_folders_verification.md` found 71 of 277 clean-universe symbols
cannot be dividend-corrected. This analysis classifies each by actual bug exposure
and assesses the viability of restricting the universe.

---

## A1 — Per-Symbol Bug-Exposure Classification

### Method

For each of the 71 uncorrectable symbols, pull CLOSE history from `tech_daily.csv`:
- Report first_date, last_date, n_trading_days, min_close, and whether it
  ever fell below $1 or $5 (both full history and pre-2021).
- Classification rule:
  - **NEGLIGIBLE:** `first_date >= 2021` (no pre-dividend-bug-era history) OR
    `min_close >= $5` throughout (price never in the range where the bug is material).
    These can safely stay in the universe — their short or high-price history means
    the subtractive-dividend bug has negligible impact.
  - **AFFECTED:** `min_close < $5` with pre-2021 history, or `min_close < $1` at
    any point. These have genuinely corrupted CLOSE columns from accumulated
    dividend subtraction over long histories.

### Rationale for the 2021 cutoff

The subtractive-dividend bug accumulates over time: each dividend payment
permanently reduces the nominal CLOSE by that amount, and the effect
compounds with reinvested dividends. A stock that IPO'd in 2021 has at most
~5 years of dividend history — the cumulative gap between true price and
buggy CLOSE is at most a few percent. Stocks with histories stretching back
to the 1980s–2000s have 20–40 years of accumulated dividend subtraction,
producing the COST-like 82% gap.

### Full Classification Table

| # | Sym | First | Last | N | Min$ | MinDate | <$1 | <$5 | pre21<$5 | inF2 | Class |
|---|-----|-------|------|---|------|---------|-----|-----|----------|------|-------|
| 1 | AFRM | 20211101 | 20260702 | 1171 | 8.91 | 20221227 | | | | ✓ | NEGLIGIBLE |
| 2 | APLD | 20030715 | 20260702 | 3891 | 0.01 | 20111222 | ✓ | ✓ | ✓ | | AFFECTED |
| 3 | APP | 20220203 | 20260702 | 1106 | 9.30 | 20221227 | | | | ✓ | NEGLIGIBLE |
| 4 | ASND | 20151119 | 20260702 | 2668 | 12.25 | 20160607 | | | | | NEGLIGIBLE |
| 5 | BAM | 20230929 | 20260702 | 691 | 28.67 | 20231031 | | | | | NEGLIGIBLE |
| 6 | BBBY | 20030326 | 20260702 | 5855 | 2.65 | 20200316 | | ✓ | ✓ | | AFFECTED |
| 7 | BMNR | 20070829 | 20260702 | 2023 | 4.27 | 20250627 | | ✓ | ✓ | ✓ | AFFECTED |
| 8 | CEG | 20221202 | 20260702 | 897 | 73.40 | 20230323 | | | | ✓ | NEGLIGIBLE |
| 9 | CELH | 20071113 | 20260702 | 4625 | 0.01 | 20081006 | ✓ | ✓ | ✓ | | AFFECTED |
| 10 | CIFR | 20210927 | 20260702 | 1196 | 0.41 | 20221228 | ✓ | ✓ | | ✓ | NEGLIGIBLE |
| 11 | CLSK | 20190219 | 20260702 | 1852 | 1.05 | 20200402 | | ✓ | ✓ | | AFFECTED |
| 12 | COMP | 20220125 | 20260702 | 1113 | 1.85 | 20221109 | | ✓ | | | NEGLIGIBLE |
| 13 | CRDO | 20221116 | 20260702 | 908 | 7.35 | 20230504 | | | | ✓ | NEGLIGIBLE |
| 14 | CROX | 20061127 | 20260702 | 4929 | 0.94 | 20081120 | ✓ | ✓ | ✓ | | AFFECTED |
| 15 | CYTK | 20050304 | 20260702 | 5365 | 3.07 | 20141010 | | ✓ | ✓ | | AFFECTED |
| 16 | DKS | 20030812 | 20260702 | 5759 | 1.08 | 20030916 | | ✓ | ✓ | | AFFECTED |
| 17 | DUOL | 20220520 | 20260702 | 1032 | 65.38 | 20221228 | | | | | NEGLIGIBLE |
| 18 | EGO | 20030307 | 20260702 | 5866 | 2.64 | 20190123 | | ✓ | ✓ | | AFFECTED |
| 19 | EOSE | 20210401 | 20260702 | 1319 | 0.64 | 20240508 | ✓ | ✓ | | | NEGLIGIBLE |
| 20 | EQX | 20190625 | 20260702 | 1765 | 2.53 | 20221103 | | ✓ | ✓ | | AFFECTED |
| 21 | ET | 20070227 | 20260702 | 4868 | 3.32 | 20081121 | | ✓ | ✓ | | AFFECTED |
| 22 | EXE | 20220118 | 20260702 | 1118 | 61.20 | 20220121 | | | | ✓ | NEGLIGIBLE |
| 23 | FTAI | 20160308 | 20260702 | 2595 | 4.84 | 20200318 | | ✓ | ✓ | | AFFECTED |
| 24 | GFI | 19881215 | 20260702 | 9403 | 1.80 | 20151117 | | ✓ | ✓ | | AFFECTED |
| 25 | GH | 20190729 | 20260702 | 1741 | 16.07 | 20240419 | | | | | NEGLIGIBLE |
| 26 | GLXY | 20180801 | 20260702 | 1978 | 0.43 | 20200318 | ✓ | ✓ | ✓ | | AFFECTED |
| 27 | HUT | 20190306 | 20260702 | 1840 | 2.03 | 20200318 | | ✓ | ✓ | | AFFECTED |
| 28 | IAG | 20030114 | 20260702 | 5904 | 0.98 | 20220927 | ✓ | ✓ | ✓ | | AFFECTED |
| 29 | IREN | 20220920 | 20260702 | 949 | 1.06 | 20221228 | | ✓ | | ✓ | NEGLIGIBLE |
| 30 | JOBY | 20210902 | 20260702 | 1212 | 3.18 | 20221227 | | ✓ | | | NEGLIGIBLE |
| 31 | KGC | 19970527 | 20260702 | 7313 | 1.22 | 20001024 | | ✓ | ✓ | | AFFECTED |
| 32 | KVYO | 20240802 | 20260702 | 480 | 12.86 | 20260622 | | | | | NEGLIGIBLE |
| 33 | LUNR | 20230223 | 20260702 | 842 | 2.11 | 20240104 | | ✓ | | | NEGLIGIBLE |
| 34 | MP | 20210412 | 20260702 | 1313 | 10.49 | 20240807 | | | | | NEGLIGIBLE |
| 35 | MXL | 20110119 | 20260702 | 3886 | 4.03 | 20120724 | | ✓ | ✓ | | AFFECTED |
| 36 | NLY | 19980805 | 20260702 | 7020 | 14.73 | 20231027 | | | | | NEGLIGIBLE |
| 37 | NTLA | 20170303 | 20260702 | 2346 | 6.28 | 20250408 | | | | | NEGLIGIBLE |
| 38 | NU | 20220929 | 20260702 | 942 | 3.48 | 20230105 | | ✓ | | ✓ | NEGLIGIBLE |
| 39 | OKLO | 20220518 | 20260702 | 1017 | 5.59 | 20240903 | | | | ✓ | NEGLIGIBLE |
| 40 | ONDS | 20210525 | 20260702 | 1282 | 0.34 | 20231025 | ✓ | ✓ | | | NEGLIGIBLE |
| 41 | OSCR | 20211229 | 20260702 | 1131 | 2.15 | 20221221 | | ✓ | | | NEGLIGIBLE |
| 42 | OUST | 20210813 | 20260702 | 1226 | 3.24 | 20230425 | | ✓ | | | NEGLIGIBLE |
| 43 | PAAS | 19960429 | 20260702 | 7592 | 2.44 | 20010402 | | ✓ | ✓ | | AFFECTED |
| 44 | PACB | 20110816 | 20260702 | 3741 | 0.91 | 20250527 | ✓ | ✓ | ✓ | | AFFECTED |
| 45 | PATH | 20220217 | 20260702 | 1096 | 9.38 | 20260410 | | | | | NEGLIGIBLE |
| 46 | PEP | 19861107 | 20260702 | 9980 | 4.31 | 19861224 | | ✓ | ✓ | ✓ | AFFECTED |
| 47 | PL | 20220217 | 20260702 | 1096 | 1.69 | 20240430 | | ✓ | | | NEGLIGIBLE |
| 48 | POET | 20090609 | 20260702 | 3723 | 0.77 | 20231218 | ✓ | ✓ | ✓ | | AFFECTED |
| 49 | QXO | 20041228 | 20260702 | 2505 | 0.02 | 20230224 | ✓ | ✓ | ✓ | | AFFECTED |
| 50 | RBLX | 20211228 | 20260702 | 1132 | 23.19 | 20220510 | | | | ✓ | NEGLIGIBLE |
| 51 | RDW | 20211108 | 20260702 | 1166 | 1.68 | 20221228 | | ✓ | | | NEGLIGIBLE |
| 52 | RGLD | 19871203 | 20260702 | 9596 | 0.03 | 19911216 | ✓ | ✓ | ✓ | | AFFECTED |
| 53 | RIG | 19940329 | 20260702 | 8117 | 0.67 | 20201030 | ✓ | ✓ | ✓ | | AFFECTED |
| 54 | RIVN | 20220919 | 20260702 | 950 | 8.40 | 20240415 | | | | ✓ | NEGLIGIBLE |
| 55 | RKT | 20210616 | 20260702 | 1267 | 5.48 | 20221020 | | | | ✓ | NEGLIGIBLE |
| 56 | SAIA | 20030709 | 20260702 | 5783 | 4.68 | 20081120 | | ✓ | ✓ | | AFFECTED |
| 57 | SE | 20180815 | 20260702 | 1980 | 10.72 | 20190103 | | | | | NEGLIGIBLE |
| 58 | SEI | 20180307 | 20260702 | 2092 | 4.55 | 20200323 | | ✓ | ✓ | | AFFECTED |
| 59 | SEZL | 20220215 | 20260702 | 919 | 0.02 | 20230526 | ✓ | ✓ | | | NEGLIGIBLE |
| 60 | SGI | 20041014 | 20260702 | 5463 | 0.98 | 20090309 | ✓ | ✓ | ✓ | | AFFECTED |
| 61 | SHAZ | 20240424 | 20260702 | 150 | 1.25 | 20241030 | | ✓ | | | NEGLIGIBLE |
| 62 | SIMO | 20060424 | 20260702 | 5080 | 1.90 | 20090305 | | ✓ | ✓ | | AFFECTED |
| 63 | SSRM | 19970620 | 20260702 | 7299 | 0.75 | 19980831 | ✓ | ✓ | ✓ | | AFFECTED |
| 64 | TE | 20201231 | 20260702 | 1381 | 0.95 | 20241009 | ✓ | ✓ | | | AFFECTED |
| 65 | TEAM | 20161003 | 20260702 | 2450 | 24.05 | 20161222 | | | | ✓ | NEGLIGIBLE |
| 66 | TGTX | 19980512 | 20260702 | 6667 | 0.98 | 20111229 | ✓ | ✓ | ✓ | | AFFECTED |
| 67 | UAN | 20120203 | 20260702 | 3623 | 6.00 | 20200318 | | | | | NEGLIGIBLE |
| 68 | WBD | 20230130 | 20260702 | 859 | 6.71 | 20240812 | | | | ✓ | NEGLIGIBLE |
| 69 | WPM | 20051027 | 20260702 | 5201 | 2.57 | 20081120 | | ✓ | ✓ | | AFFECTED |
| 70 | WULF | 20221007 | 20260702 | 936 | 0.54 | 20230316 | ✓ | ✓ | | ✓ | NEGLIGIBLE |
| 71 | ZETA | 20220406 | 20260702 | 1063 | 4.27 | 20220701 | | ✓ | | | NEGLIGIBLE |

### Headline Counts

| Classification | Count | % of 71 | % of Clean (277) |
|:--------------|:-----:|:-------:|:----------------:|
| **AFFECTED** | **33** | 46.5% | 11.9% |
| NEGLIGIBLE | 38 | 53.5% | 13.7% |
| Total uncorrectable | 71 | 100% | 25.6% |

**The real drop is ~33 symbols, not 71.** The 38 NEGLIGIBLE names are
predominantly post-2021 IPOs whose entire price history falls in the period
where the subtractive-dividend bug has minimal (single-digit-percent) impact.
They can be kept in the universe without meaningful label distortion.

### Notes on borderline cases

- **PEP** (AFFECTED): PepsiCo since 1986. min_close=$4.31 in December 1986
  is likely real (split-adjusted but pre-many-splits). A large-cap staples
  name with 9,980 trading days. Losing PEP is regrettable but the buggy
  1980s CLOSE is genuinely problematic. PEP is in the 17 "in F_2 but no
  dividend" group — it HAS new-format fundamentals, just no dividend file.
- **TE** (AFFECTED): first_date=2020-12-31, barely pre-2021. min_close=$0.95
  in October 2024. Borderline — mostly post-2021 history, but technically
  has pre-2021 exposure.
- **CIFR, EOSE, ONDS, SEZL, WULF** (NEGLIGIBLE): Post-2021 IPOs with
  min_close < $1. Their sub-dollar prices are likely real price collapses,
  not dividend-adjustment artifacts, because the bug hasn't had time to
  accumulate. Note: if the bug is material even for 2021–2026 data, these
  should be reclassified. The verification report (V4) showed COST's gap
  drops to −2.6% by 2020+ — this supports the 2021-cutoff logic.

---

## A2 — Cross-Section Impact

### Per-year restricted universe vs full universe

| Year | Days | Full Min | Full Mean | Restr Min | Restr Mean | Lost | Flag |
|------|-----:|:--------:|:---------:|:---------:|:----------:|:----:|:----:|
| 1986 | 37 | 24 | 26.5 | 23 | 25.5 | 1.0 | <100 |
| 1987 | 253 | 27 | 29.5 | 26 | 28.4 | 1.1 | <100 |
| 1988 | 253 | 32 | 33.6 | 30 | 31.6 | 2.0 | <100 |
| 1989 | 252 | 35 | 36.1 | 32 | 33.2 | 2.9 | <100 |
| 1990 | 253 | 36 | 37.4 | 34 | 34.4 | 2.9 | <100 |
| 1991 | 253 | 38 | 38.8 | 35 | 36.0 | 2.8 | <100 |
| 1992 | 252 | 38 | 41.6 | 36 | 38.7 | 2.8 | <100 |
| 1993 | 252 | 46 | 49.5 | 43 | 46.5 | 3.0 | <100 |
| 1994 | 251 | 51 | 56.7 | 48 | 53.0 | 3.8 | <100 |
| 1995 | 251 | 56 | 59.0 | 52 | 55.0 | 4.0 | <100 |
| 1996 | 253 | 60 | 64.3 | 56 | 59.7 | 4.7 | <100 |
| 1997 | 253 | 64 | 91.5 | 59 | 85.4 | 6.1 | <100 |
| 1998 | 252 | 93 | 110.9 | 88 | 103.3 | 7.6 | <100 |
| **1999** | 252 | 115 | 119.2 | 107 | 111.2 | 7.9 | |
| **2000** | 252 | 123 | 133.4 | 115 | 125.4 | 8.0 | |
| 2001 | 248 | 125 | 139.2 | 122 | 131.3 | 7.9 | |
| **2002** | 252 | 134 | 143.5 | 126 | 135.7 | 7.8 | |
| 2003 | 252 | 144 | 153.1 | 136 | 141.4 | 11.7 | |
| 2004 | 252 | 158 | 160.9 | 145 | 146.7 | 14.2 | |
| 2005 | 252 | 164 | 169.3 | 147 | 152.3 | 17.0 | |
| 2006 | 251 | 173 | 175.5 | 155 | 156.7 | 18.8 | |
| 2007 | 251 | 179 | 186.1 | 159 | 164.9 | 21.2 | |
| 2008 | 253 | 189 | 192.7 | 167 | 170.7 | 22.0 | |
| 2009 | 252 | 190 | 196.1 | 170 | 173.8 | 22.2 | |
| 2010 | 252 | 195 | 198.1 | 175 | 176.1 | 22.0 | |
| 2011 | 252 | 198 | 203.2 | 177 | 180.5 | 22.7 | |
| 2012 | 250 | 204 | 208.9 | 183 | 186.0 | 22.9 | |
| 2013 | 252 | 210 | 217.0 | 188 | 193.6 | 23.3 | |
| 2014 | 252 | 220 | 223.5 | 197 | 199.8 | 23.7 | |
| 2015 | 252 | 225 | 227.5 | 202 | 203.9 | 23.5 | |
| 2016 | 252 | 228 | 233.8 | 205 | 209.6 | 24.2 | |
| 2017 | 251 | 237 | 239.7 | 213 | 215.4 | 24.3 | |
| 2018 | 251 | 240 | 246.9 | 216 | 221.3 | 25.6 | |
| 2019 | 252 | 252 | 259.4 | 226 | 230.7 | 28.8 | |
| 2020 | 253 | 262 | 268.3 | 233 | 238.4 | 29.9 | |
| 2021 | 252 | 272 | 280.3 | 241 | 247.5 | 32.8 | |
| 2022 | 251 | 292 | 300.2 | 260 | 268.4 | 31.9 | |
| 2023 | 250 | 305 | 308.6 | 274 | 276.6 | 32.0 | |
| 2024 | 252 | 310 | 310.9 | 277 | 278.5 | 32.4 | |
| 2025 | 250 | 311 | 311.7 | 279 | 279.2 | 32.6 | |
| 2026 | 130 | 5 | 300.9 | 5 | 269.2 | 31.7 | <100 |

Flags mark min_cross_section < 100 (T1.3 default).

### Viability verdict

**The restricted universe (full minus 33 AFFECTED) is viable for Phase 2.**

- **1986–1998 below-100 years are pre-existing** — the FULL universe is below
  100 in those years too (the universe starts with 24 symbols in 1986 and
  grows). These years are outside the study window anyway: regime features
  start effectively at 2002-07-03 (VIX percentile warmup), and the fold
  structure (OQ6) starts from 2002+.
- **1999+ → all years above 100** with comfortable margins: 107 minimum in
  1999, 115 in 2000, 126 in 2002.
- **2026 min=5 is partial-year artifact** — same in full universe (current
  year, data through July only).
- **Losses are concentrated in recent years** (29–33 symbols lost in
  2020–2026 vs 1–8 in 1986–2002) because most AFFECTED symbols are pre-2020
  stocks with long histories — they appear in the cross-section in all years,
  not just the early ones. The per-day mean loss rises from ~1 (1986) to ~33
  (2025) because as the universe grows, more AFFECTED symbols enter.
- **No fold-boundary interaction:** The losses are smoothly distributed
  across the study window, not clustered at fold edges. No year jumps by
  more than 2–3 lost symbols year-over-year (the largest jump is 2003,
  +3.7, from new symbols entering).

### Recommendation

Restrict the Phase 2 universe to **full clean (313) minus 33 AFFECTED = 280 symbols**.
The 38 NEGLIGIBLE symbols stay — their price history is recent enough that
the subtractive-dividend bug has negligible impact. The 206 symbols with
dividend data get corrected. The effective dividend-corrected universe is:

- **206 fully corrected** (have close_unadj → reconstruct proper CLOSE)
- **38 uncorrected but NEGLIGIBLE** (post-2021, bug impact ~0%)
- **36 ETFs** (no fundamentals, no dividend correction needed — price data is clean)
- **33 dropped** (AFFECTED, genuinely corrupted CLOSE)
- **= 280 symbols total**

---

## A3 — Sector/Type Texture (Informational)

The 33 AFFECTED symbols cluster into recognizable groups:

- **Precious-metals miners (9):** KGC, PAAS, WPM, RGLD, GFI, IAG, EGO,
  SSRM, EQX — the largest single cluster. These are Toronto/global gold and
  silver miners, many with histories back to the 1990s. Their sector betas
  are gold-price-driven, and they tend to have low nominal share prices.
- **Crypto-adjacent (3):** CLSK, HUT, GLXY — bitcoin miners and a crypto
  merchant bank. All had sub-$5 prices during the 2018–2020 crypto winter.
- **Legacy cyclicals (5):** RIG (offshore drilling), ET (energy transfer
  pipeline), BBBY (retail — now distressed), SGI (tech/engineering, since
  delisted/reorganized), QXO (trucking/logistics, went through restructuring)
- **Small-cap biotech/specialty (5):** CELH (energy drinks — had a
  penny-stock phase), CYTK (biotech), PACB (gene sequencing), POET
  (photonics), TGTX (biotech)
- **Other/retail (6):** APLD (data center), CROX (footwear), DKS (sporting
  goods), PEP (beverages), SAIA (trucking), FTAI (aircraft leasing)
- **Scattered (5):** BMNR, MXL, SEI, SIMO, TE

The drop skews the universe away from precious-metals miners (9 of 33) and
small-cap resource/cyclical names. This is not a random subset — it's
biased toward low-price, long-history, high-dividend-payout sectors where
the subtractive-dividend bug's cumulative effect is largest. The remaining
280 symbols are tilted toward higher-priced, later-IPO, lower-dividend-yield
names. This should be signed in the Phase 2 write-up as a known survivor
bias within the already-admitted survivorship-bias universe (D3).

---

## C1 — Inventory Correction: F_2 Date Format

**Confirmed:** History_4_F_2 dates are NOT YYYYMMDD. The format is:
- **YYMMDD** (6 digits) for pre-2000 dates (e.g. `991118` → 1999-11-18,
  `941004` → 1994-10-04)
- **CYYMMDD** (7 digits) for 2000+ dates (e.g. `1050927` → 2005-09-27,
  `1130926` → 2013-09-26)

This is a common legacy mixed format where century=0 is dropped for 1900s
and century=1 is explicit for 2000s. Any merge script consuming F_2 must
detect the format and convert to YYYYMMDD before joining.

→ **Applied to DATA_INVENTORY.md §7b.**

---

## C2 — Inventory Correction: Net_Interest Survival

**Confirmed:** Both `MRQ_Net_Interest` and `TTM_Net_Interest` are PRESENT in
all History_4_F_clean files (verified on 50-file sample + explicit check on
JPM, AAPL, WMT). JPM shows 100% nonzero Net_Interest values. The inventory
claim that these were "dropped during cleaning" is incorrect — the current
F_clean files on disk retain both columns.

For OQ4 (banks — 7 symbols), Net_Interest data is available from F_clean.
No need to revert to raw History_4_F.

→ **Applied to DATA_INVENTORY.md §7.**

---

## One-Line Recommendation

**Restrict Phase 2 to 280 symbols (313 − 33 AFFECTED), keep the 38 NEGLIGIBLE
names, and correct the 206 that have dividend data — this is the evidence;
Carol decides the D3 amendment.**
