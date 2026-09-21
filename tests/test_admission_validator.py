"""Negative / mutation tests for the observation-contract validator.

Standard library only. These prove the governance laws by REJECTION: a valid
synthetic fixture is cloned and mutated in memory, and the validator must report
the corresponding violation. No fixture files are modified.

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


def _load(*parts):
    with open(os.path.join(FIXTURES_ROOT, *parts), "r", encoding="utf-8") as handle:
        return json.load(handle)


def _admitted():
    return _load("admitted", "01_valid_complete.json")


def _quarantined():
    return _load("quarantined", "01_unresolved_operator_identity.json")


def _rejected():
    return _load("rejected", "01_invalid_price.json")


class ApiSemanticsTests(unittest.TestCase):
    def test_is_admissible_removed(self):
        self.assertFalse(hasattr(gov, "is_admissible"), "is_admissible must be removed")

    def test_consistent_admitted(self):
        env = _admitted()
        self.assertTrue(gov.is_contract_consistent(env))
        self.assertTrue(gov.is_admitted(env))

    def test_consistent_quarantined(self):
        env = _quarantined()
        self.assertTrue(gov.is_contract_consistent(env))
        self.assertFalse(gov.is_admitted(env))

    def test_consistent_rejected(self):
        env = _rejected()
        self.assertTrue(gov.is_contract_consistent(env))
        self.assertFalse(gov.is_admitted(env))

    def test_inconsistent_envelope_is_neither(self):
        env = _admitted()
        env["canonical"]["event_id"] = None
        self.assertFalse(gov.is_contract_consistent(env))
        self.assertFalse(gov.is_admitted(env))


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
        self.assertFalse(gov.price_is_valid("0/1", "fractional"))
        self.assertFalse(gov.price_is_valid("3/0", "fractional"))
        self.assertFalse(gov.price_is_valid("abc", "fractional"))
        self.assertFalse(gov.price_is_valid(3, "fractional"))

    def test_unknown_format(self):
        self.assertFalse(gov.price_is_valid(2.10, "moneyline"))


class AdmittedMutationTests(unittest.TestCase):
    def _codes_after(self, mutate):
        env = _admitted()
        mutate(env)
        return gov.finding_codes(env)

    def test_admitted_loses_event_id(self):
        self.assertIn(
            "MISSING_CORE_CANONICAL_IDENTITY",
            self._codes_after(lambda e: e["canonical"].__setitem__("event_id", None)),
        )

    def test_admitted_loses_operator_id(self):
        self.assertIn(
            "MISSING_CORE_CANONICAL_IDENTITY",
            self._codes_after(lambda e: e["canonical"].__setitem__("operator_id", None)),
        )

    def test_admitted_loses_market_id(self):
        self.assertIn(
            "MISSING_CORE_CANONICAL_IDENTITY",
            self._codes_after(lambda e: e["canonical"].__setitem__("market_id", None)),
        )

    def test_admitted_loses_outcome_id(self):
        self.assertIn(
            "MISSING_CORE_CANONICAL_IDENTITY",
            self._codes_after(lambda e: e["canonical"].__setitem__("outcome_id", None)),
        )

    def test_admitted_with_unresolved_reason_retaining_canonical(self):
        def mut(e):
            e["governance"]["reason_codes"] = ["UNRESOLVED_OPERATOR_IDENTITY"]
        codes = self._codes_after(mut)
        self.assertIn("UNRESOLVED_CANONICAL_RESOLVED", codes)
        self.assertIn("REASON_STATE_INCONSISTENT", codes)

    def test_admitted_unsupported_contract_version(self):
        self.assertIn(
            "INVALID_CONTRACT_VERSION",
            self._codes_after(lambda e: e["contract"].__setitem__("contract_version", "2.0.0")),
        )

    def test_admitted_missing_provider(self):
        self.assertIn(
            "MISSING_PROVIDER_PROVENANCE",
            self._codes_after(lambda e: e["provenance"].__setitem__("provider_id", None)),
        )

    def test_admitted_missing_source_locator(self):
        def mut(e):
            e["provenance"]["source_reference"] = None
            e["provenance"]["source_record_id"] = None
        self.assertIn("MISSING_SOURCE_LOCATOR", self._codes_after(mut))

    def test_admitted_invalid_price(self):
        self.assertIn(
            "INVALID_PRICE",
            self._codes_after(lambda e: e["source_asserted"].__setitem__("price", 0.5)),
        )

    def test_admitted_unsupported_price_format(self):
        self.assertIn(
            "INVALID_PRICE_FORMAT",
            self._codes_after(lambda e: e["source_asserted"].__setitem__("price_format", "xx")),
        )

    def test_admitted_raw_id_promoted_to_canonical(self):
        def mut(e):
            e["canonical"]["operator_id"] = e["source_asserted"]["source_operator_id"]
        self.assertIn("RAW_ID_PROMOTED", self._codes_after(mut))

    def test_admitted_derived_field_injected(self):
        self.assertIn(
            "DERIVED_FIELD_PRESENT",
            self._codes_after(lambda e: e["source_asserted"].__setitem__("implied_probability", 0.4)),
        )


class TemporalSemanticsTests(unittest.TestCase):
    def test_equal_timestamps_are_not_a_violation(self):
        env = _admitted()
        env["source_asserted"]["source_observed_at"] = env["provenance"]["ingested_at"]
        codes = gov.finding_codes(env)
        self.assertNotIn("INGESTED_USED_AS_OBSERVED", codes)
        self.assertTrue(gov.is_admitted(env), "equal timestamps must remain admissible")

    def test_missing_source_observed_at_remains_admissible(self):
        env = _load("admitted", "05_missing_source_observed_at.json")
        self.assertIsNone(env["source_asserted"]["source_observed_at"])
        self.assertTrue(gov.is_admitted(env))


class FootballParticipantProfileTests(unittest.TestCase):
    def _codes(self, participants):
        env = _admitted()
        env["canonical"]["participants"] = participants
        return gov.finding_codes(env)

    def _home(self, pid="lbteam_0001"):
        return {"participant_id": pid, "participant_display_name": "Home", "role": "home"}

    def _away(self, pid="lbteam_0002"):
        return {"participant_id": pid, "participant_display_name": "Away", "role": "away"}

    def test_valid_home_away_pair_passes(self):
        env = _admitted()
        self.assertTrue(gov.is_admitted(env))

    def test_only_home_fails(self):
        self.assertIn("MISSING_PARTICIPANT_IDENTITY", self._codes([self._home()]))

    def test_only_away_fails(self):
        self.assertIn("MISSING_PARTICIPANT_IDENTITY", self._codes([self._away()]))

    def test_duplicate_home_role_fails(self):
        codes = self._codes([self._home("lbteam_0001"), self._home("lbteam_0002")])
        self.assertIn("DUPLICATE_PARTICIPANT_ROLE", codes)

    def test_same_participant_id_for_home_and_away_fails(self):
        codes = self._codes([self._home("lbteam_0001"), self._away("lbteam_0001")])
        self.assertIn("NON_DISTINCT_PARTICIPANTS", codes)


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
        env = _load("quarantined", "02_unresolved_event_identity.json")
        env["canonical"]["participants"][0]["participant_id"] = "lbteam_9999"
        self.assertIn("UNRESOLVED_CANONICAL_RESOLVED", gov.finding_codes(env))


class ReasonEvidenceTests(unittest.TestCase):
    """Declared machine-detectable rejection reasons must be evidence-backed."""

    def _rejected_from_valid(self, reason):
        env = _admitted()  # a fully valid candidate (no real defect)
        env["governance"]["admission_state"] = "REJECTED"
        env["governance"]["reason_codes"] = [reason]
        return env

    def test_fake_invalid_price(self):
        self.assertIn("REASON_EVIDENCE_MISSING", gov.finding_codes(self._rejected_from_valid("INVALID_PRICE")))

    def test_fake_invalid_price_format(self):
        self.assertIn(
            "REASON_EVIDENCE_MISSING", gov.finding_codes(self._rejected_from_valid("INVALID_PRICE_FORMAT"))
        )

    def test_fake_missing_provider(self):
        self.assertIn(
            "REASON_EVIDENCE_MISSING",
            gov.finding_codes(self._rejected_from_valid("MISSING_PROVIDER_PROVENANCE")),
        )

    def test_fake_invalid_contract_version(self):
        self.assertIn(
            "REASON_EVIDENCE_MISSING",
            gov.finding_codes(self._rejected_from_valid("INVALID_CONTRACT_VERSION")),
        )

    def test_real_defect_cannot_be_admitted(self):
        env = _admitted()
        env["source_asserted"]["price"] = 0.5  # invalid decimal
        self.assertIn("INVALID_PRICE", gov.finding_codes(env))
        self.assertFalse(gov.is_admitted(env))

    def test_real_defect_cannot_be_quarantined(self):
        env = _quarantined()
        env["source_asserted"]["price"] = 0.5  # invalid decimal
        codes = gov.finding_codes(env)
        self.assertIn("INVALID_PRICE", codes)
        self.assertFalse(gov.is_contract_consistent(env))


class DetectMachineConditionsTests(unittest.TestCase):
    def test_detect_does_not_infer_identity(self):
        env = _admitted()
        env["canonical"]["event_id"] = None  # null canonical, no reason declared
        detected = gov.detect_machine_conditions(env)
        self.assertNotIn("UNRESOLVED_EVENT_IDENTITY", detected)
        self.assertNotIn("AMBIGUOUS_EVENT_IDENTITY", detected)

    def test_detect_finds_rejection_class_only(self):
        env = _load("rejected", "03_unsupported_contract_version.json")
        detected = gov.detect_machine_conditions(env)
        self.assertEqual(detected, {"INVALID_CONTRACT_VERSION"})


class SourceRightsFailClosedTests(unittest.TestCase):
    def _publishable(self, profile):
        return profile.get("rights_matrix", {}).get("public_display") == "ALLOWED"

    def test_unknown_public_display_blocks_publication(self):
        for name in ("01_provider_alpha_profile.json", "02_provider_beta_profile.json"):
            profile = _load("source-profiles", name)
            self.assertFalse(self._publishable(profile), "%s must fail closed" % name)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
