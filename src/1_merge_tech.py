"""
merge_clean.py
==============
Stacks (unions) all per-symbol CSV files in each clean folder into a single
merged file per frequency.

Inputs:
  data/History_1_D_clean/*.csv   →  data/History_6_merge/tech_daily.csv
  data/History_2_W_clean/*.csv   →  data/History_6_merge/tech_weekly.csv
  data/History_3_M_clean/*.csv   →  data/History_6_merge/tech_monthly.csv

Output: one CSV per frequency with all symbols stacked (SYMBOL column preserved).
"""

from pathlib import Path

import duckdb


PIPELINES = {
    "daily": {
        "input_dir":  "data/History_1_D_clean",
        "output_file": "data/History_6_merge/tech_daily.csv",
    },
    "weekly": {
        "input_dir":  "data/History_2_W_clean",
        "output_file": "data/History_6_merge/tech_weekly.csv",
    },
    "monthly": {
        "input_dir":  "data/History_3_M_clean",
        "output_file": "data/History_6_merge/tech_monthly.csv",
    },
}


def main():
    project_root = Path(__file__).resolve().parent.parent

    output_root = project_root / "data/History_6_merge"
    output_root.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect()

    for label, cfg in PIPELINES.items():
        input_dir = project_root / cfg["input_dir"]
        output_file = project_root / cfg["output_file"]

        if not input_dir.is_dir():
            print(f"[SKIP] {label}: input dir not found ({input_dir})")
            continue

        csv_files = sorted(input_dir.glob("*.csv"))
        print(f"[{label}] stacking {len(csv_files)} files → {output_file}")

        # Build a single glob pattern for duckdb's read_csv
        pattern = str(input_dir / "*.csv")
        sql = f"""
            COPY (
                SELECT * FROM read_csv('{pattern}', header=true, union_by_name=true)
                ORDER BY SYMBOL, DATE
            ) TO '{output_file}' (HEADER, DELIMITER ',');
        """
        con.execute(sql)

        # Row count
        count = con.execute(f"SELECT COUNT(*) FROM read_csv('{output_file}', header=true)").fetchone()[0]
        print(f"  → {count:,} rows written")

    con.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
