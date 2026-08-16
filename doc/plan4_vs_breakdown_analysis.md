# Plan 4 vs. Breakdown — Analysis and Method Notes

A consolidated reference covering: what each plan proposes, whether Plan 4 improves on the older Breakdown, the correctness of Plan 4's "early misconception" boxes, what should be carried back from Breakdown, the outstanding issues in Plan 4, and standalone explanations of the walk-forward validation, the bootstrap, drift, the Fama-MacBeth regression, and the personal-indicator contamination problem.

---

## 1. What each plan is

### Breakdown (older) — a retrieval-and-prediction system

Turn every `(stock, date)` into a hand-built, cross-sectionally standardized factor vector ("Vector A"). Index all of history in FAISS; for any new day, retrieve the nearest historical analogues and forecast the 126-day (~6-month) forward cross-sectional return.

Prediction proceeds in two stages: first distance-weighted k-NN over the neighbors; then a two-stage upgrade — summarize the neighborhood into features (mean outcome, agreement/spread, how close the matches were, fraction positive) and feed those plus today's static factors into XGBoost for a calibrated probability. Evaluate with a purged, cost-aware walk-forward backtest reporting Sharpe / Sortino / drawdown / turnover, broken down by regime, against dumb baselines (buy-and-hold, moving-average crossover, logistic regression). Finally, a Transformer encoder ("Vector B") is tested as a *challenger* by swapping it into the identical pipeline. The deliverable is a controlled experiment: **does the learned representation beat hand-built factors?**

### Plan 4 (newer) — an exploratory study of conditional structure

