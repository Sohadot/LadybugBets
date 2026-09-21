"""Deterministic validator for LadybugBets source-qualification artifacts (LBSQ-001).

Standard library only. This is a GOVERNANCE validator, not a provider adapter:
it validates already-recorded research artifacts (evidence bundles and
qualification records). It never calls the web, never ingests odds, and never
generates identity.

Central rules:
- Capability outcomes are DETERMINISTICALLY DERIVED from the technical and rights
  matrices via a single `CAPABILITY_REQUIREMENTS` table used by both
  `derive_capabilities` and the capability-evidence-completeness check, so the
  two cannot drift. A committed outcome that disagrees with the derived outcome
  fails validation.
- A qualification record is bound to ONE evidence bundle: provider identity,
  name, and official domains must match, and every evidence item must carry the
  same provider_id. Cross-provider evidence cannot satisfy a qualification.
- A QUALIFIED capability must be machine-traceable to an evidence item for every
  required VERIFIED technical and ALLOWED right gate.
- No score, no ranking, no global winner.
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
    "multi_operator_coverage",
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

# Single source of truth for capability gates. `inherits` pulls in another
# capability's gates (used by derive_capabilities AND evidence completeness).
# multi_operator_coverage gates PUBLIC_SPOTBOARD only (operator-diverse display),
# implementing the DEC-013 / LBSQ-001 operator-diversity law. It is deliberately
# NOT required by CURRENT_PRICE_OBSERVATION (a single-operator source can still
# produce governed Price observations) nor by SOURCE_TIME_MARKET_MOVEMENT
# (movement is per one canonical operator over time).
CAPABILITY_REQUIREMENTS = {
    "CURRENT_PRICE_OBSERVATION": {
        "tech": (
            "football_coverage",
            "epl_coverage",
            "operator_level_prices",
            "stable_event_identifier",
            "operator_identifier_or_stable_label",
            "market_identifier_or_stable_key",
            "outcome_identifier_or_stable_key",
        ),
        "rights": ("ingest_use",),
    },
    "PUBLIC_SPOTBOARD": {
        "inherits": "CURRENT_PRICE_OBSERVATION",
        "tech": ("multi_operator_coverage",),
        "rights": ("public_display",),
    },
    "DERIVED_PROBABILITY_DISPLAY": {
        "inherits": "CURRENT_PRICE_OBSERVATION",
        "tech": (),
        "rights": ("derive_calculations", "public_display"),
    },
    "SOURCE_TIME_MARKET_MOVEMENT": {
        "tech": (
            "operator_level_prices",
            "operator_identifier_or_stable_label",
            "source_observed_timestamp",
            "stable_event_identifier",
            "market_identifier_or_stable_key",
            "outcome_identifier_or_stable_key",
        ),
        "rights": ("ingest_use", "retain_historical"),
    },
    "HISTORICAL_DATASET_RETENTION": {
        "tech": (),
        "rights": ("ingest_use", "retain_historical"),
    },
    "RAW_DATA_REDISTRIBUTION": {
        "tech": (),
        "rights": ("ingest_use", "redistribute_raw"),
    },
}


def required_gates(capability):
    """Flatten a capability's technical and rights gate keys (with inheritance)."""
    spec = CAPABILITY_REQUIREMENTS[capability]
    tech = []
    rights = []
    if "inherits" in spec:
        base_tech, base_rights = required_gates(spec["inherits"])
        tech.extend(base_tech)
        rights.extend(base_rights)
    for key in spec.get("tech", ()):
        if key not in tech:
            tech.append(key)
    for key in spec.get("rights", ()):
        if key not in rights:
            rights.append(key)
    return tech, rights


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
    """Tri-state gate: QUALIFIED / NOT_QUALIFIED / UNRESOLVED. Fail closed."""
    if any(t == "UNSUPPORTED" for t in tech_postures) or any(r == "PROHIBITED" for r in rights_postures):
        return "NOT_QUALIFIED"
    if all(t == "VERIFIED" for t in tech_postures) and all(r == "ALLOWED" for r in rights_postures):
        return "QUALIFIED"
    return "UNRESOLVED"


def derive_capabilities(qualification_record):
    """Deterministically derive capability outcomes from the matrices."""
    tech = qualification_record.get("technical_matrix", {})
    rights = qualification_record.get("rights_matrix", {})
    result = {}
    for cap in CAPABILITY_KEYS:
        tech_keys, right_keys = required_gates(cap)
        result[cap] = _eval([tech.get(k) for k in tech_keys], [rights.get(k) for k in right_keys])
    return result


