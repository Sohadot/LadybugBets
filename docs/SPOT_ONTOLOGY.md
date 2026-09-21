# SPOT ONTOLOGY v0.1

*The canonical definition of the Spot classes.*

A **Spot** is an observed, governed, explainable market condition that deserves
examination. It is evidence or a derived observation — not a recommendation, a
prediction, a profitable opportunity, or advice to wager.

## Universal rules (apply to every Spot class)

- A Spot must be **traceable** to its source observations and its derivation.
  No opaque Spot generation.
- A Spot must distinguish **source facts** from **derived calculations** (see
  [DATA_MODEL.md](DATA_MODEL.md)).
- A Spot must state the uncertainty and limitations relevant to its
  interpretation.
- Spot class names may evolve through governance; the meanings defined here are
  the Sprint 0 baseline that future code may implement.

---

## 1. Price Spot

- **Canonical name:** Price Spot
- **Purpose:** Record an observed price for a defined outcome, at a defined
  source, at a defined time.
- **Required inputs:** event, market, outcome, source, price, price format,
  observation timestamp.
- **Derived outputs:** none required (a Price Spot is fundamentally a source
  observation); an implied probability may be attached as an explicitly derived
  field.
- **What it means:** "This source displayed this price for this outcome at this
  moment."
- **What it does NOT mean:** that the price is correct, fair, available now, or
  advantageous.
- **Minimum provenance:** source, timestamp, event, market, outcome.
- **Can it exist without historical data?** Yes. A single observation is
  sufficient.

---

## 2. Movement Spot

- **Canonical name:** Movement Spot
- **Purpose:** Represent a governed change between comparable price observations
  over time.
- **Required inputs:** two or more comparable Price Spots with distinct
  timestamps. Comparability requires the same event, market, and outcome **and**
  the same quoted bookmaker/operator basis — i.e. the observations must be
  attributed to the same operator identity. Unless a later governed methodology
  intentionally defines cross-operator movement, movement is defined within a
  single operator's quoted prices.
- **Derived outputs:** movement amount and/or direction between the observations
  (a derived calculation).
- **What it means:** "For this operator's quoted price, between these observed
  timestamps, the price for this outcome changed by this amount."
- **What it does NOT mean:** that the movement will continue, reverse, or
  predict the outcome. A change in Bookmaker X's price and a difference between
  Bookmaker X and Bookmaker Y are **not** the same analytical object; the latter
  is a cross-operator comparison, not a Movement Spot.
- **Minimum provenance:** provenance of every underlying Price Spot (including
  provider and quoted operator identity), plus the comparison basis used.
- **Can it exist without historical data?** No. It requires at least two
  observations over time.
- **Governance note:** Cross-operator (cross-book) movement is **not** defined in
  Sprint 0. Defining it requires a later governed methodology.

---

## 3. Probability Spot

- **Canonical name:** Probability Spot
- **Purpose:** Express a probability-related interpretation derived from a
  governed market price or defined calculation.
- **Required inputs:** a governed price (or set of prices) and an explicit
  conversion/normalization method (see [METHODOLOGY.md](METHODOLOGY.md)).
- **Derived outputs:** implied probability, and where applicable a normalized
  probability with the normalization method named.
- **What it means:** "Under this stated method, this price implies this
  probability."
- **What it does NOT mean:** the true probability of the outcome, or a
  probability free of the prices' implied margin (overround) unless a
  normalization method is explicitly applied and disclosed.
- **Minimum provenance:** the underlying price's provenance plus the exact
  method used.
- **Can it exist without historical data?** Yes. It can derive from a single
  current price.

---

## 4. Consensus Spot

- **Canonical name:** Consensus Spot
- **Purpose:** Provide a cross-operator representation of comparable market
  observations for the same outcome.
- **Consensus population (MVP semantics):** Consensus is defined over multiple
  comparable quotations attributed to **distinct governed bookmaker/operator
  identities**, unless a future methodology explicitly defines another consensus
  population. Upstream **provider** diversity is not the consensus population and
  must not be equated with operator diversity (see the distinction below).
- **Required inputs:** two or more comparable observations for the same event,
  market, and outcome, attributed to **distinct bookmaker/operator identities**,
  each with full provenance (provider and operator).
- **Derived outputs:** a cross-operator representation (e.g. range, spread across
  operators, or an explicitly defined aggregate) — always labeled as derived.
- **What it means:** "Across these named operators, the observed prices for this
  outcome looked like this."
- **What it does NOT mean:** market truth. A simple arithmetic average is **not**
  "market truth"; it is one derived summary among several possible ones and must
  be presented as such.
- **Minimum provenance:** provenance of every contributing observation —
  including both provider and quoted operator identity — and the aggregation
  method used.
- **Can it exist without historical data?** Yes, if multiple operators are
  observed at (approximately) the same time; it does not require history, but it
  does require multiple distinct operators.

**Provider diversity ≠ bookmaker diversity.** Upstream data providers and quoted
bookmakers are different dimensions (see [DATA_MODEL.md](DATA_MODEL.md)):

- Provider A → Bookmaker X and Provider A → Bookmaker Y are **two distinct
  bookmaker observations**, even though both arrived through a single provider.
- Provider A → Bookmaker X and Provider B → Bookmaker X must **not** be treated
  as two independent bookmaker opinions merely because two feeds delivered the
  same bookmaker's quotation.

Any deduplication, conflict-resolution, freshness, or provider-precedence rule
(for the second case above and others) is **deferred to Sprint 1 governance**.
No independence-scoring system is defined or implied here.

---

## 5. Closing Spot

- **Canonical name:** Closing Spot
- **Purpose:** Provide a comparison involving a governed closing or near-closing
  reference price.
- **Required inputs:** a governed closing (or near-closing) reference price and
  the earlier observation(s) it is compared against, all with provenance.
- **Derived outputs:** the relationship between an earlier observation and the
  closing reference (a derived calculation).
- **What it means:** "Relative to a governed closing reference, this earlier
  observation sat here."
- **What it does NOT mean:** a guaranteed benchmark of skill or profit. The
  precise definition of "closing" and "near-closing" is **not yet ratified**.
- **Minimum provenance:** provenance of the closing reference and of every
  compared observation, plus the closing-price rule applied.
- **Can it exist without historical data?** No. It requires at least an earlier
  observation and a closing reference.
- **Governance note:** The closing-price policy (what counts as the closing
  reference, timing, and source rules) requires a later governance decision
  before implementation. See [DECISION_LOG.md](../DECISION_LOG.md).

---

## 6. Personal Spot

- **Canonical name:** Personal Spot
- **Purpose:** Represent an observation derived from a user's own recorded
  history or behavior.
- **Required inputs:** a user's own recorded observations or actions, with their
  provenance.
- **Derived outputs:** interpretations of the user's own recorded history (a
  derived calculation over user-owned data).
- **What it means:** "Based on what you recorded, here is an observation about
  your own history."
- **What it does NOT mean:** a recommendation, a prediction about the user's
  future results, or an assessment of skill.
- **Minimum provenance:** the user's own recorded observations and their
  timestamps/context.
- **Can it exist without historical data?** No. It is defined by the user's
  historical record.
- **Implementation note:** No Personal Spot implementation exists in Sprint 0.
  It is defined here only so future work has clear semantics.
