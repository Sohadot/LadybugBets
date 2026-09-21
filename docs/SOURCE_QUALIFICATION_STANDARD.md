# LBSQ-001 — LadybugBets Source Qualification Standard
Version: 1.0.0

*How LadybugBets decides which external data sources are compatible with its
governance — capability by capability, backed by evidence.*

This standard is the evidence-backed qualification layer promised by Sprint 1's
[SOURCE_GOVERNANCE.md](SOURCE_GOVERNANCE.md). It is **not** vendor procurement,
**not** API integration, and **not** a legal opinion. It performs operational
source-governance qualification from **public, official, primary-source
evidence** as of a dated review.

## Governing principles

- **Access to data is not permission to use data in every way.**
- **Technical availability is not contractual authorization.**
- **Vendor suitability is capability-specific, not a single global score.**

There is **no numerical vendor score, no ranking, and no "best provider".** A
provider can be qualified for one LadybugBets capability and unresolved or not
qualified for another; that is the expected, correct shape of the output.

## Three adjacent layers (not collapsed)

| Layer | Question | Artifact |
| --- | --- | --- |
| **Source Profile** (Sprint 1) | Who is the provider + governed rights posture? | [`contracts/source-profile.schema.json`](../contracts/source-profile.schema.json) |
| **Source Evidence** (this sprint) | What official evidence supports each claim? | [`contracts/source-evidence.schema.json`](../contracts/source-evidence.schema.json), [SOURCE_EVIDENCE_POLICY.md](SOURCE_EVIDENCE_POLICY.md) |
| **Source Qualification** (this sprint) | What LadybugBets capabilities does that evidence permit? | [`contracts/source-qualification.schema.json`](../contracts/source-qualification.schema.json) |

The Sprint 1 rights vocabulary is preserved unchanged; the qualification layer is
adjacent, not competing.

## Technical evidence posture (non-numeric)

Each documented technical capability carries exactly one posture:

- **VERIFIED** — official current evidence explicitly supports the technical claim.
- **NOT_VERIFIED** — research did not establish the claim. *Absence of
  documentation is normally NOT_VERIFIED, not UNSUPPORTED.*
- **UNSUPPORTED** — official evidence explicitly indicates the capability is
  absent/unavailable.
- **CONFLICTING** — official sources materially disagree and cannot be safely
  reconciled.

## Rights posture (unchanged from Sprint 1)

Each rights capability carries exactly one posture: **ALLOWED**, **PROHIBITED**,
or **UNKNOWN**. There is no "probably allowed". The seven rights dimensions
(`ingest_use`, `cache`, `retain_historical`, `derive_calculations`,
`public_display`, `redistribute_raw`, `redistribute_derived`) are **independent**;
one being ALLOWED never implies another. If permission is not explicit,
**UNKNOWN**, and UNKNOWN **fails closed** (DEC-024).

## Primary-source rule (DEC-023)

Material technical and rights claims require **current primary provider
evidence** — official Terms/Legal, API/product documentation, official coverage,
pricing or FAQ/support pages. Secondary sources (blogs, marketplaces, reviews)
may be used **only to discover candidates**; they may **never** establish ALLOWED
rights, PROHIBITED rights, retention, display, or redistribution permission. Do
not infer permission from silence.

## Evidence-dated qualification (DEC-026)

Every evidence item records a `retrieved_at` date and, where the page states one,
a `source_effective_date`. Qualification is tied to that dated evidence: provider
terms and capabilities can change, so **production use requires revalidation
against current evidence**, and a changed official source invalidates stale
assumptions. **No universal expiry interval is ratified.**

## Capabilities (independently qualified)

Each capability × provider receives exactly one outcome: **QUALIFIED**,
**NOT_QUALIFIED**, or **UNRESOLVED**.

- **QUALIFIED** — every required technical and rights gate for that specific
  capability is satisfied.
- **NOT_QUALIFIED** — at least one required technical is UNSUPPORTED, or at least
  one required right is PROHIBITED (an explicit blocker).
- **UNRESOLVED** — required evidence is missing, unclear, conflicting, or carries
  UNKNOWN / NOT_VERIFIED posture. Fail closed.

### A. CURRENT_PRICE_OBSERVATION
Required VERIFIED: `football_coverage`, `epl_coverage`, `operator_level_prices`,
`stable_event_identifier`, `operator_identifier_or_stable_label`,
`market_identifier_or_stable_key`, `outcome_identifier_or_stable_key`.
Required ALLOWED: `ingest_use`. (Public display is evaluated separately.)

### B. PUBLIC_SPOTBOARD
Requires **A = QUALIFIED**, `public_display = ALLOWED`, and
`multi_operator_coverage = VERIFIED` (operator diversity, below). If
`public_display` is UNKNOWN → UNRESOLVED (fail closed); if
`multi_operator_coverage` is UNSUPPORTED → NOT_QUALIFIED.

### C. DERIVED_PROBABILITY_DISPLAY
Requires **A = QUALIFIED**, `derive_calculations = ALLOWED`, and
`public_display = ALLOWED` (to publicly show the permitted derived output). If
derived-public-display rights are unclear → fail closed.

### D. SOURCE_TIME_MARKET_MOVEMENT
Requires `operator_level_prices` and `operator_identifier_or_stable_label` and
`source_observed_timestamp` and `stable_event_identifier` and market/outcome keys
all **VERIFIED**, plus `ingest_use` and `retain_historical` **ALLOWED**.
**Cannot be QUALIFIED if `source_observed_timestamp != VERIFIED`.** `ingested_at`
availability alone never satisfies this.

