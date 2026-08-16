"""rigor — joint-pipeline block bootstrap, perturbation checks, and FDR correction.

Core tools
----------
- Joint-pipeline block bootstrap: resample blocks → refit clusters →
  Hungarian matching → rerun Fama-MacBeth → empirical null distributions.
- Perturbation checks for sensitivity analysis.
- BH-FDR correction across all reported test statistics.

Work-in-progress — Phase 0 stub.
"""

from .bootstrap import BlockBootstrap

__all__ = ["BlockBootstrap"]
