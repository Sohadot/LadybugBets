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
- **Quoted operator / bookmaker** — the bookmaker or market operator *to which
  the quoted price is attributed*. This identity has both a raw source-asserted
  form (`source_operator_id` / `source_operator_name`) and a canonical
  LadybugBets form (`operator_id` / `operator_display_name`); see the
  identity-normalization law below.

The provider is not automatically the bookmaker whose price is quoted:

- A single provider may carry quotations attributed to **multiple** distinct
  bookmakers.
- Two **different** providers may each carry quotations attributed to the **same**
  bookmaker.

Neither case may be collapsed. Provider identity and quoted bookmaker/operator
identity are different semantic dimensions and must be retained separately.

### Identity-normalization law

**Raw source identity and LadybugBets canonical identity are distinct semantic
values and must never be silently collapsed.**

- A **provider-specific identifier or label** is evidence about *how that
  provider identifies an entity*. It is source-asserted.
- A **LadybugBets canonical identifier** is an *alignment construct* used to
  identify the same governed entity across providers. It is canonical/normalized.

They are not interchangeable. Different upstream providers may use different
identifiers or labels for the same bookmaker/operator (or event, competition,
market, or outcome); resolving those raw identities to one canonical identity is
a governed act, not an assumption. A raw source identifier must never be
substituted for a LadybugBets canonical identifier, and a canonical identifier
must never be presented as though the source asserted it.

This law applies to every entity where raw source identity and canonical
identity may differ. **The operator-resolution algorithm, fuzzy matching, and
precedence rules are not defined in Sprint 0** — they are deferred to Sprint 1.
Until identity resolution is governed, canonical identities may not yet be
resolvable, and raw labels must not be treated as canonical.

### Provider identity as governed provenance

`provider_id` is an **ingestion/provenance** identity: it is the *governed
LadybugBets identity of the upstream provider* (the feed/supplier), not a value
the provider asserts about itself. If a provider also supplies its own internal
identifiers for records or entities (e.g. a provider-native operator id, event
id, or record id), those provider-native identifiers remain **source-asserted**
and must not be silently substituted for LadybugBets canonical identifiers. No
additional provider-resolution system is designed here.

## Canonical market observation

The minimum canonical observation is described by the following conceptual
fields. The **Dimension** column classifies each field into **exactly one** of
the four dimensions — no field belongs to two. Where a raw source form and a
canonical form may differ, they are represented as **separate conceptual
values** (a `source_*` value and its canonical counterpart), rather than one
field straddling two dimensions. This is a conceptual model, not a schema; names
are canonical concepts, not column definitions, and listing a value does not
require that every observation populate it.

