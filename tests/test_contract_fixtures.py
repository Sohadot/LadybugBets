"""Deterministic validation of the LadybugBets observation contract fixtures.

Standard library only. This is CONTRACT VALIDATION, not an ingestion engine.
It verifies that the synthetic fixtures under fixtures/observation-contract/
and the machine-readable contracts under contracts/ uphold the Sprint 1 laws
(LBOC-001, LBIR-001, and the governance documents).

Run:
    python -m unittest discover -s tests -p "test_*.py"
"""

import json
import os
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES_ROOT = os.path.join(REPO_ROOT, "fixtures", "observation-contract")
CONTRACTS_ROOT = os.path.join(REPO_ROOT, "contracts")

OBSERVATION_DIRS = ("admitted", "quarantined", "rejected")

ADMISSION_STATES = {"ADMITTED", "QUARANTINED", "REJECTED"}

REASON_CODES = {
    "UNRESOLVED_EVENT_IDENTITY",
    "AMBIGUOUS_EVENT_IDENTITY",
    "UNRESOLVED_OPERATOR_IDENTITY",
    "AMBIGUOUS_OPERATOR_IDENTITY",
    "UNRESOLVED_MARKET_IDENTITY",
    "UNRESOLVED_OUTCOME_IDENTITY",
    "UNRESOLVED_PARTICIPANT_IDENTITY",
    "MISSING_REQUIRED_SOURCE_FIELD",
    "INVALID_PRICE",
    "INVALID_PRICE_FORMAT",
    "MISSING_PROVIDER_PROVENANCE",
    "TEMPORAL_AMBIGUITY",
    "CONFLICTING_SOURCE_ASSERTIONS",
    "INVALID_CONTRACT_VERSION",
}

# Reason code -> canonical field(s) that MUST remain unresolved (None) when the
# code is present. Enforces "unresolved canonical identity is not represented as
# resolved."
UNRESOLVED_CANONICAL = {
    "UNRESOLVED_EVENT_IDENTITY": "event_id",
    "AMBIGUOUS_EVENT_IDENTITY": "event_id",
    "UNRESOLVED_OPERATOR_IDENTITY": "operator_id",
    "AMBIGUOUS_OPERATOR_IDENTITY": "operator_id",
    "UNRESOLVED_MARKET_IDENTITY": "market_id",
    "UNRESOLVED_OUTCOME_IDENTITY": "outcome_id",
}

VALID_PRICE_FORMATS = {"decimal", "american", "fractional"}

RIGHTS_POSTURES = {"ALLOWED", "PROHIBITED", "UNKNOWN"}
RIGHTS_CAPABILITIES = {
    "ingest_use",
    "cache",
    "retain_historical",
    "derive_calculations",
    "public_display",
    "redistribute_raw",
    "redistribute_derived",
}

MAPPING_DECISION_BASES = {
    "governed_registry_entry",
    "curated_alias",
    "manual_review",
    "provider_declared_identifier",
}
MAPPING_STATUSES = {"active", "proposed", "deprecated", "rejected"}

# Derived analytical concepts must never live inside a source observation.
FORBIDDEN_DERIVED_KEYS = {
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
)
SECRET_VALUE_MARKERS = (
    "-----begin",
    "akia",
    "bearer ",
    "password=",
    "api_key=",
    "aws_secret",
)

# Real odds vendors / bookmakers / data suppliers that must not appear as
# vendor-specific names. Fixtures and contracts must be vendor-neutral/synthetic.
VENDOR_DENYLIST = (
    "bet365",
    "william hill",
    "williamhill",
    "pinnacle",
    "draftkings",
    "fanduel",
    "betfair",
    "oddsjam",
    "the odds api",
    "theoddsapi",
    "sportradar",
    "betmgm",
    "caesars",
    "paddy power",
    "paddypower",
    "ladbrokes",
    "unibet",
    "betway",
    "smarkets",
    "betfred",
    "sky bet",
    "skybet",
    "pointsbet",
    "betrivers",
    "bovada",
    "coral",
    "betvictor",
    "opta",
    "stats perform",
    "flashscore",
)


def _load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _iter_json_files(root):
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in sorted(filenames):
            if name.endswith(".json"):
                yield os.path.join(dirpath, name)


def _iter_observation_files():
    for sub in OBSERVATION_DIRS:
        directory = os.path.join(FIXTURES_ROOT, sub)
        for path in _iter_json_files(directory):
            yield sub, path, _load_json(path)


