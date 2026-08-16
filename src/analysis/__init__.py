"""analysis — downstream research package consuming all_merged.parquet.

Subpackages
-----------
data        : loaders with point-in-time visibility enforcement
features    : beta estimation, regime-relative features, financial-state features
clustering  : k-means clustering, stability metrics, episode segmentation
stats       : two-layer Fama-MacBeth (daily cross-section + Newey-West)
rigor       : joint-pipeline block bootstrap, perturbation checks, FDR correction
report      : tables, figures, results log writer
"""

from .config import Config

__all__ = ["Config"]
