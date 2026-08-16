# Merged system — decisions locked, for review

This is the reconciliation of **Plan 2** (Market State Foundation Model, per-stock
time-sequence + Transformer) and the **project breakdown** (cross-sectional (stock,
date) factor vectors + k-NN retrieval). It records what the merged system *is*, what
gets dropped, and where each remaining hard problem is handled. Review this; the html
gets rewritten from it next.

---

## The one decision everything else hangs on

The two plans are **not two versions of one design**. The breakdown is a
cross-sectional (stock, date) system; Plan 2 is a per-stock time-sequence system.
The merge is **not a blend** — it adopts the breakdown's architecture as the spine and
treats Plan 2 as (a) reusable data plumbing and (b) a catalog of things deliberately
*not* done, with the encoder held back as a single late experiment.

**Core = the breakdown, essentially in full.** Cross-sectional (stock, date) vectors
of hand-built factors, standardized against each day's point-in-time peers, in a FAISS
index, with distance-weighted k-NN as the first predictor. Plan 2's sequence
architecture, contrastive-on-label training, 768-dim encoder, and
parallel-XGBoost-not-fed-by-FAISS are all dropped from the core.

---

## Issue ranking — severity, source, problem, fix

### 1. Per-stock time-sequence architecture — CORE-WRONG (Plan 2)
**Problem.** Plan 2 represents each stock as an independent 252-day sequence collapsed
to one embedding, with no cross-sectional structure. But the label is cross-sectional
(top 10% of stocks *that day*). You'd be predicting a stock's rank *among its peers*
from a representation that never saw the peers.
**Why core, not bandaid.** Nearly every other Plan 2 problem is downstream of this one
choice. Grafting the cross-sectional label onto per-stock sequences produces a model
forced to reconstruct a cross-section it was never given.
**Fix.** Adopt the breakdown's unit wholesale: the **(stock, date) cross-sectional
factor vector, standardized against that day's peers.** Drop Plan 2's sequence framing
entirely. *This is not a fixable Plan 2 issue — it's the reason to not use Plan 2's
spine.*

### 2. Label-fitted embeddings via contrastive learning — CORE-WRONG for retrieval (Plan 2)
**Problem.** The encoder is trained using forward returns to shape the space (positive
pairs = same-outcome windows), then FAISS *and* XGBoost run on those embeddings. The
representation is bent toward the target before anything predicts the target — so
"these historical states are similar to today" partly means "they had similar
outcomes," which is what you're trying to predict. Circular.
**Fix.** Using hand-built Vector A (never sees the label) dissolves this by
construction — the label touches the pipeline exactly once, at prediction.
**Encoder caveat (for gate 6).** If an encoder is tested later, it must be trained on a
**non-label objective** (reconstruction / masked-feature / next-step), AND its inputs
must be strictly point-in-time (a self-supervised objective still leaks if the
reconstruction target contains forward-looking data). This fixes *contamination*, not
*usefulness* — the encoder still has to beat Vector A on unseen data to earn its place.

### 3. Overlapping-label autocorrelation / effective-N inflation — BOTH (worst in Plan 2)
**Problem.** Overlapping windows with long forward-return labels mean thousands of
"samples" contain only a few hundred *independent* observations. Metrics inflate
because train/val samples bleed through shared label periods. Survives the embargo,
which only protects the train/test *boundary*, not independence *within* a set.
**Resolution (NOT shrinking the dataset).** Two different things were being conflated:
- **Train** on overlapping windows — keep them, more samples still help fitting.
- **Evaluate + claim significance** using effective-N logic.
So: **train on everything; report honestly.** Concretely —
  - *Effective-N reporting:* attach every headline metric to its true independent-sample
    count (≈ calendar span ÷ label horizon), e.g. "AUC 0.71, effective N ≈ 20 periods/stock,
    not 8,000 windows."
  - *Purged evaluation:* measure test metrics only on held-out outcomes that share no
    label period with training (embargo at the boundary + neighbor-pool rule at retrieval).
  - *Significance against effective N:* bootstrap over **non-overlapping blocks**, not
    individual days, + deflated Sharpe for the number of variants tried. Report CIs, e.g.
    "Sharpe 0.8, 95% CI [0.2, 1.4] on ~20 independent periods."
