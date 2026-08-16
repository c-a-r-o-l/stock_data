"""tests/test_leakage.py — point-in-time leakage test suite.

Phase 0 skeleton.  All four tests are marked xfail(strict=False) because the
analysis code (visibility-enforcing loaders, feature pipeline, fold generator,
normalizer) does NOT exist yet.  Each test body contains the real assertion
logic written against the placeholder API documented in conftest.py.

Activation sequence (per test):
  test_a — wire  src/analysis/data/loaders.PanelLoader  +  feature provenance
  test_b — wire  src/analysis/features  compute_features()
  test_c — wire  fold generator  +  trading_calendar
  test_d — wire  normalizer.fit_date_range  property

The core property these defend:
  "No feature for day t may depend on data after t."
"""

import hashlib
from typing import Protocol

import numpy as np
import pandas as pd
import pytest

# ── Placeholder Protocols (delete when real analysis code lands) ─────────────
# These mirror the conftest.py documentation.  They exist here so the test
# bodies can reference the expected API signatures without importing from
# conftest (which pytest loads specially).

class LoaderAPI(Protocol):
    """Placeholder for src/analysis/data/loaders.PanelLoader."""
    def get_panel(self, as_of: pd.Timestamp) -> pd.DataFrame: ...

class FeatureAPI(Protocol):
    """Placeholder for src/analysis/features — feature computation."""
    def compute_features(self, as_of: pd.Timestamp) -> pd.DataFrame: ...
    @property
    def input_date_map(self) -> dict[str, str]: ...

class FoldGeneratorAPI(Protocol):
    """Placeholder for fold generator (Phase 7)."""
    def generate_folds(self, **kwargs) -> list: ...

class NormalizerAPI(Protocol):
    """Placeholder for a normalizer that records its fit-date range."""
    def fit(self, data: pd.DataFrame, window: tuple[pd.Timestamp, pd.Timestamp]) -> None: ...
    @property
    def fit_date_range(self) -> tuple[pd.Timestamp, pd.Timestamp]: ...
    def transform(self, data: pd.DataFrame) -> pd.DataFrame: ...

# ── Constants ────────────────────────────────────────────────────────────────
HORIZON_DAYS = 63  # read from cfg fixture at runtime; fallback for module-level use


# ══════════════════════════════════════════════════════════════════════════════
# test_a — feature input date ≤ observation date
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.leakage
@pytest.mark.xfail(
    strict=False,
    reason=(
        "Phase 0 stub — requires src/analysis/data/loaders.PanelLoader with "
        "per-column visibility-date enforcement, plus a feature provenance map "
        "(FeatureAPI.input_date_map) mapping each feature to its latest "
        "contributing input date column."
    ),
)
def test_a_feature_input_dates_le_t(sampled_rows: pd.DataFrame, horizon_days: int) -> None:
    """For each sampled (stock, day t), assert every feature's max input date ≤ t.

    Assumptions (documented):
      - Every feature can be traced to the latest date among the raw inputs
        that produced it.  If the feature pipeline does not yet expose this,
        the test is inactive — it cannot infer provenance from final values
        alone.
      - The ``FeatureAPI.input_date_map`` property returns a dict of
        feature_name → provenance_date_column (the raw-date column in the
        source table whose max per row is the feature's input date).

    Procedure:
      1. For each sampled row (symbol=s, date=t) in the label cross-section,
         call ``compute_features(as_of=t)``.
      2. For each feature column f, look up its provenance date column in
         ``input_date_map``.
      3. Assert that the per-row maximum of that provenance column is ≤ t.
         - Tech features (OHLC, SMA, etc.): observation date = DATE column.
           Provenance date = DATE. Always passes (T+0).
         - Macro features: provenance date = macro release date.
         - Fundamental features: provenance date = announcement date (T+1~2).

    Why it catches leaks:
      A forward-fill that carries Q4 fundamentals past their announcement
      before that announcement happens; a macro release date that extends
      into the future; a rolling z-score whose window includes tomorrow —
      all violate the per-feature input-date ≤ t assertion.
    """
    # -- placeholder implementation (real logic preserved inside xfail) --------
    # When the real LoaderAPI / FeatureAPI exist, uncomment and wire:

    # loader: LoaderAPI = PanelLoader()
    # feature_pipeline: FeatureAPI = compute_features  # or instantiated object
    #
    # for _, row in sampled_rows.iterrows():
    #     symbol, t = row["SYMBOL"], pd.Timestamp(str(row["DATE"]))
    #     features = feature_pipeline.compute_features(as_of=t)
    #     input_map = feature_pipeline.input_date_map
    #
    #     for feat_col, provenance_col in input_map.items():
    #         if feat_col not in features.columns:
    #             continue
    #         # The latest input date that contributed to this feature value
    #         max_input_date = features[provenance_col].max()
    #         assert max_input_date <= t, (
    #             f"LEAK: {symbol} @ {t.date()}: feature '{feat_col}' "
    #             f"has max input date {max_input_date.date()} > {t.date()}"
    #         )

    # -- xfail guard: test body must fail while marker is active --------------
    pytest.fail("Phase 0 stub — PanelLoader / FeatureAPI not yet implemented")


