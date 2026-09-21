# MVP SCOPE

*MVP v0.1 — frozen scope.*

This document freezes the scope of the first minimum viable product. It is a
product-scope statement. It is **not** a data-license, vendor, database, or
infrastructure decision — none of those are made here.

## Initial market scope

- **Sport:** Football / soccer.
- **Competition candidate:** English Premier League.

This is a product-scope decision only. The choice of competition does **not**
imply or ratify any data license, feed, or vendor for that competition.

## Initial public product surfaces

### SpotBoard

**Purpose:** Inspect comparable market prices and their implied probability
context. A place to look at governed Price Spots and their derived probability
context side by side.

### Probability Lab

**Initial utilities:**

- odds conversion (decimal / American / fractional)
- implied probability
- break-even probability
- simple market margin / overround calculations

All calculations follow [METHODOLOGY.md](METHODOLOGY.md).

### Market Movement

**Purpose:** Inspect governed price changes across timestamps — the surface for
Movement Spots built from comparable observations over time.

## Explicitly out of scope for MVP v0.1

The following belong to later gates and are **not** part of MVP v0.1:

- accounts
- payments
- subscriptions
- affiliate integration
- alerts
- mobile apps
- automated picks
- AI betting advice
- dozens of sports
- a B2B API
- a public "edge score"

## Initial public route candidates

These are **route candidates**, not implementation instructions and not a
commitment to build:

- `/`
- `/spotboard/`
- `/probability/`
- `/market-movement/`
- `/methodology/`
- `/learn/`
- `/responsible-use/`
- `/about/`

## Not decided here

No database, data vendor, monetization provider, pricing model, affiliate
operator, or infrastructure vendor is selected or ratified by this document. See
[../DECISION_LOG.md](../DECISION_LOG.md).
