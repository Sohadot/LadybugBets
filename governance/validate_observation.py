"""Deterministic contract validator for LBOC-001 observation envelopes.

Standard library only. This is a **contract validator**, not a production
ingestion engine. Given an already-parsed candidate envelope (a dict), it
reports every way the envelope is *inconsistent with its own declared*
`governance.admission_state` and reason codes.

It MUST NOT (and does not):

- call APIs or read a database,
- resolve identities (no fuzzy logic, no canonical-id generation),
- mutate the record,
- publish anything.

Two clearly separated notions:

- **Contract consistency** (`is_contract_consistent`) — the declared state and
  reasons correctly describe the candidate. This can legitimately be True for
  ADMITTED, QUARANTINED, *or* REJECTED.
- **Admission** (`is_admitted`) — contract-consistent AND declared ADMITTED. A
  QUARANTINED or REJECTED candidate is never admitted.

An explicit LBOC-001 structural preflight (`validate_envelope_structure`) runs
first and guarantees `is_admitted` cannot return True for an envelope whose
admission-critical shape is broken (e.g. a missing `provenance.ingested_at`). It
is hand-coded for LBOC-001 only — NOT a generic JSON Schema engine. The portable
JSON Schema remains authoritative for the complete structural shape.

Machine-detectable defects are detected independently of the declared state
(`detect_machine_conditions`), using the governed reason-code vocabulary. The
validator does NOT reconstruct identity-resolution outcomes: a declared
`UNRESOLVED_*`/`AMBIGUOUS_*` identity reason is governed evidence from the
resolution layer, and the validator only checks that the corresponding canonical
identity stays null.

The governed laws are defined in:
- docs/OBSERVATION_CONTRACT.md   (LBOC-001)
- docs/IDENTITY_RESOLUTION.md    (LBIR-001)
- docs/TEMPORAL_GOVERNANCE.md
- docs/METHODOLOGY.md            (price validity basis)
"""

import re

SUPPORTED_CONTRACT_VERSION = "1.0.0"

ADMISSION_STATES = ("ADMITTED", "QUARANTINED", "REJECTED")

# The five governed top-level sections of an LBOC-001 envelope, in order.
EXPECTED_SECTIONS = ("contract", "provenance", "source_asserted", "canonical", "governance")

# Admission-critical fields whose KEY must exist in the envelope shape, per
# section (values may still be null where the contract allows, e.g. provider_id
# for a REJECTED candidate). These mirror the portable JSON Schema `required`
# lists; a drift test asserts each appears as a declared schema property.
ADMISSION_CRITICAL_FIELDS = {
    "contract": ("contract_version", "observation_id"),
    "provenance": ("provider_id", "ingested_at"),
    "source_asserted": ("price", "price_format"),
    "governance": ("admission_state",),
}

# Canonical fields the schema requires for an ADMITTED envelope.
ADMITTED_CANONICAL_REQUIRED = ("event_id", "operator_id", "market_id", "outcome_id", "participants")

VALID_PRICE_FORMATS = ("decimal", "american", "fractional")

# The currently governed match-event profile is football/soccer (MVP scope,
# DEC-006). A football match event is participant-bearing (DEC-017) with exactly
# the roles home and away. This is NOT a universal law for every future sport.
FOOTBALL_MATCH_SPORT = "football"
MATCH_EVENT_ROLES = ("home", "away")

IDENTITY_ENTITIES = (
    "sport",
    "competition",
    "participant",
    "event",
    "operator",
    "market",
    "outcome",
    "jurisdiction",
)

_IDENTITY_REASON_CODES = tuple(
    ["UNRESOLVED_%s_IDENTITY" % e.upper() for e in IDENTITY_ENTITIES]
    + ["AMBIGUOUS_%s_IDENTITY" % e.upper() for e in IDENTITY_ENTITIES]
)

