"""tests/conftest.py — shared fixtures and placeholder API for the analysis layer.

Phase 0 scaffold.  The analysis code (visibility-enforcing loaders, feature
pipeline, clustering, fold generator) does NOT exist yet.  This file documents
the expected API so tests can be written against it now and activated later
by removing the xfail mark and wiring the real import.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

import pandas as pd
import pytest
import yaml

# ── Paths ────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
DATA_PATH = PROJECT_ROOT / "data" / "History_6_merge" / "all_merged.parquet"


# ── Config fixture ───────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def cfg() -> dict:
    """Load config.yaml once per test session."""
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def horizon_days(cfg) -> int:
    """Forward-return horizon from config (trading days)."""
    return int(cfg["horizon_days"])


@pytest.fixture(scope="session")
def seed(cfg) -> int:
    """Fixed RNG seed from config."""
    return int(cfg["seed"])


# ── Data fixtures ────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def panel() -> pd.DataFrame:
    """Load the full all_merged.parquet (date index only for embargo checks).

    For full-feature tests this will be extended to load the columns needed;
    currently loads SYMBOL + DATE to keep the session fixture lightweight.
    """
    if not DATA_PATH.exists():
        pytest.skip("all_merged.parquet not found")
    return pd.read_parquet(DATA_PATH, columns=["SYMBOL", "DATE"])


@pytest.fixture(scope="session")
def trading_dates(panel) -> pd.DatetimeIndex:
    """Sorted unique trading dates from the merged dataset.

    These are the project's canonical trading calendar — no weekends, no
    holidays present in the parquet.  All embargo / horizon arithmetic MUST
    use this index, never raw calendar-day subtraction.
    """
    dates = pd.to_datetime(
        panel["DATE"].astype(str), format="%Y%m%d"
    ).drop_duplicates().sort_values()
    return pd.DatetimeIndex(dates)


@pytest.fixture(scope="session")
def sampled_rows(panel, seed) -> pd.DataFrame:
    """A small, reproducible sample of (SYMBOL, DATE) rows for point-checks.

    Parameterisable via SAMPLE_SIZE; set to 50 for CI speed.
    """
    SAMPLE_SIZE = 50
    rng = pd.Series(panel.index, index=panel.index).sample(
        n=min(SAMPLE_SIZE, len(panel)), random_state=seed
    ).index
    return panel.loc[rng, ["SYMBOL", "DATE"]].reset_index(drop=True)


# ── Placeholder API — what the analysis layer will expose ────────────────────
#
# These Protocols document the EXPECTED call signatures of the analysis code
# that does NOT exist yet (targets: src/analysis/data/loaders.py and
# src/analysis/features/).  Tests are written against these signatures so
# activation is just: remove xfail, import real module, done.
#
# TODO: when the real implementations land, delete the Protocol stubs below
#       and update the import paths in test_leakage.py.

class LoaderAPI(Protocol):
    """Placeholder for src/analysis/data/loaders.PanelLoader."""

    def get_panel(self, as_of: pd.Timestamp) -> pd.DataFrame:
        """Return a cross-section with only data observable on or before *as_of*.

        Columns include SYMBOL, DATE, and all features visible at *as_of*.
        Any feature whose source release date exceeds *as_of* is masked to NaN.
        """
        ...


class FeatureAPI(Protocol):
    """Placeholder for src/analysis/features — the feature computation pipeline."""

    def compute_features(self, as_of: pd.Timestamp) -> pd.DataFrame:
        """Compute all features point-in-time as of *as_of*.

        Returns a DataFrame indexed by SYMBOL with feature columns.
        No input data after *as_of* is accessed during computation.
        """
        ...

    @property
    def input_date_map(self) -> dict[str, str]:
        """Map of feature_name → provenance date column name.

        Enables test (a) to trace each feature value back to its
        latest contributing input date and verify it does not exceed
        the observation date.
        """
        ...


class FoldGeneratorAPI(Protocol):
    """Placeholder for the expanding-window fold generator."""

    def generate_folds(
        self,
        train_start: str,
        train_end: str,
        validation_years: list[int],
        sealed_start: str,
    ) -> list[tuple[tuple[pd.Timestamp, pd.Timestamp], tuple[pd.Timestamp, pd.Timestamp]]]:
        """Yield (train_window, test_window) pairs.

        Each window is (start_date, end_date) as Timestamps.
        """
        ...


class NormalizerAPI(Protocol):
    """Placeholder for a normalizer that records its fit-date range."""

    def fit(self, data: pd.DataFrame, window: tuple[pd.Timestamp, pd.Timestamp]) -> None:
        """Compute statistics from data strictly within *window*."""
        ...

    @property
    def fit_date_range(self) -> tuple[pd.Timestamp, pd.Timestamp]:
        """The date range of data this normalizer was fit on."""
        ...

    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """Apply the frozen statistics to *data*."""
        ...


# ── Terminal summary — prints after all tests complete ───────────────────────

STUB_DEPS = {
    "test_a_feature_input_dates_le_t": (
        "src/analysis/data/loaders.py (PanelLoader with per-column "
        "visibility dates) + feature provenance map (input_date_map)"
    ),
    "test_b_future_corruption_invariance": (
        "src/analysis/features/ (compute_features() + raw-price panel "
        "access) — Phase 2"
    ),
    "test_c_embargo_gap": (
        "FoldGenerator + trading calendar from all_merged.parquet "
        "— Phase 7"
    ),
    "test_d_normalization_window": (
        "Normalizer with fit_date_range property — Phase 2"
    ),
}


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Print a stub-activation summary after all tests finish."""
    leakage_nodes = [
        nodeid
        for nodeid, outcomes in terminalreporter.stats.items()
        if nodeid in ("xfailed", "xpassed")
    ]
    # Find any leakage test result
    xfailed = terminalreporter.stats.get("xfailed", [])
    xpassed = terminalreporter.stats.get("xpassed", [])
    all_leakage = [r for r in xfailed + xpassed if "leakage" in r.nodeid or "test_leakage" in r.nodeid]

    if not all_leakage:
        return

    terminalreporter.write_sep("=", "LEAKAGE TEST SUITE — Phase 0 stubs")
    for result in all_leakage:
        test_name = result.nodeid.split("::")[-1]
        dep = STUB_DEPS.get(test_name, "unknown")
        terminalreporter.write_line(f"  {test_name}")
        terminalreporter.write_line(f"    → needs: {dep}")
    terminalreporter.write_sep(
        "=",
        f"{len(all_leakage)} tests xfailed — activate by removing @pytest.mark.xfail",
    )
