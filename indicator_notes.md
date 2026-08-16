# PV indicator — notes

Partner has the formula; I don't. Writing down what I know so I don't
confuse myself later.

## Columns (11 per row, one file per symbol per frequency)

- `Trend_PV` — signed leg counter. Positive = bull, negative = bear.
  Magnitude = leg number within the current trend.
- Bull side (zero during bear trends): `PV_BULL_STEP`, `PV_BULL_START`,
  `PV_BULL_STOP`, `PV_BULL_CNT`, `PV_BULL_H`
- Bear side (zero during bull trends): `PV_BEAR_STEP`, `PV_BEAR_START`,
  `PV_BEAR_STOP`, `PV_BEAR_CNT`, `PV_BEAR_L`

Best guess at semantics from staring at the values:
- `START` = trend origin price (fixed within a trend)
- `STOP` = trailing invalidation level
- `H` / `L` = trend extreme so far
- `CNT` = bar count in trend, `STEP` = bar count in leg

Three frequencies exist: daily, weekly, monthly.

## What I don't know

- The actual formula
- Which frequency to use (haven't picked)
- Whether the state at bar t uses bars after t (repaint)
- How to encode into a small number of states for the study

## Rule for myself

**Don't join any PV column to forward returns until the frequency is
picked with partner.** Once I've looked at how PV relates to returns at
one frequency, I can't honestly pick a different one later.

B0–B2 spine work doesn't touch PV at all, so it proceeds normally.
