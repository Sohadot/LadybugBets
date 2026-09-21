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

**Pre-MVP / governed-contract stage.** This repository contains public
foundational documentation and a vendor-neutral governance contract for source
observations. No application code, database, data vendor, odds API, ingestion
pipeline, or user-facing product has been built. It is **not** a live platform,
a live odds product, or a production data system.

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

## Governance contracts (Sprint 1)

Sprint 1 converts the conceptual model into a governed, vendor-neutral,
machine-inspectable observation contract. No vendor, database, or ingestion is
selected or built.

- [docs/OBSERVATION_CONTRACT.md](docs/OBSERVATION_CONTRACT.md) — **LBOC-001**, the governed observation envelope and three-state admission model (ADMITTED / QUARANTINED / REJECTED)
- [docs/IDENTITY_RESOLUTION.md](docs/IDENTITY_RESOLUTION.md) — **LBIR-001**, fail-closed identity resolution ("no guess becomes identity")
- [docs/TEMPORAL_GOVERNANCE.md](docs/TEMPORAL_GOVERNANCE.md) — temporal evidence and freshness policy
- [docs/CONFLICT_AND_DEDUPLICATION.md](docs/CONFLICT_AND_DEDUPLICATION.md) — duplicate / conflict / revision / independent observation
- [docs/SOURCE_GOVERNANCE.md](docs/SOURCE_GOVERNANCE.md) — source rights; admission is not publication authorization
- Machine-readable contracts (JSON Schema draft 2020-12): [`contracts/observation-envelope.schema.json`](contracts/observation-envelope.schema.json), [`contracts/identity-mapping.schema.json`](contracts/identity-mapping.schema.json), [`contracts/source-profile.schema.json`](contracts/source-profile.schema.json)
- Synthetic contract fixtures under [`fixtures/observation-contract/`](fixtures/observation-contract/), validated by [`tests/test_contract_fixtures.py`](tests/test_contract_fixtures.py) (Python standard library only)

## Legal and responsible-use posture

This repository does not constitute a sportsbook or wagering service. Ladybug
Bets is an analytical and educational product. Gambling involves financial
risk; market information does not guarantee outcomes, and past performance does
not establish future results. Users should comply with the laws applicable to
their jurisdiction. Jurisdiction-specific compliance must be reviewed before any
regulated commercial functionality is introduced. See
[docs/RESPONSIBLE_USE.md](docs/RESPONSIBLE_USE.md).

## Development status

Pre-MVP / governed-contract stage. The repository holds governance documents,
vendor-neutral machine-readable contracts, synthetic fixtures, and a
standard-library contract-validation test suite. It describes current intent and
governed foundations, not a built or operational product.
