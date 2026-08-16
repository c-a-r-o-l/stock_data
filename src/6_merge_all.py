"""
6_merge_all.py
==============
Merge all data into one daily table for ALL symbols using duckdb.

Sources in History_6_merge already have YYYYMMDD DATE strings.
Macro uses YYYY-MM-DD → strip hyphens.
Fundamentals from History_4_F_clean already have YYYYMMDD DATE strings.

Output: data/History_6_merge/all_merged.parquet
"""

import duckdb
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "data" / "History_6_merge"
DATA = BASE.parent

con = duckdb.connect()
con.execute("SET memory_limit = '12GB'")

out = BASE / "all_merged.parquet"
print(f"Output: {out}")

sql = f"""
WITH
spine AS (
    SELECT * EXCLUDE (BarNumber_D)
    FROM read_csv('{BASE}/tech_daily.csv', header=true)
),

mkt_d AS (
    SELECT * FROM read_csv('{BASE}/market_merge_daily.csv', header=true)
),

mkt_w AS (
    SELECT * FROM read_csv('{BASE}/market_merge_weekly.csv', header=true)
),

mkt_m AS (
    SELECT * FROM read_csv('{BASE}/market_merge_monthly.csv', header=true)
),

weekly AS (
    SELECT * FROM read_csv('{BASE}/tech_weekly.csv', header=true)
),

monthly AS (
    SELECT * FROM read_csv('{BASE}/tech_monthly.csv', header=true)
),

fund AS (
    SELECT * FROM read_csv('{DATA}/History_4_F_clean/*.csv',
                           header=true, union_by_name=true)
),

macro AS (
    SELECT * REPLACE (REPLACE(date, '-', '') AS date)
    FROM read_csv('{BASE}/macro_merge_daily.csv', header=true)
),

etf AS (
    SELECT symbol AS SYMBOL, isETF
    FROM read_csv('{DATA}/ETF_real.csv', header=true)
)

SELECT
    s.SYMBOL,
    s.DATE,
    -- Daily tech
    s.VOLUME_D, s.OPEN_D, s.HIGH_D, s.LOW_D, s.CLOSE_D,
    s.SMA_020_D, s.SMA_050_D, s.SMA_200_D,
    s.SPY_C_D, s.SPY_020_D, s.SPY_050_D, s.SPY_200_D,
    s.PFE_010_D, s.PFE_020_D,
    s.Fit_D, s.Trigger_D, s.Itrend_D,
    s.Fit_SPY_D, s.Trigger_SPY_D, s.Itrend_SPY_D,
    s.STD_20_D, s.ATR_D, s.Trend_PV_D,
    s.PV_BULL_STEP_D, s.PV_BULL_START_D, s.PV_BULL_STOP_D,
    s.PV_BULL_CNT_D, s.PV_BULL_H_D,
    s.PV_BEAR_STEP_D, s.PV_BEAR_START_D, s.PV_BEAR_STOP_D,
    s.PV_BEAR_CNT_D, s.PV_BEAR_L_D,
    s.Push_Diff_D, s.Push_Diff_SPY_D,
    s.MACD_C_D, s.MACD_H_D, s.MACD_L_D, s.MACD_DIFF_D,
    s.oSlowK_D, s.RSI_03_D,
    -- Market daily
    md.Growth_vs_Value_MKT, md.GVR_020_MKT, md.GVR_050_MKT,
    md.GVR_100_MKT, md.GVR_200_MKT,
    -- (abbreviated — duckdb SELECT * EXCLUDE can simplify this)
    -- Actually let's just use EXCLUDE for brevity
FROM spine s

-- We'll build this incrementally with duckdb's chained CTE + ASOF
"""

# DuckDB doesn't support ASOF joins natively yet.
# Use the window-function approach for forward-fill joins.

