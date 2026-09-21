"""Deterministic validator for LadybugBets source-qualification artifacts (LBSQ-001).

Standard library only. This is a GOVERNANCE validator, not a provider adapter:
it validates already-recorded research artifacts (evidence bundles and
qualification records). It never calls the web, never ingests odds, and never
generates identity.

Two record kinds:
- Evidence bundle  (contracts/source-evidence.schema.json)
- Qualification    (contracts/source-qualification.schema.json)

Central rule: capability outcomes are DETERMINISTICALLY DERIVED from the
technical and rights matrices (`derive_capabilities`). A committed outcome that
disagrees with the derived outcome fails validation, so nobody can hand-type
"QUALIFIED". There is no score, no ranking, and no global winner.
"""

from urllib.parse import urlparse

TECHNICAL_POSTURES = ("VERIFIED", "NOT_VERIFIED", "UNSUPPORTED", "CONFLICTING")
RIGHTS_POSTURES = ("ALLOWED", "PROHIBITED", "UNKNOWN")
CAPABILITY_OUTCOMES = ("QUALIFIED", "NOT_QUALIFIED", "UNRESOLVED")
SOURCE_TYPES = ("TERMS", "LEGAL", "API_DOCS", "PRODUCT_DOCS", "COVERAGE", "PRICING", "FAQ", "SUPPORT")
PRICING_ACCESS = ("PUBLIC_PLAN", "CONTACT_SALES", "UNKNOWN")

TECHNICAL_KEYS = (
    "football_coverage",
    "epl_coverage",
    "operator_level_prices",
    "stable_event_identifier",
    "operator_identifier_or_stable_label",
    "market_identifier_or_stable_key",
    "outcome_identifier_or_stable_key",
    "source_observed_timestamp",
    "historical_odds_access",
    "documented_rate_limits",
)
RIGHTS_KEYS = (
    "ingest_use",
    "cache",
    "retain_historical",
    "derive_calculations",
    "public_display",
    "redistribute_raw",
    "redistribute_derived",
)
CAPABILITY_KEYS = (
    "CURRENT_PRICE_OBSERVATION",
    "PUBLIC_SPOTBOARD",
    "DERIVED_PROBABILITY_DISPLAY",
    "SOURCE_TIME_MARKET_MOVEMENT",
    "HISTORICAL_DATASET_RETENTION",
    "RAW_DATA_REDISTRIBUTION",
)

# Technicals required to create a governed current Price observation.
CURRENT_PRICE_TECH = (
    "football_coverage",
    "epl_coverage",
    "operator_level_prices",
    "stable_event_identifier",
    "operator_identifier_or_stable_label",
    "market_identifier_or_stable_key",
    "outcome_identifier_or_stable_key",
)

# Keys that must never appear anywhere in a governance artifact.
FORBIDDEN_SCORE_KEYS = frozenset(
    {"score", "scores", "rank", "ranking", "rating", "grade", "winner", "best_provider", "weight"}
)
SECRET_KEY_SUBSTRINGS = (
    "api_key",
    "apikey",
    "api-key",
    "password",
    "passwd",
    "secret",
    "bearer",
    "credential",
    "private_key",
    "access_token",
    "client_secret",
    "account_id",
)
PRIVATE_PRICING_KEY_SUBSTRINGS = ("discount", "quote_amount", "contract_value", "negotiated")


class Finding(object):
    __slots__ = ("code", "message")

    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __repr__(self):  # pragma: no cover
        return "Finding(%r, %r)" % (self.code, self.message)

    def __eq__(self, other):
        return isinstance(other, Finding) and self.code == other.code and self.message == other.message

    def __hash__(self):
        return hash((self.code, self.message))