def _host_ok(host, official_domains):
    host = (host or "").lower()
    if host.endswith("."):
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

    provider_id = bundle.get("provider_id")
    if not provider_id:
        findings.append(Finding("MISSING_PROVIDER_ID", "bundle.provider_id required"))
    if not bundle.get("provider_name"):
        findings.append(Finding("MISSING_PROVIDER_NAME", "bundle.provider_name required"))
    if not bundle.get("checked_at"):
        findings.append(Finding("MISSING_CHECKED_AT", "bundle.checked_at required"))

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

        if provider_id and item.get("provider_id") != provider_id:
            findings.append(
                Finding("EVIDENCE_PROVIDER_MISMATCH", "evidence %r provider_id != bundle provider_id" % eid)
            )

        url = item.get("source_url", "")
        if not isinstance(url, str) or not url.startswith("https://"):
            findings.append(Finding("EVIDENCE_URL_NOT_HTTPS", "evidence %r url not HTTPS: %r" % (eid, url)))
        else:
            host = urlparse(url).hostname
            if not _host_ok(host, official):
                findings.append(
                    Finding("EVIDENCE_DOMAIN_MISMATCH", "evidence %r host %r not in official_domains" % (eid, host))
                )
        if not _host_ok(item.get("publisher_domain"), official):
            findings.append(
                Finding("EVIDENCE_PUBLISHER_MISMATCH", "evidence %r publisher not official" % eid)
            )
        if not item.get("retrieved_at"):
            findings.append(Finding("MISSING_RETRIEVED_AT", "evidence %r missing retrieved_at" % eid))
        if not item.get("claim_key"):
            findings.append(Finding("MISSING_CLAIM_KEY", "evidence %r missing claim_key" % eid))
        if not item.get("claim_summary"):
            findings.append(Finding("MISSING_CLAIM_SUMMARY", "evidence %r missing claim_summary" % eid))
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
    index = {}
    for item in (bundle.get("evidence_items") or []):
        if isinstance(item, dict) and item.get("evidence_id"):
            index[item["evidence_id"]] = item
    return index


def validate_qualification(record, bundle):
    """Validate one qualification record against its bound evidence bundle."""
    findings = []
    if not isinstance(record, dict):
        return [Finding("MALFORMED", "qualification is not an object")]
    if not isinstance(bundle, dict):
        return [Finding("MALFORMED", "bundle is not an object")]

    index = _evidence_index(bundle)

    # --- Provider/bundle binding --------------------------------------------
    if record.get("provider_id") != bundle.get("provider_id"):
        findings.append(Finding("PROVIDER_ID_MISMATCH", "qualification.provider_id != bundle.provider_id"))
    if record.get("provider_name") != bundle.get("provider_name"):
        findings.append(Finding("PROVIDER_NAME_MISMATCH", "qualification.provider_name != bundle.provider_name"))
    if set(record.get("official_domains") or []) != set(bundle.get("official_domains") or []):
        findings.append(Finding("OFFICIAL_DOMAIN_SET_MISMATCH", "official_domains differ from bundle"))

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

    referenced = set(record.get("evidence_ids") or [])

    def _backed_by(claim_key, field, posture_value, pool):
        for eid in pool:
            item = index.get(eid)
            if item and item.get("claim_key") == claim_key and item.get(field) == posture_value:
                return True
        return False

    # Matrix-level evidence backing (record-wide pool).
    for key in RIGHTS_KEYS:
        posture = rights.get(key)
        if posture in ("ALLOWED", "PROHIBITED") and not _backed_by(key, "rights_posture", posture, referenced):
            findings.append(Finding("RIGHT_WITHOUT_EVIDENCE", "rights_matrix.%s=%s lacks referenced evidence" % (key, posture)))
    for key in TECHNICAL_KEYS:
        posture = tech.get(key)
        if posture in ("VERIFIED", "UNSUPPORTED", "CONFLICTING") and not _backed_by(key, "technical_posture", posture, referenced):
            findings.append(Finding("TECHNICAL_WITHOUT_EVIDENCE", "technical_matrix.%s=%s lacks referenced evidence" % (key, posture)))

    # --- Capability derivation + per-capability evidence completeness --------
    derived = derive_capabilities(record)
    committed = record.get("capabilities", {})
    for cap in CAPABILITY_KEYS:
        cap_record = committed.get(cap)
        if not isinstance(cap_record, dict) or cap_record.get("outcome") not in CAPABILITY_OUTCOMES:
            findings.append(Finding("BAD_CAPABILITY_OUTCOME", "capability %s malformed" % cap))
            continue
        if cap_record["outcome"] != derived[cap]:
            findings.append(
                Finding("CAPABILITY_DERIVATION_MISMATCH", "%s committed %s but derived %s" % (cap, cap_record["outcome"], derived[cap]))
            )
        cap_pool = set(cap_record.get("evidence_ids") or [])
        for eid in cap_pool:
            if eid not in index:
                findings.append(Finding("UNRESOLVED_EVIDENCE_REFERENCE", "%s references missing evidence %r" % (cap, eid)))
        # A QUALIFIED capability must trace to evidence for every required gate.
        if cap_record["outcome"] == "QUALIFIED":
            tech_keys, right_keys = required_gates(cap)
            for gate in tech_keys:
                if not _backed_by(gate, "technical_posture", "VERIFIED", cap_pool):
                    findings.append(Finding("CAPABILITY_EVIDENCE_INCOMPLETE", "%s missing VERIFIED evidence for %s" % (cap, gate)))
            for gate in right_keys:
                if not _backed_by(gate, "rights_posture", "ALLOWED", cap_pool):
                    findings.append(Finding("CAPABILITY_EVIDENCE_INCOMPLETE", "%s missing ALLOWED evidence for %s" % (cap, gate)))

    findings.extend(_hygiene_findings(record, "qualification"))
    return findings


def is_valid_evidence_bundle(bundle):
    return not validate_evidence_bundle(bundle)


def is_valid_qualification(record, bundle):
    return not validate_qualification(record, bundle)
