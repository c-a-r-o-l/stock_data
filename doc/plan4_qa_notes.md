# Plan 4 — Q&A Notes
*Distilled from a working conversation on the "Conditional Structure in Stock Returns" project (Plan 4), with reference to the older "breakdown" document.*

---

## 1. What the project is trying to prove

**The claim:** the relationship between a stock's characteristics and its future returns is not fixed — it changes depending on the market environment — and that change is real, measurable, and stable enough to be trusted out of sample. That is what "conditional structure" means. Not "I can predict returns," but "the *rules* governing returns shift with regime, and I can show when and by how much."

**The concrete question:** for every stock on every day, record three condition variables and one outcome, then ask whether the return associated with a given (financial state × price structure) combination flips or shifts when the market regime changes. If every cell behaves the same in every regime, the regime axis carries no information and the hypothesis is dead. If cells genuinely flip (e.g., high-leverage cyclicals with intact structure outperform in "calm growth" but get crushed in "panic"), conditional structure exists and has been quantified.

**What a positive finding looks like:** *"High-leverage cyclicals with intact structure earn top-quartile cross-sectional ranks in expansion regimes but bottom-quartile in risk-off regimes; the effect held in the 2000s and 2010s slices, survived multiple-testing correction, and confirmed on the held-out period. Structure states added incremental conditioning power over regime alone (B2 > B1)."*

**Failure is also a finding:** *"Once effective sample size and multiple testing were accounted for, no conditional pattern survived confirmation; the apparent regime-dependence in exploration was noise."* That is a defensible research result — whereas for a "prediction machine" project, a null result is just a machine that doesn't work. This asymmetry is the design's real cleverness.

---

## 2. The dataset: one big table, one row per (stock, day)

The raw stock data doesn't disappear — it gets **condensed into the columns** of this table. Example row:

> (AAPL, 2018-03-15) → regime = #2 "calm growth" · financial cluster = #1 "profitable compounder" · structure = intact, leg 3, +12% above leg origin · **label** = 0.83

Where each column comes from:

| Column | Source | Method | Varies by |
|---|---|---|---|
| Regime (4–6 "seasons") | Market-level data: index returns, volatility, VIX, rate/credit spreads | Clustering | Day only — same for every stock on a given day |
| Financial state ("body type") | Fundamentals as of latest *announcement*: margins, leverage, growth, quality | Clustering | Stock and day |
| Structure state | Raw price/volume series | **The personal indicator** (hand-encoded) | Stock and day |
| Label | Future prices | Return over next ~3 months → percentile rank vs. all stocks in the universe that day (0.83 = beat 83% of peers) | Stock and day |

**Key architectural fact (a common confusion):** the price data is **not clustered**. Only market data and fundamentals get clustered. The price series is encoded by the personal indicator into readable states (intact/broken, which leg, distance from leg origin) — the indicator *is* the third axis, not something separate from "stock stuff." There is no fourth ingredient.

**Why the asymmetry** (cluster two axes, hand-encode the third): clustering is what you do when you *don't* have a theory and want the data to sort itself into groups (no strong prior on what the market's "seasons" are). For price structure you *do* have a theory — the indicator — so you impose the structure already worked out rather than letting an algorithm grope for it. This is also why the structure axis is the interpretable, novel part: it carries a specific hypothesis rather than a generic algorithm's grouping.

**Pipeline:**

```
price series → personal indicator → structure state ┐
market data  → clustering         → regime state    ├─→ (stock, day) table → Fama-MacBeth
fundamentals → clustering         → financial state ┘
```

**Why not feed raw price series in directly:** raw paths aren't comparable across stocks and eras, and learning a representation from them is the path Plan 4 deliberately killed — effective sample size can't support it. Everything enters pre-digested into a small number of nameable states.