sql2 = f"""
WITH
spine AS (
    SELECT * FROM read_csv('{BASE}/tech_daily.csv', header=true)
),

-- Daily market: plain left join
mkt_d AS (
    SELECT * FROM read_csv('{BASE}/market_merge_daily.csv', header=true)
),

-- Build a combined table with: spine + mkt_d + macro
step1 AS (
    SELECT
        s.*,
        md.* EXCLUDE (DATE)
    FROM spine s
    LEFT JOIN mkt_d md ON s.DATE = md.DATE
),

-- Macro: plain left join
macro AS (
    SELECT * REPLACE (REPLACE(date::VARCHAR, '-', '') AS DATE)
    FROM read_csv('{BASE}/macro_merge_daily.csv', header=true)
),

step2 AS (
    SELECT s1.*, m.* EXCLUDE (DATE)
    FROM step1 s1
    LEFT JOIN macro m ON s1.DATE = m.DATE
),

-- Weekly tech: forward-fill via window + cross join with max date per symbol
weekly AS (
    SELECT * FROM read_csv('{BASE}/tech_weekly.csv', header=true)
),

step3 AS (
    SELECT s2.*, w.* EXCLUDE (SYMBOL, DATE)
    FROM step2 s2
    LEFT JOIN weekly w
        ON s2.SYMBOL = w.SYMBOL
        AND w.DATE = (
            SELECT MAX(w2.DATE) FROM weekly w2
            WHERE w2.SYMBOL = s2.SYMBOL AND w2.DATE <= s2.DATE
        )
),

-- Monthly tech
monthly AS (
    SELECT * FROM read_csv('{BASE}/tech_monthly.csv', header=true)
),

step4 AS (
    SELECT s3.*, m.* EXCLUDE (SYMBOL, DATE)
    FROM step3 s3
    LEFT JOIN monthly m
        ON s3.SYMBOL = m.SYMBOL
        AND m.DATE = (
            SELECT MAX(m2.DATE) FROM monthly m2
            WHERE m2.SYMBOL = s3.SYMBOL AND m2.DATE <= s3.DATE
        )
),

-- Market weekly (by DATE only)
mkt_w AS (
    SELECT * FROM read_csv('{BASE}/market_merge_weekly.csv', header=true)
),

step5 AS (
    SELECT s4.*, mw.* EXCLUDE (DATE)
    FROM step4 s4
    LEFT JOIN mkt_w mw
        ON mw.DATE = (
            SELECT MAX(mw2.DATE) FROM mkt_w mw2 WHERE mw2.DATE <= s4.DATE
        )
),

-- Market monthly
mkt_m AS (
    SELECT * FROM read_csv('{BASE}/market_merge_monthly.csv', header=true)
),

step6 AS (
    SELECT s5.*, mm.* EXCLUDE (DATE)
    FROM step5 s5
    LEFT JOIN mkt_m mm
        ON mm.DATE = (
            SELECT MAX(mm2.DATE) FROM mkt_m mm2 WHERE mm2.DATE <= s5.DATE
        )
),

-- Fundamentals (per symbol)
fund AS (
    SELECT * FROM read_csv('{DATA}/History_4_F_clean/*.csv',
                           header=true, union_by_name=true)
),

step7 AS (
    SELECT s6.*, f.* EXCLUDE (SYMBOL, DATE)
    FROM step6 s6
    LEFT JOIN fund f
        ON s6.SYMBOL = f.SYMBOL
        AND f.DATE = (
            SELECT MAX(f2.DATE) FROM fund f2
            WHERE f2.SYMBOL = s6.SYMBOL AND f2.DATE <= s6.DATE
        )
),

-- ETF
etf AS (
    SELECT symbol AS SYMBOL, isETF
    FROM read_csv('{DATA}/ETF_real.csv', header=true)
)

SELECT s7.*, COALESCE(e.isETF, 0) AS isETF
FROM step7 s7
LEFT JOIN etf e ON s7.SYMBOL = e.SYMBOL
ORDER BY s7.SYMBOL, s7.DATE
"""

print("Executing (correlated subqueries for asof joins)...")
con.execute(f"COPY ({sql2}) TO '{out}' (FORMAT PARQUET, COMPRESSION 'zstd')")

count = con.execute(f"SELECT COUNT(*) FROM read_parquet('{out}')").fetchone()[0]
cols = con.execute(f"""SELECT COUNT(*) FROM (
    DESCRIBE SELECT * FROM read_parquet('{out}')
)""").fetchone()[0]
syms = con.execute(f"SELECT COUNT(DISTINCT SYMBOL) FROM read_parquet('{out}')").fetchone()[0]
etfs = con.execute(f"SELECT SUM(isETF) FROM read_parquet('{out}')").fetchone()[0]
dt = con.execute(f"SELECT MIN(DATE), MAX(DATE) FROM read_parquet('{out}')").fetchone()

print(f"Rows: {count:,}  |  Cols: {cols}  |  Symbols: {syms}  |  ETFs: {int(etfs)}")
print(f"Range: {dt[0]} → {dt[1]}")

# Size
import os
mb = os.path.getsize(out) / 1024 / 1024
print(f"Size: {mb:.0f} MB")

con.close()
