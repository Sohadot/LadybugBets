"""Validation of the LadybugBets observation-contract fixtures and vocabularies.

Standard library only. This module:

- confirms every JSON file parses;
- runs the reusable deterministic validator
  (governance.validate_observation) over every synthetic fixture and asserts
  each fixture is internally consistent with its own declared admission state;
- checks identity-mapping and source-profile fixtures;
- asserts the JSON Schema contracts and the validator share the same controlled
  vocabularies (no silent drift);
- performs repository hygiene checks (no secrets, no vendor-specific names).

Run:
    python -m unittest discover -s tests -p "test_*.py"
"""

import json
import os
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from governance import validate_observation as gov  # noqa: E402

FIXTURES_ROOT = os.path.join(REPO_ROOT, "fixtures", "observation-contract")
CONTRACTS_ROOT = os.path.join(REPO_ROOT, "contracts")

OBSERVATION_DIRS = ("admitted", "quarantined", "rejected")

# Vocabularies for the mapping and source-profile contracts (the observation
# vocabularies live in the validator module as the single source of truth).
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
MAPPING_ENTITY_TYPES = set(gov.IDENTITY_ENTITIES)

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
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield ("key", key)
            yield from _walk(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk(item)
    else:
        yield ("value", obj)


class ParsingTests(unittest.TestCase):
    def test_all_json_parses(self):
        for root in (FIXTURES_ROOT, CONTRACTS_ROOT):
            for path in _iter_json_files(root):
                try:
                    _load_json(path)
                except json.JSONDecodeError as exc:  # pragma: no cover
                    self.fail("JSON did not parse: %s (%s)" % (path, exc))


class FixtureConsistencyTests(unittest.TestCase):
    def test_observation_fixtures_exist(self):
        counts = {sub: 0 for sub in OBSERVATION_DIRS}
        for sub, _path, _data in _iter_observation_files():
            counts[sub] += 1
        for sub in OBSERVATION_DIRS:
            self.assertGreater(counts[sub], 0, "no fixtures under %s/" % sub)

    def test_directory_matches_admission_state(self):
        expected = {"admitted": "ADMITTED", "quarantined": "QUARANTINED", "rejected": "REJECTED"}
        for sub, path, data in _iter_observation_files():
            self.assertEqual(
                data["governance"]["admission_state"],
                expected[sub],
                "%s admission_state does not match its directory" % path,
            )

    def test_every_fixture_is_internally_consistent(self):
        """Each fixture must satisfy the invariants for its own declared state."""
        for _sub, path, data in _iter_observation_files():
            findings = gov.validate_observation(data)
            self.assertEqual(
                findings,
                [],
                "%s produced findings: %s" % (path, [(f.code, f.message) for f in findings]),
            )

    def test_rejected_fixtures_carry_reason_codes(self):
        for sub, path, data in _iter_observation_files():
            if sub in ("rejected", "quarantined"):
                self.assertTrue(
                    data["governance"].get("reason_codes"),
                    "%s must carry a reason code" % path,
                )

    def test_intended_rejection_reasons_present_and_evidence_backed(self):
        """Each machine-detectable rejected fixture (A) declares its intended
        reason and (B) the validator independently detects that defect."""
        expected = {
            "01_invalid_price.json": "INVALID_PRICE",
            "02_missing_provider_provenance.json": "MISSING_PROVIDER_PROVENANCE",
            "03_unsupported_contract_version.json": "INVALID_CONTRACT_VERSION",
            "04_invalid_price_format.json": "INVALID_PRICE_FORMAT",
        }
        seen = {}
        for sub, path, data in _iter_observation_files():
            if sub != "rejected":
                continue
            name = os.path.basename(path)
            if name in expected:
                seen[name] = data
        for name, code in expected.items():
            self.assertIn(name, seen, "missing rejected fixture %s" % name)
            data = seen[name]
            # (A) declared reason present
            self.assertIn(code, data["governance"].get("reason_codes", []), "%s reason" % name)
            # (B) validator independently detects the defect
            self.assertIn(
                code,
                gov.detect_machine_conditions(data),
                "%s defect not independently detected" % name,
            )


class IdentityMappingTests(unittest.TestCase):
    def _mapping_files(self):
        return list(_iter_json_files(os.path.join(FIXTURES_ROOT, "identity-mappings")))

    def test_mapping_fixtures_exist(self):
        self.assertTrue(self._mapping_files(), "no identity-mapping fixtures found")

    def test_mapping_controlled_vocabulary(self):
        for path in self._mapping_files():
            data = _load_json(path)
            self.assertIn(data.get("decision_basis"), MAPPING_DECISION_BASES, path)
            self.assertIn(data.get("status"), MAPPING_STATUSES, path)
            self.assertIn(data.get("entity_type"), MAPPING_ENTITY_TYPES, path)

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
        return list(_iter_json_files(os.path.join(FIXTURES_ROOT, "source-profiles")))

    def test_profile_fixtures_exist(self):
        self.assertTrue(self._profile_files(), "no source-profile fixtures found")

    def test_rights_matrix_uses_controlled_postures(self):
        for path in self._profile_files():
            data = _load_json(path)
            matrix = data.get("rights_matrix", {})
            for capability in RIGHTS_CAPABILITIES:
                self.assertIn(capability, matrix, "%s missing capability %s" % (path, capability))
            for capability, posture in matrix.items():
                self.assertIn(capability, RIGHTS_CAPABILITIES, "%s unknown %s" % (path, capability))
                self.assertIn(posture, RIGHTS_POSTURES, "%s bad posture %r" % (path, posture))


class SchemaValidatorDriftTests(unittest.TestCase):
    """The JSON Schema contracts and the validator must share vocabularies."""

    def _schema(self, name):
        return _load_json(os.path.join(CONTRACTS_ROOT, name))

    def test_envelope_schema_vocab_matches_validator(self):
        schema = self._schema("observation-envelope.schema.json")
        defs = schema["$defs"]
        self.assertEqual(
            set(defs["admission_state"]["enum"]), set(gov.ADMISSION_STATES),
            "admission_state vocab drift",
        )
        self.assertEqual(
            set(defs["reason_code"]["enum"]), set(gov.REASON_CODES),
            "reason_code vocab drift",
        )
        self.assertEqual(
            set(defs["supported_price_format"]["enum"]), set(gov.VALID_PRICE_FORMATS),
            "supported_price_format vocab drift",
        )

    def test_mapping_schema_vocab_matches_constants(self):
        schema = self._schema("identity-mapping.schema.json")
        props = schema["properties"]
        self.assertEqual(set(props["entity_type"]["enum"]), MAPPING_ENTITY_TYPES)
        self.assertEqual(set(props["status"]["enum"]), MAPPING_STATUSES)
        self.assertEqual(set(props["decision_basis"]["enum"]), MAPPING_DECISION_BASES)

    def test_source_profile_schema_postures_match_constants(self):
        schema = self._schema("source-profile.schema.json")
        self.assertEqual(set(schema["$defs"]["posture"]["enum"]), RIGHTS_POSTURES)
        matrix_props = schema["properties"]["rights_matrix"]["properties"]
        self.assertEqual(set(matrix_props.keys()), RIGHTS_CAPABILITIES)

    def test_admission_critical_fields_exist_in_schema(self):
        """Every field the validator treats as admission-critical required must
        exist as a declared property in the JSON Schema (drift guard only; this
        does not evaluate the schema)."""
        schema = self._schema("observation-envelope.schema.json")
        section_props = schema["properties"]
        for section, fields in gov.ADMISSION_CRITICAL_FIELDS.items():
            props = section_props[section]["properties"]
            for field in fields:
                self.assertIn(field, props, "%s.%s missing from schema" % (section, field))
        # ADMITTED canonical required fields appear in an ADMITTED conditional branch.
        canonical_required_sets = []
        for branch in schema.get("allOf", []):
            canonical = branch.get("then", {}).get("properties", {}).get("canonical", {})
            if "required" in canonical:
                canonical_required_sets.append(set(canonical["required"]))
        self.assertTrue(
            any(set(gov.ADMITTED_CANONICAL_REQUIRED) <= req for req in canonical_required_sets),
            "ADMITTED canonical required fields not represented in schema conditionals",
        )

    def test_all_contract_schemas_declare_2020_12(self):
        for path in _iter_json_files(CONTRACTS_ROOT):
            data = _load_json(path)
            self.assertEqual(
                data.get("$schema"),
                "https://json-schema.org/draft/2020-12/schema",
                "%s is not JSON Schema draft 2020-12" % path,
            )


class RepositoryHygieneTests(unittest.TestCase):
    def _all_governed_files(self):
        return list(_iter_json_files(FIXTURES_ROOT)) + list(_iter_json_files(CONTRACTS_ROOT))

    def test_no_obvious_secrets(self):
        for path in self._all_governed_files():
            data = _load_json(path)
            for kind, value in _walk(data):
                if kind == "key":
                    lowered = value.lower()
                    for needle in SECRET_KEY_SUBSTRINGS:
                        self.assertNotIn(needle, lowered, "%s secret-like key %r" % (path, value))
                elif kind == "value" and isinstance(value, str):
                    lowered = value.lower()
                    for marker in SECRET_VALUE_MARKERS:
                        self.assertNotIn(marker, lowered, "%s secret-like value %r" % (path, value))

    def test_contracts_and_fixtures_have_no_vendor_names(self):
        for path in self._all_governed_files():
            with open(path, "r", encoding="utf-8") as handle:
                text = handle.read().lower()
            for vendor in VENDOR_DENYLIST:
                self.assertNotIn(vendor, text, "%s contains vendor name %r" % (path, vendor))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