# ══════════════════════════════════════════════════════════════════════════════
# test_b — future-price corruption invariance (the strong catch-all)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.leakage
@pytest.mark.xfail(
    strict=False,
    reason=(
        "Phase 0 stub — requires src/analysis/features.compute_features() "
        "to recompute all features from a raw-price panel.  Will be wired in "
        "Phase 2 (label construction)."
    ),
)
def test_b_future_corruption_invariance(
    panel: pd.DataFrame, seed: int, horizon_days: int,
) -> None:
    """Deep-copy the price panel; corrupt all post-t prices with noise;
    recompute features at t on both panels; assert bitwise-identical.

    This is the strong, model-free catch-all: it does NOT rely on enumerating
    every possible leak path (the blind spot of test_a).  If ANY feature at t
    depends on data after t — through a rolling window, forward-fill,
    cross-sectional normalization, or an obscure interaction — the noise
    injection will change it and the hash comparison will catch it.

    Procedure:
      1. Select N random (symbol, date=t) rows from the sample.
      2. For each row:
         a. Clone the full raw-price panel (only price columns: OPEN, HIGH,
            LOW, CLOSE, plus SPY equivalents).
         b. Compute features at t on the clean panel → reference DataFrame.
         c. Corrupt all price values for dates > t with multiplicative noise:
            price_corrupted = price × U where U ~ Uniform(0.5, 1.5), with a
            fixed seed so corruption is deterministic per t.
         d. Recompute features at t on the corrupted panel.
         e. Hash both feature DataFrames (row-order-stable sort first).
         f. Assert hashes are identical.

    Constraints:
      - Uses EXACT equality (SHA-256 hash), never approximate / allclose.
      - Corrupts only price columns, not dates or symbol identifiers.
      - Fixed seed per call so the same t always gets the same noise.
    """
    # -- placeholder implementation (real logic preserved inside xfail) --------
    # rng = np.random.default_rng(seed)
    # price_cols = ["OPEN_D", "HIGH_D", "LOW_D", "CLOSE_D",
    #                "SPY_C_D", "SPY_O_D", "SPY_H_D", "SPY_L_D"]
    #
    # sample = panel.sample(n=min(20, len(panel)), random_state=seed)
    #
    # for _, row in sample.iterrows():
    #     t = pd.Timestamp(str(row["DATE"]))
    #
    #     # a) clone panel
    #     clean = panel.copy()
    #
    #     # b) reference features at t
    #     ref = compute_features(panel=clean, as_of=t)
    #     ref_hash = hashlib.sha256(
    #         ref.sort_index().to_csv(index=False).encode()
    #     ).hexdigest()
    #
    #     # c) corrupt post-t prices
    #     corrupted = clean.copy()
    #     future_mask = corrupted["DATE"] > int(t.strftime("%Y%m%d"))
    #     for col in price_cols:
    #         if col in corrupted.columns:
    #             noise = rng.uniform(0.5, 1.5, size=future_mask.sum())
    #             corrupted.loc[future_mask, col] *= noise
    #
    #     # d) recompute
    #     corrupted_feat = compute_features(panel=corrupted, as_of=t)
    #     corrupted_hash = hashlib.sha256(
    #         corrupted_feat.sort_index().to_csv(index=False).encode()
    #     ).hexdigest()
    #
    #     # e+f) assert bitwise-identical
    #     assert ref_hash == corrupted_hash, (
    #         f"LEAK: {row['SYMBOL']} @ {t.date()}: future price corruption "
    #         f"changed features — hash mismatch"
    #     )

    # -- xfail guard -----------------------------------------------------------
    pytest.fail("Phase 0 stub — compute_features() not yet implemented")


