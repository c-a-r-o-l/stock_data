# Regime model — frozen artifact manifest

Frozen 2026-07-26.  k=4, trained on 2002-07-03 → 2011-12-30 (2,393 days).

## Artifact files

| File | Content |
|------|---------|
| `regime_model_frozen.json` | K, seed, feature list, scaler stats, centroids, unclassified thresholds, train-window bounds, training-matrix hash, git commit, freeze timestamp |
| `regime_model_frozen.parquet` | Scaler stats (feature, mean, std) — redundant with the JSON, kept for convenience |
| `regime_scaler_stats_T3.2a.parquet` | Origin scaler (fitted in T3.2a, reused here — identical) |
| `regime_labels.parquet` | Forward-applied labels: DATE, regime (0–3 or 'unclassified'), dist_to_centroid |

## Features (11, in order)

`spy_ret_21`, `spy_ret_63`, `spy_rvol_21`, `vix_pct_2y`, `gv_z`,
`baa10y_z_1y`, `baa10y_chg_21`, `curve_z_1y`, `curve_chg_21`,
`dgs10_z_1y`, `nfci_z_1y`

## Unclassified threshold

Per-cluster, 95th percentile of within-cluster Euclidean distances
(in standardized space) measured on the training window:

| Cluster | Threshold | Interpretation |
|---------|-----------|---------------|
| 0 | 3.59 | Calm/risk-off — tight spread |
| 1 | 6.48 | Panic — widest spread (stress days vary more) |
| 2 | 3.89 | Elevated stress — moderate spread |
| 3 | 2.77 | Risk-on/calm — tightest spread |

Per-cluster chosen because cluster spreads differ materially (panic cluster
is ~2.3× wider than calm-risk-on).  95 is a perturbation-list constant
(Phase 8 will vary 90/95/97.5).

## How to reproduce

```python
from sklearn.cluster import KMeans
# 1. Load regime_features.parquet, slice to 2002-07-03 → 2011-12-30
# 2. Standardize using mean/std from regime_model_frozen.json
# 3. KMeans(k=4, seed=42, n_init=10).fit(X).cluster_centers_
# → matches stored centroids
```

Training matrix hash: stored in the JSON (SHA-256 of standardized X_train bytes).
Git commit at freeze: stored in the JSON.

## Forward-apply rule

For any new day:
1. Standardize the 11 features using frozen mean/std.
2. Compute Euclidean distance to each of the 4 centroids.
3. Nearest centroid → regime label.
4. If distance > that cluster's frozen threshold → "unclassified."

## What is NOT in this artifact

- Human-readable regime names (stored separately, to keep math and
  interpretation decoupled)
- Any post-2011 data
- Any re-estimated scaler or threshold
