# SOURCE EVIDENCE POLICY
Version: 1.0.0

*What counts as acceptable qualification evidence.* Part of
[LBSQ-001](SOURCE_QUALIFICATION_STANDARD.md). Machine form:
[`contracts/source-evidence.schema.json`](../contracts/source-evidence.schema.json).

## Required fields for every committed evidence item

- `evidence_id` — unique within the bundle.
- `provider_id` — the governed LadybugBets identity of the provider.
- `source_url` — the exact official URL (HTTPS, on an official domain).
- `source_title` — the page/document title.
- `source_type` — one of `TERMS`, `LEGAL`, `API_DOCS`, `PRODUCT_DOCS`,
  `COVERAGE`, `PRICING`, `FAQ`, `SUPPORT`.
- `retrieved_at` — the date the source was retrieved.
- `publisher_domain` — the publishing domain (must be an official domain).
- `claim_key` — the stable key of the claim this evidence supports.
- `claim_summary` — a concise paraphrase (**not** a copy of the Terms).
- `source_effective_date` — the page's stated effective/last-updated/revision
  date when available, else null.
- `technical_posture` / `rights_posture` — the posture this evidence supports, or
  null for a purely descriptive item.
- `excerpt` — optional, minimal verbatim quote only when necessary (kept short).
- `notes` — optional clarification.

## Source precedence

Prefer primary provider sources in this order: (1) Terms/ToS, (2) legal/licensing
pages, (3) API documentation, (4) product documentation, (5) coverage pages,
(6) pricing/plan pages, (7) FAQ/support. Secondary sources may **discover**
candidates but must never establish rights (DEC-023).

## Terms-vs-product-page precedence and conflicts (DEC-023 posture)

- If product docs say "historical odds available" but the Terms do not establish
  retention, then `historical_odds_access` may be VERIFIED while
  `retain_historical` stays UNKNOWN.
- If marketing implies broad commercial use but the Terms contain a narrower
  restriction, record the conflict and **fail closed**; do not resolve a material
  contradiction in the provider's favour or against it without evidence. Where
  official sources materially disagree, the posture is **CONFLICTING**, and both
  sources are recorded.

## Freshness and dates (DEC-026)

Every item records `retrieved_at`; capture the page's own effective/last-updated
date in `source_effective_date` when shown. Older evidence is **not** removed
merely because a newer page exists within the same sprint. No numeric expiry
threshold is ratified; production use requires revalidation against current terms.

## Claim granularity

Avoid broad claims like "Provider X supports everything LadybugBets needs".
Prefer narrow, independently evidenced statements, e.g. "Official API
documentation verifies EPL current operator-level odds" or "Public evidence did
not establish raw-feed redistribution rights".

## Public repository safety (DEC-010, DEC-022)

Committed evidence **may** contain: provider names, public URLs, public-doc
references, public-safe summaries, public plan **category** names
(`pricing_access`: `PUBLIC_PLAN` / `CONTACT_SALES` / `UNKNOWN` plus the pricing
URL), documented rate-limit facts, and public rights statements.

Committed evidence **must never** contain: API keys, credentials, account ids,
private sales correspondence, negotiated discounts, private quotations, contract
drafts or private contract terms, confidential legal documents, customer/user or
personal data, commercial negotiation strategy, or **numeric private pricing**.
Full Terms-of-Service documents are **not** copied into the repository; only
concise paraphrases (and minimal excerpts where necessary) are stored. The
standard-library validator scans for secret-like and private-pricing fields and
for score/ranking fields, and rejects any it finds.
