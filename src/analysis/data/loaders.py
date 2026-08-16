"""loaders — visibility-date-aware panel loading.

Design
------
Every source column has an effective release / visibility date.
``get_panel(as_of=date)`` returns a cross-section where no column value
is drawn from a release *after* ``as_of``.  This is the sole gate that
prevents look-ahead bias from entering the analysis pipeline.

Sources consumed
----------------
- ``all_merged.parquet``  — tech + market + macro + fundamentals + isETF
- ``macro_merge_daily.csv`` — forward-filled macro release-date grid
- ``ETF_real.csv`` — ETF classification flags

Quarantine note
---------------
PV indicator columns (Trend_PV, PV_BULL_*, PV_BEAR_*) are PRESENT in
all_merged.parquet but INTENTIONALLY QUARANTINED from analysis code
pending T0.4 completion and formula transcription.  See
``indicator/indicator_spec.md`` and D12.  Do not join any PV column to
forward returns, labels, or return-derived quantities until the spec is
complete and the formula is committed.

Work-in-progress — Phase 0 stub.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


_MERGE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "History_6_merge"


class PanelLoader:
    """Load merged data with point-in-time visibility enforcement.

    Parameters
    ----------
    parquet_path : Path, optional
        Path to ``all_merged.parquet``.
    """

    def __init__(self, parquet_path: Path | None = None):
        self._path = parquet_path or _MERGE_DIR / "all_merged.parquet"

    def get_panel(self, as_of: str | pd.Timestamp) -> pd.DataFrame:
        """Return a cross-section with only data observable on or before *as_of*.

        Parameters
        ----------
        as_of : str or Timestamp
            Point-in-time cutoff.  Any feature whose underlying source was
            released after this date is masked to NaN.

        Returns
        -------
        pd.DataFrame
            Columns: SYMBOL, DATE, and all features visible at *as_of*.

        Notes
        -----
        Stub — Phase 0.  Always returns the raw parquet contents with no
        visibility filtering.  Will be replaced with column-level release-date
        masking.
        """
        df = pd.read_parquet(self._path)
        # TODO: apply per-column visibility masks based on release schedules
        #   - tech columns: available at observation date (T+0)
        #   - macro columns: available at calculated release date (T+1 to M+2)
        #   - fundamentals columns: available at earnings announcement date (T+1~2)
        #   - isETF: always available
        return df
