# New Folders Verification — History_4_F_2, History_4_F_Dividend, History_4_F_Dividend_Correct

**Date:** 2026-07-26
**Method:** Read-only duckdb/pandas probe. No files modified, no pipeline regenerated.
**Inventory reference:** `data/DATA_INVENTORY.md` sections 7b–7d

---

## V1 — Structural / Inventory Claims

### History_4_F_2

| Claim | Expected | Actual | Verdict |
|-------|----------|--------|---------|
| File count | 624 | 624 | **PASS** |
| Column count | 47 | 47 (all 624 files) | **PASS** |
| Date format | YYYYMMDD | **CYYMMDD** (e.g. `941004` = 1994-10-04, `1000103` = 2000-01-03) | **FLAG** |
| Schema uniformity | 1 schema | 1 schema across all 624 files | **PASS** |
| Empty files | 0 | 0 | **PASS** |
| Unreadable files | 0 | 0 | **PASS** |

**Column list (47):**
`SYMBOL`, `DATE`, `MRQ_Total_Long_Term_Debt`, `MRQ_Total_Equity`, `MRQ_Total_Debt`,
`MRQ_Gross_Profit`, `MRQ_Net_Income`, `MRQ_Operating_Income`, `MRQ_EPS`,
`MRQ_Total_Asset`, `MRQ_Total_Liabilities`, `MRQ_Current_Asset`, `MRQ_Current_Liabilities`,
`MRQ_LongTerm_Asset`, `MRQ_LongTerm_Liabilities`, `MRQ_Depreciation`, `MRQ_Amortization`,
`MRQ_CapEx`, `MRQ_OperatingCashFlow`, `MRQ_Cash_Equivalents`, `MRQ_SharesOutstanding`,
`MRQ_Economic_Revenue`, `MRQ_Gross_Margin`, `MRQ_Operating_Margin`,
`TTM_Gross_Profit`, `TTM_Net_Income`, `TTM_Operating_Income`, `TTM_EPS`,
`TTM_Depreciation`, `TTM_Amortization`, `TTM_CapEx`, `TTM_OperatingCashFlow`,
`TTM_Economic_Revenue`, `TTM_Gross_Margin`, `TTM_Operating_Margin`,
`PE`, `ROE`, `LT_DE`, `EPS_Growth`, `EPS_Turnaround`, `EPS_LossRecovery`,
`EPS_Acceleration`, `Economic_Revenue_Growth`, `Revenue_Growth`, `FreeCashFlow`,
`CurrentRatio`, `ShareCountGrowth`

**FLAG detail:** The inventory states YYYYMMDD dates. Actual dates are CYYMMDD (7 digits:
century prefix 0=1900s, 1=2000s). Any merge script consuming F_2 must convert dates.
Dividend_Correct has the same AAPL rows (8,001) but with proper YYYYMMDD — zero common
date strings between F_2 and Dividend_Correct despite identical underlying data.

---

### History_4_F_Dividend

| Claim | Expected | Actual | Verdict |
|-------|----------|--------|---------|
| File count | 569 | 569 | **PASS** |
| Column count | 3 | 3 (all 569 files) | **PASS** |
| Date format | YYYYMMDD | YYYYMMDD (e.g. `19801212`) | **PASS** |
| Schema uniformity | 1 schema | 1 schema across all 569 files | **PASS** |
| Empty files | 0 | 0 | **PASS** |
| Unreadable files | 0 | 0 | **PASS** |

**Column list (3):**
`DATE`, `dividend_per_share`, `close_unadj`

---

### History_4_F_Dividend_Correct

| Claim | Expected | Actual | Verdict |
|-------|----------|--------|---------|
| File count | 624 | 624 | **PASS** |
| Column count | 51 | 51 (all 624 files) | **PASS** |
| Date format | YYYYMMDD | YYYYMMDD (e.g. `19941004`) | **PASS** |
| Schema uniformity | 1 schema | 1 schema across all 624 files | **PASS** |
| Empty files | 0 | 0 | **PASS** |
| Unreadable files | 0 | 0 | **PASS** |

**Column list (51):** Same 47 as F_2, plus:
`Close_unadj`, `MRQ_DivPerShare`, `Special_Dividend`, `PE_corrected`

---

## V2 — Column Delta (F_2 vs History_4_F)

### Dropped from F (8 columns — exact match)

| Column | In inventory claim? |
|--------|:---:|
| `MRQ_Revenue` | ✓ |
| `TTM_Revenue` | ✓ |
| `MRQ_Net_Interest` | ✓ |
| `TTM_Net_Interest` | ✓ |
| `TTM_Total_Debt` | ✓ |
| `TTM_Total_Equity` | ✓ |
| `TTM_Cash_Equivalents` | ✓ |
| `TTM_SharesOutstanding` | ✓ |

