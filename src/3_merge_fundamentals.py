"""
3_merge_fundamentals.py
=======================
Union all cleaned fundamentals CSVs into one merged file.

Input:  data/History_4_F_clean/*.csv
Output: data/History_6_merge/fundamentals.csv
"""

import duckdb
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "data"
INPUT = BASE / "History_4_F_clean"
OUTPUT = BASE / "History_6_merge" / "fundamentals.csv"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

con = duckdb.connect()

pattern = str(INPUT / "*.csv")
sql = f"""
    COPY (
        SELECT * FROM read_csv('{pattern}', header=true, union_by_name=true)
        ORDER BY SYMBOL, DATE
    ) TO '{OUTPUT}' (HEADER, DELIMITER ',');
"""

con.execute(sql)

count = con.execute(f"SELECT COUNT(*) FROM read_csv('{OUTPUT}', header=true)").fetchone()[0]
syms = con.execute(f"SELECT COUNT(DISTINCT SYMBOL) FROM read_csv('{OUTPUT}', header=true)").fetchone()[0]

print(f"Output: {OUTPUT}")
print(f"Rows: {count:,}  |  Symbols: {syms}")

con.close()
