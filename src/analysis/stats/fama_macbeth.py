"""fama_macbeth — two-layer Fama-MacBeth regression pipeline.

Layer 1: Per-day cross-sectional OLS of forward returns on features.
Layer 2: Newey-West time-series aggregation of coefficient estimates.

Supports regime-stratified runs (B0–B3) and era slicing.
Applies min_cross_section and episode-count sufficiency filters.

Work-in-progress — Phase 0 stub.
"""

from __future__ import annotations


class FamaMacBeth:
    """Two-layer Fama-MacBeth estimator.

    Parameters
    ----------
    horizon : int
        Forward return horizon in trading days.
    min_cross_section : int
        Minimum stocks required per day for layer-1 regression.
    """

    def __init__(self, horizon: int = 63, min_cross_section: int = 100):
        self.horizon = horizon
        self.min_cross_section = min_cross_section

    def fit(self, panel: "pd.DataFrame", features: list[str]) -> "FamaMacBeth":  # noqa: F821
        """Run layer-1 daily cross-sections, then layer-2 Newey-West aggregation."""
        raise NotImplementedError("Phase 0 stub — implementation TBD")

    def summary(self) -> "pd.DataFrame":  # noqa: F821
        """Return coefficient estimates, t-stats, and regime × era groupings."""
        raise NotImplementedError("Phase 0 stub — implementation TBD")