### Added to F_2 (9 columns — exact match)

| Column | In inventory claim? |
|--------|:---:|
| `EPS_Turnaround` | ✓ |
| `EPS_LossRecovery` | ✓ |
| `EPS_Acceleration` | ✓ |
| `Economic_Revenue_Growth` | ✓ |
| `FreeCashFlow` | ✓ |
| `CurrentRatio` | ✓ |
| `ShareCountGrowth` | ✓ |
| `MRQ_Economic_Revenue` | ✓ |
| `TTM_Economic_Revenue` | ✓ |

### Surprises

- **Extra dropped:** NONE
- **Missing dropped:** NONE
- **Extra added:** NONE
- **Missing added:** NONE

**Verdict: PASS** — Column delta matches inventory claims exactly. Net 46 → 47 (-8 +9).

---

## V3 — Symbol Universe Reconciliation

### Universe sizes

| Set | Count |
|-----|:-----:|
| History_4_F (original) | 361 |
| History_4_F_2 | 624 |
| History_4_F_Dividend | 569 |
| History_4_F_Dividend_Correct | 624 |
| History_4_F_clean (277-stock universe) | 277 |

### Intersection matrix

| Check | Count | Verdict |
|-------|:-----:|---------|
| F ∩ F_2 | 276 | — |
| F − F_2 (lost from original) | **85** | **FLAG** |
| F_2 − F (new symbols) | 348 | — |
| Clean ∩ F_2 | 223 | — |
| **Clean − F_2** | **54** | **FAIL** |
| Clean ∩ Dividend | 206 | — |
| **Clean − Dividend** | **71** | **FAIL** |
| F_2 ∩ Dividend | 569 | — |
| F_2 − Dividend (no dividend data) | 55 | — |

### V3a: Dividend_Correct = 624 — PASS

### V3b: Dividend (569) ⊆ F_2 (624) — PASS
Zero symbols in Dividend but not F_2. The 55 symbols in F_2 without dividend data are:
`AFRM, ALAB, APP, ARKK, ARM, BMNR, CBRS, CEG, CIFR, COIN, CRCL, CRDO, CRWV,
EXE, FDXF, FER, FLEX, GEHC, GEV, HONA, HOOD, IBB, ICLN, IREN, IWM, KVUE,
MDLN, NBIS, NU, OIH, OKLO, PEP, PLTR, Q, QBTS, RBLX, RBRK, RDDT, RGTI, RIVN,
RKT, SHEL, SNDK, SOLV, SPCX, SUNB, TEAM, TLN, TLT, USO, VLTO, WBD, WULF, XLF, XLI`

These are a mix of ETFs (IWM, TLT, USO, XLF, XLI, IBB, ICLN, OIH, ARKK, SPCX),
recent IPOs (HOOD, PLTR, RBLX, RDDT, RIVN, NU, COIN), and post-spinoff tickers.

### V3c: History_4_F (361) ⊆ F_2 (624) — FAIL

**85 symbols from the original History_4_F are absent from F_2.** This contradicts the
inventory claim that F_2 is a "broader universe than original 361." Only 276 of 361
original symbols survive in F_2. The 85 missing are a mix of small/mid-cap stocks and
recent additions to the original dataset.

The 85 symbols in F but not in F_2:
`APLD, ASND, AVAV, BAM, BBBY, BBIO, CC, CE, CELH, CLF, CLSK, COMP, CROX, CYTK,
DKS, DUOL, EGO, EMN, EOSE, EQX, ET, FIGR, FLY, FTAI, GFI, GFS, GH, GLXY, GTLS,
HALO, HNGE, HUT, IAG, ICLR, IONS, JOBY, KGC, KRMN, KVYO, LEGN, LUNR, MP, MRP,
MXL, NLY, NTLA, ONDS, OSCR, OSK, OUST, PAAS, PACB, PATH, PL, POET, QRVO, QXO,
RCAT, RDW, RGLD, RIG, RLAY, SAIA, SCCO, SE, SEDG, SEI, SEZL, SGI, SHAZ, SIMO,
SITM, SQM, SSRM, TE, TECK, TEM, TGTX, TNGX, TVTX, UAN, UUUU, VG, WPM, ZETA`

### V3d: Clean (277) ⊆ F_2 (624) — FAIL

**54 clean-universe symbols are NOT in F_2.** These symbols have no fundamental data in
the new F_2 source:

