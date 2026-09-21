# LBOC-001 — LadybugBets Observation Contract
Version: 1.0.0

*The governed logical envelope of a LadybugBets source observation.*

This contract converts the Sprint 0 conceptual model into a governed,
vendor-neutral, machine-inspectable observation contract. It is the authority for
what a LadybugBets source observation **is**, which parts are provider-asserted,
which parts are LadybugBets canonical identities, and how a record moves from
"arrived from a feed" to "governed observation".

It is a **governance contract**, not a database schema and not an ingestion
engine. No data vendor, database, or infrastructure is selected or named by this
document (DEC-009 stands).

## Operational law

> A raw record is not a governed LadybugBets observation merely because it
> arrived from a feed.

A record becomes a governed observation only through an explicit, ordered
pipeline:

```
SOURCE ASSERTION → PROVENANCE → CANONICALIZATION → IDENTITY RESOLUTION → ADMISSION
```

And a second, independent law:

> ADMISSION ≠ PUBLICATION AUTHORIZATION

A structurally valid observation may be **ADMITTED** for governed internal use
while still being **blocked from public display** because its source-rights
posture is unknown or does not permit publication (see
[SOURCE_GOVERNANCE.md](SOURCE_GOVERNANCE.md) and DEC-018).

## Envelope structure

The governed observation envelope has five clearly separated sections. A value
lives in exactly one section; the sections are never silently merged.

1. **`contract`** — contract metadata.
2. **`provenance`** — provider/provenance identity and ingestion metadata.
3. **`source_asserted`** — values actually asserted by the upstream source.
4. **`canonical`** — LadybugBets canonical identities and lossless canonical
   representations.
5. **`governance`** — admission state, reason codes, and correction/supersession
   metadata.

The machine-readable form is
[`contracts/observation-envelope.schema.json`](../contracts/observation-envelope.schema.json)
(JSON Schema draft 2020-12).

### 1. Contract metadata (`contract`)

| Field | Meaning |
| --- | --- |
| `contract_version` | The LBOC contract version this envelope conforms to (e.g. `1.0.0`). |
| `observation_id` | A LadybugBets **opaque, stable** identifier for this observation. |

`observation_id` is a LadybugBets construct, not a source value. **The
UUID/version/hash generation algorithm for `observation_id` is not ratified in
Sprint 1.** It is opaque and stable; nothing here fixes how it is minted.

### 2. Provider / provenance identity (`provenance`)

| Field | Dimension | Meaning |
| --- | --- | --- |
| `provider_id` | Ingestion/provenance | Governed LadybugBets identity of the upstream provider/feed. Not a value the provider asserts about itself. |
| `source_reference` | Ingestion/provenance | Reference back to the specific source record/feed the observation came from. Provenance, **not** canonical sporting identity. |
| `source_record_id` | Source-asserted (optional) | A provider-native record identifier, when the provider supplies one. Remains source-asserted; never substituted for a canonical id. |
| `ingested_at` | Ingestion/provenance | Timestamp for when LadybugBets received or recorded the observation. |

`source_reference` is provenance metadata: it says *where the record came from*,
never *which sporting entity it is about*.

### 3. Raw / source-asserted identity (`source_asserted`)

These are vendor-native / source-native representations exactly as received.
**A provider is not required to supply every native id; absence remains absence,
and LadybugBets does not fabricate source identifiers.**

