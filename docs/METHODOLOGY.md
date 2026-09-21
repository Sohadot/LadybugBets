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

## Overround / book percentage / implied margin measure

For a market with mutually exclusive and collectively exhaustive outcomes with
prices implying probabilities `p_1, p_2, ..., p_n`, the **overround** (also
called the **book percentage** or an **implied margin measure**) is:

```
overround = (p_1 + p_2 + ... + p_n) - 1
```

The sum `p_1 + ... + p_n` is the "book sum" or "book percentage".

### What overround is — and is not

The overround is the market's calculated overround **under the observed quoted
prices**. It is a property of the prices as observed, not a measurement of the
bookmaker's business results.

It is **not**, by itself, a measurement of the bookmaker's realized profit,
hold, revenue, or actual margin. A bookmaker's realized margin depends on
customer behavior, staking distribution across outcomes, limits, and risk
management — none of which the quoted prices reveal. Two markets with the same
overround can produce very different realized outcomes for the operator.
Treat overround as an **implied margin measure derived from prices**, not as
proof of realized profitability.

### Why raw implied probabilities may sum above 100%

For a real bookmaker's market, the raw implied probabilities typically sum to
**more than 1** (100%). This excess is the overround — the implied margin built
into the quoted prices. It is not an error; it is structural. A "fair" set of
prices with no implied margin would sum to exactly 1.

### Why removing the implied margin requires an explicit normalization method

Because the raw probabilities sum above 1, converting them into probabilities
that sum to 1 requires **removing** the implied margin — and there is more than
one way to do this (e.g. proportional normalization by dividing each by the book
sum, or other margin-allocation methods). Different methods produce different
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
