"""Deterministic contract validator for LBOC-001 observation envelopes.

Standard library only. This is a **contract validator**, not a production
ingestion engine. Given an already-parsed candidate envelope (a dict), it
returns deterministic findings describing every way the envelope violates the
admission invariants for its own declared `governance.admission_state`.

It MUST NOT (and does not):

- call APIs or read a database,
- resolve identities (no fuzzy logic, no canonical-id generation),
- mutate the record,
- publish anything.

The governed laws it enforces are defined in:
- docs/OBSERVATION_CONTRACT.md   (LBOC-001)
- docs/IDENTITY_RESOLUTION.md    (LBIR-001)
- docs/TEMPORAL_GOVERNANCE.md
- docs/METHODOLOGY.md            (price validity basis)

The controlled vocabularies below are the single source of truth for the
repository-local gate; tests assert that the JSON Schema contracts declare the
same vocabularies so the two encodings cannot silently drift.
"""

import re

SUPPORTED_CONTRACT_VERSION = "1.0.0"

ADMISSION_STATES = ("ADMITTED", "QUARANTINED", "REJECTED")

VALID_PRICE_FORMATS = ("decimal", "american", "fractional")

# Complete, symmetric identity reason-code vocabulary plus non-identity codes.
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

REASON_CODES = tuple(
    ["UNRESOLVED_%s_IDENTITY" % e.upper() for e in IDENTITY_ENTITIES]
    + ["AMBIGUOUS_%s_IDENTITY" % e.upper() for e in IDENTITY_ENTITIES]
    + [
        "MISSING_REQUIRED_SOURCE_FIELD",
        "MISSING_SOURCE_LOCATOR",
        "INVALID_PRICE",
        "INVALID_PRICE_FORMAT",
        "MISSING_PROVIDER_PROVENANCE",
        "TEMPORAL_AMBIGUITY",
        "CONFLICTING_SOURCE_ASSERTIONS",
        "INVALID_CONTRACT_VERSION",
    ]
)

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

# Raw source id -> canonical id pairs that must never be identical (no raw id
# silently promoted to canonical).
RAW_CANONICAL_ID_PAIRS = (
    ("source_event_id", "event_id"),
    ("source_operator_id", "operator_id"),
    ("source_market_id", "market_id"),
    ("source_outcome_id", "outcome_id"),
    ("source_competition_id", "competition_id"),
)

# Derived-analysis keys that must never appear inside a source observation.
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
    """A single deterministic contract violation."""

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


def validate_observation(envelope):
    """Return a list of Finding objects for one candidate envelope.

    An empty list means the envelope is internally consistent with the
    admission invariants for its own declared admission_state. This function
    never raises for a well-typed dict; structural problems are returned as
    findings.
    """
    findings = []

    if not isinstance(envelope, dict):
        return [Finding("MALFORMED_ENVELOPE", "envelope is not an object")]

    # --- Structural sections -------------------------------------------------
    for section in ("contract", "provenance", "source_asserted", "canonical", "governance"):
        if not isinstance(envelope.get(section), dict):
            findings.append(Finding("MISSING_SECTION", "missing/!object section: %s" % section))
    if findings:
        # Without the sections we cannot check the rest meaningfully.
        return findings

    contract = envelope["contract"]
    provenance = envelope["provenance"]
    source = envelope["source_asserted"]
    canonical = envelope["canonical"]
    governance = envelope["governance"]

    if not _is_nonempty_str(contract.get("observation_id")):
        findings.append(Finding("MISSING_OBSERVATION_ID", "contract.observation_id required"))
    if not _is_nonempty_str(contract.get("contract_version")):
        findings.append(Finding("MISSING_CONTRACT_VERSION", "contract.contract_version required"))

    state = governance.get("admission_state")
    if state not in ADMISSION_STATES:
        findings.append(Finding("STATE_INVALID", "unknown admission_state %r" % state))

    # --- Reason codes / state consistency ------------------------------------
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

    # --- Universal laws (all states) -----------------------------------------
    for key in _walk_keys(envelope):
        if isinstance(key, str) and key.lower() in FORBIDDEN_DERIVED_KEYS:
            findings.append(Finding("DERIVED_FIELD_PRESENT", "derived field in envelope: %s" % key))

    ingested_at = provenance.get("ingested_at")
    observed_at = source.get("source_observed_at")
    if observed_at is not None and ingested_at is not None and observed_at == ingested_at:
        findings.append(
            Finding("INGESTED_USED_AS_OBSERVED", "ingested_at equals source_observed_at")
        )

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

    # Unresolved/ambiguous identity reasons must leave the canonical field null.
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

    # --- Stronger invariants for ADMITTED and QUARANTINED --------------------
    if state in ("ADMITTED", "QUARANTINED"):
        if contract.get("contract_version") != SUPPORTED_CONTRACT_VERSION:
            findings.append(
                Finding(
                    "UNSUPPORTED_CONTRACT_VERSION",
                    "%s requires contract_version %s" % (state, SUPPORTED_CONTRACT_VERSION),
                )
            )
        if not _is_nonempty_str(provenance.get("provider_id")):
            findings.append(
                Finding("MISSING_PROVIDER_ID", "%s requires governed provider_id" % state)
            )
        if not (
            _is_nonempty_str(provenance.get("source_reference"))
            or _is_nonempty_str(provenance.get("source_record_id"))
        ):
            findings.append(
                Finding(
                    "MISSING_SOURCE_LOCATOR",
                    "%s requires source_reference or source_record_id" % state,
                )
            )
        price_format = source.get("price_format")
        if price_format not in VALID_PRICE_FORMATS:
            findings.append(
                Finding("PRICE_FORMAT_UNSUPPORTED", "unsupported price_format %r" % price_format)
            )
        elif not price_is_valid(source.get("price"), price_format):
            findings.append(
                Finding(
                    "PRICE_INVALID",
                    "price %r invalid for format %r" % (source.get("price"), price_format),
                )
            )

    # --- Strongest invariants for ADMITTED -----------------------------------
    if state == "ADMITTED":
        for field in CORE_ADMITTED_CANONICAL:
            if not _is_nonempty_str(canonical.get(field)):
                findings.append(
                    Finding(
                        "MISSING_CORE_CANONICAL_IDENTITY",
                        "ADMITTED requires canonical.%s" % field,
                    )
                )
        # DEC-017: participant-bearing event identity. An ADMITTED event must
        # carry at least one resolved canonical participant with a role.
        participants = canonical.get("participants", []) or []
        resolved = [
            p
            for p in participants
            if isinstance(p, dict)
            and _is_nonempty_str(p.get("participant_id"))
            and _is_nonempty_str(p.get("role"))
        ]
        if not resolved:
            findings.append(
                Finding(
                    "MISSING_PARTICIPANT_IDENTITY",
                    "ADMITTED event requires resolved canonical participants (DEC-017)",
                )
            )

    return findings


def is_admissible(envelope):
    """True when the envelope satisfies the invariants for its declared state."""
    return not validate_observation(envelope)


def finding_codes(envelope):
    """Convenience: the set of finding codes for an envelope."""
    return {finding.code for finding in validate_observation(envelope)}