Not a predictor. Cluster market-level data into 4–6 regimes; cluster company fundamentals into a few "financial states"; encode a personal path-dependent price indicator into discrete, human-readable states (structure intact/broken, which leg, distance from the leg's origin). Then run two-layer Fama-MacBeth statistics on the `regime × financial-state × structure` interactions against next-H-period cross-sectional return ranks, with progressive baselines (B0 unconditional → B1 regime only → B2 full). Success is measured by the **stability and size of the conditional differences** (plus rank IC where ranking is needed) — explicitly not accuracy, not a backtest, no trading claim. Retrieval is demoted to an optional visualization; the encoder to a stretch goal; reinforcement learning is explicitly rejected.

### Headline differences

| Dimension | Breakdown | Plan 4 |
|---|---|---|
| Goal | Prediction system | Descriptive / inferential research |
| Spine | FAISS retrieval + k-NN/XGBoost | Two-layer Fama-MacBeth |
| Prediction layer | k-NN → XGBoost calibrated probability | None |
| Evaluation | Backtest, Sharpe/drawdown | Conditional-effect stability + rank IC |
| Regime handling | Continuous regime features (raw magnitudes) | Discrete regime clusters |
| Personal indicator | Absent | Central, novel ingredient |
| Trading claim | Implied (net-of-cost Sharpe) | None (out of scope by design) |

---

## 2. Does Plan 4 improve on Breakdown?

Mostly yes — and it improves by continuing Breakdown's own logic further than Breakdown did. Breakdown's thesis was "rigor beats architecture"; Plan 4 takes that seriously enough to delete the architecture.

- **The weakest claim is gone.** Breakdown still ultimately promised a Sharpe ratio — the exact number it admitted rests on ~20 effective independent observations. Plan 4 reframes success around whether a conditional regularity is *stable*, a claim the data can actually support. This is the single biggest upgrade.
- **Metrics now match the effective sample size.** Breakdown diagnosed the effective-N problem and then reported Sharpe anyway. Plan 4 designs the whole evaluation around it: minimum independent-episode thresholds, coarse clusters as "controlled fuzziness," refusal to conclude below threshold.
- **The drift taxonomy (5.8) is genuinely new and good.** Breakdown only had "break results down by regime." Distinguishing Drift A (fix with relative features) from Drift B (can't fix; measure and report by era) is more sophisticated, and the relative-features principle is interview-grade.
- **New concrete mechanisms:** cluster stability via bootstrap; exploration/confirmation separation applied to the classifications themselves (refitting clusters on the full sample is itself leakage).
- **A real differentiator entered the project:** the path-dependent indicator, handled correctly as a *testable hypothesis fed in explicitly*, not a premise.
- **Scope realism:** minimum-core / extensions / won't-do is more finishable in a summer than Breakdown's seven gates; "evaluated RL and rejected it" is a smart talking point.

**Honest tradeoff:** Breakdown gave the desk-flavored "did the sophisticated thing beat the simple thing, net of costs" story. Plan 4 trades that for a research-flavored one — probably the better trade for quant *research* roles, but be ready for the "is any of this tradable?" question with a deliberate "out of scope, and here's why."

---

## 3. Are Plan 4's "early misconception" boxes correct?

Most are correct; one contains a real technical error.

**Correct:**
- **§2.2** — Automatic cluster-count selection just hides the subjectivity in the choice of criterion; stability + interpretability is the sturdier standard. (Textbook cluster validation.)
- **§2.6** — Look-ahead comes from *usage*, not source cleanliness; the three risk locations (visibility dates, restatements, full-sample normalization) are exactly right.
- **§4 Stage A** — Merging the financial and macro clusterings would destroy the interaction being studied; you need independent axes to cross. Correct and subtle.
- **§5.8 (RL rejected)** — Defensible. Worth adding a second reason: RL is catastrophically sample-inefficient and effective N here is tiny — an argument even harder to rebut than the non-stationarity one.

**Correct in practice, slightly overstated:**
- **§2.4 (autoencoder can't learn the indicator)** — In principle a sequence model *can represent* a path-dependent rule; the accurate claim is that a reconstruction objective gives it *no incentive* to learn that specific predicate, and on this data volume it essentially never will. Conclusion (feed the indicator in directly) is right.
- **§0** — "A prediction project is actually a negative" is a bit strong (a rigorously evaluated one is fine, per Breakdown), but the direction is right.

**Flawed — §3, the beta/label box.** The *diagnosis* is correct (top-decile total return in a bull market largely selects high-beta names). But the prescribed fix, "excess return relative to the market," is a **no-op under Plan 4's own label**, which is a *cross-sectional rank within each day's universe*. Subtracting the same market return from every stock changes no ranks: `rank(rᵢ) = rank(rᵢ − r_m)` identically. The beta problem lives in the *ordering*, not the level — high-beta names rank top in up-markets and bottom in down-markets regardless. Actual fixes: (a) rank beta-residualized returns `rank(rᵢ − βᵢ·r_m)`, or (b) accept the beta channel but control for beta as a feature so "conditional structure" isn't just rediscovering "beta works in bull regimes." **This box must be rewritten before it faces an interviewer.**

---

## 4. What from Breakdown should be carried back

Cheap to restore and materially strengthening:

- **Leakage unit test + engineering craft.** Plan 4 says "reproducible codebase" in one line. Breakdown's specifics — a test asserting no feature at `t` uses data from `t+1`, modular pipeline, config/seeds, a logged `config → out-of-sample result` table — are the difference between "engineered" and "vibe-coded." The concern didn't vanish because the model got simpler.
- **Explicit purge/embargo mechanics + overlap-aware inference.** Plan 4 keeps the sealed final exam (5.7) and the effective-N concept (2.7) but dropped the mechanics: a gap of ≥ H between exploration and confirmation data, and Newey-West / non-overlapping / block-bootstrap corrections for the layer-two statistics on overlapping H-period labels.
- **Corporate-action adjustment.** Plan 4 says price/volume "has no look-ahead problem" and stops. Splits and dividends still exist and matter *more* here: the indicator depends on absolute historical levels ("has the previous leg's origin been broken?"), and adjusted vs. unadjusted series can flip that answer.
- **Staleness / forward-fill awareness.** Fundamentals are quarterly; forward-filled to daily they're constant ~98% of the time, distorting both the financial-state clustering and any distance metric. Breakdown's constancy profiling and days-since-update idea apply directly.
- **Neighbor-pool admissibility rule (conditional).** If the optional Stage-E retrieval is built, Breakdown's rule must come with it: a historical point may be shown as an analogue for query `t` only if its entire label period ended before `t` (i.e., dated ≥ H before `t`). This leak survives every other guardrail.
- **Gated build order.** Breakdown's gate structure (data → clusters → indicator states → two-layer stats → baselines → guardrails → writeup, each with a "done-when" bar) is what actually protects a summer timeline.

**Not a regression:** Breakdown said "enter regime features as raw magnitudes, not binarized"; Plan 4 discretizes regimes into clusters. These serve different purposes — Breakdown's warning was about distance metrics for *retrieval*; Plan 4's clusters are *conditioning axes* for interaction analysis, where discreteness is the point and the stability bootstrap guards the boundaries. Deliberate design change, but worth being able to articulate since it superficially contradicts the older doc.

---

## 5. Outstanding issues in Plan 4

None fatal, but two are technical errors as written, two are structural tensions, one is a practical/timeline risk.

### 5.1 Stage C is mis-specified

Section 4 says layer one estimates the effect of a `regime × financial-state × structure` combination *within each single day*. But the regime is constant within a day (Plan 4 says so in §2.2, "shared market-wide"), so a within-day cross-sectional regression **cannot** estimate a regime effect — it's absorbed into the day's intercept. The regime only becomes estimable in *layer two*, by grouping the daily coefficients by regime. Almost certainly the intent, but the current wording describes an impossible regression. **Rewrite:** layer one estimates financial-state × structure effects each day; layer two tests whether those effects shift with the regime.

### 5.2 Layer-two inference needs an overlap correction

The label is a forward H-period return sampled daily, so consecutive daily estimates share ~all of their label window and are massively autocorrelated. Naive Fama-MacBeth standard errors overstate significance by a large factor. Use Newey-West errors with ~H lags, or non-overlapping sampling, or a block bootstrap over the coefficient series. Breakdown had this instinct; Plan 4 kept the *concept* (2.7) but dropped it from the *procedure*.

### 5.3 The three-way cross collides with Plan 4's own sample threshold

4–6 regimes × ~4 financial states × ~3–4 structure states = 50–100 cells. §2.7 says a regime offers maybe 4–5 independent episodes; §5.4 forbids conclusions below a minimum episode count. Together, most B2 cells will be stamped "insufficient data" by the project's own guardrail — meaning the full three-way object may be mostly unanswerable. Better to know this before the summer, not in week nine. Fixes: make the *two-way* interactions the primary results and treat the three-way cross as exploratory; pre-register a *small* set of specific three-way hypotheses (five, not five hundred) so the multiple-testing correction doesn't annihilate everything; or use partial pooling (hierarchical shrinkage toward the two-way margins).

### 5.4 The sealed final exam can't examine most of the syllabus

§5.7 reserves one contiguous, never-touched stretch — which contains only the regimes that happened to occur during it. So the confirmation step, the project's only hard boundary against overfitting, is structurally unable to confirm regime-conditional claims about regimes absent from the holdout (direct collision with §2.7). No clean escape, but honest handlings: state up front which regimes the holdout can/cannot adjudicate; use two or three separated holdout blocks from different eras; for untestable regimes, fall back to era-sliced consistency (the Drift B machinery), explicitly labeled as weaker. *(The expanding-window scheme in §7.1 is the fuller fix.)*

### 5.5 The indicator's provenance isn't protected by the exploration/confirmation split

§8 flags hindsight risk in the indicator's "rides the move start to finish" claim, but the deeper issue is that the indicator's *rules* were developed by looking at charts over years — including years that will land inside the sealed holdout. The 5.5/5.7 machinery only protects against patterns *selected during this project's exploration phase*; it does nothing about parameters tuned informally beforehand. The holdout is pristine only relative to things chosen after it was sealed. Mitigation is procedural — see §8.

### 5.6 The label-fix box is a no-op (see §3 above)

Carried here because it is an error *inside* Plan 4, not just a comparison point.

### 5.7 Quieter issues

- **Cluster-stability bootstrap (5.3) must be a *block* bootstrap over time.** Market observations are heavily autocorrelated; resampling days i.i.d. produces near-identical resamples and certifies almost any clustering as "stable." Resample multi-month blocks or whole episodes.
- **The financial-state clustering will partly rediscover sectors,** because raw fundamental ratios aren't comparable across industries (a bank's leverage ≠ an industrial's). "High-leverage cyclicals underperform in regime X" may be "financials underperform in regime X" in disguise. Use sector-relative fundamentals or state the confound. Membership also jumps discretely on announcement dates and is stale between them (same forward-fill staleness issue).
- **Corporate-action adjustment is absent from §3** and matters unusually much: the indicator's core predicate is whether price broke a specific historical level, and a split or large dividend can flip that answer.
- **No purge gap between exploration and confirmation.** Labels look H periods forward, so the last H of exploration overlaps the holdout's returns. Breakdown's embargo applies verbatim.
- **The confirmation protocol is under-specified.** §5.6 says report the number of tests; a real confirmation also needs the count *and threshold* fixed in advance (how many hypotheses graduate, what effect size / t-statistic counts as confirmed, which correction applies). Otherwise the final exam degrades into a second exploration.
- **Presentational trap:** the secondary metric (quantile-portfolio monotonicity) is implicitly a portfolio, inviting turnover/cost questions despite the no-tradability stance. Present quantile *returns* purely as an effect-size display with that caveat, or have the one-sentence answer ready.

### 5.8 The biggest practical risk — data sourcing

The single most expensive item is stated as a bullet: announcement-dated, as-originally-reported fundamentals for a universe *including delisted names*. Free/cheap data gives restated figures for today's survivors; the clean version lives in CRSP / Compustat-tier subscriptions. **Resolve the data question in week one, before writing any statistics code** — every guardrail in §5 is downstream of it.

---

## 6. Net assessment

Plan 4 is the better project — sharper question, honest metrics, real differentiator. It should:
1. Reabsorb Breakdown's mechanical hygiene (leakage test, embargo/overlap corrections, corporate actions, staleness profiling).
2. Fix the §3 label box (diagnosis right, remedy inert under a rank label).
3. Repair the two mis-specified procedures (Stage C's regression, 5.3's bootstrap).
4. Right-size its guarantees to the effective sample (two-way primary, three-way exploratory; regime-aware holdout).
5. Lock down the fundamentals data source first.

---

## 7. Method deep-dives

### 7.1 Expanding-window (walk-forward) validation

Scheme:

```
Train 2000–2008 → Test 2009
Train 2000–2009 → Test 2010
Train 2000–2010 → Test 2011
...
```

This is essentially Breakdown's walk-forward validation and is the right fix for the "sealed exam can't see most regimes" problem: every year from 2009 on becomes an out-of-sample test year, so every regime episode after the initial block gets tested on data the classifications never saw. Coverage problem largely solved — under four conditions:

1. **Preserve "touched once."** If you run it, look at results, tweak clusters/thresholds, and rerun, every test year silently became development data. Either pre-register the whole procedure and run once at the end, or split the folds: iterate freely on early folds (e.g. 2009–2018 = validation) and seal later folds (2019+ = true final exam). The hybrid is the practical choice.
2. **Embargo at every boundary.** The label looks ~3 months forward, so "train through Dec 2008" includes labels realized inside test-2009. Purge the last H from each training window (train through September to test January onward).
3. **Fix the cluster rule up front.** If regimes are refit each fold, "regime 3" in 2009 isn't automatically "regime 3" in 2015, and cross-fold aggregation becomes meaningless. Either freeze regime definitions after the first training window and apply forward, or refit each fold and match clusters by centroid similarity. Freezing is cleaner and matches §5.5.
4. **The physical ceiling stays.** Walk-forward stops you *wasting* episodes but creates none. If "panic" occurred three times after 2009, you have three out-of-sample panic episodes — aggregate across folds by *episode*, not by year or day. Early folds will be noisy (test-2009 rests on ~9 years containing maybe 1.5 recessions).

### 7.2 The bootstrap

**Problem it solves:** you have one run of history and computed some number from it (a cluster partition, an average effect). You want to know: if history had gone slightly differently, would you get roughly the same answer? You can't rerun history, so the bootstrap fakes it — build many pseudo-histories by resampling your own data *with replacement* (draw N from your N; some picked twice, some not at all), recompute the number on each, and look at the spread. Small spread → the result is a property of the data. Large spread → you measured noise. The spread also directly yields a confidence interval.

**Two uses in Plan 4:**
- *Cluster stability (5.3):* re-cluster each pseudo-history and check whether the same groups keep re-forming. If yes, the regimes are real; if every resample partitions differently, the original clusters were an arbitrary slice.
- *Confidence intervals:* resample, recompute the average effect, report the spread instead of a bare point estimate.

**Why it must be a *block* bootstrap.** The plain bootstrap resamples observations independently, assuming independence. Market days aren't independent: today ≈ yesterday, everyone shares the regime, and forward labels overlap by ~62 of 63 days. If you resample *days* independently, every pseudo-history contains an almost identical mix of the same few episodes — you're shuffling near-duplicates, so the statistic barely varies and the bootstrap cheerfully certifies everything as "stable" and "significant." (This is the restaurant-review problem from §2.7: 1,000 reviews from 3 visits are 3 pieces of evidence, not 1,000.) **Fix:** draw contiguous *blocks* of time — multi-month chunks or whole regime episodes — with replacement. Now some pseudo-histories omit the 2008 crash and others contain it twice, and that variety is the honest answer to "what if history had gone differently." Applies to both the confidence intervals and the 5.3 cluster-stability check.

### 7.3 Drift

Drift = "the pattern isn't the same across eras." §5.8's point: this happens for two different reasons requiring opposite responses.

**Drift A — coordinates moved, not the economy.** Rates were 6% in the 1990s, ~0% in the 2010s. Regime features on *absolute levels* put "tightening in 1994" and "tightening in 2017" in different clusters purely because the baseline shifted — a measurement artifact. **Fixable:** measure everything *relative* to its own recent history (z-score vs a trailing window, use changes not levels, use spreads and curve slopes not raw rates). Both tightenings then look alike, cluster together, and pool as evidence. Principle: pick features insensitive to what permanently changed but sensitive to what recurs.

**Drift B — the economy actually changed.** Same features, same regimes, but the *relationship* flipped: "value outperforms in risk-off" held in the 1990s and reversed after 2008. Nothing was mismeasured — the world moved. **Not fixable, only reportable:** slice results by era (90s / 2000s / 2010s+) and state where the pattern held and where it broke. "Held until 2008, then broke" is itself a finding.

**Telling them apart:** switch to relative features first. If old and new eras now cluster into the same regimes but the effect *within* those regimes still differs by era, that residual difference is Drift B.

### 7.4 The two-layer Fama-MacBeth regression

**Layer 1 — one day at a time.** On day `t`, ~200 stocks each carry a financial state, a structure state, and a label (that day's forward-return rank). Ask: *within this day*, did stocks with "healthy financials + intact structure" rank higher than the rest? Formally, regress the rank on dummies for the financial×structure cells; practically, mean label per cell minus the day's grand mean is the same idea. Output: a small set of numbers for day `t` (e.g. "intact-structure premium was +0.04 ranks"). One estimate per day. Comparing *within* the day is the whole trick — everything shared market-wide that day (market direction, sentiment, the regime itself) cancels because every stock experienced it equally.

That is exactly why the regime cannot enter Layer 1 (it's constant within the day; see §5.1).

**Layer 2 — the time series of daily estimates β(t).** Two questions:
- *Stability:* is the average positive, and *consistently* positive rather than driven by one lucky stretch?
- *The research question:* group the days by regime and compare the average β across groups. "Intact-structure premium averaged +0.06 on panic days and −0.01 on calm days" — that cross-regime difference *is* the conditional structure. The regime is never a stock feature; it's the grouping variable for the daily estimates.

**The trap (see §5.2):** the daily estimates aren't independent — with a 3-month horizon, β(Monday) and β(Tuesday) share ~62 of 63 label days, nearly the same measurement twice. Naive SE with N = number of days overstates significance badly. Fixes: Newey-West SE with ~H lags, sample every H days, or block-bootstrap the β series. Effective N ≈ calendar span ÷ horizon — the same number from §2.7 reappearing in the machinery.

*(Structural summary: each day's cross-section → one effect estimate → the estimates form a time series → group by regime → compare average effect across regimes → a difference means conditional structure exists.)*

### 7.5 The personal indicator — how to "solve" the contamination

The instinct ("stick to one version, no changing numbers, run it over the entire history, and if you slightly change the numbers the result should stay roughly the same") is correct, with three refinements:

1. **Freeze in writing, before touching project data.** A spec defining exactly what a leg is, its origin, the numerical threshold for "broken," and the bar frequency — every rule mechanical enough that *code, not your eye*, makes the call. Any rule needing judgment ("looks like accumulation") can't be frozen and can't be tested.
2. **Run that one frozen version across the entire history and universe with zero per-stock discretion, and don't touch the rules after seeing results.** A genuine mid-project improvement is allowed, but results using it revert to *exploration*, not confirmation.
3. **Perturbation check.** Vary the arbitrary constants (break threshold 0% / 1% / 2%, alternate leg definitions) and confirm the *conclusions* stay qualitatively the same — same sign, same regimes, roughly similar magnitude — not that the numbers are identical. A pattern that exists only at one magic setting is almost certainly curve-fit; one that survives perturbation is hard to dismiss.

**Residual caveat:** this handles the *tuning* problem but can't fully erase the deeper contamination — you developed the rule over years of charts, some overlapping the test data, and you can't un-see them. Two mitigations: **breadth** (the most convincing evidence comes from stocks/markets you never personally charted — if the rule works on hundreds of unseen names, hindsight can't explain it) and **naming the residual limitation in §8** (which Plan 4 already half-does). Freeze + full-history + perturbation + breadth is about as close to "solved" as this problem gets.