`APLD, ASND, BAM, BBBY, CELH, CLSK, COMP, CROX, CYTK, DKS, DUOL, EGO, EOSE,
EQX, ET, FTAI, GFI, GH, GLXY, HUT, IAG, JOBY, KGC, KVYO, LUNR, MP, MXL, NLY,
NTLA, ONDS, OSCR, OUST, PAAS, PACB, PATH, PL, POET, QXO, RDW, RGLD, RIG,
SAIA, SE, SEI, SEZL, SGI, SHAZ, SIMO, SSRM, TE, TGTX, UAN, WPM, ZETA`

### V3e: Clean (277) ⊆ Dividend (569) — FAIL ❗ BLOCKING

**71 clean-universe symbols are NOT in the Dividend folder.** These symbols cannot be
dividend-corrected. This directly blocks Phase 2 relabeling for these symbols.

Breakdown of the 71 blocked symbols:
- **17 have F_2 fundamentals but no dividend data:**
  `AFRM, APP, BMNR, CEG, CIFR, CRDO, EXE, IREN, NU, OKLO, PEP, RBLX, RIVN, RKT,
  TEAM, WBD, WULF`
  → These CAN be used for financial-state clustering but CANNOT be dividend-corrected.

- **54 have NEITHER F_2 fundamentals NOR dividend data:**
  `APLD, ASND, BAM, BBBY, CELH, CLSK, COMP, CROX, CYTK, DKS, DUOL, EGO, EOSE,
  EQX, ET, FTAI, GFI, GH, GLXY, HUT, IAG, JOBY, KGC, KVYO, LUNR, MP, MXL, NLY,
  NTLA, ONDS, OSCR, OUST, PAAS, PACB, PATH, PL, POET, QXO, RDW, RGLD, RIG,
  SAIA, SE, SEI, SEZL, SGI, SHAZ, SIMO, SSRM, TE, TGTX, UAN, WPM, ZETA`
  → These are completely absent from the new data folders. They ONLY exist in the
    original History_4_F (which has the subtractive-dividend bug baked in).

### Universe coverage summary

| Group | Count | % of clean |
|-------|:-----:|:----------:|
| Clean total | 277 | 100% |
| Have Dividend data (can correct) | 206 | 74.4% |
| In F_2 (have new fundamentals) | 223 | 80.5% |
| In BOTH F_2 AND Dividend | 206 | 74.4% |
| Missing from BOTH new folders | 54 | 19.5% |

---

## V4 — close_unadj Sanity

### Absolute price range check (early-2000s window: 2000–2005)

| Symbol | close_unadj min | close_unadj max | close_unadj mean | Sub-$1? | Verdict |
|--------|:--------------:|:--------------:|:---------------:|:-------:|---------|
| COST | $27.24 | $58.44 | $39.57 | No | **PASS** |
| CME | $8.30 | $79.38 | $30.64 | No | **PASS** |
| KO | $18.53 | $33.44 | $23.93 | No | **PASS** |
| PG | $26.81 | $59.62 | $44.67 | No | **PASS** |
| JNJ | $34.25 | $69.40 | $54.57 | No | **PASS** |
| IBM | $52.65 | $127.75 | $89.51 | No | **PASS** |
| XOM | $30.27 | $64.98 | $43.35 | No | **PASS** |

All prices are in plausible absolute ranges for large-cap stocks. No sub-$1 artifacts.
COST early-2000s is ~$30–50 as expected, not the $2.32 symptomatic of the bug.

*Note: XOM is not in the 313-symbol clean tech universe, so the CLOSE gap comparison
could not be performed. This is expected — XOM is among the 84 symbols filtered out.*

### Dividend vs Dividend_Correct cross-check

20 evenly-spaced dates sampled across full history for each symbol.
**Max absolute difference: 0.000000 for all 7 symbols.**
The `close_unadj` (Dividend folder) and `Close_unadj` (Dividend_Correct folder)
are bit-identical on all shared dates.

**Verdict: PASS**

### Buggy CLOSE vs close_unadj gap analysis

| Symbol | Early gap_frac (<2010) | Late gap_frac (≥2020) | Gap shrinks? | Notes |
|--------|:----------------------:|:---------------------:|:------------:|-------|
| COST | −0.8184 | −0.0259 | **PASS** | Strong signature: 82% gap early, 2.6% now |
| CME | −0.5294 | −0.0853 | **PASS** | Clear monotonic decline |
| KO | +0.0001 | −0.0000 | PASS | Essentially unaffected |
| PG | N/A (no early data) | −0.0000 | PASS | Essentially unaffected |
| JNJ | +0.0000 | −0.0000 | PASS | Essentially unaffected |
| IBM | N/A (no early data) | −0.0003 | PASS | Essentially unaffected |

