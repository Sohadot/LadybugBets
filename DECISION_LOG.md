# DECISION LOG

Durable decisions for LadybugBets. Each entry has an ID, a date, a status, and a
statement. Decisions are recorded so future work does not re-invent settled
foundations.

- **Status values:** `Ratified` (agreed and in force), `Deferred` (explicitly
  postponed to a later governance decision).
- Sprint 0 decisions (DEC-001 – DEC-014) and Sprint 1 decisions
  (DEC-015 – DEC-021) are all dated **2026-09-21**.

| ID | Date | Status | Decision |
| --- | --- | --- | --- |
| DEC-001 | 2026-09-21 | Ratified | LadybugBets is positioned as a betting-intelligence and probability-discovery platform, not a sportsbook operation. It does not accept, transmit, or settle wagers, and it does not custody funds. |
| DEC-002 | 2026-09-21 | Ratified | The **Spot** is adopted as the primary analytical object of LadybugBets — an observed, governed, explainable market condition, distinct from "the bet". |
| DEC-003 | 2026-09-21 | Ratified | Spot Ontology v0.1 contains six Spot classes: Price, Movement, Probability, Consensus, Closing, and Personal. |
| DEC-004 | 2026-09-21 | Ratified | Source observations and derived calculations must remain semantically distinct; derived values must never be stored or published as source facts. |
| DEC-005 | 2026-09-21 | Ratified | The initial MVP is constrained to three public product surfaces: SpotBoard, Probability Lab, and Market Movement. |
| DEC-006 | 2026-09-21 | Ratified | The initial sport scope is football/soccer; the English Premier League is the initial competition candidate. This is a product-scope decision only, not a data-license or vendor decision. |
| DEC-007 | 2026-09-21 | Ratified | MVP v0.1 includes no betting execution, no funds custody, no guaranteed-win positioning, and no opaque recommendation engine. |
| DEC-008 | 2026-09-21 | Ratified | Historical observations should be preserved when technically and contractually permitted, because temporal price movement is a first-class analytical property. |
| DEC-009 | 2026-09-21 | Ratified | No data vendor, database, monetization provider, pricing model, affiliate operator, or infrastructure vendor is ratified in Sprint 0. |
| DEC-010 | 2026-09-21 | Ratified | The public repository must not contain secrets or sensitive internal commercial information. |
| DEC-011 | 2026-09-21 | Deferred | The closing-price policy (definition of "closing"/"near-closing", timing, and source rules) that the Closing Spot depends on requires a later governance decision before implementation. |
| DEC-012 | 2026-09-21 | Deferred | No "edge score" or numerical scoring system is ratified; introducing one requires a later, explicit governance decision. |
| DEC-013 | 2026-09-21 | Ratified | **Observation Provenance Dimensions.** LadybugBets treats upstream provider identity, quoted bookmaker/operator identity, canonical LadybugBets metadata, source-observed time, ingestion time, and derived calculations as distinct semantic dimensions. They must not be silently conflated. In particular, provider diversity is not bookmaker/operator diversity, ingestion time is not source-observed (quote) time, and overround is a price-derived implied margin measure, not a measurement of realized operator margin. |
| DEC-014 | 2026-09-21 | Ratified | **Raw Identity vs Canonical Identity.** LadybugBets preserves source-asserted entity identities separately from LadybugBets canonical identities. Provider-native operator identifiers or labels (and likewise raw event, competition, market, outcome, start-time, and jurisdiction forms) must not be silently treated as canonical identity. Cross-provider comparison, consensus, and movement depend on governed canonical identity resolution. The identity-resolution algorithm itself is not ratified here and remains deferred to Sprint 1. |
| DEC-015 | 2026-09-21 | Ratified | **LBOC-001 Observation Contract v1.0.0.** LadybugBets adopts a vendor-neutral governed observation envelope (contract / provenance / source-asserted / canonical / governance sections) and a three-state integrity admission model — `ADMITTED`, `QUARANTINED`, `REJECTED` — with a controlled categorical reason-code vocabulary (not scores). Records are never silently discarded. See [docs/OBSERVATION_CONTRACT.md](docs/OBSERVATION_CONTRACT.md). |
| DEC-016 | 2026-09-21 | Ratified | **Fail-Closed Identity Resolution (LBIR-001).** No guess becomes identity. Raw identity resolves to canonical identity only through governed deterministic evidence (existing governed mapping or curated alias already in the registry). Fuzzy/approximate/embedding/AI similarity must not create canonical identity automatically. Zero mappings → unresolved; more than one candidate → ambiguous; both fail closed. See [docs/IDENTITY_RESOLUTION.md](docs/IDENTITY_RESOLUTION.md). |
| DEC-017 | 2026-09-21 | Ratified | **Participant-Bearing Event Identity.** Governed event identity depends on canonical participant identity in addition to canonical sport/competition/time context. Raw and canonical participant forms remain distinct. No teams database or real team registry is built or populated in Sprint 1 (synthetic participants only). |
| DEC-018 | 2026-09-21 | Ratified | **Admission Is Not Publication Authorization.** Semantic admission (structural/semantic sufficiency) and source-rights/publication authorization are separate gates. An observation may be `ADMITTED` internally while public display is blocked. Where public-display rights are `UNKNOWN`, public publication fails closed. See [docs/SOURCE_GOVERNANCE.md](docs/SOURCE_GOVERNANCE.md). |
| DEC-019 | 2026-09-21 | Ratified | **Provenance-Preserving Conflict and Correction.** Duplicates require demonstrated same source assertion (not merely matching canonical identity + price); different providers are separate provenance paths. Same-provider incompatible assertions are retained, never silently last-write-wins. Corrections are append-only via `supersedes_observation_id`, and superseded records remain traceable. Provider precedence is not ratified. See [docs/CONFLICT_AND_DEDUPLICATION.md](docs/CONFLICT_AND_DEDUPLICATION.md). |
| DEC-020 | 2026-09-21 | Ratified | **Temporal Evidence and Freshness.** Source-observed time and ingestion time remain distinct; `ingested_at` cannot silently substitute for source quote time, and an observation lacking adequate source-observed timing cannot support a source-time Movement claim. Freshness exists only under an explicitly named governed policy; `current`/`live`/`fresh`/`stale` are not intrinsic source facts; no universal numeric freshness threshold is ratified. See [docs/TEMPORAL_GOVERNANCE.md](docs/TEMPORAL_GOVERNANCE.md). |
| DEC-021 | 2026-09-21 | Ratified | **Derived Values Reference Source Observations.** Derived analytical outputs (implied/normalized probability, movement, consensus, future closing comparison) must reference governed source `observation_id`(s) and must not overwrite source fields or masquerade as source assertions. This reinforces DEC-004; derived values never appear inside the source observation envelope. |

## Deferred / open questions

- **DEC-011** — Closing-price policy is intentionally unresolved (see
  [docs/SPOT_ONTOLOGY.md](docs/SPOT_ONTOLOGY.md)). **Remains Deferred** through
  Sprint 1; no closing price is defined.
- **DEC-012** — Any numerical scoring / "edge score" is intentionally unresolved
  (see [docs/METHODOLOGY.md](docs/METHODOLOGY.md)). **Remains Deferred** through
  Sprint 1; no scoring is introduced.
- Data vendor, database, and infrastructure choices remain open by DEC-009 and
  are out of scope for Sprint 0 and Sprint 1.
- **Sprint 1 deferrals within LBIR-001 / conflict governance:** provider
  precedence between disagreeing providers, and any timing tolerance for event
  merge, are **not** ratified and await later evidence. The `observation_id`
  minting algorithm is likewise not ratified.