| Field | Meaning |
| --- | --- |
| `source_event_id` | Event identifier supplied by the provider, when available. |
| `source_event_name` | Provider-supplied event label/name, when available. |
| `source_sport_label` | Sport label as provided. |
| `source_competition_id` | Competition identifier supplied by the provider, when available. |
| `source_competition_label` | Competition/league label as provided. |
| `source_operator_id` | Operator/bookmaker identifier supplied by the provider, when available. |
| `source_operator_name` | Operator/bookmaker label as provided. |
| `source_market_id` | Market identifier supplied by the provider, when available. |
| `source_market_label` | Market label as provided. |
| `source_outcome_id` | Outcome identifier supplied by the provider, when available. |
| `source_outcome_label` | Outcome label as provided. |
| `source_participants` | Participants as asserted by the source (see [participants](#participant-identity)). |
| `source_start_time` | Scheduled start time exactly as asserted, including the source's stated offset. |
| `source_observed_at` | Source's own quote-state timestamp, when trustworthy. **May be absent.** |
| `source_jurisdiction` | Jurisdiction as asserted by the source, when supplied. |
| `price` | The price as asserted by the source for this operator. |
| `price_format` | The format of `price`: `decimal`, `american`, or `fractional`. |

### 4. Canonical identity layer (`canonical`)

LadybugBets canonical identities and lossless canonical representations produced
under the identity-normalization law (Sprint 0) and the Identity Resolution
Standard ([LBIR-001](IDENTITY_RESOLUTION.md)). Any canonical identity that has
not been resolved is represented as **null / unresolved** — never guessed, never
copied from the raw form.

| Field | Meaning |
| --- | --- |
| `sport` | Canonical sport. |
| `competition_id` / `competition` | Canonical competition identity and display. |
| `event_id` | Canonical event identity (participant-bearing; see LBIR-001). |
| `participants` | Canonical participants with roles. |
| `operator_id` / `operator_display_name` | Canonical operator identity and display. |
| `market_id` / `market` | Canonical market identity and display. |
| `outcome_id` / `outcome` | Canonical outcome identity and display. |
| `jurisdiction` | Canonical jurisdiction representation. |
| `start_time` | Lossless canonical representation of the **same instant** as `source_start_time` (e.g. UTC-normalized). Not an independently asserted different time. |

**Raw identity ≠ canonical identity.** No raw source value may silently become a
canonical value merely because it looks familiar. Canonical id namespaces are
distinct from source id namespaces by construction.

### 5. Governance / admission metadata (`governance`)

| Field | Meaning |
| --- | --- |
| `admission_state` | Exactly one of `ADMITTED`, `QUARANTINED`, `REJECTED` (see [admission states](#admission-states)). |
| `reason_codes` | Controlled categorical reason codes. Required non-empty for `QUARANTINED` and `REJECTED`; empty/absent for `ADMITTED`. |
| `supersedes_observation_id` | Optional. The `observation_id` this record corrects/supersedes (append-only; see [CONFLICT_AND_DEDUPLICATION.md](CONFLICT_AND_DEDUPLICATION.md)). |

`reason_codes` are **categorical reasons, not severity scores.** No scoring is
introduced (DEC-012 stands).

## Participant identity

Governed event identity cannot be robustly resolved without participants, so the
contract models them explicitly, in raw and canonical forms kept distinct.

**Source participants** (`source_asserted.source_participants[]`):

| Field | Meaning |
| --- | --- |
| `source_participant_id` | Participant identifier as supplied by the provider, when available. |
| `source_participant_name` | Participant label as supplied. |
| `source_role` | Role label as supplied (e.g. `home`, `away`). |

**Canonical participants** (`canonical.participants[]`):

| Field | Meaning |
| --- | --- |
| `participant_id` | LadybugBets canonical participant identity. |
| `participant_display_name` | Governed display label. |
| `role` | Canonical role. |

For the initial football scope, roles are `home` and `away`. The model is written
so that additional role-bearing participants can be added later without rewriting
the contract; **no teams database is built and no real team registry is populated
in Sprint 1** (synthetic participants only). See DEC-017.

## Admission states

Exactly three integrity states are ratified (DEC-015). See
[CONFLICT_AND_DEDUPLICATION.md](CONFLICT_AND_DEDUPLICATION.md) for how conflicts
map to these states.

### ADMITTED

The record is structurally and semantically sufficient for governed **internal**
use under the contract.

- Admission does **not** mean every Spot type may use it (e.g. Movement needs an
  adequate temporal basis; see [TEMPORAL_GOVERNANCE.md](TEMPORAL_GOVERNANCE.md)).
- Admission does **not** mean it may be published (DEC-018).

### QUARANTINED

The record may be legitimate but cannot safely enter governed analytical use yet.
Examples: unresolved canonical event, ambiguous operator identity, unresolved
market/outcome identity, conflicting same-observation assertions, temporal
ambiguity material to the intended analysis.

Quarantine is **not deletion**. Provenance is preserved.

### REJECTED

The record is not admissible under the contract. Examples: malformed price,
impossible required value, missing provider provenance, invalid contract version,
a record that cannot be attributed to a governed provider, structurally corrupt
payload.

Rejection must carry an explicit reason code. **Records are never silently
discarded.**

## Admission reason codes

Controlled initial vocabulary (categorical, not scores):

- `UNRESOLVED_EVENT_IDENTITY`
- `AMBIGUOUS_EVENT_IDENTITY`
- `UNRESOLVED_OPERATOR_IDENTITY`
- `AMBIGUOUS_OPERATOR_IDENTITY`
- `UNRESOLVED_MARKET_IDENTITY`
- `UNRESOLVED_OUTCOME_IDENTITY`
- `UNRESOLVED_PARTICIPANT_IDENTITY`
- `MISSING_REQUIRED_SOURCE_FIELD`
- `INVALID_PRICE`
- `INVALID_PRICE_FORMAT`
- `MISSING_PROVIDER_PROVENANCE`
- `TEMPORAL_AMBIGUITY`
- `CONFLICTING_SOURCE_ASSERTIONS`
- `INVALID_CONTRACT_VERSION`

When an `UNRESOLVED_*` or `AMBIGUOUS_*` identity code is present, the
corresponding canonical identity **must** be represented as unresolved (null /
absent). An unresolved identity is never represented as resolved.

## Source observation immutability and derived separation

A source observation record is an **immutable factual / provenance object after
admission**, except through governed correction / supersession semantics
(append-only; see [CONFLICT_AND_DEDUPLICATION.md](CONFLICT_AND_DEDUPLICATION.md)).

Derived values — implied probability, normalized probability, movement, consensus
aggregate, future closing comparison — **must not** appear inside the source
observation envelope (DEC-004, DEC-021). A derived record is a separate object
that **references input `observation_id`(s)** and never overwrites or masquerades
as a source field.

### Minimal derived-record concept (conceptual only)

To express the rule without building a derived schema: a derived record
conceptually carries its own identifier, the named method that produced it, and a
list of input `observation_id` references. It contains no source assertions of
its own. This is stated to fix the boundary; the full derived-record schema is
**not** built in Sprint 1.

## What Sprint 1 deliberately does not do

- No data vendor is selected or named.
- No database, API integration, or production ingestion is built.
- No `observation_id` minting algorithm is ratified.
- No timing tolerances, freshness thresholds, closing-price policy (DEC-011), or
  edge score (DEC-012) are introduced.