**"Relative to the market" means the other stocks, not an ETF.** With a cross-sectional rank label, "the market" is literally the rest of the universe that day. In a raging bull market every raw return might be +20%, but ranks still separate winners from losers. Raw return contains beta (the part that's just "the market went up"); a model trained on raw returns can win by secretly betting on market direction. Ranks strip that out. (Some people instead mean "return minus the index" — subtracting SPY. Same intent, different implementation; rank is the more robust version and is what Plan 4 uses.)

**Horizon is ~3 months, single horizon** (others as optional extension). A practical reason to prefer it over 6–12 months: ten years of history contains ~40 non-overlapping 3-month windows but only ~10 annual ones — a shorter horizon means more independent evidence, which is the project's scarcest resource.

---

## 3. The statistical machinery

### Is this supervised learning?

In structure, yes: features (the three condition columns) and a label (forward rank), estimating the relationship between them. But there is **no model training in the ML sense** — no encoder, no neural network, no XGBoost in the core. The "model" is regressions and group averages.

### Fama-MacBeth (the measurement)

Not an architecture — a two-step statistical procedure from a 1973 paper, the workhorse of academic asset pricing.

- **Layer one — one estimate per day.** Take a single day; across all ~200 stocks that day, measure the effect of interest (e.g., "among profitable compounders in regime #2, stocks with intact structure ranked on average +7 percentile points higher over the next 3 months than those with broken structure"). One number, one day. Repeat for every day → a *time series* of daily effect estimates (+7, +3, −1, +5, …). Working within each day automatically respects the cross-sectional nature of the label.
- **Layer two — statistics on that time series.** What's the mean effect? Is it distinguishable from zero given how few *independent* periods really exist (overlapping 3-month windows → ~40 per decade, not ~2,500 days)? Is it *consistent* — did it hold in the 2000s and the 2010s, or did one lucky stretch produce the whole average? Layer two is where "stable enough to trust" stops being a vibe and becomes a number.

**Why not one giant pooled regression:** on any given day all stocks move together — 2020-03-16 gives 200 rows but roughly *one* piece of evidence about crash days. Estimating day-by-day and then averaging across days respects that a **day, not a row, is the true unit of evidence**. Fama-MacBeth is far more robust than throwing all data into one big regression.

### B0 / B1 / B2 (the attribution)

**These are not betas/coefficients** — the letter is a naming collision. In a regression, betas are coefficients inside one model. B0/B1/B2 are **three separate runs of the entire Fama-MacBeth procedure** ("B" = baseline), like three experimental conditions in a lab (control, one-variable, full treatment):

- **B0** — no conditions: the unconditional characteristic→return picture.
- **B1** — split by regime only: does the picture change with the market season?
- **B2** — regime × financial state × structure: the full nested conditioning.

Each run internally produces its own estimates. Findings are stated as **increments**: B1 over B0 tells you whether the regime axis matters at all; B2 over B1 tells you whether financial state and *the indicator* carry information beyond regime. Without this, "my conditional model shows X" is unfalsifiable hand-waving.

**The indicator's specific test lives here:** the structure axis in B2 is entirely the personal indicator, so "does B2 beat B1" is largely "does the indicator carry information about future returns beyond what regime and fundamentals already tell you — and does that information flip across regimes?" If B2 ≈ B1, the indicator failed. That possibility is what makes it a real hypothesis rather than a belief.

---

## 4. Is the project unique / obvious / done before?

**The skeleton is not novel, and an interviewer will recognize it immediately:**

- Conditional factor models go back to Ferson–Harvey (early 1990s); regime-switching return models to Hamilton (1989).
- "Value works in some environments and not others" has a whole practitioner literature (AQR, Man Group, etc. publish regime-conditioned factor performance regularly).
- Clustering macro data into 4–6 regimes and studying factor behavior within each has been publicly blogged by several funds.
- Fama-MacBeth is the workhorse of half of empirical asset pricing.

**Why that's fine, and arguably good:**

1. Nobody expects a student summer project to discover new alpha; they expect **craft**, and a well-trodden framework means the methodology can be judged against a known standard.
2. The hypothesis being obvious doesn't make the *answer* obvious — the interesting outputs are magnitude, stability across eras, and what survives multiple-testing correction. Plenty of "obvious" conditional effects don't survive.
3. Plan 4 contains one genuinely idiosyncratic element: the path-dependent structure indicator. Nobody has tested *that* as a state variable inside this framework, and the plan correctly treats it as a hypothesis to falsify rather than a premise.

**One-line positioning:** the framework is standard; the indicator and the rigor discipline are yours. Don't sell novelty — both documents already say the selling point is rigor, and that's correct.

**Resolving "this is so obvious":** the *hypothesis* ("relationships depend on regime") is obvious; the *answer* is not. Which specific combinations flip? By how many percentile points? Did the flip survive 2008? How many apparent patterns die after multiple-testing correction? (Empirically, in studies like this: most.) Nobody can answer those off the top of their head. "Exercise is good for you" is obvious; a dose-response study with confidence intervals is science. The deliverable — the quantified, correction-surviving, out-of-sample-confirmed map of which conditional effects are real — is exactly the non-obvious part.

**Interview answer to "isn't this just conditional factor models?":** "Yes, deliberately, plus one novel state variable and an unusually honest treatment of effective sample size" — delivered without flinching. What distinguishes the project isn't the question; it's whether every choice can be defended under hostile questioning.

---

## 5. Why discretize instead of using a continuous model?

**First, disambiguate:** this is a *different* discretization question than the one in the old breakdown. There, "discretize" meant tokenizing factors to feed a sequence model, and the verdict was rightly "don't." In Plan 4, discretization (regime clusters, financial-state clusters, structure states) serves a different purpose.

**The core justification is the effective-N constraint (§2.7):** the research object is an *interaction* — "does the effect of X flip across regimes?" To make that claim, a regime must be a nameable, countable thing you can condition on, count independent episodes of, and compare across. With maybe 4–6 truly independent regime episodes in the sample, a continuous interaction surface (a coefficient on VIX × leverage × structure-distance, or a boosted tree learning interactions) has essentially nothing to pin it down — you'd be fitting a smooth function to a handful of independent observations. **Coarse discrete buckets are deliberate variance reduction sized to the data** — the plan's "controlled fuzziness," which is the honest name for it.

**Two rigor properties that are hard to get continuously:**

- A **countable number of hypotheses**: "we tested 40 cells, here's the correction" — a continuous model implicitly tests infinitely many.
- A **well-defined stability check**: bootstrap the clustering and see whether the partition survives (§5.3); there's no equally clean analogue for a fitted surface.

**But continuous isn't impossible — use it as a robustness check.** Fama-MacBeth with continuous interaction terms is completely standard. If "leverage hurts in risk-off regimes" shows up in the discrete cells but the continuous interaction coefficient is zero, that's a warning the result lives at an arbitrary bin boundary.

**Honest costs of discretizing:** boundaries are arbitrary, observations near an edge flip clusters, and results can be sensitive to the chosen number of clusters — exactly why §5.3 exists.

**The defensible answer:** "discrete as the primary design because effective N demands it and interpretability is the deliverable; continuous interactions as a secondary check" — not "continuous is impossible."

---

## 6. Does reducing features fix the sample-size problem? (No — and the plan doesn't claim it does)

Two different problems that both sound like "not enough data":

- **Problem 1 — too many features relative to rows** (curse of dimensionality, from the old breakdown). 500 columns on 500 rows lets a model fit noise perfectly; each feature is another knob to overfit with. Fewer features helps *this*.
- **Problem 2 — too few independent observations** (effective N, the Plan 4 problem). If a recession has happened 4 times in history, you have 4 pieces of evidence about recessions no matter how many rows or columns exist. Reducing features does **not** manufacture more recessions.

**What coarse bucketing actually does for Problem 2:** it doesn't add evidence — it stops you from *spending* the evidence too thinly. With 4 recession episodes, 3 financial buckets × 2 structure states leaves "recession × high-leverage × broken-structure" as one cell with a handful of stock-days to average. With 20 financial buckets × 10 structure states, that same cell has almost nothing — the scarce evidence is divided into hundreds of tiny cells, most empty or containing one lucky observation.

**The honest statement:** coarseness doesn't cure the sample-size ceiling, it **rations** against it. The ceiling is fixed by history; bucketing decides whether the evidence funds a few well-populated claims or fragments into noise. §2.7 and §5.4 say exactly this — the ceiling is a "physical" limit that cannot be conjured away.

---

## 7. The cell-count collision: the headline object may be mostly unanswerable

**The arithmetic:** 4–6 regimes × ~4 financial states × ~3–4 structure states ≈ **50–100 cells**. A rare regime (e.g., "panic": 2008, March 2020, maybe 2011, maybe late 2018) offers only ~4 genuinely independent *episodes* — not 4 days; 4 episodes, each spanning weeks/months of highly correlated days that count as roughly one piece of evidence.

**Why more stocks don't help:** the regime is shared market-wide, so every stock in a given panic shares that same episode. Independent evidence for any panic-involving cell is capped at ~4 episodes, further thinned because only a fraction of firms are in a given (financial × structure) combination during each episode — and adjacent cells draw from the *same* 4 episodes.

**The collision:** total independent evidence across the entire regime axis is maybe 20–30 episodes; spread over 50–100 cells, most cells get well under one episode's worth of clean evidence. §5.4's minimum-independent-episode threshold then stamps the majority of B2's cells **"insufficient data" — by the project's own honesty rule.** For any cell involving a rare regime, the threshold and the physical ceiling collide, and the ceiling wins.

**The uncomfortable structure of the problem:** the cells that would show the most interesting flips (the ones involving crashes) are exactly the ones with the least evidence. The interesting part is where the data is thinnest. Not an engineering bug — the structure of the problem. Two individually-correct safeguards (§2.7's ceiling and §5.4's threshold), multiplied together, constrain the project's own headline goal; the plan states both but never multiplies them.

**Design options (decide in June, not week nine):**

1. **Collapse from cells to axes.** Ask lower-dimensional questions that pool evidence: "does the fundamentals→return relationship differ between risk-on and risk-off?" (two coarse regimes, not six). Two-way beats three-way; coarse beats fine. This is what "controlled fuzziness" is really for — survival, not elegance.
2. **Reframe the deliverable so "mostly insufficient" *is* the finding.** "We attempted the full three-way map; here are the 3–4 cells with enough independent episodes to survive our threshold and correction, and the honest catalogue of the 90+ that did not." Legitimate, even impressive — it directly demonstrates understanding of effective N — but a very different-*feeling* project than "I mapped the full conditional structure," and that must be made peace with in advance.
3. **Lengthen the history** to buy more episodes (more stocks doesn't add episodes; more *years* does) — but this drags in worse survivorship-bias data and non-stationarity (Drift B). A trade, not a free win.

---

## 8. Survivorship bias in Plan 4

**Conceptually handled, practically still an issue.** §3 requires the universe to include delisted companies, but most accessible data sources (yfinance and friends) carry only currently-listed tickers, so dead companies vanish by default.

**Why it's *worse* for Plan 4 than for a generic predictor:** the bias isn't uniform — it concentrates in exactly the cells being studied. Firms delisted through bankruptcy are disproportionately the high-leverage cyclicals in risk-off regimes. Delete them and that cell's returns are inflated precisely where the conditional structure would be most interesting — the bias attacks the research object directly, not just headline numbers. The cross-sectional rank label mitigates market-level survivorship (everyone in the sample is ranked against each other) but does nothing for the within-cross-section distortion.

**Mitigations if it can't be fixed now:**

- Restrict to large caps, where bankruptcy delisting is rarer — a mitigation, not a fix.
- In the write-up, don't just *name* the limitation — **sign it**: state which cells are biased in which direction and why. "Our 'high-leverage in stress regimes' estimates are upward-biased because the casualties are missing" is a much stronger limitations section than "survivorship bias may exist."

**Data sources that fix it:** Sharadar (via Nasdaq Data Link) and Norgate carry delisted US equities at student-affordable prices; CRSP is the gold standard with academic access.

---

## 9. The personal indicator: the legitimate worry, precisely aimed

**What's wrong with the loose version of the worry ("the analysis only sees stocks through an unvalidated indicator"):**

- The indicator is **not the only lens** on stock information. Fundamentals are a whole separate axis (margins, leverage, growth) entering un-indicator'd, and the label is the actual future return — raw truth, no indicator involved. Only the price axis is mediated by the indicator.
- **A dud indicator doesn't corrupt the regime finding.** If "intact/broken/leg-3" is noise, the structure axis contributes nothing and B2's structure component simply won't beat B1 — the experiment returning "no," which is fine. Regime (axis 1) and fundamentals (axis 2) stand entirely on their own; you could delete the structure axis and still have a complete B0→B1 study of whether the fundamentals→return relationship flips across regimes. The indicator is **additive, not load-bearing**.

**Where the suspicion is genuinely correct — and sharper than "we don't know if it works":** the indicator has **researcher degrees of freedom baked in**. Someone designed it — how many legs count, how far a pullback can go before "broken," daily vs. weekly bars — and those choices were almost certainly made by looking at charts where the pattern "worked." That's hindsight fitting, and §8 flags exactly this (the "rides the move from start to finish" claim is the kind most easily distorted by reading the chart in hindsight). So the indicator isn't just unvalidated — it's *pre-loaded with a bias toward looking good*, because its parameters were tuned on the same kind of data now being used to test it. It was built to look like it works, and is now being graded on a related exam.

**It genuinely is two experiments' worth of validation burden in one project:**

1. Does regime-conditioning matter? (Clean; indicator irrelevant.)
2. Does *this specific indicator, with these hand-chosen parameters*, carry real out-of-sample information — or was it curve-fit?

Plan 4's handling (§8: treat it as a testable hypothesis, validated out-of-sample across many stocks, not a given premise; §5.7's sealed hold-out stops it grading its own homework) is the right move, but stapling an unvalidated proprietary indicator to a factor study does dilute the clean part with a messy part.

**Two defensible designs — choose on purpose:**

- **Option A — demote the indicator to an axis, keep it honest.** The regime × fundamentals study is the spine and stands alone; the indicator is one additional axis whose parameters are *frozen on the training period before forward returns are ever consulted*, with its contribution reported separately as "structure added / didn't add X beyond regime+fundamentals" — allowed to come back negative. (This is Plan 4's current intent.)
- **Option B — validate the indicator as its own clean experiment first.** Before it touches the conditional study: does "intact structure" predict higher forward cross-sectional rank, out of sample, across many stocks, with parameters fixed in advance? If it can't clear that bar unconditionally, it has no business as an axis in the harder conditional study. More work, but it *untangles* the two experiments instead of hoping the hold-out absorbs them.

**The forbidden move:** quietly re-tuning the indicator's parameters during exploration because "structure intact wasn't separating returns well, let me adjust the pullback threshold." That's the indicator eating the test set through the back door — precisely the p-hacking mechanism from the replication crisis, wearing a proprietary badge. Frozen before forward returns are consulted → fair hypothesis. Not frozen → the project is compromised and the gut feeling fully vindicated.

---

## 10. The replication crisis: why "obvious regularities failing" is real

One of the central controversies in empirical finance over the last decade, and directly relevant to why Plan 4's guardrails exist.

- Academics published hundreds of "factors" — the literature calls it the **"zoo" of over 300 documented anomalies**.
- **Hou, Xue & Zhang** replicated 447 published anomalies with consistent methods: **286 (64%) insignificant at the 5% level**; raising the bar to the stricter t-statistic of 3 recommended by Harvey–Liu–Zhu makes **380 of 447 (85%) insignificant**. The trading-frictions/liquidity category was the biggest casualty (93% insignificant).
- **Harvey, Liu & Zhu (2016)** concluded that "most claimed research findings in financial economics are likely false."
- **Diagnosed causes:** p-hacking; pressure to publish; poor use of statistics; publication bias (significant results make a bigger splash → publication, tenure, prestige); a purely empirical literature with little theoretical guidance; overwhelming financial interest. Thousands of researchers testing thousands of characteristics, everyone reporting winners, nobody correcting for how many combinations were tried across the whole field — the multiple-testing problem at the scale of a discipline. Findings often failed when the universe was altered or variable definitions changed.
- **The debate isn't settled:** Jensen et al. (2023, *Journal of Finance*) argue the crisis is overstated — replication rates of ~75–82% under a Bayesian approach, and factors discarded by frequentist corrections still earned significant out-of-sample returns. "Most factors are fake" vs. "most survive proper analysis" is genuinely contested — but every side agrees the field got burned by multiple testing, and that rigor of the kind Plan 4 encodes is what settles it.

**Connection to Plan 4:** scanning many (regime × financial × structure) cells is *structurally the same activity* that produced the zoo — searching a large space of characteristic-return relationships and keeping what looks significant. That's why §5.6 (report how many combinations were tested), §5.7 (sealed hold-out touched once), and effective-N counting aren't optional polish — they're the machinery separating "a real conditional effect" from "the finance equivalent of a coin that landed heads eight times because 500 coins were flipped." A write-up saying "we tested 40 cells, corrected, and 3 survived out-of-sample" demonstrates the single most important methodological lesson of the field's last decade.

**The right read of the "so obvious" reaction:** the fact that obvious-sounding regularities fail this often is *why* a project whose deliverable is "I tested honestly and here's what survived" has value. If they always replicated, nobody would need the rigor and the project would be trivial.

---

## 11. Runtime: what's slow and what isn't

**The project is bottlenecked by thinking and data-wrangling time, not machine time.** A feature — but it also means "it's still running" is rarely a valid excuse.

**Fast (seconds to minutes):**
- Fama-MacBeth core: a cross-sectional regression per day + averaging — small-matrix linear algebra a few thousand times. Seconds.
- Clustering (regimes, financial states): k-means-ish on modest data. Seconds to minutes.
- B0/B1/B2, conditional cell statistics, rank IC: all fast.
- The indicator across all stocks/dates: minutes if vectorized; tens of minutes if written as sloppy loops (a code-quality problem, not a compute problem).

**Slow only by multiplication — the resampling wrappers:**
- Bootstrap cluster stability (§5.3): re-cluster on perturbed data ~500–1,000×.
- Block-bootstrap confidence intervals (§5.4, §8): the estimation re-run across many resamples.
- Permutation/multiple-testing nulls (§5.6): another ×hundreds-to-thousands wrapper.

Realistically the full rigor suite is minutes to a couple of hours on a laptop, and it **parallelizes trivially** (each iteration independent). The real cost is iteration speed during development — a 40-minute loop waited on 15×/day is a drag. Vectorize, cache, subsample during development, full runs only for final numbers. (No neural-network training exists in the core, so there are no long training runs — the only component that would have needed them was deliberately cut from scope.)

**The actual time sinks (not "runs" at all):**
- **Building the point-in-time dataset** — sourcing delisted companies, aligning financials to announcement dates, first-release macro values, correct forward-filling. Days to weeks of finicky work; where the project lives or dies. By far the longest pole.
- **Implementing the indicator correctly** on daily/weekly/monthly bars, leg-tracking logic right, no look-ahead. Days.
- **The exploration/iteration loop** — looking at results, forming hypotheses, checking cells, deciding what survives. Weeks — but that's the research itself.

Budget: essentially zero for waiting on core computations; an hour or two for the full rigor suite (parallelizable to minutes); the rest of the summer for data engineering and thinking. A genuinely long-running core computation usually signals un-vectorized code, not an inherently big problem — at this data size, it isn't one.
