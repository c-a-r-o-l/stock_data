"""clustering — k-means clustering with stability metrics and episode segmentation.

Approach
--------
- Market regimes: k-means over trailing z-scores, VIX percentile, spreads
  with k in {4, 5, 6}.
- Financial states: k-means over announcement-snapshot features with
  k in {3, 4, 5}.
- Stability assessed via block-bootstrap + adjusted Rand index.
- Best model frozen (scaler stats + centroids serialized).
- Unclassified threshold: distance percentile (default 95th).
- Episode segmentation: minimum 10-day contiguous regime spans.

Work-in-progress — Phase 0 stub.
"""

from .kmeans import RegimeClusterer, FinstateClusterer

__all__ = ["RegimeClusterer", "FinstateClusterer"]