# ══════════════════════════════════════════════════════════════════════════════
# test_c — embargo gap (trading days, not calendar days)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.leakage
@pytest.mark.xfail(
    strict=False,
    reason=(
        "Phase 0 stub — requires fold generator (Phase 7).  The trading-day "
        "gap logic using the canonical date index from all_merged.parquet is "
        "implemented below and will activate once the fold generator exists."
    ),
)
def test_c_embargo_gap(
    trading_dates: pd.DatetimeIndex, cfg: dict, horizon_days: int,
) -> None:
    """For every (train_window, test_fold) pair, assert train_end + horizon_days
    ≤ test_start in trading-day space.

    Uses the project's canonical trading calendar — the unique sorted DATE
    values from all_merged.parquet — NOT raw calendar-day subtraction.
    63 calendar days ≈ 43–44 trading days, so a calendar-based embargo
    under-protects by ~20 days.  Trading-day arithmetic is non-negotiable.

    Procedure:
      1. Parse fold boundaries from config.yaml.
      2. Call the fold generator to produce (train_window, test_window) pairs.
      3. For each pair:
         a. Find the index position of train_end in the trading calendar.
         b. Advance by horizon_days positions → earliest_allowed_test_start.
         c. Find the index position of the actual test_start.
         d. Assert actual_test_start_position ≥ earliest_allowed_test_start_position.

    Also verifies:
      - The exploration period (after initial train_end, before sealed_start)
        is purged of the 63-trading-day gap before sealed folds begin.
    """
    # -- parse fold boundaries from config ------------------------------------
    folds = cfg.get("folds", {})
    train_start = pd.Timestamp(folds.get("train_start", "2000-07-01"))
    train_end = pd.Timestamp(folds.get("train_end", "2011-12-31"))
    validation_years = folds.get("validation", [2012, 2019])
    sealed_start = pd.Timestamp(folds.get("sealed_start", "2020-01-01"))

    # -- helper: advance N trading days in the canonical calendar -------------
    def trading_day_offset(date: pd.Timestamp, n: int) -> pd.Timestamp | None:
        """Return the date *n* trading days after *date*, or None if out of bounds."""
        pos = trading_dates.searchsorted(date, side="right") - 1
        if pos < 0:
            return None
        target = pos + n
        if target >= len(trading_dates):
            return None
        return trading_dates[target]

    # -- when the fold generator exists ---------------------------------------
    # generator: FoldGeneratorAPI = FoldGenerator(trading_dates=trading_dates)
    # fold_pairs = generator.generate_folds(
    #     train_start=str(train_start.date()),
    #     train_end=str(train_end.date()),
    #     validation_years=validation_years,
    #     sealed_start=str(sealed_start.date()),
    # )
    #
    # for (tw_start, tw_end), (te_start, te_end) in fold_pairs:
    #     # Advance horizon_days trading days from train_end
    #     embargo_end = trading_day_offset(tw_end, horizon_days)
    #     assert embargo_end is not None, (
    #         f"Train end {tw_end.date()} + {horizon_days} trading days "
    #         f"exceeds available trading calendar"
    #     )
    #     assert embargo_end <= te_start, (
    #         f"EMBARGO VIOLATION: train window [{tw_start.date()}, {tw_end.date()}] "
    #         f"→ test fold [{te_start.date()}, {te_end.date()}]; "
    #         f"embargo end ({embargo_end.date()}) > test start ({te_start.date()}); "
    #         f"gap is {te_start - tw_end} calendar days but embargo requires "
    #         f"{horizon_days} trading days"
    #     )

    # -- static sanity check: config boundaries are in-bounds -----------------
    assert train_start < train_end < sealed_start, (
        f"Fold boundary order violated: {train_start.date()} < "
        f"{train_end.date()} < {sealed_start.date()}"
    )

    # Validate that the embargo gap exists in trading-day space between the
    # initial training period and the first sealed fold — a minimal static
    # check that doesn't require the fold generator.
    last_train_date = pd.Timestamp("2011-12-31")
    first_sealed_date = sealed_start
    if last_train_date in trading_dates and first_sealed_date in trading_dates:
        train_pos = trading_dates.get_loc(last_train_date)
        sealed_pos = trading_dates.get_loc(first_sealed_date)
        gap_days = sealed_pos - train_pos
        # This is the gap between end-of-training and start-of-sealed, which
        # includes the entire validation period — should be comfortably > horizon.
        # The actual per-fold embargo is enforced by the fold generator above.
        assert gap_days > horizon_days, (
            f"Gap between train_end ({last_train_date.date()}) and "
            f"sealed_start ({first_sealed_date.date()}) is only "
            f"{gap_days} trading days — less than horizon {horizon_days}"
        )

    # -- xfail guard -----------------------------------------------------------
    pytest.fail("Phase 0 stub — FoldGenerator not yet implemented (Phase 7)")


