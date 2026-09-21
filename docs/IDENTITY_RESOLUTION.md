# LBIR-001 — LadybugBets Identity Resolution Standard
Version: 1.0.0

*How raw source identities become LadybugBets canonical identities.*

This standard governs the **CANONICALIZATION → IDENTITY RESOLUTION** stages of
the observation pipeline defined in
[LBOC-001](OBSERVATION_CONTRACT.md). It is deterministic and **fail-closed**.

## Governing principle

> No guess becomes identity.

A raw source identity is resolved to a LadybugBets canonical identity **only**
through governed deterministic evidence. If governed evidence is absent or
inconclusive, resolution fails closed — it does not guess.

Failing closed means the identity is marked **unresolved** or **ambiguous**, and
the observation is quarantined under LBOC-001, never admitted with a fabricated
canonical identity.

## Scope

Resolution applies to every entity that has a raw form and a canonical form:
`sport`, `competition`, `participant`, `event`, `operator`, `market`, `outcome`,
`jurisdiction`.

The governed mapping format is
[`contracts/identity-mapping.schema.json`](../contracts/identity-mapping.schema.json).

## Resolution rules

### 1. Existing governed mapping

If a governed mapping already exists keyed by:

```
provider_id + entity_type + source-native identifier
```

then that mapping resolves the source entity to its canonical LadybugBets
identity. This is the primary deterministic path. The mapping must be present in
the governed identity-mapping registry; it is not inferred at ingestion time.

### 2. Curated aliases

An exact alias may resolve an entity **only** if that alias already exists in the
governed mapping registry (a mapping keyed by `provider_id + entity_type +
source_label`, with `status: active`).

> An arbitrary string comparison at ingestion time is **not** enough.

A label that merely *looks* like a known entity, but has no governed mapping, does
not resolve.

### 3. Fuzzy matching — prohibited for automatic assignment

No fuzzy automatic identity merge is permitted in Sprint 1. The following must
**not** create canonical identity automatically:

- edit distance / string similarity
- semantic embeddings
- AI guessing
- approximate name similarity
- uncontrolled abbreviation inference

These techniques **may** later assist human/governed review, but they can never
silently create canonical identity. Any canonical identity they suggest must pass
through a governed mapping before it is used (DEC-016).

### 4. Ambiguity — fail closed

- **Zero** governed mappings match → **unresolved**.
- **More than one** canonical candidate matches → **ambiguous**.

Both cases fail closed. Neither is resolved by picking a "best" candidate. The
observation is quarantined with the corresponding `UNRESOLVED_*` or `AMBIGUOUS_*`
reason code, and the canonical identity remains null.

## Event identity resolution

Event identity is resolved conservatively and is **participant-bearing**
(DEC-017).

A provider-native `source_event_id` is **not** the canonical `event_id`.

The canonical event-identity candidate depends on governed canonical components:

- canonical `sport`
- canonical `competition`
- ordered canonical **participants and roles** (e.g. `home`, `away`)
- canonical scheduled `start_time`

Rules:

- If an existing governed `source → canonical` event mapping exists (rule 1),
  that mapping resolves the event.
- Otherwise, an event resolves only when **all** governed canonical components
  above are themselves resolved and together identify exactly one canonical
  event. If the components are unresolved or identify zero/many events, the event
  is unresolved/ambiguous and quarantined.
- **No fuzzy event auto-merge.**

### Conflicting scheduled times

If two providers assert **materially different** scheduled times and no governed
mapping already resolves them to the same event:

> do **not** auto-merge.

Mark the identity **unresolved** or **ambiguous**.

**No arbitrary timing tolerance is introduced in Sprint 1.** A tolerance window
("times within N minutes are the same event") is exactly the kind of guess this
standard forbids without governed evidence. Conflict/tolerance rules may be
refined later with evidence; until then, differing times without a governed
mapping do not merge.

Note: a **lossless** timezone normalization of the *same* asserted instant is not
a "different time" — that is representational (see LBOC-001 and
[TEMPORAL_GOVERNANCE.md](TEMPORAL_GOVERNANCE.md)). Materially different instants
are conflicts.

## Relationship to canonical identity law

This standard operationalizes the Sprint 0 identity-normalization law (DEC-014):
raw identity and canonical identity are distinct, and canonicalization is a
governed act. LBIR-001 states precisely *when* that governed act may succeed:
only via rules 1–2, never via rules 3, and never by resolving ambiguity through a
guess (rule 4).

## Deferred

- Provider precedence between conflicting providers is **not** ratified (see
  [CONFLICT_AND_DEDUPLICATION.md](CONFLICT_AND_DEDUPLICATION.md)).
- Timing tolerances for event merge are **not** ratified.
- The governance workflow for creating new mappings (review, approval, evidence
  capture) is acknowledged via the mapping contract's `decision_basis` and
  `evidence_reference` fields but its process is left to later governance.
