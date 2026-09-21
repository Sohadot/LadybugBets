# SOURCE GOVERNANCE
Version: 1.0.0

*What must be known about a source before its data may be used or published.*

Sprint 1 does **not** qualify any real provider. This document defines the
**Source Profile** concept and the rights posture that Sprint 2 will require
before any real provider is onboarded. No real provider is named, and no secrets,
credentials, commercial pricing, or negotiated terms appear here or in the public
repository (DEC-010).

The machine-readable form is
[`contracts/source-profile.schema.json`](../contracts/source-profile.schema.json).

## The governing law

> Admission is not publication authorization. (DEC-018)

A source observation may be semantically **ADMITTED** for governed internal use
(LBOC-001) while public **publication remains blocked** by source-rights policy.
These are two independent gates:

1. **Semantic admission** — is the record structurally and semantically
   sufficient? (Governed by LBOC-001.)
2. **Publication authorization** — do the source's rights permit this specific
   use (e.g. public display)? (Governed by the Source Profile here.)

Passing gate 1 says nothing about gate 2.

## Source Profile

A Source Profile is governance metadata about a provider. Fields:

| Field | Meaning |
| --- | --- |
| `provider_id` | Governed LadybugBets identity of the provider. |
| `provider_name` | Human-readable provider name (public-safe). |
| `access_basis` | The basis on which LadybugBets accesses the data (e.g. public, licensed, agreement) — described in public-safe terms only. |
| `terms_reference` | A pointer to the governing terms/evidence (a reference, not the contents). |
| `terms_checked_date` | The date the terms posture was last reviewed. |
| `attribution_requirements` | Any attribution the source requires when its data is shown. |
| `geographic_restrictions` | Geographic restrictions, if any. |
| `rights_matrix` | The capability postures below. |
| `qualification_status` | Overall governed status (e.g. `unqualified`, `under_review`, `qualified`). |

## Rights matrix

The rights matrix tracks each capability **independently**. Access to data does
**not** imply the right to retain, publish, or redistribute it.

Capabilities (each tracked separately):

- `ingest_use` — may LadybugBets ingest and use the data internally?
- `cache` — may LadybugBets cache it?
- `retain_historical` — may LadybugBets build/retain historical datasets from it?
- `derive_calculations` — may LadybugBets compute derived values from it?
- `public_display` — may LadybugBets show it publicly?
- `redistribute_raw` — may LadybugBets redistribute the raw source data?
- `redistribute_derived` — may LadybugBets redistribute derived data?

Each capability uses a **controlled posture** and nothing else:

- `ALLOWED`
- `PROHIBITED`
- `UNKNOWN`

### Explicit non-implication

Do not assume that the right to access data implies:

- the right to **retain** it,
- the right to **publish** it,
- the right to **redistribute** it,
- the right to build **historical datasets** from it.

Each is a separate posture and must be independently established.

## Fail-closed publication

> If `public_display` is `UNKNOWN`, public publication must **fail closed**.

Only an explicit `ALLOWED` posture permits the corresponding use. `UNKNOWN` is
treated as "not permitted" for publication and for any other capability whose
absence would create legal or ethical exposure. `PROHIBITED` obviously blocks the
use. This mirrors the publication policy principle that an ungoverned value must
not be published (see [PUBLICATION_POLICY.md](PUBLICATION_POLICY.md)).

## Scope boundary

- **Sprint 1** defines the Source Profile and rights model only.
- **Actual provider qualification** — filling in a real provider's profile,
  reviewing real terms, and setting real postures — belongs to **Sprint 2**.
- The public repository holds **structure and public-safe governance metadata
  only**. Secrets, API keys, credentials, commercial pricing, private contracts,
  affiliate schedules, negotiated terms, and non-public correspondence are never
  committed (DEC-010).