def _eval(tech_postures, rights_postures):
    """Tri-state gate: QUALIFIED / NOT_QUALIFIED / UNRESOLVED.

    - NOT_QUALIFIED if any technical is UNSUPPORTED or any right is PROHIBITED
      (an explicit blocker).
    - QUALIFIED only if every technical is VERIFIED and every right is ALLOWED.
    - Otherwise UNRESOLVED (missing/unclear evidence: NOT_VERIFIED, CONFLICTING,
      or UNKNOWN). Fail closed.
    """
    if any(t == "UNSUPPORTED" for t in tech_postures) or any(r == "PROHIBITED" for r in rights_postures):
        return "NOT_QUALIFIED"
    if all(t == "VERIFIED" for t in tech_postures) and all(r == "ALLOWED" for r in rights_postures):
        return "QUALIFIED"
    return "UNRESOLVED"


def _dependent(base_outcome, extra_rights):
    """A capability that additionally requires `base_outcome` == QUALIFIED."""
    if base_outcome == "NOT_QUALIFIED" or any(r == "PROHIBITED" for r in extra_rights):
        return "NOT_QUALIFIED"
    if base_outcome == "QUALIFIED" and all(r == "ALLOWED" for r in extra_rights):
        return "QUALIFIED"
    return "UNRESOLVED"


def derive_capabilities(qualification_record):
    """Deterministically derive capability outcomes from the matrices.

    Returns {capability_key: outcome}. Never consults committed outcomes.
    """
    tech = qualification_record.get("technical_matrix", {})
    rights = qualification_record.get("rights_matrix", {})

    def t(key):
        return tech.get(key)

    def r(key):
        return rights.get(key)

    current_price = _eval([t(k) for k in CURRENT_PRICE_TECH], [r("ingest_use")])

    public_spotboard = _dependent(current_price, [r("public_display")])
    derived_display = _dependent(current_price, [r("derive_calculations"), r("public_display")])

    movement = _eval(
        [
            t("operator_level_prices"),
            t("operator_identifier_or_stable_label"),
            t("source_observed_timestamp"),
            t("stable_event_identifier"),
            t("market_identifier_or_stable_key"),
            t("outcome_identifier_or_stable_key"),
        ],
        [r("ingest_use"), r("retain_historical")],
    )

    historical_retention = _eval([], [r("ingest_use"), r("retain_historical")])
    raw_redistribution = _eval([], [r("ingest_use"), r("redistribute_raw")])

    return {
        "CURRENT_PRICE_OBSERVATION": current_price,
        "PUBLIC_SPOTBOARD": public_spotboard,
        "DERIVED_PROBABILITY_DISPLAY": derived_display,
        "SOURCE_TIME_MARKET_MOVEMENT": movement,
        "HISTORICAL_DATASET_RETENTION": historical_retention,
        "RAW_DATA_REDISTRIBUTION": raw_redistribution,
    }


def _host_ok(host, official_domains):
    host = (host or "").lower()
    if host.endswith(".") :
        host = host[:-1]
    for domain in official_domains:
        d = domain.lower()
        if host == d or host.endswith("." + d):
            return True
    return False


