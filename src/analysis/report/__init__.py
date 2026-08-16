"""report — table/figure generation and results-log persistence.

Results log
    Appends one JSONL record per analysis run with timestamp, config hash,
    git commit, phase label, and summary statistics.  The log is the
    project's single source of truth for "what run produced what result."

Work-in-progress — Phase 0 stub.
"""

from .results_log import ResultsLog

__all__ = ["ResultsLog"]