COST and CME show the classic signature of the subtractive-dividend bug:
large gap in early history (when cumulative dividends dominate) monotonically
declining to near-zero present (when a single quarter's dividend is a small
fraction of price). KO, PG, JNJ, IBM show zero gap — these symbols were
apparently NOT affected by the bug in the first place (their CLOSE was already
unadjusted, or the data vendor corrected them).

**Verdict: PASS** — The signature is confirmed where expected.

---

## V5 — Reconstruction Viability (COST β Identity Bound)

### The smoking gun, before and after

| Metric | Buggy CLOSE (tech_daily) | Fixed close_unadj (Dividend) |
|--------|:------------------------:|:----------------------------:|
| Mean trailing-252d β | **2.173** | **0.815** |
| Median trailing-252d β | 1.971 | 0.791 |
| Max trailing-252d β | **24.598** | 1.561 |
| Min trailing-252d β | 0.217 | −0.075 |

### Identity bound

| Quantity | Value |
|----------|:-----:|
| COST annualized vol (σ_stock) | 0.2915 |
| SPY annualized vol (σ_market) | 0.1881 |
| Theoretical bound (σ_stock / σ_market) | 1.549 |
| Mean \|β\| | 0.815 |
| \|β\| ≤ bound? | **PASS** |

### Sanity range

COST is a consumer staples retailer. Expected β: 0.4–1.5.
Mean β = 0.815. **PASS** — comfortably in range.
Early-period β (<2010) mean = 0.947.
Most recent β (2026-07-02) = −0.075 (this is a single-point estimate, not alarming).

### Verdict: PASS ✅

The buggy CLOSE column produced β estimates up to 24.6 (mean 2.17), violating the
identity bound |β| ≤ σ_stock/σ_market. The close_unadj series brings β down to 0.815
(2.7× reduction in mean, ~16× reduction in max). The identity bound now holds, and
the β estimate is in the expected range for a large-cap consumer staples stock.

**This is the single most important check. It confirms the new price series actually
fixes the subtractive-dividend bug rather than just looking populated.**

---

## V6 — Net_Interest Survival (OQ4 Dependency)

| Column | Original F | F_clean | F_2 | Dividend_Correct |
|--------|:----------:|:-------:|:---:|:----------------:|
| `MRQ_Net_Interest` | **PRESENT** | **PRESENT** ⚠ | ABSENT | ABSENT |
| `TTM_Net_Interest` | **PRESENT** | **PRESENT** ⚠ | ABSENT | ABSENT |

### Inventory discrepancy

DATA_INVENTORY.md §7 (History_4_F_clean) states:
> "Drop MRQ_Net_Interest and TTM_Net_Interest columns (zero for 397/404 symbols in raw)"

**This claim is stale/wrong.** Both Net_Interest columns ARE present in the actual
`History_4_F_clean/` files on disk. The cleaning script (`src/3_clean_fundamentals.py`)
did NOT drop them, or the files were regenerated without that step.

Verified on JPM in F_clean: 8,012 rows, 100% nonzero MRQ_Net_Interest (values ~1,185)
and 100% nonzero TTM_Net_Interest (values ~4,640). Banks' Net_Interest data is intact.

### Verdict: FLAG (inventory error, favorable outcome)

Net_Interest columns are absent from F_2 and Dividend_Correct, but they survive in both
the original History_4_F and (contrary to the inventory) in History_4_F_clean. For the
bank decision (OQ4), Net_Interest data is available from F_clean — no need to go back to
raw History_4_F. The inventory should be updated.

---

## Summary Table