def _walk(obj):
    """Yield ('key', name) and ('value', scalar) pairs recursively."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield ("key", key)
            yield from _walk(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk(item)
    else:
        yield ("value", obj)


class ObservationEnvelopeTests(unittest.TestCase):
    def test_all_json_parses(self):
        for root in (FIXTURES_ROOT, CONTRACTS_ROOT):
            for path in _iter_json_files(root):
                try:
                    _load_json(path)
                except json.JSONDecodeError as exc:  # pragma: no cover
                    self.fail("JSON did not parse: %s (%s)" % (path, exc))

    def test_observation_fixtures_exist(self):
        counts = {sub: 0 for sub in OBSERVATION_DIRS}
        for sub, _path, _data in _iter_observation_files():
            counts[sub] += 1
        for sub in OBSERVATION_DIRS:
            self.assertGreater(counts[sub], 0, "no fixtures under %s/" % sub)

    def test_required_sections_present(self):
        required = ("contract", "provenance", "source_asserted", "canonical", "governance")
        for _sub, path, data in _iter_observation_files():
            for section in required:
                self.assertIn(section, data, "%s missing section %s" % (path, section))
            self.assertIn("contract_version", data["contract"], path)
            self.assertIn("observation_id", data["contract"], path)

    def test_admission_states_controlled(self):
        for _sub, path, data in _iter_observation_files():
            state = data["governance"].get("admission_state")
            self.assertIn(state, ADMISSION_STATES, "%s bad admission_state %r" % (path, state))

    def test_directory_matches_admission_state(self):
        expected = {"admitted": "ADMITTED", "quarantined": "QUARANTINED", "rejected": "REJECTED"}
        for sub, path, data in _iter_observation_files():
            self.assertEqual(
                data["governance"]["admission_state"],
                expected[sub],
                "%s admission_state does not match its directory" % path,
            )

    def test_reason_codes_controlled_and_present_when_required(self):
        for _sub, path, data in _iter_observation_files():
            gov = data["governance"]
            state = gov["admission_state"]
            codes = gov.get("reason_codes", [])
            for code in codes:
                self.assertIn(code, REASON_CODES, "%s unknown reason code %r" % (path, code))
            if state in ("QUARANTINED", "REJECTED"):
                self.assertTrue(codes, "%s (%s) must carry >=1 reason code" % (path, state))
            if state == "ADMITTED":
                self.assertEqual(codes, [], "%s ADMITTED must have empty reason_codes" % path)

    def test_raw_and_canonical_operator_are_distinct_fields(self):
        for _sub, path, data in _iter_observation_files():
            src = data["source_asserted"]
            can = data["canonical"]
            # Distinct field locations must both be modeled.
            self.assertTrue(
                "source_operator_id" in src or "source_operator_name" in src,
                "%s missing source operator identity fields" % path,
            )
            self.assertIn("operator_id", can, "%s missing canonical operator_id field" % path)
            s_id = src.get("source_operator_id")
            c_id = can.get("operator_id")
            if s_id and c_id:
                self.assertNotEqual(
                    s_id, c_id, "%s raw and canonical operator ids are identical" % path
                )

    def test_raw_and_canonical_event_are_distinct_fields(self):
        for _sub, path, data in _iter_observation_files():
            src = data["source_asserted"]
            can = data["canonical"]
            self.assertIn("source_event_id", src, "%s missing source_event_id field" % path)
            self.assertIn("event_id", can, "%s missing canonical event_id field" % path)
            s_id = src.get("source_event_id")
            c_id = can.get("event_id")
            if s_id and c_id:
                self.assertNotEqual(
                    s_id, c_id, "%s raw and canonical event ids are identical" % path
                )

    def test_no_raw_id_promoted_to_canonical(self):
        id_pairs = (
            ("source_event_id", "event_id"),
            ("source_operator_id", "operator_id"),
            ("source_market_id", "market_id"),
            ("source_outcome_id", "outcome_id"),
            ("source_competition_id", "competition_id"),
        )
        for _sub, path, data in _iter_observation_files():
            src = data["source_asserted"]
            can = data["canonical"]
            for s_key, c_key in id_pairs:
                s_val = src.get(s_key)
                c_val = can.get(c_key)
                if s_val and c_val:
                    self.assertNotEqual(
                        s_val,
                        c_val,
                        "%s promotes raw %s into canonical %s" % (path, s_key, c_key),
                    )
            # Participants: canonical ids must be disjoint from source ids.
            source_pids = {
                p.get("source_participant_id")
                for p in src.get("source_participants", [])
                if p.get("source_participant_id")
            }
            canon_pids = {
                p.get("participant_id")
                for p in can.get("participants", [])
                if p.get("participant_id")
            }
            overlap = source_pids & canon_pids
            self.assertFalse(
                overlap, "%s participant raw ids reused as canonical: %s" % (path, overlap)
            )

    def test_ingested_at_not_used_as_source_observed_at(self):
        for _sub, path, data in _iter_observation_files():
            ingested = data["provenance"].get("ingested_at")
            observed = data["source_asserted"].get("source_observed_at")
            if observed is not None and ingested is not None:
                self.assertNotEqual(
                    observed,
                    ingested,
                    "%s uses ingested_at as source_observed_at" % path,
                )

    def test_unresolved_identity_not_represented_as_resolved(self):
        for _sub, path, data in _iter_observation_files():
            codes = data["governance"].get("reason_codes", [])
            can = data["canonical"]
            for code in codes:
                field = UNRESOLVED_CANONICAL.get(code)
                if field is not None:
                    self.assertIsNone(
                        can.get(field),
                        "%s has %s but canonical.%s is resolved" % (path, code, field),
                    )
            if "UNRESOLVED_PARTICIPANT_IDENTITY" in codes:
                for participant in can.get("participants", []):
                    self.assertIsNone(
                        participant.get("participant_id"),
                        "%s claims unresolved participants but one is resolved" % path,
                    )

    def test_admitted_core_canonical_identities_resolved(self):
        for sub, path, data in _iter_observation_files():
            if sub != "admitted":
                continue
            can = data["canonical"]
            for field in ("event_id", "operator_id", "market_id", "outcome_id"):
                self.assertIsNotNone(
                    can.get(field),
                    "%s ADMITTED but canonical.%s is unresolved" % (path, field),
                )

    def test_admitted_price_format_controlled(self):
        for sub, path, data in _iter_observation_files():
            if sub != "admitted":
                continue
            fmt = data["source_asserted"].get("price_format")
            self.assertIn(
                fmt, VALID_PRICE_FORMATS, "%s ADMITTED with bad price_format %r" % (path, fmt)
            )

    def test_no_derived_fields_in_source_observations(self):
        for _sub, path, data in _iter_observation_files():
            for kind, value in _walk(data):
                if kind == "key" and value.lower() in FORBIDDEN_DERIVED_KEYS:
                    self.fail("%s contains derived-analysis field %r" % (path, value))


class IdentityMappingTests(unittest.TestCase):
    def _mapping_files(self):
        directory = os.path.join(FIXTURES_ROOT, "identity-mappings")
        return list(_iter_json_files(directory))

    def test_mapping_fixtures_exist(self):
        self.assertTrue(self._mapping_files(), "no identity-mapping fixtures found")

    def test_mapping_controlled_vocabulary(self):
        for path in self._mapping_files():
            data = _load_json(path)
            self.assertIn(data.get("decision_basis"), MAPPING_DECISION_BASES, path)
            self.assertIn(data.get("status"), MAPPING_STATUSES, path)
            self.assertIn(
                data.get("entity_type"),
                {
                    "sport",
                    "competition",
                    "participant",
                    "event",
                    "operator",
                    "market",
                    "outcome",
                    "jurisdiction",
                },
                path,
            )

    def test_mapping_has_source_key_and_distinct_canonical(self):
        for path in self._mapping_files():
            data = _load_json(path)
            self.assertTrue(
                data.get("source_native_id") or data.get("source_label"),
                "%s mapping has no source-side key" % path,
            )
            canonical_id = data.get("canonical_id")
            self.assertTrue(canonical_id, "%s mapping missing canonical_id" % path)
            if data.get("source_native_id"):
                self.assertNotEqual(
                    data["source_native_id"],
                    canonical_id,
                    "%s maps a raw id onto an identical canonical id" % path,
                )


class SourceProfileTests(unittest.TestCase):
    def _profile_files(self):
        directory = os.path.join(FIXTURES_ROOT, "source-profiles")
        return list(_iter_json_files(directory))

    def test_profile_fixtures_exist(self):
        self.assertTrue(self._profile_files(), "no source-profile fixtures found")

    def test_rights_matrix_uses_controlled_postures(self):
        for path in self._profile_files():
            data = _load_json(path)
            matrix = data.get("rights_matrix", {})
            for capability in RIGHTS_CAPABILITIES:
                self.assertIn(capability, matrix, "%s missing capability %s" % (path, capability))
            for capability, posture in matrix.items():
                self.assertIn(
                    capability, RIGHTS_CAPABILITIES, "%s unknown capability %s" % (path, capability)
                )
                self.assertIn(
                    posture, RIGHTS_POSTURES, "%s bad posture %r for %s" % (path, posture, capability)
                )


class RepositoryHygieneTests(unittest.TestCase):
    def _all_governed_files(self):
        paths = list(_iter_json_files(FIXTURES_ROOT))
        paths.extend(_iter_json_files(CONTRACTS_ROOT))
        return paths

    def test_no_obvious_secrets(self):
        for path in self._all_governed_files():
            data = _load_json(path)
            for kind, value in _walk(data):
                if kind == "key":
                    lowered = value.lower()
                    for needle in SECRET_KEY_SUBSTRINGS:
                        self.assertNotIn(
                            needle, lowered, "%s has secret-like key %r" % (path, value)
                        )
                elif kind == "value" and isinstance(value, str):
                    lowered = value.lower()
                    for marker in SECRET_VALUE_MARKERS:
                        self.assertNotIn(
                            marker, lowered, "%s has secret-like value in %r" % (path, value)
                        )

    def test_contracts_and_fixtures_have_no_vendor_names(self):
        for path in self._all_governed_files():
            with open(path, "r", encoding="utf-8") as handle:
                text = handle.read().lower()
            for vendor in VENDOR_DENYLIST:
                self.assertNotIn(
                    vendor, text, "%s contains vendor-specific name %r" % (path, vendor)
                )

    def test_contract_schemas_declare_2020_12(self):
        for path in _iter_json_files(CONTRACTS_ROOT):
            data = _load_json(path)
            self.assertEqual(
                data.get("$schema"),
                "https://json-schema.org/draft/2020-12/schema",
                "%s is not JSON Schema draft 2020-12" % path,
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
