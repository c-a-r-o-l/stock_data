# CLAUDE.md — Stock Project

Quantitative trading research project building a Market State Foundation Model
using Transformer Encoders. Goal: encode 252-day market windows into dense
embeddings for similarity search (Faiss) + prediction (XGBoost).

## Project structure

```
/home/carol/projects/stock_project/
├── src/                           Pipeline scripts (numbered by execution order)
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
│   ├── History_4_F/               Raw quarterly fundamentals (404 symbols)
│   ├── History_4_F_clean/         Cleaned fundamentals (276 symbols)
│   └── History_6_merge/           Final merged outputs (9 CSVs)
├── Summer_Project_Plan_3.txt      Project architecture & feature selection
├── CLAUDE.md                      This file
├── DATA_INVENTORY.md              Comprehensive data catalog
└── doc/                           Documentation
```

## Key conventions

### Date formats
- **Raw files (CYYMMDD)**: `1180716` = century 1, year 18, month 07, day 16 = 2018-07-16
- **Cleaned files (YYYYMMDD)**: `20180716`
- All merge outputs use YYYYMMDD

### Symbol universe
- **313 symbols** aligned across daily/weekly/monthly after cleaning
- **276 symbols** have fundamental data (37 missing from History_4_F)
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
| 4 | `4_download_macro.py` | Download FRED+ALFRED → `History_4_E_Alfred/` |
| 4 | `4_download_macro_release.py` | Add release dates → `History_4_E_Alfred_Release/` |
| 4 | `4_merge_macro.py` | Merge macro to daily grid → `macro_merge_daily.csv` |
| — | `merge_wide.py` | (Legacy) Merge tech+fundamentals → parquet |

### Running the full pipeline
```
source .venv/bin/activate
python3 src/1_clean_tech.py
python3 src/3_clean_fundamentals.py
python3 src/1_merge_tech.py
python3 src/2_merge_market_daily.py && python3 src/2_merge_market_weekly.py && python3 src/2_merge_market_monthly.py
python3 src/4_merge_macro.py
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
1. Keep only 313-symbol clean set (drops 127 symbols)
2. Convert DATE, deduplicate, strip leading/trailing all-zero rows
3. Drop MRQ_Net_Interest and TTM_Net_Interest (zero for 397/404 symbols)

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
| `tech_daily.csv` | 1.7M | 42 | Per-symbol daily price/technicals |
| `tech_weekly.csv` | 376K | 39 | Per-symbol weekly |
| `tech_monthly.csv` | 89K | 38 | Per-symbol monthly |
| `market_merge_daily.csv` | 6.5K | 115 | MKT + SPY + QQQ daily |
| `market_merge_weekly.csv` | 1.4K | 115 | Same, weekly |
| `market_merge_monthly.csv` | 313 | 115 | Same, monthly |
| `fundamentals.csv` | 74K | 44 | Per-symbol quarterly fundamentals |
| `macro_merge_daily.csv` | 39K | 140 | All macro series, daily grid |

## FRED API

- API key: `0c8e39c6b19bdd2631af9dc2cdc3b872` (free tier, 120 req/min)
- Base URL: `https://api.stlouisfed.org/fred/`
- ALFRED: query in ≤3-month realtime windows to avoid 0-result responses

## Project memory

Persistent memory at `/home/carol/.claude/projects/-home-carol-projects-stock-project/memory/`
- `MEMORY.md` — index
- `project-knowledge.md` — full technical details on all 140 FRED series,
  revision schedules, vintage data, cleaning rules, and pipeline architecture
- `track-all-prompts.md` — prompt logging preference
