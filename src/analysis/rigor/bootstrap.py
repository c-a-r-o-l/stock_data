"""bootstrap — joint-pipeline block bootstrap for regime-clustering inference.

Procedure
---------
1. Resample trading-day blocks (length = bootstrap_block_days) with replacement.
2. Refit k-means clustering on each resample.
3. Hungarian-match cluster labels to original centroids.
4. Rerun Fama-MacBeth stats on matched labels.
5. Aggregate across resamples → empirical null distributions.
6. Optionally apply BH-FDR correction.

Work-in-progress — Phase 0 stub.
"""

from __future__ import annotations


class BlockBootstrap:
    """Joint-pipeline block bootstrap for regime + stats inference.

    Parameters
    ----------
    n_resamples : int
        Number of bootstrap resamples (default 500).
    block_length : int
        Block length in trading days (default 126).
    seed : int
        Random seed for reproducibility.
    """

    def __init__(self, n_resamples: int = 500, block_length: int = 126, seed: int = 42):
        self.n_resamples = n_resamples
        self.block_length = block_length
        self.seed = seed

    def run(
        self,
        panel: "pd.DataFrame",  # noqa: F821
        clusterer: "RegimeClusterer",  # noqa: F821
        stats: "FamaMacBeth",  # noqa: F821
    ) -> "pd.DataFrame":  # noqa: F821
        """Execute the full joint-pipeline bootstrap and return empirical distributions."""
        raise NotImplementedError("Phase 0 stub — implementation TBD")
