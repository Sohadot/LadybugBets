# SOURCE QUALIFICATION REGISTER
Version: 1.0.0 · Reviewed: 2026-09-21

*Public register of evidence-backed, capability-specific source qualification.*
Governed by [LBSQ-001](SOURCE_QUALIFICATION_STANDARD.md). **No numerical score,
no ranking, no "best" — no final vendor is selected.** Providers are listed
**alphabetically**. Capability outcomes are `QUALIFIED` / `NOT_QUALIFIED` /
`UNRESOLVED`, derived deterministically from the recorded evidence.

Capability legend: **CPO** = Current Price Observation · **PSB** = Public
SpotBoard · **DPD** = Derived Probability Display · **STM** = Source-Time Market
Movement · **HDR** = Historical Dataset Retention · **RDR** = Raw Data
Redistribution.

---

## Betfair Exchange API
Checked 2026-09-21 · Evidence: [`betfair-exchange.evidence.json`](../evidence/source-qualification/betfair-exchange.evidence.json) · Qualification: [`betfair-exchange.qualification.json`](../evidence/source-qualification/betfair-exchange.qualification.json) · Pricing access: UNKNOWN

- EPL technical: **NOT_VERIFIED** · Operator-level: **VERIFIED** (but a **single** operator — Betfair's own exchange) · Source timestamp: **NOT_VERIFIED** · Historical availability: **NOT_VERIFIED**
- Rights — retain-historical: **UNKNOWN** · public-display: **UNKNOWN** · derived-calculations: **UNKNOWN** · raw-redistribution: **UNKNOWN**
- Capabilities — CPO: UNRESOLVED · PSB: UNRESOLVED · DPD: UNRESOLVED · STM: UNRESOLVED · HDR: UNRESOLVED · RDR: UNRESOLVED
- Key blockers: single-operator source cannot supply multi-operator diversity for governed Consensus/SpotBoard (DEC-013); data-use rights not established by public evidence (commercial use reportedly needs a licensed-vendor arrangement); deeper API reference pages were not retrievable this sprint.

## Sportmonks
Checked 2026-09-21 · Evidence: [`sportmonks.evidence.json`](../evidence/source-qualification/sportmonks.evidence.json) · Qualification: [`sportmonks.qualification.json`](../evidence/source-qualification/sportmonks.qualification.json) · Pricing access: PUBLIC_PLAN

- EPL technical: **VERIFIED** · Operator-level: **VERIFIED** (`bookmaker_id`, 120+ bookmakers) · Source timestamp: **VERIFIED** (`latest_bookmaker_update`) · Historical availability: **VERIFIED** (limited window, ~7 days post kick-off)
- Rights — retain-historical: **ALLOWED** · public-display: **UNKNOWN** · derived-calculations: **ALLOWED** · raw-redistribution: **PROHIBITED**
- Capabilities — CPO: QUALIFIED · PSB: UNRESOLVED · DPD: UNRESOLVED · STM: QUALIFIED · HDR: QUALIFIED · RDR: NOT_QUALIFIED
- Key blockers: public display of the odds data not explicitly established by the public Terms (fails closed); raw redistribution prohibited without written approval; Terms page shows no effective date (revalidate).

## Sportradar
Checked 2026-09-21 · Evidence: [`sportradar.evidence.json`](../evidence/source-qualification/sportradar.evidence.json) · Qualification: [`sportradar.qualification.json`](../evidence/source-qualification/sportradar.qualification.json) · Pricing access: CONTACT_SALES

- EPL technical: **NOT_VERIFIED** · Operator-level: **VERIFIED** (Odds Comparison, 140+ bookmakers) · Source timestamp: **NOT_VERIFIED** · Historical availability: **NOT_VERIFIED**
- Rights — retain-historical: **UNKNOWN** · public-display: **UNKNOWN** · derived-calculations: **UNKNOWN** · raw-redistribution: **UNKNOWN**
- Capabilities — CPO: UNRESOLVED · PSB: UNRESOLVED · DPD: UNRESOLVED · STM: UNRESOLVED · HDR: UNRESOLVED · RDR: UNRESOLVED
- Key blockers: B2B, contract-governed rights — no public evidence establishes any ALLOWED right (fails closed); EPL/operator-field/market/outcome/timestamp specifics not confirmed from accessible public docs.

## The Odds API
Checked 2026-09-21 · Evidence: [`the-odds-api.evidence.json`](../evidence/source-qualification/the-odds-api.evidence.json) · Qualification: [`the-odds-api.qualification.json`](../evidence/source-qualification/the-odds-api.qualification.json) · Pricing access: PUBLIC_PLAN

- EPL technical: **VERIFIED** · Operator-level: **VERIFIED** (bookmaker `key`/`title`) · Source timestamp: **VERIFIED** (`last_update` + historical snapshot state time) · Historical availability: **VERIFIED** (from 2020-06-06)
- Rights — retain-historical: **ALLOWED** · public-display: **ALLOWED** · derived-calculations: **ALLOWED** · raw-redistribution: **PROHIBITED**
- Capabilities — CPO: QUALIFIED · PSB: QUALIFIED · DPD: QUALIFIED · STM: QUALIFIED · HDR: QUALIFIED · RDR: NOT_QUALIFIED
- Key blockers: raw redistribution as a standalone data product is prohibited (acceptable for the consumer MVP, which does not redistribute raw feeds). Open question: redistribution (not display) of derived data is UNKNOWN.

---

## Discovered but not fully investigated

Recorded for completeness; **not** qualified because primary evidence was not
established this sprint. Discovery-only mentions are candidates, not endorsements.

- **API-Football (api-sports.io / api-football.com)** — self-serve football + odds
  API with bookmaker odds and long historical coverage; primary documentation and
  Terms pages were not retrievable in this environment (HTTP 403), so no primary
  rights/technical evidence could be committed.
- **SportsDataIO (sportsdata.io)** — soccer/odds API with a historical data
  warehouse; developer docs are JS-rendered and did not expose field-level
  evidence, and the public site Terms are a general website ToS (not a data
  licence), so commercial-use/retention/display rights were UNKNOWN from public
  evidence.
- **OddsPapi, SportsGameOdds, and similar self-serve odds APIs** — surfaced during
  discovery via marketing/secondary pages; per DEC-023, secondary sources cannot
  establish rights, so these remain discovery-only pending primary-source review.

## What this register is not

It does not rank providers, does not compute a score, and does not select a
vendor. A provider `QUALIFIED` for a capability is an **evidence outcome for that
capability**, not a recommendation to procure. Procurement, licence review, and
integration are explicitly out of scope (Sprint 3+).