# ══════════════════════════════════════════════════════════════════════════════
# test_d — normalization statistics computed strictly within window
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.leakage
@pytest.mark.xfail(
    strict=False,
    reason=(
        "Phase 0 stub — requires Normalizer with fit_date_range property "
        "(Phase 2: feature engineering).  The runtime-checkable portion is "
        "implemented below; the residual static-discipline items are "
        "documented for code review."
    ),
)
def test_d_normalization_window(
    panel: pd.DataFrame, seed: int,
) -> None:
    """Assert no normalization statistic is computed from data outside the
    window it is applied to.

    Runtime-checkable portion:
      Every Normalizer must record the date range of the data it was ``fit``
      on (exposed as ``fit_date_range`` property).  For any (normalizer,
      application_window) pair, assert::

          normalizer.fit_date_range ⊆ application_window

      i.e., the fit-start ≥ window-start and fit-end ≤ window-end.

    Residual static-discipline items (code-review checklist):
      - Winsorization cut-points must be computed per cross-section, not
        from the full history.
      - Percentile-rank features must use a trailing reference window, not
        the full-series quantiles.
      - Cluster scaler statistics (mean, std) must be frozen from the
        training window and applied unchanged to all later folds.
      - Any z-score must use μ, σ from the exact window it serves — never
        the full column, never a future-inclusive window.
      - Cross-sectional normalization (rank, z-score-within-day) is
        inherently point-in-time and needs no extra check beyond test (a).
    """
    # -- placeholder implementation (real logic preserved inside xfail) --------
    # rng = np.random.default_rng(seed)
    #
    # # Simulate a normalizer fit on a sub-window of the panel
    # all_dates = sorted(panel["DATE"].unique())
    # mid = len(all_dates) // 2
    # window_start = pd.Timestamp(str(all_dates[0]))
    # window_end = pd.Timestamp(str(all_dates[mid]))
    # fit_window = (window_start, window_end)
    #
    # window_data = panel[
    #     (panel["DATE"] >= int(window_start.strftime("%Y%m%d"))) &
    #     (panel["DATE"] <= int(window_end.strftime("%Y%m%d")))
    # ]
    #
    # normalizer: NormalizerAPI = Normalizer()
    # normalizer.fit(window_data, window=fit_window)
    #
    # fit_start, fit_end = normalizer.fit_date_range
    # assert fit_start >= window_start, (
    #     f"NORMALIZATION LEAK: fit start {fit_start.date()} < "
    #     f"window start {window_start.date()}"
    # )
    # assert fit_end <= window_end, (
    #     f"NORMALIZATION LEAK: fit end {fit_end.date()} > "
    #     f"window end {window_end.date()}"
    # )
    #
    # # Also verify the normalizer can transform data within the same window
    # transformed = normalizer.transform(window_data)
    # assert len(transformed) == len(window_data)

    # -- xfail guard -----------------------------------------------------------
    pytest.fail("Phase 0 stub — Normalizer not yet implemented (Phase 2)")


# ══════════════════════════════════════════════════════════════════════════════
# test_e — unclassified threshold invariant (frozen p95 = pre-filter p95)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.leakage
def test_e_unclassified_threshold_equals_freeze_step_p95(cfg) -> None:
    """Assert the frozen unclassified threshold for every cluster equals the
    p95 of pre-filter within-cluster training distances.

    CRITICAL: reads ``regime_train_distances.parquet`` (PRE-FILTER freeze-step
    labels), NOT ``regime_labels.parquet`` (forward-apply, post-unclassified-
    filter).  Computing per-cluster p95 on the forward-apply labels trims the
    >p95 tail that the threshold itself removed, shifting the recomputed p95
    downward.  That measurement artifact is exactly why this assertion exists —
    it caught a false alarm where the panic p95 appeared to be 5.81 instead of
    the correct 6.48.  See data_issues_log.md item 7.
    """
    from pathlib import Path
    import json
    import numpy as np
    import polars as pl

    model_path = Path("data/History_6_merge/regime_model_frozen.json")
    dist_path = Path("data/History_6_merge/regime_train_distances.parquet")

    if not model_path.exists() or not dist_path.exists():
        pytest.skip("T3.2b model artifacts not found")

    with open(model_path) as f:
        model = json.load(f)
    frozen = model["unclassified_thresholds_per_cluster"]

    df = pl.read_parquet(dist_path)
    for c in range(model["K"]):
        dists = df.filter(pl.col("cluster") == c)["dist_to_centroid"].to_numpy()
        p95 = float(np.percentile(dists, 95))
        assert abs(p95 - frozen[str(c)]) < 1e-9, (
            f"Cluster {c}: frozen threshold {frozen[str(c)]:.6f} ≠ "
            f"pre-filter p95 {p95:.6f} (Δ={abs(p95-frozen[str(c)]):.6f}). "
            f"Threshold was not computed from freeze-step p95 — was a "
            f"different statistic stored?  Check the freeze code."
        )


# ══════════════════════════════════════════════════════════════════════════════
# Collection hook — tag all leakage items
# ══════════════════════════════════════════════════════════════════════════════

def pytest_collection_modifyitems(config, items):
    """Add the 'leakage' marker to every item in this module."""
    for item in items:
        if "leakage" in item.keywords or "test_leakage" in str(item.fspath):
            item.add_marker(pytest.mark.leakage)