# Machine-detectable defects. These are objectively derivable from the envelope
# WITHOUT performing identity resolution. They are all rejection-class: a
# candidate exhibiting any of them cannot enter governed analytical use as-is.
MACHINE_DETECTABLE_CODES = (
    "INVALID_CONTRACT_VERSION",
    "MISSING_PROVIDER_PROVENANCE",
    "MISSING_SOURCE_LOCATOR",
    "MISSING_REQUIRED_SOURCE_FIELD",
    "INVALID_PRICE_FORMAT",
    "INVALID_PRICE",
)
REJECTION_CLASS_CODES = MACHINE_DETECTABLE_CODES

# Quarantine-class: identity uncertainty/ambiguity and governed conflicts that
# may be resolvable without treating the source candidate as structurally
# invalid. These are DECLARED governed outcomes, never machine-reconstructed.
QUARANTINE_CLASS_CODES = tuple(
    list(_IDENTITY_REASON_CODES) + ["TEMPORAL_AMBIGUITY", "CONFLICTING_SOURCE_ASSERTIONS"]
)

REASON_CODES = tuple(list(_IDENTITY_REASON_CODES) + list(MACHINE_DETECTABLE_CODES)
                     + ["TEMPORAL_AMBIGUITY", "CONFLICTING_SOURCE_ASSERTIONS"])

# Reason code -> the canonical field that MUST remain unresolved (null) when the
# code is present. Participant identity is handled separately (a list).
UNRESOLVED_CANONICAL_FIELD = {
    "UNRESOLVED_SPORT_IDENTITY": "sport",
    "AMBIGUOUS_SPORT_IDENTITY": "sport",
    "UNRESOLVED_COMPETITION_IDENTITY": "competition_id",
    "AMBIGUOUS_COMPETITION_IDENTITY": "competition_id",
    "UNRESOLVED_EVENT_IDENTITY": "event_id",
    "AMBIGUOUS_EVENT_IDENTITY": "event_id",
    "UNRESOLVED_OPERATOR_IDENTITY": "operator_id",
    "AMBIGUOUS_OPERATOR_IDENTITY": "operator_id",
    "UNRESOLVED_MARKET_IDENTITY": "market_id",
    "AMBIGUOUS_MARKET_IDENTITY": "market_id",
    "UNRESOLVED_OUTCOME_IDENTITY": "outcome_id",
    "AMBIGUOUS_OUTCOME_IDENTITY": "outcome_id",
    "UNRESOLVED_JURISDICTION_IDENTITY": "jurisdiction",
    "AMBIGUOUS_JURISDICTION_IDENTITY": "jurisdiction",
}
PARTICIPANT_UNRESOLVED_CODES = (
    "UNRESOLVED_PARTICIPANT_IDENTITY",
    "AMBIGUOUS_PARTICIPANT_IDENTITY",
)

# Core canonical identities a governed Price observation must carry to be ADMITTED.
CORE_ADMITTED_CANONICAL = ("event_id", "operator_id", "market_id", "outcome_id")

# Raw source id -> canonical id pairs that must never be identical.
RAW_CANONICAL_ID_PAIRS = (
    ("source_event_id", "event_id"),
    ("source_operator_id", "operator_id"),
    ("source_market_id", "market_id"),
    ("source_outcome_id", "outcome_id"),
    ("source_competition_id", "competition_id"),
)

FORBIDDEN_DERIVED_KEYS = frozenset(
    {
        "implied_probability",
        "normalized_probability",
        "movement_amount",
        "movement",
        "cross_operator_difference",
        "consensus",
        "consensus_aggregate",
        "overround",
        "book_percentage",
        "implied_margin",
        "closing_comparison",
        "closing",
        "edge_score",
    }
)


class Finding(object):
    """A single deterministic contract-consistency violation."""

    __slots__ = ("code", "message")

    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __repr__(self):  # pragma: no cover - debug aid
        return "Finding(%r, %r)" % (self.code, self.message)

    def __eq__(self, other):
        return (
            isinstance(other, Finding)
            and self.code == other.code
            and self.message == other.message
        )

    def __hash__(self):
        return hash((self.code, self.message))


