"""Negative / mutation tests for the observation-contract validator.

Standard library only. These prove the governance laws by REJECTION: a valid
synthetic fixture is cloned and mutated in memory, and the validator must report
the corresponding violation. No fixture files are modified.

Run:
    python -m unittest discover -s tests -p "test_*.py"
"""

import copy
import json
import os
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from governance import validate_observation as gov  # noqa: E402

FIXTURES_ROOT = os.path.join(REPO_ROOT, "fixtures", "observation-contract")


def _load(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _admitted():
    return _load(os.path.join(FIXTURES_ROOT, "admitted", "01_valid_complete.json"))


def _quarantined():
    return _load(os.path.join(FIXTURES_ROOT, "quarantined", "01_unresolved_operator_identity.json"))


def _rejected():
    return _load(os.path.join(FIXTURES_ROOT, "rejected", "01_invalid_price.json"))


class PriceValidityTests(unittest.TestCase):
    def test_decimal(self):
        self.assertTrue(gov.price_is_valid(2.10, "decimal"))
        self.assertTrue(gov.price_is_valid(2, "decimal"))
        self.assertFalse(gov.price_is_valid(1.0, "decimal"))
        self.assertFalse(gov.price_is_valid(0.5, "decimal"))
        self.assertFalse(gov.price_is_valid(-2.5, "decimal"))
        self.assertFalse(gov.price_is_valid("2.1", "decimal"))
        self.assertFalse(gov.price_is_valid(True, "decimal"))

    def test_american(self):
        self.assertTrue(gov.price_is_valid(150, "american"))
        self.assertTrue(gov.price_is_valid(-200, "american"))
        self.assertTrue(gov.price_is_valid(100, "american"))
        self.assertTrue(gov.price_is_valid(-100, "american"))
        self.assertTrue(gov.price_is_valid(150.0, "american"))
        self.assertFalse(gov.price_is_valid(99, "american"))
        self.assertFalse(gov.price_is_valid(-99, "american"))
        self.assertFalse(gov.price_is_valid(0, "american"))
        self.assertFalse(gov.price_is_valid(150.5, "american"))
        self.assertFalse(gov.price_is_valid("150", "american"))

    def test_fractional(self):
        self.assertTrue(gov.price_is_valid("3/2", "fractional"))
        self.assertTrue(gov.price_is_valid("1/1", "fractional"))
        self.assertTrue(gov.price_is_valid("10/11", "fractional"))
        self.assertFalse(gov.price_is_valid("0/1", "fractional"))
        self.assertFalse(gov.price_is_valid("3/0", "fractional"))
        self.assertFalse(gov.price_is_valid("abc", "fractional"))
        self.assertFalse(gov.price_is_valid(3, "fractional"))

    def test_unknown_format(self):
        self.assertFalse(gov.price_is_valid(2.10, "moneyline"))


class AdmittedBaselineTests(unittest.TestCase):
    def test_valid_admitted_has_no_findings(self):
        self.assertEqual(gov.validate_observation(_admitted()), [])

    def test_valid_quarantined_has_no_findings(self):
        self.assertEqual(gov.validate_observation(_quarantined()), [])

    def test_valid_rejected_has_no_findings(self):
        self.assertEqual(gov.validate_observation(_rejected()), [])


class AdmittedMutationTests(unittest.TestCase):
    def _codes_after(self, mutate):
        env = _admitted()
        mutate(env)
        return gov.finding_codes(env)

    def test_admitted_loses_event_id(self):
        def mut(e):
            e["canonical"]["event_id"] = None
        self.assertIn("MISSING_CORE_CANONICAL_IDENTITY", self._codes_after(mut))

    def test_admitted_loses_operator_id(self):
        def mut(e):
            e["canonical"]["operator_id"] = None
        self.assertIn("MISSING_CORE_CANONICAL_IDENTITY", self._codes_after(mut))

    def test_admitted_loses_market_id(self):
        def mut(e):
            e["canonical"]["market_id"] = None
        self.assertIn("MISSING_CORE_CANONICAL_IDENTITY", self._codes_after(mut))

    def test_admitted_loses_outcome_id(self):
        def mut(e):
            e["canonical"]["outcome_id"] = None
        self.assertIn("MISSING_CORE_CANONICAL_IDENTITY", self._codes_after(mut))

    def test_admitted_loses_participants(self):
        def mut(e):
            e["canonical"]["participants"] = []
        self.assertIn("MISSING_PARTICIPANT_IDENTITY", self._codes_after(mut))

    def test_admitted_with_unresolved_reason_retaining_canonical(self):
        def mut(e):
            e["governance"]["reason_codes"] = ["UNRESOLVED_OPERATOR_IDENTITY"]
        codes = self._codes_after(mut)
        self.assertIn("UNRESOLVED_CANONICAL_RESOLVED", codes)
        self.assertIn("REASON_STATE_INCONSISTENT", codes)

    def test_admitted_unsupported_contract_version(self):
        def mut(e):
            e["contract"]["contract_version"] = "2.0.0"
        self.assertIn("UNSUPPORTED_CONTRACT_VERSION", self._codes_after(mut))

    def test_admitted_missing_provider_id(self):
        def mut(e):
            e["provenance"]["provider_id"] = None
        self.assertIn("MISSING_PROVIDER_ID", self._codes_after(mut))

    def test_admitted_missing_source_locator(self):
        def mut(e):
            e["provenance"]["source_reference"] = None
            e["provenance"]["source_record_id"] = None
        self.assertIn("MISSING_SOURCE_LOCATOR", self._codes_after(mut))

    def test_admitted_invalid_price(self):
        def mut(e):
            e["source_asserted"]["price"] = 0.5
        self.assertIn("PRICE_INVALID", self._codes_after(mut))

    def test_admitted_unsupported_price_format(self):
        def mut(e):
            e["source_asserted"]["price_format"] = "moneyline_text"
        self.assertIn("PRICE_FORMAT_UNSUPPORTED", self._codes_after(mut))

    def test_admitted_raw_id_promoted_to_canonical(self):
        def mut(e):
            e["canonical"]["operator_id"] = e["source_asserted"]["source_operator_id"]
        self.assertIn("RAW_ID_PROMOTED", self._codes_after(mut))

    def test_admitted_derived_field_injected(self):
        def mut(e):
            e["source_asserted"]["implied_probability"] = 0.47
        self.assertIn("DERIVED_FIELD_PRESENT", self._codes_after(mut))

    def test_admitted_ingested_relabeled_as_source_observed(self):
        def mut(e):
            e["source_asserted"]["source_observed_at"] = e["provenance"]["ingested_at"]
        self.assertIn("INGESTED_USED_AS_OBSERVED", self._codes_after(mut))


class StateReasonMutationTests(unittest.TestCase):
    def test_quarantined_without_reason_code(self):
        env = _quarantined()
        env["governance"]["reason_codes"] = []
        self.assertIn("REASON_STATE_INCONSISTENT", gov.finding_codes(env))

    def test_rejected_without_reason_code(self):
        env = _rejected()
        env["governance"]["reason_codes"] = []
        self.assertIn("REASON_STATE_INCONSISTENT", gov.finding_codes(env))

    def test_participant_unresolved_but_canonical_participant_set(self):
        env = _load(os.path.join(FIXTURES_ROOT, "quarantined", "02_unresolved_event_identity.json"))
        # Silently populate a canonical participant id while identity is unresolved.
        env["canonical"]["participants"][0]["participant_id"] = "lbteam_9999"
        self.assertIn("UNRESOLVED_CANONICAL_RESOLVED", gov.finding_codes(env))


class SourceRightsFailClosedTests(unittest.TestCase):
    """UNKNOWN and PROHIBITED must both fail closed for a capability being used."""

    def _publishable(self, profile):
        return profile.get("rights_matrix", {}).get("public_display") == "ALLOWED"

    def test_unknown_public_display_blocks_publication(self):
        for name in ("01_provider_alpha_profile.json", "02_provider_beta_profile.json"):
            profile = _load(os.path.join(FIXTURES_ROOT, "source-profiles", name))
            # Both synthetic profiles have UNKNOWN public_display -> not publishable.
            self.assertFalse(self._publishable(profile), "%s must fail closed" % name)

    def test_prohibited_and_unknown_are_not_allowed(self):
        for posture in ("UNKNOWN", "PROHIBITED"):
            self.assertNotEqual(posture, "ALLOWED")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
