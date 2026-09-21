# DECISION LOG

Durable decisions for LadybugBets. Each entry has an ID, a date, a status, and a
statement. Decisions are recorded so future work does not re-invent settled
foundations.

- **Status values:** `Ratified` (agreed and in force), `Deferred` (explicitly
  postponed to a later governance decision).
- All Sprint 0 decisions below are dated **2026-09-21**.

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

## Deferred / open questions

- **DEC-011** — Closing-price policy is intentionally unresolved (see
  [docs/SPOT_ONTOLOGY.md](docs/SPOT_ONTOLOGY.md)).
- **DEC-012** — Any numerical scoring / "edge score" is intentionally unresolved
  (see [docs/METHODOLOGY.md](docs/METHODOLOGY.md)).
- Data vendor, database, and infrastructure choices remain open by DEC-009 and
  are out of scope for Sprint 0.