def _is_nonempty_str(value):
    return isinstance(value, str) and value.strip() != ""


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def price_is_valid(price, price_format):
    """Format-aware price validity, grounded in docs/METHODOLOGY.md.

    - decimal:    numeric and > 1.0
    - american:   integer-valued and |A| >= 100
    - fractional: string "a/b" with positive integers a >= 1, b >= 1
    Any other/unknown format is invalid here (format support is checked
    separately so INVALID_PRICE_FORMAT stays distinct from INVALID_PRICE).
    """
    if price_format == "decimal":
        return _is_number(price) and price > 1.0
    if price_format == "american":
        if isinstance(price, bool):
            return False
        if isinstance(price, int):
            magnitude = price
        elif isinstance(price, float) and price.is_integer():
            magnitude = int(price)
        else:
            return False
        return abs(magnitude) >= 100
    if price_format == "fractional":
        if not isinstance(price, str):
            return False
        match = re.fullmatch(r"\s*(\d+)\s*/\s*(\d+)\s*", price)
        if not match:
            return False
        numerator, denominator = int(match.group(1)), int(match.group(2))
        return numerator >= 1 and denominator >= 1
    return False


def detect_machine_conditions(envelope):
    """Return the set of governed reason codes for machine-provable defects.

    Independent of the declared admission_state. Uses ONLY objectively derivable
    facts; it never infers identity-resolution outcomes (a null canonical field
    does not tell us whether identity was unresolved, ambiguous, not applicable,
    or simply not yet run). All codes returned are rejection-class.
    """
    detected = set()
    if not isinstance(envelope, dict):
        return detected
    contract = envelope.get("contract") or {}
    provenance = envelope.get("provenance") or {}
    source = envelope.get("source_asserted") or {}

    version = contract.get("contract_version")
    if _is_nonempty_str(version) and version != SUPPORTED_CONTRACT_VERSION:
        detected.add("INVALID_CONTRACT_VERSION")

    if not _is_nonempty_str(provenance.get("provider_id")):
        detected.add("MISSING_PROVIDER_PROVENANCE")

    if not (
        _is_nonempty_str(provenance.get("source_reference"))
        or _is_nonempty_str(provenance.get("source_record_id"))
    ):
        detected.add("MISSING_SOURCE_LOCATOR")

    has_price = "price" in source
    has_format = "price_format" in source
    if not has_price or not has_format:
        detected.add("MISSING_REQUIRED_SOURCE_FIELD")
    if has_format:
        price_format = source.get("price_format")
        if price_format not in VALID_PRICE_FORMATS:
            detected.add("INVALID_PRICE_FORMAT")
        elif has_price and not price_is_valid(source.get("price"), price_format):
            detected.add("INVALID_PRICE")

    return detected


