"""stats — two-layer Fama-MacBeth with regime grouping and era slices.

Layer 1
    Per-day cross-sectional regressions of forward-horizon returns on
    features, run separately for each regime × era combination.

Layer 2
    Newey-West aggregation of daily coefficient estimates, with
    regime-grouped and era-sliced reporting.  Episode-count sufficiency
    filter applied before reporting.

Work-in-progress — Phase 0 stub.
"""

from .fama_macbeth import FamaMacBeth

__all__ = ["FamaMacBeth"]
