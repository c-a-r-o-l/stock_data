"""
8_zero_audit.py — v3: optimized batch queries.
"""

import duckdb
import csv
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).resolve().parent.parent / "data" / "History_6_merge"
DATA = BASE.parent

con = duckdb.connect()
con.execute("SET memory_limit = '8GB'")

results = []

def add(source, col, pattern, action, reason):
    results.append({"source": source, "column": col, "pattern": pattern,
                    "proposed_action": action, "reason": reason})


# ── 1. Full-history zeros — single query per source ────────────────────────
print("=" * 70)
print("1. FULL-HISTORY ZEROS (batch query)")
print("=" * 70)

for label, path in [
    ("fundamentals", BASE / "fundamentals.csv"),
    ("tech_daily", BASE / "tech_daily.csv"),
    ("tech_weekly", BASE / "tech_weekly.csv"),
    ("tech_monthly", BASE / "tech_monthly.csv"),
]:
    if not path.exists():
        continue

    n_syms = con.execute(f"SELECT COUNT(DISTINCT SYMBOL) FROM read_csv('{path}', header=true)").fetchone()[0]
    cols = [r[0] for r in con.execute(
        f"DESCRIBE SELECT * FROM read_csv('{path}', header=true)"
    ).fetchall() if r[0] not in ('SYMBOL', 'DATE')]

    # Single batch: count non-zero rows per (symbol, column)
    # Use SUM of CASE WHEN != 0
    parts = [f'SUM(CASE WHEN "{c}"::FLOAT != 0 THEN 1 ELSE 0 END) AS "{c}"' for c in cols]
    query = f"""
        SELECT SYMBOL, {', '.join(parts)}
        FROM read_csv('{path}', header=true)
        GROUP BY SYMBOL
    """
    df = con.execute(query).fetchdf()

    per_sym_full = defaultdict(list)  # col -> [symbols with full-history zeros]

    for col in cols:
        nz_syms = (df[col] == 0).sum()
        if nz_syms == 0:
            continue
        zero_sym_list = df[df[col] == 0]['SYMBOL'].tolist()

        if nz_syms == n_syms:
            is_net_interest = 'Net_Interest' in col
            action = "convert" if is_net_interest else "drop"
            reason = (f"zero for all {n_syms} symbols — keep column, convert zeros→NaN (banks only)"
                      if is_net_interest else
                      f"always zero for all {n_syms} symbols")
            print(f"  [{label}] {col}: globally dead ({nz_syms}/{n_syms}) → {action}")
            add(label, col, "global_zero", action, reason)
        elif nz_syms >= n_syms * 0.9:
            is_net_interest = 'Net_Interest' in col
            action = "convert" if is_net_interest else "drop"
            reason = (f"zero for {nz_syms}/{n_syms} symbols — keep, convert zeros→NaN (banks only)"
                      if is_net_interest else
                      f"zero for {nz_syms}/{n_syms} symbols")
            print(f"  [{label}] {col}: near-dead ({nz_syms}/{n_syms}) → {action}")
            add(label, col, "near_dead_zero", action, reason)
        elif nz_syms >= 1:
            per_sym_full[col] = zero_sym_list

    # Report per-symbol full-history zeros (structural: banks, etc.)
    if per_sym_full and label == "fundamentals":
        # Group by set of symbols (same symbols affected = same root cause)
        by_symset = defaultdict(list)
        for col, syms in per_sym_full.items():
            by_symset[tuple(sorted(syms))].append(col)

        print(f"\n  [{label}] Per-symbol full-history zeros ({len(per_sym_full)} columns):")
        for syms_key, cols_list in sorted(by_symset.items(), key=lambda x: -len(x[1])):
            syms = list(syms_key)
            # Bank P&L pattern?
            is_bank = any(s in ['JPM','BAC','C','WFC','COF','PNFP','SOFI'] for s in syms)
            pattern = "bank_P&L" if is_bank else "structural_gap"
            action = "convert"
            reason = (f"{len(cols_list)} cols, {len(syms)} symbols {syms[:5]}..."
                      f" — {'bank accounting: no Revenue/GrossProfit/OpIncome' if is_bank else 'structural gap'}")
            print(f"    {len(cols_list)} cols × {len(syms)} symbols: {cols_list[:5]}... → {pattern}")
            for c in cols_list:
                add(label, c, pattern, action, reason)


# ── 2. Net_Interest note ──────────────────────────────────────────────────
print("\n" + "=" * 70)
print("2. NET_INTEREST: change proposal from 'drop' to 'convert'")
print("   Reason: 3-7 banks' non-zero values are their only P&L income line.")
print("   This column was explicitly protected in merge_decisions.md.")
print("   Two independent cleaning passes have now proposed dropping it —")
print("   classification corrected to 'convert' above.")
print("=" * 70)


