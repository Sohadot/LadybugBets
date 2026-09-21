# FOUNDATION

*Public strategic foundation — LadybugBets, Sprint 0.*

## Purpose

LadybugBets exists to make betting-market prices more legible.

Odds are prices. Prices are easy to display but harder to interpret. LadybugBets
is the layer that helps a person read a price for what it actually implies, see
how it compares to other prices, and observe how it changes over time.

## Core problem

Raw odds are cheap to show and hard to understand. A single displayed price says
little on its own about:

- **implied probability** — what the price implies about the chance of the
  outcome
- **implied margin (overround)** — the book percentage baked into a set of
  prices, which is not by itself the operator's realized margin
- **disagreement across sources** — where different providers or bookmakers
  imply different probabilities for the same outcome
- **movement over time** — how a price has drifted or shifted since it opened
- **closing price** — where a market settled relative to earlier observations
- **personal historical behavior** — how a user's own past observations and
  decisions have looked

Each of these requires interpretation the raw number does not provide.

## Thesis

The useful layer is not merely more odds. It is **governed interpretation** of
what those prices mean and how they change.

"Governed" is load-bearing: every interpretation must be traceable to source
observations and an explicit derivation. More data alone is not the product; a
disciplined, reproducible reading of that data is.

## Brand and product relationship

Ladybugs have spots. LadybugBets identifies and organizes market **Spots**.

A Spot is a specific, observed, governed market condition worth examining. The
name gives the product a coherent language: the platform's fundamental object is
not "the bet" but the "Spot" — a small, legible, attributable unit of market
observation. The brand and the product vocabulary reinforce the same idea:
looking closely at distinct marks in the market and organizing them.

## Long-horizon product direction

LadybugBets may evolve across several directions, none of which are committed
features and all of which remain subject to governance:

- consumer intelligence tools
- historical market analysis
- personal tracking
- data interfaces
- embeddable analytical surfaces

This document states direction, not a roadmap. No feature beyond the governed
MVP scope (see [MVP_SCOPE.md](MVP_SCOPE.md)) is promised, and none should be
implemented before it is governed.