### E. HISTORICAL_DATASET_RETENTION
Requires `ingest_use` and `retain_historical` **ALLOWED**. **Availability of a
historical endpoint alone does not satisfy this** — retention is a rights
question (DEC-024).

### F. RAW_DATA_REDISTRIBUTION
Requires `redistribute_raw` and `ingest_use` **ALLOWED**. **Not required for the
consumer MVP**; a provider may be excellent for LadybugBets while raw
redistribution is PROHIBITED, and that is not an automatic disqualification.

## Operator diversity gate (`multi_operator_coverage`)

`multi_operator_coverage` is a technical posture (VERIFIED / NOT_VERIFIED /
UNSUPPORTED / CONFLICTING) that machine-encodes the DEC-013 operator-diversity
law — it is an **implementation** of DEC-013 + LBSQ-001, not a new decision.

- **VERIFIED** — official evidence establishes multiple distinct quoted
  operators/bookmakers.
- **UNSUPPORTED** — official evidence establishes that the source exposes only
  **one** quoted operator (e.g. a single exchange).
- **NOT_VERIFIED** — research did not establish either state.

This is **not** provider diversity; provider identity remains distinct from
operator identity. `CURRENT_PRICE_OBSERVATION` does **not** require it (a
single-operator source can still produce governed Price observations), and
`SOURCE_TIME_MARKET_MOVEMENT` does **not** require it (movement is computed per
one canonical operator over time). `PUBLIC_SPOTBOARD` (and any future
multi-operator Consensus capability) **does** require
`multi_operator_coverage = VERIFIED`.

## Deterministic derivation (no hand-typed verdicts)

Capability outcomes are **computed** from the technical and rights matrices by
`derive_capabilities` in
[`governance/validate_source_qualification.py`](../governance/validate_source_qualification.py).
A committed outcome that disagrees with the derived outcome **fails validation**
(`CAPABILITY_DERIVATION_MISMATCH`). A capability is never QUALIFIED because a
reviewer felt a vendor "seems suitable". The rules are explicit, testable, and
carry **no weights and no score**.

## Evidence-to-qualification traceability (DEC-025 support)

Every VERIFIED/UNSUPPORTED/CONFLICTING technical and every ALLOWED/PROHIBITED
right must be backed by a referenced evidence item whose `claim_key` and posture
match. UNKNOWN and NOT_VERIFIED need no evidence — they are the absence of
establishment.

A capability committed **QUALIFIED** must be machine-traceable to an evidence
item for **every** required gate: for each required VERIFIED technical and each
required ALLOWED right (including inherited gates), the capability's
`evidence_ids` must include an item with the matching `claim_key` and posture, or
validation fails (`CAPABILITY_EVIDENCE_INCOMPLETE`). NOT_QUALIFIED / UNRESOLVED
capabilities may reference only the evidence relevant to their blocker/unresolved
condition. The capability gate map lives in one place
(`CAPABILITY_REQUIREMENTS`) and drives both derivation and completeness so the
two cannot diverge.

## Provider/bundle binding

A qualification record is bound to exactly one evidence bundle: `provider_id`,
`provider_name`, and `official_domains` must match the bundle, and every evidence
item must carry the same `provider_id`. Evidence from another governed provider
identity can never satisfy a qualification, even if `claim_key` and posture
match.

## Timestamp qualification

`source_observed_timestamp` is only VERIFIED when official documentation defines a
timestamp as the **time/state of the quoted market observation** (e.g. a
per-bookmaker last-update time, or the explicit state time of a historical
snapshot). A generic "API response generated_at" is **not** a source-observed
time. If unclear → NOT_VERIFIED. Do not guess. (Preserves the Sprint 1 rule that
ingestion time ≠ source quote time.)

## Historical data — four separate questions

For every provider, keep these distinct and never let one answer another:

1. Is historical data **technically available**? (`historical_odds_access`)
2. May LadybugBets **retain** it? (`retain_historical`)
3. May LadybugBets **publicly display** it? (`public_display`)
4. May LadybugBets **redistribute** it? (`redistribute_raw` / `redistribute_derived`)

## Operator identity (DEC-013 preserved)

The quoted operator/bookmaker must remain distinct from the upstream provider. A
source that supplies only an aggregated consensus price with no attributable
operator identity, or that supplies a **single** operator's prices, cannot on its
own support governed operator-level SpotBoard/Consensus diversity. Provider
diversity ≠ operator diversity. Such limitations are recorded as blockers.

## Event identity

Providers expose **raw/source** event components (event id, competition,
home/away participants, start time). A provider event id is **never** a
LadybugBets canonical id (LBIR-001). Sprint 2 records raw identity availability
only; it does not build cross-provider canonical mappings or a team registry.

## No legal overclaiming (DEC-023 posture)

Findings use wording such as "the currently published terms state…", "official
documentation explicitly permits…", "public evidence did not establish…". This is
operational governance, not a legal opinion, and never asserts an absolute legal
right the evidence does not support.

## Out of scope for Sprint 2

No final vendor selection, no subscription, no account, no credentials, no
authenticated calls, no production ingestion, no adapters, no database, no UI, no
Sprint 3. The output is **evidence + qualification**, not procurement (DEC-022).
