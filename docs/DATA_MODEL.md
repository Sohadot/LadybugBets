# DATA MODEL

*The minimum canonical observation model.*

This document defines the conceptual shape of a market observation. It is a
future-compatible model, not a production schema. **No database and no data
vendor are selected in Sprint 0.**

## The four semantic dimensions

Before listing fields, the model establishes that a market observation is
composed of values belonging to **four distinct semantic dimensions**. Every
conceptual field is classifiable as exactly one of these, and they must never be
silently conflated:

1. **SOURCE-ASSERTED** — values actually asserted or provided by the governed
   upstream source, recorded as received and attributed to that source.
2. **CANONICAL / NORMALIZED** — LadybugBets identifiers or normalized
   representations used to align records across sources (e.g. a canonical event
   identity). These are LadybugBets constructs, not raw source facts.
3. **DERIVED** — values calculated by LadybugBets from source-asserted values
   under a stated method.
4. **INGESTION / PROVENANCE METADATA** — values LadybugBets records about *how
   and when* it obtained the observation (e.g. receipt time, source reference).

A field may, in future implementation, preserve **both** a raw source-asserted
form and a canonical/normalized form. Nothing here pre-commits to a physical
storage design; the point is that the raw and canonical forms remain
distinguishable and are never merged into one indistinct value.

### Provider identity ≠ bookmaker/operator identity

Two identity dimensions are commonly (and wrongly) collapsed. They are separate:

- **Upstream data source / provider** (`provider_id`) — the governed system or
  feed *from which LadybugBets obtained the record*. This is the data supplier.
- **Quoted operator / bookmaker** (`operator_id`, and optionally a separate
  `operator_display_name`) — the bookmaker or market operator *to which the
  quoted price is attributed*.

The provider is not automatically the bookmaker whose price is quoted:

- A single provider may carry quotations attributed to **multiple** distinct
  bookmakers.
- Two **different** providers may each carry quotations attributed to the **same**
  bookmaker.

Neither case may be collapsed. Provider identity and quoted bookmaker/operator
identity are different semantic dimensions and must be retained separately.

## Canonical market observation

The minimum canonical observation is described by the following conceptual
fields. The **Dimension** column classifies each field per the four dimensions
above. This is a conceptual model, not a schema; names are canonical concepts,
not column definitions.

| Field | Dimension | Meaning |
| --- | --- | --- |
| `event_id` | Canonical/normalized | LadybugBets canonical identifier for the sporting event (an alignment key, not a verbatim source value). |
| `sport` | Canonical/normalized (may retain raw) | Normalized sport (e.g. football/soccer); a source's raw label may be retained alongside. |
| `competition` | Canonical/normalized (may retain raw) | Normalized competition/league (e.g. English Premier League); raw source label may be retained alongside. |
| `start_time` | Source-asserted (normalizable) | Scheduled start time as asserted by the source; may be normalized (e.g. timezone) while retaining the raw form. |
| `provider_id` | Ingestion/provenance | Identifier of the upstream governed data source/feed from which the record was obtained. |
| `operator_id` | Source-asserted | Identifier of the bookmaker/market operator to which the quoted price is attributed. |
| `operator_display_name` | Source-asserted (optional) | Human-readable name of the quoted operator, kept separately from its identifier. |
| `market` | Canonical/normalized (may retain raw) | Normalized market being priced (e.g. match result); raw source label may be retained alongside. |
| `outcome` | Canonical/normalized (may retain raw) | Normalized outcome within the market; raw source label may be retained alongside. |
| `price` | Source-asserted | The price as asserted by the source for this operator. |
| `price_format` | Source-asserted | The format of `price` (decimal, American, fractional). |
| `source_observed_at` | Source-asserted (may be absent) | Timestamp for when the quoted market state applied *according to the source*, when the source provides a trustworthy one. May be unavailable. |
| `ingested_at` | Ingestion/provenance | Timestamp for when LadybugBets received or recorded the observation. |
| `jurisdiction` | Canonical/normalized or source-asserted | Jurisdiction context; whether asserted by the source or normalized by LadybugBets must be recorded. |
| `source_reference` | Ingestion/provenance | Reference back to the specific source record/feed the observation came from. |

Time semantics for `source_observed_at` and `ingested_at` are defined in
[Time semantics](#time-semantics) below.

## Source-asserted values vs. derived fields

The single most important rule of this model: **source-asserted values,
canonical/normalized values, and derived values must remain semantically
distinct, and derived values must never be stored or presented as though they
were source facts.**

### Source-asserted values

Facts actually asserted by a governed data source (for example `price`,
`price_format`, the quoted `operator_id`). These are recorded as received and
attributed to their source. Membership in a dimension is per field, as marked in
the table above — the table is not uniformly "source observations".

### Canonical / normalized values

LadybugBets identifiers or normalized representations (for example `event_id`,
and the normalized forms of `sport`, `competition`, `market`, `outcome`, and,
where applicable, `jurisdiction`). If LadybugBets normalizes any of these, that
normalization **must not be silently represented as a raw source fact**. Where
useful, a raw source-asserted form may be retained alongside the canonical form.

### Derived fields

Values calculated by LadybugBets from source observations. Examples:

- `implied_probability` — implied probability derived from `price` and
  `price_format` under a stated method.
- `normalized_probability` — a probability after an explicitly named margin
  normalization method is applied (only where applicable).
- `movement_amount` — a change computed between comparable observations over
  time.
- `cross_operator_difference` — a difference computed across comparable
  observations attributed to distinct bookmaker/operator identities.

Every derived field must record which method produced it and which source
observations it was derived from. A derived field is always labeled as derived.

## Time semantics

A single "observed_at" is ambiguous, so the model distinguishes two timestamps:

- **`source_observed_at` — source observation time.** The time at which the
  quoted market state applied *according to the governed source*, when the source
  provides such a timestamp and it is trustworthy. This is source-asserted.
- **`ingested_at` — ingestion / receipt time.** The time at which LadybugBets
  received or recorded the observation. This is ingestion/provenance metadata.

Fallback and integrity rules:

- If a governed source provides an observation timestamp, preserve it as
  `source_observed_at`.
- LadybugBets separately retains `ingested_at` for every observation.
- `ingested_at` must **not** be silently presented as the bookmaker's exact quote
  time. Receipt time is not quote time.
- A source timestamp is **not** forced to exist. If `source_observed_at` is
  unavailable, that limitation must remain explicit; `ingested_at` must not be
  substituted for it as though it were the source's own time.

This distinction matters because Movement Spots — and future Closing Spots —
depend on temporal comparability. The closing-price policy is **not** ratified
by this amendment; **DEC-011 remains Deferred** (see
[../DECISION_LOG.md](../DECISION_LOG.md)).

## Provenance requirements

Every market observation must remain attributable to:

- its **provider** (upstream data source/feed)
- its **quoted operator/bookmaker**
- its **time** (source-observed time where available, and ingestion time)
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
