# PRODUCT BOUNDARY

*What LadybugBets may and may not do in the current governed phase.*

This document is authoritative for scope. If a proposed feature is not clearly
permitted here, it is out of scope until governance says otherwise.

## Current allowed scope

LadybugBets may:

- display market data from governed sources
- calculate implied probabilities from governed prices
- calculate overround / implied margin (book percentage) where mathematically
  applicable — as a price-derived measure, not a claim about realized operator
  margin
- compare prices across outcomes and sources
- show historical price movement between comparable observations
- describe market observations in plain, sober language
- provide educational material about odds, probability, and market structure
- allow future personal tracking of a user's own recorded observations
- identify analytical **Spots** under explicitly documented rules (see
  [SPOT_ONTOLOGY.md](SPOT_ONTOLOGY.md))

## Current prohibited scope

LadybugBets must not:

- accept wagers
- transmit or route wagers
- hold player funds
- operate a sportsbook or act as a bookmaker
- present a Spot as guaranteed profit
- make deceptive "AI winner" claims
- present fabricated or unverifiable historical performance
- publish undisclosed sponsored rankings
- encourage loss-chasing
- use language targeted toward minors
- imply certainty where uncertainty exists

## The four distinct concepts

These four concepts are not interchangeable and must never be silently
conflated in product, copy, or data:

**Observation** ≠ **Recommendation** ≠ **Prediction** ≠ **Execution**

- **Observation** — a governed record of a market condition (e.g. "this source
  showed this price for this outcome at this time"). This is what LadybugBets
  produces.
- **Recommendation** — advice to take a particular action. LadybugBets does not
  make recommendations to wager.
- **Prediction** — a claim about a future outcome. Observing a price is not
  predicting a result.
- **Execution** — placing, transmitting, or settling a bet. LadybugBets does not
  execute anything.

A Spot is an **observation** (or a derived observation). It is never, by virtue
of existing, a recommendation, a prediction, or an execution. Any surface that
displays Spots must preserve this distinction explicitly.
