# METHODOLOGY

*Mathematical and interpretive discipline.*

This document establishes the standard conversions and the interpretive limits
that apply to them. It uses only established, non-proprietary mathematics. **No
"edge score" or numerical scoring system is ratified in Sprint 0**; introducing
one requires a later governance decision.

## Odds → implied probability

### Decimal odds

For decimal odds `d`:

```
implied_probability = 1 / d
```

Example: `d = 2.50` → `1 / 2.50 = 0.40` (40%).

### American odds

For positive American odds `A` (e.g. `+150`):

```
implied_probability = 100 / (A + 100)
```

For negative American odds `A` (e.g. `-200`), using `|A|` for the absolute
value:

```
implied_probability = |A| / (|A| + 100)
```

Example: `A = +150` → `100 / 250 = 0.40` (40%).
Example: `A = -200` → `200 / 300 ≈ 0.667` (66.7%).

### Fractional odds

For fractional odds `a/b` (e.g. `3/2`):

```
implied_probability = b / (a + b)
```

Example: `3/2` → `2 / (3 + 2) = 0.40` (40%).

## Break-even probability

The break-even probability of a price is the implied probability computed above:
it is the probability at which the expected value of a stake at that price is
zero, before any margin considerations. For decimal odds `d`, break-even
probability is `1 / d`. A wager is only expected-value-positive if the true
probability exceeds the break-even probability — and the true probability is not
observable from price alone.

## Overround / bookmaker margin

For a market with mutually exclusive and collectively exhaustive outcomes with
prices implying probabilities `p_1, p_2, ..., p_n`, the **overround** (also
called the margin or "vig") is:

```
overround = (p_1 + p_2 + ... + p_n) - 1
```

The sum `p_1 + ... + p_n` is often called the "book sum" or "book percentage".

### Why raw implied probabilities may sum above 100%

For a real bookmaker's market, the raw implied probabilities typically sum to
**more than 1** (100%). This excess is the overround — the margin built into the
prices. It is not an error; it is structural. A "fair" set of prices with no
margin would sum to exactly 1.

### Why removing margin requires an explicit normalization method

Because the raw probabilities sum above 1, converting them into probabilities
that sum to 1 requires **removing** the margin — and there is more than one way
to do this (e.g. proportional/normalization by dividing each by the book sum,
or other margin-allocation methods). Different methods produce different
"de-margined" probabilities. Therefore:

- A normalized probability is only meaningful when the **method is named**.
- LadybugBets must never present a de-margined probability without disclosing
  the normalization method used.

## Interpretive limits

These constraints are as important as the formulas.

### Price disagreement is not automatically arbitrage

Different sources implying different probabilities for the same outcome is
common. It does not, by itself, constitute an arbitrage opportunity. Real
execution involves availability, limits, timing, fees, and margin, none of which
a displayed price captures. Disagreement is an observation to inspect, not a
guaranteed opportunity.

### Historical movement does not predict future outcomes

That a price moved in some direction over time is a record of what happened. It
does not, on its own, predict the event's outcome or the price's future
direction. Movement is descriptive, not predictive.

### A model output must not be presented as certainty

Any computed value — implied probability, normalized probability, movement,
consensus summary — is a derivation under stated assumptions, not a fact about
the future. Outputs must be presented with their uncertainty and never as
guarantees.

## Explicitly deferred

- No proprietary algorithms are introduced.
- No "edge score" or numerical scoring system is ratified. Any such system
  requires a later, explicit governance decision before it may be designed or
  implemented.