| Field | Dimension | Meaning |
| --- | --- | --- |
| `event_id` | Canonical/normalized | LadybugBets canonical identifier for the sporting event (an alignment key, not a verbatim source value). |
| `source_sport_label` | Source-asserted | Sport label exactly as provided by the source, when available. |
| `sport` | Canonical/normalized | LadybugBets canonical sport (e.g. football/soccer). |
| `source_competition_label` | Source-asserted | Competition/league label exactly as provided by the source, when available. |
| `competition` | Canonical/normalized | LadybugBets canonical competition/league (e.g. English Premier League). |
| `source_start_time` | Source-asserted | Scheduled start time exactly as asserted by the source, including its stated offset/timezone. |
| `start_time` | Canonical/normalized | A lossless canonical representation of the **same asserted instant** (e.g. normalized to UTC) used for cross-source alignment — not an independently asserted different time. See [Start-time semantics](#start-time-semantics). |
| `provider_id` | Ingestion/provenance | Governed LadybugBets identity of the upstream provider/feed the record was obtained from. |
| `source_operator_id` | Source-asserted | Operator/bookmaker identifier supplied by the upstream provider, when available. |
| `source_operator_name` | Source-asserted | Operator/bookmaker label supplied by the upstream provider, when available. |
| `operator_id` | Canonical/normalized | LadybugBets canonical identity for the quoted bookmaker/operator. |
| `operator_display_name` | Canonical/normalized | LadybugBets governed display label for that canonical operator. |
| `source_market_label` | Source-asserted | Market label exactly as provided by the source, when available. |
| `market` | Canonical/normalized | LadybugBets canonical market (e.g. match result). |
| `source_outcome_label` | Source-asserted | Outcome label exactly as provided by the source, when available. |
| `outcome` | Canonical/normalized | LadybugBets canonical outcome within the market. |
| `price` | Source-asserted | The price as asserted by the source for this operator. |
| `price_format` | Source-asserted | The format of `price` (decimal, American, fractional). |
| `source_observed_at` | Source-asserted | Timestamp for when the quoted market state applied *according to the source*, when the source provides a trustworthy one. May be absent. |
| `ingested_at` | Ingestion/provenance | Timestamp for when LadybugBets received or recorded the observation. |
| `source_jurisdiction` | Source-asserted | Jurisdiction as asserted by the source, when supplied. |
| `jurisdiction` | Canonical/normalized | LadybugBets canonical jurisdiction representation. |
| `source_reference` | Ingestion/provenance | Reference back to the specific source record/feed the observation came from. |

Note: the `source_*` label and identifier fields are source-asserted **evidence**
of how a provider identifies an entity; their canonical counterparts
(`event_id`, `sport`, `competition`, `operator_id`, `operator_display_name`,
`market`, `outcome`, `jurisdiction`) are LadybugBets alignment constructs
produced under the identity-normalization law above. Until identity resolution is
governed (Sprint 1), a canonical counterpart may be unresolved; a raw label must
not be promoted to canonical by assumption.

Time semantics for `source_observed_at` and `ingested_at` are defined in
[Time semantics](#time-semantics) below.

## Source-asserted values vs. derived fields

The single most important rule of this model: **source-asserted values,
canonical/normalized values, and derived values must remain semantically
distinct, and derived values must never be stored or presented as though they
were source facts.**

### Source-asserted values

Facts actually asserted by a governed data source (for example `price`,
`price_format`, `source_operator_id`, `source_operator_name`, and the other
`source_*` labels and timestamps). These are recorded as received and attributed
to their source. Membership in a dimension is per field, as marked in the table
above — the table is not uniformly "source observations".

### Canonical / normalized values

LadybugBets identifiers or normalized representations (for example `event_id`,
`operator_id`, `operator_display_name`, and the canonical forms of `sport`,
`competition`, `market`, `outcome`, `start_time`, and `jurisdiction`). These are
LadybugBets alignment constructs produced under the identity-normalization law.
A canonical value **must not be silently represented as a raw source fact**, and
its corresponding raw source form is retained as a separate `source_*` value
rather than merged into it.

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

## Start-time semantics

The event's scheduled start time is modeled as two distinct values:

- **`source_start_time` — source-asserted.** The scheduled start time exactly as
  the source asserts it, including the offset/timezone the source states.
- **`start_time` — canonical/normalized.** A **lossless** canonical
  representation of the *same asserted instant* (for example, normalized to a
  single reference timezone) used for cross-source alignment.

Because the canonical form is a representation of the same instant, LadybugBets
does **not** thereby assert a different event time; timezone normalization is
representational, not a new source fact. Where a source's scheduled start time
genuinely differs from another source's, that is **conflicting source
assertions**, not a normalization artifact — and conflict resolution between
differing source start times is **deferred to Sprint 1**.

## Jurisdiction semantics

Jurisdiction is likewise modeled as two distinct values rather than one
ambiguous field:

- **`source_jurisdiction` — source-asserted.** Jurisdiction as asserted by the
  source, when supplied.
- **`jurisdiction` — canonical/normalized.** LadybugBets canonical jurisdiction
  representation.

If jurisdiction is both supplied by a source and normalized by LadybugBets, the
two forms are kept distinct. Jurisdiction-resolution rules are **not defined in
Sprint 0**.

## Provenance requirements

Every market observation must remain attributable to:

- its **provider** (upstream data source/feed)
- its **quoted operator/bookmaker** — preserving both the raw source-asserted
  operator identity/label and, where resolved, the canonical operator identity
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
