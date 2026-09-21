# CONFLICT AND DEDUPLICATION
Version: 1.0.0

*How LadybugBets distinguishes duplicates, conflicts, revisions, and independent
observations — without destroying provenance.*

This document governs the pipeline behavior when multiple records relate to the
same apparent market fact. It works with [LBOC-001](OBSERVATION_CONTRACT.md) and
[IDENTITY_RESOLUTION.md](IDENTITY_RESOLUTION.md). Provider precedence is **not**
ratified in Sprint 1 (DEC-019).

## Four distinct concepts

**DUPLICATE ≠ CONFLICT ≠ REVISION ≠ INDEPENDENT OBSERVATION.**

These must not be collapsed. Each has a different provenance meaning.

## Duplicate

Two records may be treated as duplicates **only** when their provider-level
provenance and source identity demonstrate that they represent the **same source
assertion** — i.e. the same provider, the same source record/snapshot,
re-delivered.

> Do **not** deduplicate solely because canonical event/operator/market/outcome
> and price happen to match.

Two different providers carrying the same quoted operator are **separate
provenance paths**, not duplicates. Collapsing them would destroy the record that
two independent feeds asserted the value, and would falsely manufacture or
falsely erase apparent agreement.

## Same-provider conflict

If the **same provider** supplies materially incompatible values for what should
be the same source observation / snapshot (e.g. two different prices for the same
operator, market, outcome, and observation time):

- **Retain both.** Do **not** silently last-write-wins.
- Flag the conflict under the governed policy: quarantine with
  `CONFLICTING_SOURCE_ASSERTIONS` (and/or `TEMPORAL_AMBIGUITY` where the
  incompatibility is about timing).

Silent last-write-wins is prohibited (DEC-019): it would erase evidence that the
provider emitted incompatible assertions.

## Cross-provider disagreement

Provider A and Provider B disagreeing about the same canonical operator's
quotation is:

- **not automatically a duplicate**, and
- **not automatically evidence of two operator opinions.**

Both provenance paths are preserved. Whether the disagreement is a data-quality
issue, a timing difference, or a genuine divergence is not decided by discarding
one side.

> **Provider precedence is NOT ratified in Sprint 1.**

No rule such as "Provider A wins over Provider B" is adopted. Until precedence is
governed with evidence, disagreements are retained with full provenance and, where
they block safe analytical use, quarantined.

## Revision / correction

Corrections are **append-only** in the governed record. History is never
destructively rewritten (DEC-019).

- A corrected observation is a **new** observation record with its own
  `observation_id`.
- It may reference the record it corrects via `supersedes_observation_id`.
- The superseded observation **remains traceable** — it is not deleted or
  overwritten.

Constraints:

- **Do not invent correction history** where the provider did not indicate one. A
  correction is recorded because the provider signalled one (or a governed
  correction process produced one), not because a later value simply differs.
- A supersession chain must remain fully walkable back to the original admitted
  observation.

## Independent observation

An independent observation is a distinct source assertion — a different provider,
a different snapshot, or a genuinely new observation event — that is neither a
duplicate of, nor a correction to, another record. Independent observations are
retained as separate governed records, each with its own provenance. Multiple
independent observations are the normal, expected state and are what later
Consensus and Movement analysis draw upon (under their own governed rules).

## Interaction with admission states

| Situation | Typical outcome |
| --- | --- |
| Same provider, same snapshot, re-delivered | Duplicate — collapse only on demonstrated same source assertion. |
| Same provider, incompatible values for same snapshot | `QUARANTINED` — `CONFLICTING_SOURCE_ASSERTIONS`; retain both. |
| Different providers disagree | Both retained; quarantine the analytical use that the disagreement blocks, not the records themselves. |
| Provider-signalled correction | New record with `supersedes_observation_id`; prior record retained. |
| Distinct independent assertions | Retained as separate governed observations. |

In all cases, **provenance is preserved**. No record is silently discarded, and
no history is rewritten.
