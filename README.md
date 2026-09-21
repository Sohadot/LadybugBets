# Ladybug Bets

**Spot the Edge.**

Ladybug Bets is a betting-intelligence and probability-discovery platform. It
exists to make betting-market prices more legible: to turn raw odds into
implied probabilities, to surface where different sources disagree, and to let
those market conditions be inspected, understood, and tracked over time.

## What this project is

An analytical, tracking, and educational layer between raw market prices and
informed human decision-making. Its fundamental object is not "the bet" but the
**Spot** — an observed, governed, explainable market condition that deserves
examination.

## What this project is not

Ladybug Bets is **not**, at this stage:

- a sportsbook
- a casino or wagering operator
- a custodian of player funds
- a bookmaker
- a tipster service promising winning picks
- a "guaranteed profit" product

It does not accept, transmit, or settle wagers, and it makes no claim of
regulatory status.

## Current project status

**Foundation / pre-MVP.** This repository currently contains public
foundational documentation only. No application code, database, data vendor,
odds API, or user-facing product has been built.

## Initial product surfaces (planned)

These are planned surfaces, not shipped features:

- **SpotBoard** — inspect comparable market prices and their implied
  probability context.
- **Probability Lab** — odds conversion, implied probability, break-even
  probability, and simple market-margin utilities.
- **Market Movement** — inspect governed price changes across timestamps.

## Principles

- A Spot is evidence or a derived observation, not a recommendation,
  prediction, or advice to wager.
- Source facts and derived calculations must remain distinct and never be
  silently conflated.
- Every governed market observation must be traceable to its source, time,
  event, market, and outcome.
- Sober, precise language. Uncertainty is stated, not hidden.

## Foundation documents

- [docs/FOUNDATION.md](docs/FOUNDATION.md) — strategic foundation
- [docs/PRODUCT_BOUNDARY.md](docs/PRODUCT_BOUNDARY.md) — allowed and prohibited scope
- [docs/SPOT_ONTOLOGY.md](docs/SPOT_ONTOLOGY.md) — Spot Ontology v0.1
- [docs/DATA_MODEL.md](docs/DATA_MODEL.md) — canonical observation model
- [docs/METHODOLOGY.md](docs/METHODOLOGY.md) — mathematical and interpretive discipline
- [docs/RESPONSIBLE_USE.md](docs/RESPONSIBLE_USE.md) — responsible-use policy
- [docs/PUBLICATION_POLICY.md](docs/PUBLICATION_POLICY.md) — publication policy
- [docs/MVP_SCOPE.md](docs/MVP_SCOPE.md) — MVP v0.1 scope
- [DECISION_LOG.md](DECISION_LOG.md) — durable decisions

## Legal and responsible-use posture

This repository does not constitute a sportsbook or wagering service. Ladybug
Bets is an analytical and educational product. Gambling involves financial
risk; market information does not guarantee outcomes, and past performance does
not establish future results. Users should comply with the laws applicable to
their jurisdiction. Jurisdiction-specific compliance must be reviewed before any
regulated commercial functionality is introduced. See
[docs/RESPONSIBLE_USE.md](docs/RESPONSIBLE_USE.md).

## Development status

Pre-MVP. Documentation-only. Contents describe current intent and governed
foundations, not built functionality.