def _walk(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield ("key", key)
            for nested in _walk(value):
                yield nested
    elif isinstance(obj, list):
        for item in obj:
            for nested in _walk(item):
                yield nested
    else:
        yield ("value", obj)


def _hygiene_findings(record, label):
    findings = []
    for kind, value in _walk(record):
        if kind == "key" and isinstance(value, str):
            lowered = value.lower()
            if lowered in FORBIDDEN_SCORE_KEYS:
                findings.append(Finding("SCORE_OR_RANKING_FIELD", "%s: forbidden field %r" % (label, value)))
            for needle in SECRET_KEY_SUBSTRINGS:
                if needle in lowered:
                    findings.append(Finding("SECRET_LIKE_FIELD", "%s: secret-like key %r" % (label, value)))
            for needle in PRIVATE_PRICING_KEY_SUBSTRINGS:
                if needle in lowered:
                    findings.append(Finding("PRIVATE_PRICING_FIELD", "%s: private-pricing key %r" % (label, value)))
    return findings


def validate_evidence_bundle(bundle):
    """Validate one evidence bundle. Returns a list of Finding."""
    findings = []
    if not isinstance(bundle, dict):
        return [Finding("MALFORMED", "evidence bundle is not an object")]

    official = bundle.get("official_domains")
    if not isinstance(official, list) or not official:
        findings.append(Finding("MISSING_OFFICIAL_DOMAINS", "official_domains required"))
        official = official if isinstance(official, list) else []

    items = bundle.get("evidence_items")
    if not isinstance(items, list) or not items:
        findings.append(Finding("MISSING_EVIDENCE_ITEMS", "evidence_items required"))
        items = []

    seen_ids = set()
    for item in items:
        if not isinstance(item, dict):
            findings.append(Finding("MALFORMED_EVIDENCE_ITEM", "evidence item not an object"))
            continue
        eid = item.get("evidence_id")
        if not eid:
            findings.append(Finding("MISSING_EVIDENCE_ID", "evidence item missing id"))
        elif eid in seen_ids:
            findings.append(Finding("DUPLICATE_EVIDENCE_ID", "duplicate evidence_id %r" % eid))
        else:
            seen_ids.add(eid)

        url = item.get("source_url", "")
        if not isinstance(url, str) or not url.startswith("https://"):
            findings.append(Finding("EVIDENCE_URL_NOT_HTTPS", "evidence %r url not HTTPS: %r" % (eid, url)))
        else:
            host = urlparse(url).hostname
            if not _host_ok(host, official):
                findings.append(
                    Finding("EVIDENCE_DOMAIN_MISMATCH", "evidence %r host %r not in official_domains" % (eid, host))
                )
        publisher = item.get("publisher_domain")
        if not _host_ok(publisher, official):
            findings.append(
                Finding("EVIDENCE_PUBLISHER_MISMATCH", "evidence %r publisher %r not official" % (eid, publisher))
            )
        if not item.get("retrieved_at"):
            findings.append(Finding("MISSING_RETRIEVED_AT", "evidence %r missing retrieved_at" % eid))
        st = item.get("source_type")
        if st not in SOURCE_TYPES:
            findings.append(Finding("BAD_SOURCE_TYPE", "evidence %r bad source_type %r" % (eid, st)))
        tp = item.get("technical_posture")
        if tp is not None and tp not in TECHNICAL_POSTURES:
            findings.append(Finding("BAD_TECHNICAL_POSTURE", "evidence %r bad technical_posture %r" % (eid, tp)))
        rp = item.get("rights_posture")
        if rp is not None and rp not in RIGHTS_POSTURES:
            findings.append(Finding("BAD_RIGHTS_POSTURE", "evidence %r bad rights_posture %r" % (eid, rp)))

    findings.extend(_hygiene_findings(bundle, "evidence"))
    return findings


def _evidence_index(bundle):
    """Map evidence_id -> item (for a validated-or-not bundle)."""
    index = {}
    for item in (bundle.get("evidence_items") or []):
        if isinstance(item, dict) and item.get("evidence_id"):
            index[item["evidence_id"]] = item
    return index


def validate_qualification(record, bundle):
    """Validate one qualification record against its evidence bundle."""
    findings = []
    if not isinstance(record, dict):
        return [Finding("MALFORMED", "qualification is not an object")]

    index = _evidence_index(bundle) if isinstance(bundle, dict) else {}

    # Referenced evidence ids must resolve in the bundle.
    for eid in (record.get("evidence_ids") or []):
        if eid not in index:
            findings.append(Finding("UNRESOLVED_EVIDENCE_REFERENCE", "evidence_id %r not in bundle" % eid))

    tech = record.get("technical_matrix", {})
    rights = record.get("rights_matrix", {})

    for key in TECHNICAL_KEYS:
        if tech.get(key) not in TECHNICAL_POSTURES:
            findings.append(Finding("BAD_TECHNICAL_POSTURE", "technical_matrix.%s = %r" % (key, tech.get(key))))
    for key in RIGHTS_KEYS:
        if rights.get(key) not in RIGHTS_POSTURES:
            findings.append(Finding("BAD_RIGHTS_POSTURE", "rights_matrix.%s = %r" % (key, rights.get(key))))
    if record.get("pricing_access") not in PRICING_ACCESS:
        findings.append(Finding("BAD_PRICING_ACCESS", "pricing_access = %r" % record.get("pricing_access")))

    # Evidence-backing: an ALLOWED/PROHIBITED right, or a VERIFIED/UNSUPPORTED/
    # CONFLICTING technical, must be backed by a referenced evidence item whose
    # claim_key matches and whose posture matches.
    referenced = set(record.get("evidence_ids") or [])

    def _has_backing(claim_key, field, posture_value):
        for eid in referenced:
            item = index.get(eid)
            if not item:
                continue
            if item.get("claim_key") == claim_key and item.get(field) == posture_value:
                return True
        return False

    for key in RIGHTS_KEYS:
        posture = rights.get(key)
        if posture in ("ALLOWED", "PROHIBITED") and not _has_backing(key, "rights_posture", posture):
            findings.append(
                Finding("RIGHT_WITHOUT_EVIDENCE", "rights_matrix.%s=%s lacks matching referenced evidence" % (key, posture))
            )
    for key in TECHNICAL_KEYS:
        posture = tech.get(key)
        if posture in ("VERIFIED", "UNSUPPORTED", "CONFLICTING") and not _has_backing(key, "technical_posture", posture):
            findings.append(
                Finding("TECHNICAL_WITHOUT_EVIDENCE", "technical_matrix.%s=%s lacks matching referenced evidence" % (key, posture))
            )

    # Capability outcomes must equal the deterministically derived outcomes.
    derived = derive_capabilities(record)
    committed = record.get("capabilities", {})
    for cap in CAPABILITY_KEYS:
        cap_record = committed.get(cap)
        if not isinstance(cap_record, dict) or cap_record.get("outcome") not in CAPABILITY_OUTCOMES:
            findings.append(Finding("BAD_CAPABILITY_OUTCOME", "capability %s malformed" % cap))
            continue
        if cap_record["outcome"] != derived[cap]:
            findings.append(
                Finding(
                    "CAPABILITY_DERIVATION_MISMATCH",
                    "%s committed %s but derived %s" % (cap, cap_record["outcome"], derived[cap]),
                )
            )
        for eid in (cap_record.get("evidence_ids") or []):
            if eid not in index:
                findings.append(
                    Finding("UNRESOLVED_EVIDENCE_REFERENCE", "%s references missing evidence %r" % (cap, eid))
                )

    # Hard capability guards (belt-and-braces; the derivation already enforces).
    if committed.get("PUBLIC_SPOTBOARD", {}).get("outcome") == "QUALIFIED" and rights.get("public_display") != "ALLOWED":
        findings.append(Finding("PUBLIC_SPOTBOARD_WITHOUT_DISPLAY", "PUBLIC_SPOTBOARD QUALIFIED needs public_display ALLOWED"))
    if committed.get("HISTORICAL_DATASET_RETENTION", {}).get("outcome") == "QUALIFIED" and rights.get("retain_historical") != "ALLOWED":
        findings.append(Finding("RETENTION_WITHOUT_RIGHT", "HISTORICAL_DATASET_RETENTION QUALIFIED needs retain_historical ALLOWED"))
    if committed.get("DERIVED_PROBABILITY_DISPLAY", {}).get("outcome") == "QUALIFIED" and rights.get("derive_calculations") != "ALLOWED":
        findings.append(Finding("DERIVED_WITHOUT_RIGHT", "DERIVED_PROBABILITY_DISPLAY QUALIFIED needs derive_calculations ALLOWED"))
    if committed.get("SOURCE_TIME_MARKET_MOVEMENT", {}).get("outcome") == "QUALIFIED" and tech.get("source_observed_timestamp") != "VERIFIED":
        findings.append(Finding("MOVEMENT_WITHOUT_SOURCE_TIME", "SOURCE_TIME_MARKET_MOVEMENT QUALIFIED needs source_observed_timestamp VERIFIED"))

    findings.extend(_hygiene_findings(record, "qualification"))
    return findings


def is_valid_evidence_bundle(bundle):
    return not validate_evidence_bundle(bundle)


def is_valid_qualification(record, bundle):
    return not validate_qualification(record, bundle)
