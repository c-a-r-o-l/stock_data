"""
download_macro_release.py — Copy History_4_E_Alfred → History_4_E_Alfred_Release
with computed release_date added to files that lack it.

Step 1: Copy all files from History_4_E_Alfred to History_4_E_Alfred_Release.
Step 2: For files without a release-date column (latest + TIC), compute and add
         release_date based on the official delay rules in _ALFRED_MANIFEST.csv.

Revision_timeline files (54) already have released_on → copied as-is.
"""
import csv
import logging
import re
import shutil
from calendar import monthrange
from datetime import datetime, timedelta
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR  = PROJECT_ROOT / "data" / "History_4_E_Alfred"
OUT_DIR  = PROJECT_ROOT / "data" / "History_4_E_Alfred_Release"
MANIFEST = PROJECT_ROOT / "data" / "_ALFRED_MANIFEST.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Helpers ─────────────────────────────────────────────────────────────

def next_business_day(d: datetime) -> datetime:
    """Return the next business day (skip Sat/Sun)."""
    d = d + timedelta(days=1)
    while d.weekday() >= 5:
        d = d + timedelta(days=1)
    return d

def end_of_month(d: datetime) -> datetime:
    _, last = monthrange(d.year, d.month)
    return d.replace(day=last)

def end_of_quarter(d: datetime) -> datetime:
    q = (d.month - 1) // 3
    last_month = q * 3 + 3
    _, last = monthrange(d.year, last_month)
    return d.replace(month=last_month, day=last)


def parse_delay(delay_str: str):
    """
    Parse release_delay from manifest into a computable rule.
    Returns (rule_type, rule_value) where:
      - ("skip", 0)              — already has release dates
      - ("daily", 1)             — next business day
      - ("weekly", target_wd)    — next specific weekday (Mon=0..Sun=6)
      - ("monthly", days)        — end_of_month + days
      - ("quarterly", days)      — end_of_quarter + days
      - ("unknown", 0)
    """
    delay_str = delay_str.strip()
    if delay_str.startswith("N/A"):
        return ("skip", 0)
    if delay_str.startswith("T+"):
        return ("daily", 1)

    # Weekly: "W+0 (Thu 4:30pm ET, H.4.1)" → extract day abbreviation
    if delay_str.startswith("W+"):
        m = re.search(r'\(([A-Z][a-z]{2})', delay_str)
        if m:
            day_map = {'Mon': 0, 'Tue': 1, 'Wed': 2, 'Thu': 3, 'Fri': 4, 'Sat': 5, 'Sun': 6}
            return ("weekly", day_map.get(m.group(1), 3))
        return ("weekly", 3)

    # Monthly: "M+Nw" or "M+Nd"
    m = re.match(r'M\+(\d+)([dw])', delay_str)
    if m:
        num = int(m.group(1))
        unit = m.group(2)
        return ("monthly", num * 7 if unit == 'w' else num)

    # Quarterly: "Q+Nw" or "Q+Nd"
    m = re.match(r'Q\+(\d+)([dw])', delay_str)
    if m:
        num = int(m.group(1))
        unit = m.group(2)
        return ("quarterly", num * 7 if unit == 'w' else num)

    return ("unknown", 0)


def compute_release_date(obs_str: str, rule_type: str, rule_value: int) -> datetime | None:
    """Compute release_date from observation_date + delay rule.

    The manifest delay values (e.g. M+8w, M+6w) are conservative ceilings
    representing the maximum expected publication lag.  When the ceiling
    overshoots (i.e. the data is already in FRED but the formula predicts a
    future date), we cap the release at today — the data cannot have been
    released *after* we downloaded it."""
    obs = datetime.strptime(obs_str.strip(), "%Y-%m-%d")
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    rel = None

    if rule_type == "daily":
        rel = next_business_day(obs)

    elif rule_type == "weekly":
        # W+0 => the value is released in the SAME week as the observation
        # date, on the labeled release weekday — NOT the next future
        # occurrence. Snap to the CLOSEST occurrence of target_wd:
        #   - If the observation date already IS the release weekday
        #     (e.g. MORTGAGE30US obs on Thu, "W+0 (Thu ...)"), release == obs.
        #   - If obs is a Wed level published Thu (WALCL, TGA), this lands on
        #     the Thu of that same week.
        target_wd = rule_value
        delta = (target_wd - obs.weekday()) % 7   # 0..6, forward distance
        if delta > 3:                             # closer going backward
            delta -= 7                            # -3..-1
        rel = obs + timedelta(days=delta)
        # Freddie Mac PMMS holiday exception: when the target Thursday is a
        # fixed-date US federal holiday, PMMS publishes the day before (Wed).
        # Only shift for the three fixed-date holidays that can land midweek.
        if (rel.month, rel.day) in {(1, 1), (7, 4), (12, 25)}:
            rel = rel - timedelta(days=1)

    elif rule_type == "monthly":
        eom = end_of_month(obs)
        rel = eom + timedelta(days=rule_value)

    elif rule_type == "quarterly":
        eoq = end_of_quarter(obs)
        rel = eoq + timedelta(days=rule_value)

    else:
        return None

    # Cap at today: the data was downloaded from FRED and therefore had to
    # have been released on or before today.  This prevents conservative
    # ceiling delays (e.g. M+8w for OECD, M+6w for BIS) from projecting
    # into the future when the actual release calendar — published by each
    # agency — shipped the data earlier.
    if rel is not None and rel > today:
        rel = today

    return rel


