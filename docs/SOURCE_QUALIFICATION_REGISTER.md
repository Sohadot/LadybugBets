# SOURCE QUALIFICATION REGISTER
Version: 1.1.0 · Reviewed: 2026-09-21

*Public register of evidence-backed, capability-specific source qualification.*
Governed by [LBSQ-001](SOURCE_QUALIFICATION_STANDARD.md). **No numerical score,
no ranking, no "best" — no final vendor is selected.** Providers are listed
**alphabetically**. Capability outcomes are `QUALIFIED` / `NOT_QUALIFIED` /
`UNRESOLVED`, derived deterministically from the recorded evidence.

Capability legend: **CPO** = Current Price Observation · **PSB** = Public
SpotBoard · **DPD** = Derived Probability Display · **STM** = Source-Time Market
Movement · **HDR** = Historical Dataset Retention · **RDR** = Raw Data
Redistribution.

Investigation depth: **fully investigated** = The Odds API, Sportmonks,
Sportradar; **partially investigated** = Betfair Exchange (accessible primary
support pages only; deeper API reference pages were not retrievable this sprint).

---

## Betfair Exchange API — partially investigated
Checked 2026-09-21 · Evidence: [`betfair-exchange.evidence.json`](../evidence/source-qualification/betfair-exchange.evidence.json) · Qualification: [`betfair-exchange.qualification.json`](../evidence/source-qualification/betfair-exchange.qualification.json) · Pricing access: UNKNOWN

- Football technical: **VERIFIED** (Soccer = EventTypeId 1) · EPL: **NOT_VERIFIED** · Operator-level: **VERIFIED** · **Operator diversity: UNSUPPORTED** (single exchange operator — Betfair) · Event/market id: **VERIFIED** · Outcome id: **NOT_VERIFIED** · Source timestamp: **NOT_VERIFIED** · Historical: **NOT_VERIFIED**
- Rights — retain-historical: **UNKNOWN** · public-display: **UNKNOWN** · derived-calculations: **UNKNOWN** · raw-redistribution: **UNKNOWN**
- Capabilities — CPO: UNRESOLVED · **PSB: NOT_QUALIFIED** · DPD: UNRESOLVED · STM: UNRESOLVED · HDR: UNRESOLVED · RDR: UNRESOLVED
- Key blockers: single-operator source (multi-operator UNSUPPORTED) cannot support an operator-diverse SpotBoard/Consensus (DEC-013); data-use rights not established by public evidence (a required vendor licence is not itself a granted right); EPL competition, outcome identifiers, timestamps, historical, and limits not confirmable from accessible pages.

## Sportmonks — fully investigated
Checked 2026-09-21 · Evidence: [`sportmonks.evidence.json`](../evidence/source-qualification/sportmonks.evidence.json) · Qualification: [`sportmonks.qualification.json`](../evidence/source-qualification/sportmonks.qualification.json) · Pricing access: PUBLIC_PLAN

- EPL: **VERIFIED** · Operator-level: **VERIFIED** (`bookmaker_id`) · **Operator diversity: VERIFIED** (120+ bookmakers) · Source timestamp: **VERIFIED** (`latest_bookmaker_update`) · Historical: **VERIFIED** (limited window, ~7 days post kick-off)
- Rights — retain-historical: **ALLOWED** · public-display: **UNKNOWN** · derived-calculations: **ALLOWED** · raw-redistribution: **UNKNOWN** (distribution/transfer/storage allowed; only resale-without-approval is clearly prohibited, which does not establish the broad right either way — fail closed)
- Capabilities — CPO: QUALIFIED · PSB: UNRESOLVED · DPD: UNRESOLVED · STM: QUALIFIED · HDR: QUALIFIED · RDR: UNRESOLVED
- Key blockers: public display of the odds data not explicitly established by the public Terms (fails closed); Terms page shows no effective date (revalidate).

## Sportradar — fully investigated
Checked 2026-09-21 · Evidence: [`sportradar.evidence.json`](../evidence/source-qualification/sportradar.evidence.json) · Qualification: [`sportradar.qualification.json`](../evidence/source-qualification/sportradar.qualification.json) · Pricing access: CONTACT_SALES

- Football: **VERIFIED** · EPL: **NOT_VERIFIED** · Operator-level: **VERIFIED** · **Operator diversity: VERIFIED** (Odds Comparison, 140+ bookmakers) · Source timestamp: **NOT_VERIFIED** · Historical: **NOT_VERIFIED**
- Rights — all **UNKNOWN** (B2B, contract-governed)
- Capabilities — CPO: UNRESOLVED · PSB: UNRESOLVED · DPD: UNRESOLVED · STM: UNRESOLVED · HDR: UNRESOLVED · RDR: UNRESOLVED
- Key blockers: contract-governed rights — no public evidence establishes any ALLOWED right (fails closed); EPL/operator-field/market/outcome/timestamp specifics not confirmed from accessible public docs.

## The Odds API — fully investigated
Checked 2026-09-21 · Evidence: [`the-odds-api.evidence.json`](../evidence/source-qualification/the-odds-api.evidence.json) · Qualification: [`the-odds-api.qualification.json`](../evidence/source-qualification/the-odds-api.qualification.json) · Pricing access: PUBLIC_PLAN

- EPL: **VERIFIED** · Operator-level: **VERIFIED** (bookmaker `key`/`title`) · **Operator diversity: VERIFIED** (many bookmakers by region) · Source timestamp: **VERIFIED** (`last_update` = the last time The Odds API's system saw the bookmaker market; provider-observed, not bookmaker-originated) · Historical: **VERIFIED** (from 2020-06-06)
- Rights — retain-historical: **ALLOWED** · public-display: **ALLOWED** · derived-calculations: **ALLOWED** · raw-redistribution: **PROHIBITED** — all permitted uses are conditional: *"provided The Odds API data is not the primary product being sold or redistributed"*
- Capabilities — CPO: QUALIFIED · PSB: QUALIFIED · DPD: QUALIFIED · STM: QUALIFIED · HDR: QUALIFIED · RDR: NOT_QUALIFIED
- Key blockers: raw redistribution as a standalone data product is prohibited (acceptable for the consumer MVP). Open question: redistribution (not display) of derived data is UNKNOWN. The permitted-use condition above applies to all uses.

---

## Discovered but not fully investigated

Recorded for completeness; **not** qualified because primary evidence was not
established this sprint. Discovery-only mentions are candidates, not endorsements.

- **API-Football (api-sports.io / api-football.com)** — self-serve football + odds
  API; primary documentation and Terms pages were not retrievable in this
  environment (HTTP 403), so no primary rights/technical evidence could be
  committed.
- **SportsDataIO (sportsdata.io)** — soccer/odds API with a historical data
  warehouse; developer docs are JS-rendered (no field-level evidence), and the
  public site Terms are a general website ToS (not a data licence).
- **OddsPapi, SportsGameOdds, and similar self-serve odds APIs** — surfaced via
  secondary pages; per DEC-023, secondary sources cannot establish rights.

## What this register is not

It does not rank providers, does not compute a score, and does not select a
vendor. A provider `QUALIFIED` for a capability is an **evidence outcome for that
capability**, not a recommendation to procure. Procurement, licence review, and
integration are explicitly out of scope (Sprint 3+).
