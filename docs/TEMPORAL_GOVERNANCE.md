# TEMPORAL GOVERNANCE
Version: 1.0.0

*Governed temporal evidence for Price, Movement, and future Closing analysis.*

This document ratifies how LadybugBets treats time in the observation contract
([LBOC-001](OBSERVATION_CONTRACT.md)). It preserves every Sprint 0 temporal
distinction and adds the rules needed before temporal analysis may proceed.

## The four temporal values

| Value | Dimension | Meaning |
| --- | --- | --- |
| `source_start_time` | Source-asserted | Scheduled event start exactly as the source asserts it, including its stated offset. |
| `source_observed_at` | Source-asserted (may be absent) | The time at which the quoted market state applied **according to the source**, when the source provides a trustworthy one. |
| `ingested_at` | Ingestion/provenance | The time LadybugBets received or recorded the observation. |
| `start_time` (canonical) | Canonical/normalized | A **lossless** canonical representation of the *same instant* as `source_start_time` (e.g. UTC-normalized), for cross-source alignment. |

**Core integrity rule (DEC-020):** `source_observed_at` and `ingested_at` are
distinct and are never conflated. `ingested_at` is **not** the bookmaker's quote
time.

## Price observation

A Price Spot-compatible source observation **MAY** be structurally **ADMITTED**
when `source_observed_at` is unavailable, provided:

- `ingested_at` exists;
- the missing source time is **explicit** (recorded as absent, not filled in);
- `ingested_at` is **not** represented as the bookmaker's quote time.

This lets LadybugBets admit a current price whose source-time is unknown, without
inventing precision it does not have.

## Movement eligibility

Movement analysis requires a **governed temporal basis**.

For Sprint 1:

- `ingested_at` alone **MUST NOT** silently substitute for source quote time.
- A source observation without adequate source-observed timing **must not** be
  used to claim source-time market movement.

In other words: an observation may be admitted as a Price observation with only
`ingested_at`, but that same observation does **not** by itself satisfy the
temporal basis for a source-time Movement claim. Do not create fake precision.

Movement comparability also requires the same canonical event/market/outcome and
the same canonical operator identity (see
[SPOT_ONTOLOGY.md](SPOT_ONTOLOGY.md)); temporal adequacy is an **additional**
requirement, not a replacement for identity comparability.

## Closing analysis

**DEC-011 remains Deferred.** The definition of a closing / near-closing
reference price is not ratified. This document does **not** define closing price
and introduces no closing timing rule.

## Freshness

Freshness is **not** an intrinsic property of a source observation, and **no
universal numeric threshold** (e.g. "X minutes = fresh") is ratified in Sprint 1.

Ratified instead (DEC-020):

- Freshness is derived under an **explicitly named policy**.
- The labels `current`, `live`, `fresh`, and `stale` are **not** intrinsic source
  facts; they are policy-derived interpretations.
- A surface **must** have a governed freshness policy before using any of those
  labels.
- **No numeric freshness threshold is ratified in Sprint 1.**

This allows later source-specific or product-specific freshness policies without
corrupting provenance: the underlying observation keeps its true timestamps, and
any freshness label is attributed to the named policy that produced it.

## Summary of temporal fail-closed behavior

- Missing `source_observed_at` → Price admission still possible; Movement
  source-time claims are not.
- Materially conflicting scheduled times without a governed mapping → not merged
  (see [IDENTITY_RESOLUTION.md](IDENTITY_RESOLUTION.md)); may be quarantined with
  `TEMPORAL_AMBIGUITY` or an identity reason code.
- No timestamp is ever fabricated, and `ingested_at` is never relabeled as source
  quote time.