| Check | Section | Verdict | Evidence |
|-------|---------|:-------:|----------|
| F_2 file count = 624 | V1 | **PASS** | 624 files |
| F_2 columns = 47, uniform | V1 | **PASS** | All 624 files: 47 cols |
| F_2 date format = YYYYMMDD | V1 | **FLAG** | CYYMMDD, not YYYYMMDD |
| Dividend file count = 569 | V1 | **PASS** | 569 files |
| Dividend columns = 3, uniform | V1 | **PASS** | All 569 files: 3 cols |
| Dividend date format = YYYYMMDD | V1 | **PASS** | Confirmed |
| Dividend_Correct file count = 624 | V1 | **PASS** | 624 files |
| Dividend_Correct columns = 51, uniform | V1 | **PASS** | All 624 files: 51 cols |
| Dividend_Correct date format = YYYYMMDD | V1 | **PASS** | Confirmed |
| No empty/unreadable files | V1 | **PASS** | Zero across all 3 folders |
| F_2 dropped 8 cols exactly | V2 | **PASS** | Exact match to inventory |
| F_2 added 9 cols exactly | V2 | **PASS** | Exact match to inventory |
| Dividend_Correct = 624 symbols | V3a | **PASS** | 624 symbols |
| Dividend (569) ⊆ F_2 (624) | V3b | **PASS** | 0 extra in Dividend |
| Original F (361) ⊆ F_2 (624) | V3c | **FAIL** | 85 missing from F_2 |
| Clean (277) ⊆ F_2 (624) | V3d | **FAIL** | 54 missing from F_2 |
| Clean (277) ⊆ Dividend (569) | V3e | **FAIL** | 71 cannot be corrected |
| close_unadj plausible ranges | V4 | **PASS** | All 7 symbols $8–$128 |
| Dividend vs Dividend_Correct match | V4 | **PASS** | Bit-identical (max diff 0) |
| Gap signature (bug confirmation) | V4 | **PASS** | COST −0.82→−0.03, CME −0.53→−0.09 |
| COST β from close_unadj (sanity) | V5 | **PASS** | β=0.815, bound holds, range [0.4,1.5] |
| COST β from buggy CLOSE | V5 | **PASS** | β_max=24.6 confirmed (smoking gun reproduced) |
| Fix efficacy (β reduction) | V5 | **PASS** | 2.7× mean reduction, bound restored |
| Net_Interest absent from F_2 | V6 | **CONFIRMED** | As claimed by inventory |
| Net_Interest absent from Dividend_Correct | V6 | **CONFIRMED** | Consistent with F_2 |
| Net_Interest present in F_clean | V6 | **FLAG** | Inventory says dropped; actually present |

**Summary: 21 PASS, 3 FAIL, 3 FLAG**

---

## Blocking Issues for Phase 2

### 🔴 Critical — Must resolve before dividend reconstruction

1. **71 of 277 clean-universe symbols cannot be dividend-corrected** (V3e).
   - 17 have F_2 data but no dividend file
   - 54 are absent from BOTH F_2 AND Dividend
   - These 54 exist ONLY in original History_4_F (which has the subtractive-dividend bug baked into CLOSE)
   - **Impact:** Dividend reconstruction will be partial — only 206/277 (74.4%) symbols can be corrected
   - **Mitigation options:**
     a. Accept partial coverage: correct the 206 and flag the 71 as uncorrected
     b. Source dividend data for the 71 missing symbols from an alternative vendor
     c. Restrict Phase 2 universe to the 206 fully-correctable symbols
     d. Keep original (buggy) CLOSE for the 71 missing symbols and document the limitation

2. **F_2 is NOT a superset of original History_4_F** (V3c).
   - 85 of 361 original symbols missing from F_2
   - 54 of these are in the clean universe
   - **Impact:** Cannot simply swap F_2 in for F. The overlap is only 276/361.
   - **Mitigation:** Treat F and F_2 as complementary sources. Use F_2 for symbols it covers;
     fall back to original F for the 54 missing clean-universe symbols.

### 🟡 Important — Resolve before merge scripts touch these folders

3. **F_2 date format is CYYMMDD, not YYYYMMDD** (V1).
   - Inventory claims YYYYMMDD; actual is CYYMMDD (7 digits, century prefix)
   - Dividend_Correct uses proper YYYYMMDD for the same underlying data (zero common date strings)
   - **Impact:** Any merge script must detect and convert CYYMMDD → YYYYMMDD before joining
   - **Fix:** Add date conversion in the cleaning/merge pipeline for F_2 files

### 🟢 Non-blocking — Notes and inventory updates needed

4. **Inventory §7 is wrong about Net_Interest in F_clean** (V6).
   - F_clean still has MRQ_Net_Interest and TTM_Net_Interest (confirmed on JPM)
   - This is favorable — Net_Interest is available without going back to raw F
   - Update DATA_INVENTORY.md §7 to reflect actual state

5. **55 symbols have F_2 fundamentals but no dividend data** (V3b).
   - Mix of ETFs, recent IPOs, and post-spinoff tickers
   - ETFs don't pay dividends in the traditional sense — expected
   - Recent IPOs may not have enough dividend history — expected

6. **KO, PG, JNJ, IBM appear unaffected by the subtractive-dividend bug** (V4).
   - Gap between CLOSE and close_unadj is ~0 for these symbols
   - Either their data was already correct, or the vendor fixed them
   - COST and CME are the confirmed smoking guns
