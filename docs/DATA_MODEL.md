# DATA MODEL

*The minimum canonical observation model.*

This document defines the conceptual shape of a market observation. It is a
future-compatible model, not a production schema. **No database and no data
vendor are selected in Sprint 0.**

## Canonical market observation

The minimum canonical observation is described by the following fields:

| Field | Meaning |
| --- | --- |
| `event_id` | Stable identifier for the sporting event. |
| `sport` | The sport (e.g. football/soccer). |
| `competition` | The competition or league (e.g. English Premier League). |
| `start_time` | Scheduled start time of the event. |
| `source_id` | Identifier of the governed data source of the observation. |
| `bookmaker` | The bookmaker the price is attributed to. |
| `market` | The market being priced (e.g. match result). |
| `outcome` | The specific outcome within the market. |
| `price` | The observed price. |
| `price_format` | The format of `price` (decimal, American, fractional). |
| `observed_at` | Timestamp at which the price was observed. |
| `jurisdiction` | Jurisdiction context relevant to the observation. |
| `source_reference` | Reference back to the source record/feed for the observation. |

## Source observations vs. derived fields

The single most important rule of this model: **source observations and derived
fields must remain semantically distinct, and derived values must never be
stored as though they were source facts.**

### Source observations

Facts received from a governed data source. These are recorded as observed and
attributed to their source. The fields in the table above are source
observations (except where a specific field is explicitly a derivation).

### Derived fields

Values calculated by LadybugBets from source observations. Examples:

- `implied_probability` — implied probability derived from `price` and
  `price_format` under a stated method.
- `normalized_probability` — a probability after an explicitly named margin
  normalization method is applied (only where applicable).
- `movement_amount` — a change computed between comparable observations over
  time.
- `cross_source_difference` — a difference computed across comparable
  observations from distinct sources.

Every derived field must record which method produced it and which source
observations it was derived from. A derived field is always labeled as derived.

## Provenance requirements

Every market observation must remain attributable to:

- its **source**
- its **time**
- its **event**
- its **market**
- its **outcome**

Provenance is not optional. A value that cannot be attributed back to these is
not a governed LadybugBets market observation (see
[PUBLICATION_POLICY.md](PUBLICATION_POLICY.md)).

## Historical observations

Historical observations should be preserved when technically and contractually
permitted, because temporal price movement is a first-class analytical property
(it is what Movement Spots and Closing Spots depend on). Whether and how history
is retained is subject to the eventual data-source terms and infrastructure
governance — not decided here.

## Explicitly deferred

- No database is selected in this sprint.
- No data vendor is selected in this sprint.
- No production schema, indexing strategy, or storage engine is designed here.

This model is intended to remain compatible with those later decisions, not to
pre-empt them.