- *One-liner:* **train on everything, measure on purged held-out outcomes, attach every
  number to its true independent-sample count.**
- Shortening the label horizon genuinely increases independent draws; shrinking the
  *input window* does not.

### 4. Two-stage XGBoost leakage through the neighbor pool — (breakdown)
**Problem.** Stage-1 features summarize neighbors' *forward outcomes*. If a neighbor's
label period extends past the query date *t*, that feature leaks post-*t* info. Standard
train/test purging does NOT catch this — the leak is at *query construction*.
**What the neighbor set is.** For a query "score stock X on date *t*," you build X's
vector as of *t* and ask FAISS for the *k* nearest historical (stock, date) points.
That returned set is the neighbor set; you read *their* forward outcomes to predict.
**Fix / admissibility rule.** A historical point may enter the neighbor set for query
*t* **only if its entire label period ended strictly before *t*** — with a 252-day
horizon, the neighbor must be dated ≥ 252 days before *t*. Enforced at *every*
retrieval, separate from and stricter than the embargo. **Purge in two places: the
split AND the neighbor pool.**

### 5. Oversized embedding / parameter count — (Plan 2, only if encoder kept)
**Problem.** 768-dim, ~28M params (the plan's "10–15M" is itself an underestimate),
cargo-culted from BERT, against ~50 factors and few effective samples. Massive
over-parameterization; also degrades FAISS (distances go meaningless in 768-dim).
**Fix.** If/when an encoder is tested, size to the problem: **64–128 dim**, not 768.
Mostly moot — the encoder is a gate-6 experiment, not the foundation.

### 6. Forward-fill distorting the distance metric — BOTH (worse/uninspectable in Plan 2)
**Problem.** Quarterly features forward-filled to daily are constant ~98% of the time;
in a distance metric a stale constant can dominate "closeness" or be over-represented
by column count. Plan 2 asks you to *trust* a black-box encoder to handle this — you
can't inspect it.
**Fix (make staleness visible, not trusted).** Check each factor's constancy/variance
share; down-weight or drop near-constant features in the distance; optionally add a
"days-since-last-update" feature so staleness is *modeled*. Inspectable in Vector A;
not in a learned embedding — another vote for the Vector A core.

### 7. Cross-sectional standardization erases regime info — genuine tradeoff (breakdown)
**Problem.** Z-scoring within each day removes the market's *absolute* level, so "+2σ
momentum in calm 2017" and "+2σ in the 2020 crash" land at the same coordinate. For a
*market-state* system you've normalized away regime signal you may want neighbors to
share. Not a bug — an inherent tradeoff of the standardization you need.
**Fix (design, not bandaid).** Add explicit **regime features** — same for every stock
on a given day, describing the environment: volatility regime (VIX / realized vol),
trend regime (index vs 200-day MA, breadth), cross-sectional dispersion, rate/macro
regime (yield-curve slope, credit spreads — the *continuous* macro indicators, entered
as raw magnitudes, not binarized). Then **decide deliberately** whether retrieval should
match within-regime or across-regime, rather than letting standardization decide by
accident.

### 8. Cheap k-NN neighborhoods with a small universe — MINOR (breakdown), shelved
With ~200 stocks, "100 neighbors" can be half the universe. Resolves as the universe
grows (CRSP). Pool neighbors across all dates (pool = decades × universe), set k
relative to pool size. Not a blocker.

---

## Vector A vs the encoder — sequencing, not co-equal cores

Keep both methods available, but they are **not** two parallel foundations. **Vector A
is the core; the encoder is the challenger that must beat it.** Build A, prove it
end-to-end, freeze the pipeline, then swap Vector B into the *identical* pipeline (same
DB, same backtest, same everything — only the vector source changes) and re-run. That
sequencing is what turns "I have two methods" into "I ran a controlled experiment" —
which per the breakdown's own thesis *is* the project.

---

## What survives from Plan 2
- Multi-frequency data sourcing and forward-fill **plumbing** (reusable).
- **Release-date alignment** of macro data (Plan 2 gets this right — keep it).
- The encoder itself, **demoted** to a single gate-6 experiment: non-label objective,
  64–128 dim, kept only if it beats Vector A on unseen data.

## What is dropped from Plan 2
- Per-stock time-sequence architecture (→ cross-sectional (stock, date)).
- Contrastive-on-the-label training.
- 768-dim embedding / ~28M-param encoder as the foundation.
- FAISS and XGBoost as parallel paths — in the merge, **XGBoost stage-1 features come
  FROM the FAISS neighborhood**, not alongside it.

---

## Open items still to confirm
- Exact label horizon (drives effective N, embargo width, and the ≥252-day neighbor
  rule — if you shorten the horizon, all three move together).
- Whether retrieval should match within-regime or across-regime (issue 7).
- Effective-N target: the honest independent-sample count you're comfortable reporting.

---

## SPY_C formula — confirmed (2026-07-09)

**Definition** (from `doc/backup/Column_Description.txt` line 119):
> `SPY_X = 1,000,000 × Stock_X / SPX_X`

SPX is the S&P 500 **index** (not the SPY ETF). The SPY ETF trades at roughly 1/10
of the index level, which accounts for the apparent 10× discrepancy when comparing
against SPY close prices.

**Verified on 200 random AAPL dates (2026-07-09), updated with role swap:**

- **Primary check (SPY ETF, same-day):** `SPY_C_D × MKT_SPY_CLOSE_MKT / CLOSE_D ≈ 100,000` —
  10/10 within ±1.5% (all 10 under ±0.9%). SPY/SPX tracking drift accounts for the
  decade-level K variation (100,246 in 2000s → 99,773 in 2020s). This is the formula
  to use for same-day consistency checks.

- **Macro staleness probe (FRED SP500):** `SPY_C_D × SP500_MAC / CLOSE_D` expects
  to deviate from 1,000,000 by approximately −(day's SPY return) on big-move days,
  because the macro series is T+1 aligned. Confirmed on 4/5 big-move days:
  - 2018-04-10: SPY +1.59%, K_dev −1.65% (residual −0.06pp)
  - 2022-10-06: SPY −1.03%, K_dev +1.04% (residual +0.01pp)
  - 2017-10-20: SPY +0.52%, K_dev −0.51% (residual +0.01pp)
  - 2018-05-10: SPY +0.94%, K_dev −0.93% (residual +0.01pp)
  - 2023-08-15: SPY −1.16%, K_dev +1.17% (residual +0.00pp)
  - 2020-03-20 resolved: the original probe used SPY return as an SPX proxy
    with a linear approximation (K_dev ≈ −ret).  On a −4.87% SPY / −4.33% SPX
    crash day, the 0.54pp tracking gap produced a false residual.  The data
    was correct all along — L_SP500 on 03-20 equals SPX_implied(03-19) at
    0.00% precision.

**Final probe (2026-07-09): direct comparison, no proxy, no approximation.**
  - SPX_implied(t) = 1,000,000 × CLOSE_D / SPY_C_D  (precise, no SPY/SPX gap)
  - Test: on trading day t, L_SP500(t) should equal SPX_implied(t−1), not
    SPX_implied(t).  A macro value matching SPX_implied(t) would be same-day
    alignment (lookahead leak).
  - Result: 20/20 random dates (incl. 2020-03-20) show L_SP500(t) =
    SPX_implied(t−1) within 0.1%.  Zero instances of L_SP500(t) =
    SPX_implied(t) where a market move occurred.  The two dates where both
    comparisons fell within 0.1% (2021-01-12, 2024-02-12) were flat-market
    days where SPX_implied barely changed — the macro matched t−1 at 0.00%
    on both, confirming T+1.
  - Leak signature: L_SP500(t) ≈ SPX_implied(t) AND L_SP500(t) ≉
    SPX_implied(t−1) on a day with a meaningful market move.  Never observed.
