"""kmeans — regime and financial-state clustering via k-means.

RegimeClusterer
    k-means over regime features with k in {4, 5, 6}.
    Includes block-bootstrap stability assessment, adjusted Rand
    scoring, model serialisation, and unclassified-state detection.

FinstateClusterer
    k-means over financial-state features with k in {3, 4, 5}.
    Operates on quarterly announcement-snapshot data.

Work-in-progress — Phase 0 stub.
"""

from __future__ import annotations


class RegimeClusterer:
    """k-means market regime clustering.

    Parameters
    ----------
    k_range : list[int]
        Candidate k values, e.g. [4, 5, 6].
    unclassified_pctile : float
        Distance percentile above which a point is marked unclassified.
    """

    def __init__(self, k_range: list[int] | None = None, unclassified_pctile: float = 95):
        self.k_range = k_range or [4, 5, 6]
        self.unclassified_pctile = unclassified_pctile

    def fit(self, features: "pd.DataFrame") -> "RegimeClusterer":  # noqa: F821
        raise NotImplementedError("Phase 0 stub — implementation TBD")

    def predict(self, features: "pd.DataFrame") -> "pd.Series":  # noqa: F821
        raise NotImplementedError("Phase 0 stub — implementation TBD")


class FinstateClusterer:
    """k-means financial-state clustering (quarterly snapshots).

    Parameters
    ----------
    k_range : list[int]
        Candidate k values, e.g. [3, 4, 5].
    """

    def __init__(self, k_range: list[int] | None = None):
        self.k_range = k_range or [3, 4, 5]

    def fit(self, features: "pd.DataFrame") -> "FinstateClusterer":  # noqa: F821
        raise NotImplementedError("Phase 0 stub — implementation TBD")

    def predict(self, features: "pd.DataFrame") -> "pd.Series":  # noqa: F821
        raise NotImplementedError("Phase 0 stub — implementation TBD")