# ── 3. Check weekly/monthly clean files for dead SMA ──────────────────────
print("\n" + "=" * 70)
print("3. WEEKLY/MONTHLY CLEAN SMA DEAD CHECK")
print("=" * 70)

for freq, folder in [("weekly", "History_2_W_clean"), ("monthly", "History_3_M_clean")]:
    dirpath = DATA / folder
    files = sorted(dirpath.glob("*.csv"))[:30]  # sample 30 files

    # Get columns from first file
    with open(files[0]) as f:
        reader = csv.DictReader(f)
        sma_cols = [c for c in reader.fieldnames if 'SMA' in c]

    if not sma_cols:
        print(f"  {freq}: no SMA columns")
        continue

    sma_zero = {c: 0 for c in sma_cols}
    for fp in files:
        with open(fp) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        for c in sma_cols:
            if all(float(r.get(c, '0') or '0') == 0 for r in rows if r.get(c, '').strip()):
                sma_zero[c] += 1

    if sma_zero:
        for col, n in sorted(sma_zero.items(), key=lambda x: -x[1]):
            dead = n == len(files)
            marker = " ← GLOBALLY DEAD" if dead else ""
            print(f"  [{freq}] {col}: {n}/{len(files)}{marker}")
            if dead:
                add(f"tech_{freq}_clean", col, "global_zero", "drop",
                    f"always zero — SMA not computed at {freq} frequency")
    else:
        print(f"  {freq}: no dead SMA columns")


# ── 4. PV violations ──────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("4. PV ZERO VIOLATIONS")
print("=" * 70)

for label, path in [
    ("tech_daily", BASE / "tech_daily.csv"),
    ("tech_weekly", BASE / "tech_weekly.csv"),
    ("tech_monthly", BASE / "tech_monthly.csv"),
]:
    if not path.exists():
        continue

    print(f"\n  --- {label} ---")
    for side, step_col, check_cols in [
        ("BULL", "PV_BULL_STEP", ["PV_BULL_START", "PV_BULL_STOP", "PV_BULL_CNT", "PV_BULL_H"]),
        ("BEAR", "PV_BEAR_STEP", ["PV_BEAR_START", "PV_BEAR_STOP", "PV_BEAR_CNT", "PV_BEAR_L"]),
    ]:
        for chk in check_cols:
            rows = con.execute(f"""
                SELECT SYMBOL, DATE, "{step_col}" AS STEP, "{chk}" AS ZERO_COL
                FROM read_csv('{path}', header=true)
                WHERE "{chk}"::FLOAT = 0 AND "{step_col}"::FLOAT != 0
                ORDER BY SYMBOL, DATE
            """).fetchall()

            if not rows:
                continue

            # Check: first-bar clustering
            sym_mins = {}
            for r in rows:
                if r[0] not in sym_mins:
                    sym_mins[r[0]] = con.execute(f"""
                        SELECT MIN(DATE) FROM read_csv('{path}', header=true)
                        WHERE SYMBOL = '{r[0]}'
                    """).fetchone()[0]

            first_bar = 0; mid = 0; mid_ex = []
            for sym, date, step, zero in rows:
                try:
                    if int(date) <= int(float(sym_mins[sym])) + 100:
                        first_bar += 1
                    else:
                        mid += 1
                        if len(mid_ex) < 3:
                            mid_ex.append((sym, date, step, zero))
                except (ValueError, TypeError):
                    first_bar += 1  # treat parse errors as first-bar

            v = "initialization" if mid == 0 else f"{first_bar} first-bar, {mid} mid-history"
            action = "leave" if mid <= 5 else "investigate"
            print(f"    {chk}: {len(rows)} violations — {v}")
            for sym, d, s, z in mid_ex:
                print(f"      MID: {sym} {d}: STEP={s}, {chk}={z}")
            add(label, chk, "pv_zero_violation", action,
                f"{len(rows)} zeros where {step_col}!=0: {v}")


# ── 5. CLASSIFICATION CSV ─────────────────────────────────────────────────
print("\n" + "=" * 70)
print("5. CLASSIFICATION CSV")
print("=" * 70)

out = BASE / "zero_audit.csv"
with open(out, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=["source", "column", "pattern", "proposed_action", "reason"])
    writer.writeheader()
    writer.writerows(results)

actions = defaultdict(int)
for r in results:
    actions[r["proposed_action"]] += 1

print(f"Output: {out}")
print(f"Total: {len(results)}")
for a in ["drop", "convert", "leave"]:
    n = actions.get(a, 0)
    if n:
        print(f"\n  {a.upper()} ({n}):")
        for r in results:
            if r["proposed_action"] == a:
                print(f"    [{r['source']}] {r['column']}: {r['reason']}")

con.close()