def _walk_keys(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield key
            for nested in _walk_keys(value):
                yield nested
    elif isinstance(obj, list):
        for item in obj:
            for nested in _walk_keys(item):
                yield nested


def _resolved_participants(canonical):
    return [
        p
        for p in (canonical.get("participants", []) or [])
        if isinstance(p, dict)
        and _is_nonempty_str(p.get("participant_id"))
        and _is_nonempty_str(p.get("role"))
    ]


def validate_envelope_structure(envelope):
    """Explicit LBOC-001 structural preflight (NOT a generic JSON Schema engine).

    Enforces only the admission-critical structural subset that guarantees
    ``is_admitted()`` cannot return True for an envelope whose shape violates the
    core LBOC-001 contract. The portable JSON Schema remains authoritative for
    the *complete* structural shape (including full ``additionalProperties:
    false`` coverage); this function hand-codes the subset that matters for safe
    admission and for representing rejections.

    Returns a list of Finding objects (empty when the structure is sound). It
    never fabricates values and never substitutes one field for another.
    """
    if not isinstance(envelope, dict):
        return [Finding("MALFORMED_ENVELOPE", "envelope is not an object")]

    findings = []

    # Exactly the five governed sections, each an object; no extra top-level keys
    # (the portable schema uses additionalProperties: false).
    for section in EXPECTED_SECTIONS:
        if section not in envelope:
            findings.append(Finding("MISSING_SECTION", "missing section: %s" % section))
        elif not isinstance(envelope[section], dict):
            findings.append(Finding("MALFORMED_SECTION", "section not an object: %s" % section))
    for extra in sorted(set(envelope.keys()) - set(EXPECTED_SECTIONS)):
        findings.append(
            Finding("UNEXPECTED_TOP_LEVEL_FIELD", "unexpected top-level field: %s" % extra)
        )

    def _section(name):
        value = envelope.get(name)
        return value if isinstance(value, dict) else {}

    contract = _section("contract")
    provenance = _section("provenance")
    source = _section("source_asserted")
    canonical = _section("canonical")
    governance = _section("governance")
    state = governance.get("admission_state")

    # contract: non-empty string identifiers (all states).
    if not _is_nonempty_str(contract.get("contract_version")):
        findings.append(
            Finding("MISSING_CONTRACT_VERSION", "contract.contract_version required (non-empty string)")
        )
    if not _is_nonempty_str(contract.get("observation_id")):
        findings.append(
            Finding("MISSING_OBSERVATION_ID", "contract.observation_id required (non-empty string)")
        )

    # provenance: the fields belong to the shape (provider_id may be null for a
    # REJECTED candidate); ingested_at must be a non-empty string to be ADMITTED
    # or QUARANTINED.
    if "provider_id" not in provenance:
        findings.append(
            Finding("MISSING_PROVIDER_FIELD", "provenance.provider_id field required (may be null)")
        )
    if "ingested_at" not in provenance:
        findings.append(Finding("MISSING_INGESTED_AT", "provenance.ingested_at field required"))
    if state in ("ADMITTED", "QUARANTINED") and not _is_nonempty_str(provenance.get("ingested_at")):
        findings.append(
            Finding("MISSING_INGESTED_AT", "%s requires a non-empty ingested_at" % state)
        )

    # source_asserted: required fields must be present (absence != invalid value).
    for field in ("price", "price_format"):
        if field not in source:
            findings.append(
                Finding("MISSING_REQUIRED_SOURCE_FIELD", "source_asserted.%s field required" % field)
            )

    # governance: admission_state field must exist.
    if "admission_state" not in governance:
        findings.append(Finding("MISSING_ADMISSION_STATE", "governance.admission_state required"))

    # canonical.participants, when present, must be an array (any state).
    if "participants" in canonical and not isinstance(canonical.get("participants"), list):
        findings.append(Finding("PARTICIPANTS_NOT_ARRAY", "canonical.participants must be an array"))

    # Admission-critical nested types for ADMITTED.
    if state == "ADMITTED":
        participants = canonical.get("participants")
        if not isinstance(participants, list):
            findings.append(
                Finding("PARTICIPANTS_NOT_ARRAY", "ADMITTED canonical.participants must be an array")
            )
        else:
            for participant in participants:
                if not isinstance(participant, dict):
                    findings.append(
                        Finding("MALFORMED_PARTICIPANT", "ADMITTED participant must be an object")
                    )
                    continue
                for key in ("participant_id", "role"):
                    if key in participant and participant[key] is not None and not isinstance(
                        participant[key], str
                    ):
                        findings.append(
                            Finding(
                                "MALFORMED_PARTICIPANT",
                                "ADMITTED participant %s must be a string" % key,
                            )
                        )

    return findings


def validate_observation(envelope):
    """Return a list of Finding objects (contract-consistency violations).

    An empty list means the envelope is internally consistent with the
    admission invariants for its own declared admission_state. Never raises for
    a well-typed dict; structural problems are returned as findings.

    The admission-critical structural preflight runs first; if it reports any
    finding the envelope is not contract-consistent (so it can never be admitted)
    and we return those findings directly, since the deeper semantic checks
    assume a sound shape.
    """
    structural = validate_envelope_structure(envelope)
    if structural:
        return structural

    findings = []

    contract = envelope["contract"]
    provenance = envelope["provenance"]
    source = envelope["source_asserted"]
    canonical = envelope["canonical"]
    governance = envelope["governance"]

    state = governance.get("admission_state")
    if state not in ADMISSION_STATES:
        findings.append(Finding("STATE_INVALID", "unknown admission_state %r" % state))

    reason_codes = governance.get("reason_codes", []) or []
    if not isinstance(reason_codes, list):
        findings.append(Finding("REASON_CODES_MALFORMED", "reason_codes must be a list"))
        reason_codes = []
    for code in reason_codes:
        if code not in REASON_CODES:
            findings.append(Finding("REASON_CODE_UNKNOWN", "unknown reason code %r" % code))
    if state == "ADMITTED" and reason_codes:
        findings.append(Finding("REASON_STATE_INCONSISTENT", "ADMITTED must have no reason codes"))
    if state in ("QUARANTINED", "REJECTED") and not reason_codes:
        findings.append(
            Finding("REASON_STATE_INCONSISTENT", "%s requires >=1 reason code" % state)
        )

    # --- Machine-detected defects vs. declared reasons -----------------------
    detected = detect_machine_conditions(envelope)

    # (a) Truthfulness: a declared machine-detectable rejection reason must be
    #     backed by an actual detected defect. (Identity/temporal/conflict
    #     reasons are governed declarations and are NOT required to be detected.)
    for code in reason_codes:
        if code in MACHINE_DETECTABLE_CODES and code not in detected:
            findings.append(
                Finding(
                    "REASON_EVIDENCE_MISSING",
                    "declared %s is not supported by a detected defect" % code,
                )
            )

    # (b) Fail closed: a real rejection-class defect cannot be ADMITTED or
    #     QUARANTINED. Report each detected condition using its governed code.
    if state in ("ADMITTED", "QUARANTINED"):
        for code in sorted(detected):
            findings.append(
                Finding(code, "detected %s; a %s candidate must be REJECTED" % (code, state))
            )

    # --- Universal laws (all states) -----------------------------------------
    for key in _walk_keys(envelope):
        if isinstance(key, str) and key.lower() in FORBIDDEN_DERIVED_KEYS:
            findings.append(Finding("DERIVED_FIELD_PRESENT", "derived field in envelope: %s" % key))

    # NOTE (DEC-020 / temporal semantics): source_observed_at and ingested_at are
    # distinct semantic fields, but they MAY legitimately hold the same value.
    # Numerical equality does not prove that ingestion time was used as a source
    # quote time, so equality is NOT a violation. The structural separation of
    # the two fields is preserved by the envelope shape, and a missing
    # source_observed_at stays missing (never substituted).

    for source_key, canonical_key in RAW_CANONICAL_ID_PAIRS:
        source_value = source.get(source_key)
        canonical_value = canonical.get(canonical_key)
        if source_value and canonical_value and source_value == canonical_value:
            findings.append(
                Finding(
                    "RAW_ID_PROMOTED",
                    "raw %s reused as canonical %s" % (source_key, canonical_key),
                )
            )
    source_pids = {
        p.get("source_participant_id")
        for p in source.get("source_participants", []) or []
        if isinstance(p, dict) and p.get("source_participant_id")
    }
    canonical_pids = {
        p.get("participant_id")
        for p in canonical.get("participants", []) or []
        if isinstance(p, dict) and p.get("participant_id")
    }
    if source_pids & canonical_pids:
        findings.append(
            Finding("RAW_ID_PROMOTED", "raw participant id reused as canonical participant id")
        )

    # Declared unresolved/ambiguous identity reasons must leave the canonical
    # field null. (The validator does not perform resolution; it only checks the
    # null invariant against the governed declaration.)
    for code in reason_codes:
        field = UNRESOLVED_CANONICAL_FIELD.get(code)
        if field is not None and canonical.get(field) is not None:
            findings.append(
                Finding(
                    "UNRESOLVED_CANONICAL_RESOLVED",
                    "%s present but canonical.%s is resolved" % (code, field),
                )
            )
    if any(code in reason_codes for code in PARTICIPANT_UNRESOLVED_CODES):
        for participant in canonical.get("participants", []) or []:
            if isinstance(participant, dict) and participant.get("participant_id") is not None:
                findings.append(
                    Finding(
                        "UNRESOLVED_CANONICAL_RESOLVED",
                        "participant identity unresolved but a canonical participant_id is set",
                    )
                )
                break

    # --- ADMITTED admission tier ---------------------------------------------
    if state == "ADMITTED":
        for field in CORE_ADMITTED_CANONICAL:
            if not _is_nonempty_str(canonical.get(field)):
                findings.append(
                    Finding(
                        "MISSING_CORE_CANONICAL_IDENTITY",
                        "ADMITTED requires canonical.%s" % field,
                    )
                )
        findings.extend(_admitted_participant_findings(canonical))

    return findings


def _admitted_participant_findings(canonical):
    """Participant-bearing event identity for ADMITTED records (DEC-017).

    For the governed football/soccer match-event profile (MVP scope, DEC-006):
    require a resolved canonical `home` participant and a resolved canonical
    `away` participant, with distinct participant_ids and no duplicated role.
    For any other sport (out of current MVP scope), fall back to the DEC-017
    baseline of at least one resolved canonical participant.
    """
    findings = []
    resolved = _resolved_participants(canonical)
    sport = canonical.get("sport")

    if sport == FOOTBALL_MATCH_SPORT:
        by_role = {}
        for participant in resolved:
            by_role.setdefault(participant["role"], []).append(participant)
        for role in MATCH_EVENT_ROLES:
            if role not in by_role:
                findings.append(
                    Finding(
                        "MISSING_PARTICIPANT_IDENTITY",
                        "ADMITTED football event requires a resolved '%s' participant" % role,
                    )
                )
            elif len(by_role[role]) > 1:
                findings.append(
                    Finding(
                        "DUPLICATE_PARTICIPANT_ROLE",
                        "ADMITTED football event has multiple '%s' participants" % role,
                    )
                )
        home = by_role.get("home")
        away = by_role.get("away")
        if home and away and home[0]["participant_id"] == away[0]["participant_id"]:
            findings.append(
                Finding(
                    "NON_DISTINCT_PARTICIPANTS",
                    "ADMITTED football event home and away share a participant_id",
                )
            )
    else:
        if not resolved:
            findings.append(
                Finding(
                    "MISSING_PARTICIPANT_IDENTITY",
                    "ADMITTED event requires >=1 resolved canonical participant (DEC-017)",
                )
            )
    return findings


def is_contract_consistent(envelope):
    """True when the declared state and reasons correctly describe the candidate.

    May legitimately be True for ADMITTED, QUARANTINED, or REJECTED.
    """
    return not validate_observation(envelope)


def is_admitted(envelope):
    """True ONLY for a contract-consistent envelope whose declared state is ADMITTED.

    Never True for a QUARANTINED or REJECTED candidate.
    """
    if not isinstance(envelope, dict):
        return False
    governance = envelope.get("governance")
    if not isinstance(governance, dict) or governance.get("admission_state") != "ADMITTED":
        return False
    return is_contract_consistent(envelope)


def finding_codes(envelope):
    """Convenience: the set of finding codes for an envelope."""
    return {finding.code for finding in validate_observation(envelope)}