# ── Main ───────────────────────────────────────────────────────────────

def main() -> None:
    logger.info("=" * 55)
    logger.info("  RELEASE-DATE ENRICHMENT")
    logger.info(f"  Source:  {SRC_DIR}")
    logger.info(f"  Output:  {OUT_DIR}")
    logger.info("=" * 55)

    # Load manifest
    logger.info("Loading manifest...")
    delay_map = {}
    with open(MANIFEST) as f:
        for row in csv.DictReader(f):
            delay_map[row["filename"]] = row.get("release_delay", "?")

    logger.info(f"  {len(delay_map)} entries loaded")

    # Ensure output directory
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Process files
    stats = {"copied": 0, "enriched": 0, "skipped": 0}
    weekly_samples = []  # (fname, [(obs, rel), ...]) for eyeball validation

    for src_path in sorted(SRC_DIR.iterdir()):
        if src_path.suffix.lower() != '.csv':
            continue
        if src_path.name == "_ALFRED_MANIFEST.csv":
            continue

        fname = src_path.name
        dst_path = OUT_DIR / fname

        # Read source
        with open(src_path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)

        if not rows:
            logger.warning(f"  SKIP empty: {fname}")
            stats["skipped"] += 1
            continue

        header = rows[0]
        data_rows = rows[1:]

        # Check if already has release-date column
        has_release_col = any("release" in col.lower() for col in header)

        if has_release_col:
            # revision_timeline file — copy as-is
            shutil.copy2(src_path, dst_path)
            stats["copied"] += 1
            continue

        # Need to add release_date
        delay_str = delay_map.get(fname, "?")
        if delay_str == "?":
            logger.warning(f"  SKIP (no delay): {fname}")
            shutil.copy2(src_path, dst_path)
            stats["skipped"] += 1
            continue

        rule_type, rule_value = parse_delay(delay_str)
        if rule_type in ("skip", "unknown"):
            shutil.copy2(src_path, dst_path)
            stats["skipped"] += 1
            continue

        # Find date column
        date_col = 0
        for i, col in enumerate(header):
            if col.lower() in ("observation_date", "date"):
                date_col = i
                break

        # Compute release_date
        new_header = header + ["release_date"]
        new_rows = [new_header]
        bad = 0

        sample = []
        for row in data_rows:
            if not row or not row[date_col].strip():
                continue
            obs_str = row[date_col].strip()
            try:
                rel = compute_release_date(obs_str, rule_type, rule_value)
                if rel:
                    new_rows.append(row + [rel.strftime("%Y-%m-%d")])
                    if rule_type == "weekly" and len(sample) < 5:
                        obs_dt = datetime.strptime(obs_str, "%Y-%m-%d")
                        sample.append((obs_str, obs_dt.strftime("%a"),
                                       rel.strftime("%Y-%m-%d"),
                                       rel.strftime("%a")))
                else:
                    new_rows.append(row + [""])
            except Exception:
                bad += 1
                new_rows.append(row + [""])

        if rule_type == "weekly" and sample and len(weekly_samples) < 3:
            weekly_samples.append((fname, sample))

        # Write
        with open(dst_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(new_rows)

        if bad:
            logger.warning(f"  {fname}: {bad} bad dates")
        stats["enriched"] += 1

    # Summary
    logger.info("=" * 55)
    logger.info(f"  COMPLETE")
    logger.info(f"    Copied as-is (has released_on): {stats['copied']}")
    logger.info(f"    Enriched (added release_date):  {stats['enriched']}")
    logger.info(f"    Skipped:                         {stats['skipped']}")
    logger.info(f"    Total:                           {stats['copied'] + stats['enriched'] + stats['skipped']}")
    logger.info(f"  Output: {OUT_DIR}")
    logger.info("=" * 55)

    # Weekly-series validation: obs vs. computed release should be same week
    if weekly_samples:
        logger.info("  WEEKLY VALIDATION (obs_date [wd] -> release_date [wd]):")
        for fname, sample in weekly_samples:
            logger.info(f"    {fname}")
            for obs_s, obs_wd, rel_s, rel_wd in sample:
                logger.info(f"      {obs_s} [{obs_wd}] -> {rel_s} [{rel_wd}]")
        logger.info("=" * 55)


if __name__ == "__main__":
    main()
