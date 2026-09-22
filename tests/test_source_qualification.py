"""Tests for the LadybugBets source-qualification governance (LBSQ-001).

Standard library only. Negative tests mutate a synthetic fixture in memory;
the real provider evidence/qualification files must also pass the same
validator. Tests validate recorded artifacts only — they never touch the web.

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

from governance import validate_source_qualification as vq  # noqa: E402

FIX = os.path.join(REPO_ROOT, "fixtures", "source-qualification")
EVID = os.path.join(REPO_ROOT, "evidence", "source-qualification")
REAL_PROVIDERS = ("the-odds-api", "sportmonks", "sportradar", "betfair-exchange")


def _load(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _synth():
    bundle = _load(os.path.join(FIX, "synthetic-provider.evidence.json"))
    qual = _load(os.path.join(FIX, "synthetic-provider.qualification.json"))
    return bundle, qual


def _sync_committed(qual):
    """Set committed capability outcomes to the derived outcomes (so a validate
    test isolates the single injected defect rather than a derivation mismatch)."""
    derived = vq.derive_capabilities(qual)
    for cap, outcome in derived.items():
        qual["capabilities"][cap]["outcome"] = outcome
    return qual


def _codes(findings):
    return {f.code for f in findings}


def _by_claim(bundle, claim_key):
    """Return the single evidence item carrying claim_key (fails if not exactly one)."""
    matches = [it for it in bundle["evidence_items"] if it.get("claim_key") == claim_key]
    if len(matches) != 1:
        raise AssertionError("expected exactly one %r item, found %d" % (claim_key, len(matches)))
    return matches[0]


class DerivationTests(unittest.TestCase):
    """Capability outcomes derive deterministically from the matrices."""

    def _derive_with(self, **overrides):
        _, qual = _synth()
        for key, value in overrides.items():
            if key in vq.RIGHTS_KEYS:
                qual["rights_matrix"][key] = value
            elif key in vq.TECHNICAL_KEYS:
                qual["technical_matrix"][key] = value
        return vq.derive_capabilities(qual)

    def test_1_unknown_public_display_blocks_spotboard(self):
        self.assertEqual(self._derive_with(public_display="UNKNOWN")["PUBLIC_SPOTBOARD"], "UNRESOLVED")

    def test_2_prohibited_public_display_blocks_spotboard(self):
        self.assertEqual(self._derive_with(public_display="PROHIBITED")["PUBLIC_SPOTBOARD"], "NOT_QUALIFIED")

    def test_3_allowed_display_insufficient_without_epl(self):
        d = self._derive_with(public_display="ALLOWED", epl_coverage="NOT_VERIFIED")
        self.assertEqual(d["CURRENT_PRICE_OBSERVATION"], "UNRESOLVED")
        self.assertEqual(d["PUBLIC_SPOTBOARD"], "UNRESOLVED")

    def test_4_unknown_retain_blocks_retention(self):
        self.assertEqual(self._derive_with(retain_historical="UNKNOWN")["HISTORICAL_DATASET_RETENTION"], "UNRESOLVED")

    def test_5_prohibited_retain_blocks_retention(self):
        self.assertEqual(self._derive_with(retain_historical="PROHIBITED")["HISTORICAL_DATASET_RETENTION"], "NOT_QUALIFIED")

    def test_6_historical_access_does_not_imply_retention(self):
        d = self._derive_with(historical_odds_access="VERIFIED", retain_historical="UNKNOWN")
        self.assertEqual(d["HISTORICAL_DATASET_RETENTION"], "UNRESOLVED")

    def test_single_operator_can_qualify_cpo(self):
        d = self._derive_with(multi_operator_coverage="UNSUPPORTED")
        self.assertEqual(d["CURRENT_PRICE_OBSERVATION"], "QUALIFIED")

    def test_single_operator_cannot_qualify_spotboard(self):
        d = self._derive_with(multi_operator_coverage="UNSUPPORTED")
        self.assertEqual(d["PUBLIC_SPOTBOARD"], "NOT_QUALIFIED")

    def test_multi_operator_verified_spotboard_qualified(self):
        d = self._derive_with(multi_operator_coverage="VERIFIED", public_display="ALLOWED")
        self.assertEqual(d["PUBLIC_SPOTBOARD"], "QUALIFIED")

    def test_7_notverified_source_time_blocks_movement(self):
        self.assertEqual(self._derive_with(source_observed_timestamp="NOT_VERIFIED")["SOURCE_TIME_MARKET_MOVEMENT"], "UNRESOLVED")

    def test_8_ingested_time_does_not_satisfy_source_observed(self):
        # Everything else VERIFIED/ALLOWED, but source-observed time NOT_VERIFIED
        # (e.g. only an ingestion/response time exists) -> movement not qualified.
        d = self._derive_with(source_observed_timestamp="NOT_VERIFIED", historical_odds_access="VERIFIED")
        self.assertNotEqual(d["SOURCE_TIME_MARKET_MOVEMENT"], "QUALIFIED")

    def test_9_provider_identity_not_operator_identity(self):
        # No operator-level identity -> cannot make governed operator-level obs.
        d = self._derive_with(operator_identifier_or_stable_label="NOT_VERIFIED")
        self.assertEqual(d["CURRENT_PRICE_OBSERVATION"], "UNRESOLVED")
        self.assertEqual(d["SOURCE_TIME_MARKET_MOVEMENT"], "UNRESOLVED")

    def test_10_unknown_derived_rights_block_derived_display(self):
        self.assertEqual(self._derive_with(derive_calculations="UNKNOWN")["DERIVED_PROBABILITY_DISPLAY"], "UNRESOLVED")

    def test_11_prohibited_raw_redistribution_does_not_block_spotboard(self):
        d = self._derive_with(redistribute_raw="PROHIBITED", public_display="ALLOWED")
        self.assertEqual(d["PUBLIC_SPOTBOARD"], "QUALIFIED")
        self.assertEqual(d["RAW_DATA_REDISTRIBUTION"], "NOT_QUALIFIED")

    def test_committed_outcome_must_equal_derived(self):
        bundle, qual = _synth()
        qual["technical_matrix"]["epl_coverage"] = "NOT_VERIFIED"  # now derived != QUALIFIED
        # committed still says QUALIFIED (hand-typed) -> mismatch
        self.assertIn("CAPABILITY_DERIVATION_MISMATCH", _codes(vq.validate_qualification(qual, bundle)))


class ValidatorStructureTests(unittest.TestCase):
    def test_12_unresolved_evidence_reference_fails(self):
        bundle, qual = _synth()
        _sync_committed(qual)
        qual["evidence_ids"].append("does-not-exist")
        self.assertIn("UNRESOLVED_EVIDENCE_REFERENCE", _codes(vq.validate_qualification(qual, bundle)))

    def test_13_duplicate_evidence_id_fails(self):
        bundle, _ = _synth()
        bundle["evidence_items"].append(copy.deepcopy(bundle["evidence_items"][0]))
        self.assertIn("DUPLICATE_EVIDENCE_ID", _codes(vq.validate_evidence_bundle(bundle)))

    def test_14_right_allowed_without_evidence_fails(self):
        bundle, qual = _synth()
        _sync_committed(qual)
        qual["evidence_ids"].remove("syn-public_display")  # drop backing for an ALLOWED right
        self.assertIn("RIGHT_WITHOUT_EVIDENCE", _codes(vq.validate_qualification(qual, bundle)))

    def test_15_official_domain_mismatch_fails(self):
        bundle, _ = _synth()
        bundle["evidence_items"][0]["source_url"] = "https://not-official.example/docs"
        self.assertIn("EVIDENCE_DOMAIN_MISMATCH", _codes(vq.validate_evidence_bundle(bundle)))

    def test_16_non_https_evidence_url_fails(self):
        bundle, _ = _synth()
        bundle["evidence_items"][0]["source_url"] = "http://synthetic-odds.example/docs"
        self.assertIn("EVIDENCE_URL_NOT_HTTPS", _codes(vq.validate_evidence_bundle(bundle)))

    def test_17_score_or_ranking_field_fails(self):
        bundle, qual = _synth()
        _sync_committed(qual)
        qual["score"] = 5
        self.assertIn("SCORE_OR_RANKING_FIELD", _codes(vq.validate_qualification(qual, bundle)))

    def test_18_secret_like_field_fails(self):
        bundle, _ = _synth()
        bundle["evidence_items"][0]["api_key"] = "abc123"
        self.assertIn("SECRET_LIKE_FIELD", _codes(vq.validate_evidence_bundle(bundle)))

    def test_technical_verified_without_evidence_fails(self):
        bundle, qual = _synth()
        _sync_committed(qual)
        qual["evidence_ids"].remove("syn-epl_coverage")
        self.assertIn("TECHNICAL_WITHOUT_EVIDENCE", _codes(vq.validate_qualification(qual, bundle)))


class RealProviderTests(unittest.TestCase):
    def _pair(self, slug):
        bundle = _load(os.path.join(EVID, "%s.evidence.json" % slug))
        qual = _load(os.path.join(EVID, "%s.qualification.json" % slug))
        return bundle, qual

    def test_19_real_records_pass_validator(self):
        for slug in REAL_PROVIDERS:
            bundle, qual = self._pair(slug)
            self.assertEqual(vq.validate_evidence_bundle(bundle), [], "%s evidence" % slug)
            self.assertEqual(vq.validate_qualification(qual, bundle), [], "%s qualification" % slug)

    def test_real_committed_equals_derived(self):
        for slug in REAL_PROVIDERS:
            bundle, qual = self._pair(slug)
            derived = vq.derive_capabilities(qual)
            for cap in vq.CAPABILITY_KEYS:
                self.assertEqual(qual["capabilities"][cap]["outcome"], derived[cap], "%s/%s" % (slug, cap))

    def test_20_capability_specific_no_global_winner(self):
        # No provider collapses to a single global verdict; outcomes vary by
        # capability and/or by provider, and there is no score/winner field.
        outcomes_by_provider = {}
        for slug in REAL_PROVIDERS:
            _, qual = self._pair(slug)
            outcomes = {cap: qual["capabilities"][cap]["outcome"] for cap in vq.CAPABILITY_KEYS}
            outcomes_by_provider[slug] = outcomes
            # no forbidden score/ranking/winner keys anywhere
            self.assertEqual(_codes(vq._hygiene_findings(qual, slug)), set())
        # At least one provider must show more than one distinct outcome across
        # capabilities (capability-specific, not one global label).
        self.assertTrue(
            any(len(set(o.values())) > 1 for o in outcomes_by_provider.values()),
            "expected capability-specific (mixed) outcomes for at least one provider",
        )
        # The four providers are not all identical -> qualification is per-provider.
        distinct = {tuple(sorted(o.items())) for o in outcomes_by_provider.values()}
        self.assertGreater(len(distinct), 1)


class ProviderBindingTests(unittest.TestCase):
    def test_provider_id_mismatch_fails(self):
        bundle, qual = _synth()
        qual["provider_id"] = "PRV_OTHER"
        self.assertIn("PROVIDER_ID_MISMATCH", _codes(vq.validate_qualification(qual, bundle)))

    def test_provider_name_mismatch_fails(self):
        bundle, qual = _synth()
        qual["provider_name"] = "Other Provider"
        self.assertIn("PROVIDER_NAME_MISMATCH", _codes(vq.validate_qualification(qual, bundle)))

    def test_evidence_provider_mismatch_fails(self):
        bundle, _ = _synth()
        bundle["evidence_items"][0]["provider_id"] = "PRV_OTHER"
        self.assertIn("EVIDENCE_PROVIDER_MISMATCH", _codes(vq.validate_evidence_bundle(bundle)))

    def test_official_domain_set_mismatch_fails(self):
        bundle, qual = _synth()
        qual["official_domains"] = ["different.example"]
        self.assertIn("OFFICIAL_DOMAIN_SET_MISMATCH", _codes(vq.validate_qualification(qual, bundle)))


class CapabilityEvidenceCompletenessTests(unittest.TestCase):
    def test_qualified_cpo_missing_gate_evidence_fails(self):
        bundle, qual = _synth()
        cpo = qual["capabilities"]["CURRENT_PRICE_OBSERVATION"]["evidence_ids"]
        cpo.remove("syn-epl_coverage")  # drop a required VERIFIED gate
        self.assertIn("CAPABILITY_EVIDENCE_INCOMPLETE", _codes(vq.validate_qualification(qual, bundle)))

    def test_qualified_spotboard_missing_inherited_cpo_evidence_fails(self):
        bundle, qual = _synth()
        psb = qual["capabilities"]["PUBLIC_SPOTBOARD"]["evidence_ids"]
        psb.remove("syn-operator_level_prices")  # inherited CPO gate
        self.assertIn("CAPABILITY_EVIDENCE_INCOMPLETE", _codes(vq.validate_qualification(qual, bundle)))

    def test_capability_evidence_wrong_claim_key_fails(self):
        bundle, qual = _synth()
        ids = qual["capabilities"]["CURRENT_PRICE_OBSERVATION"]["evidence_ids"]
        ids[ids.index("syn-epl_coverage")] = "syn-cache"  # resolves but wrong claim_key
        self.assertIn("CAPABILITY_EVIDENCE_INCOMPLETE", _codes(vq.validate_qualification(qual, bundle)))

    def test_capability_evidence_wrong_posture_fails(self):
        bundle, qual = _synth()
        # Add a same-claim item with a non-VERIFIED posture and reference it
        # instead of the VERIFIED one for the epl gate.
        bundle["evidence_items"].append({
            "evidence_id": "syn-epl_coverage-weak", "provider_id": "PRV_SYNTH",
            "source_url": "https://synthetic-odds.example/docs", "source_title": "Docs",
            "source_type": "API_DOCS", "retrieved_at": "2026-09-21", "source_effective_date": None,
            "publisher_domain": "synthetic-odds.example", "claim_key": "epl_coverage",
            "claim_summary": "weak", "technical_posture": "NOT_VERIFIED", "rights_posture": None,
            "excerpt": None, "notes": None,
        })
        ids = qual["capabilities"]["CURRENT_PRICE_OBSERVATION"]["evidence_ids"]
        ids[ids.index("syn-epl_coverage")] = "syn-epl_coverage-weak"
        self.assertIn("CAPABILITY_EVIDENCE_INCOMPLETE", _codes(vq.validate_qualification(qual, bundle)))


class SportmonksRedistributionTests(unittest.TestCase):
    def test_broad_raw_redistribution_not_prohibited_from_resale_only(self):
        bundle = _load(os.path.join(EVID, "sportmonks.evidence.json"))
        qual = _load(os.path.join(EVID, "sportmonks.qualification.json"))
        self.assertEqual(qual["rights_matrix"]["redistribute_raw"], "UNKNOWN")
        self.assertEqual(qual["capabilities"]["RAW_DATA_REDISTRIBUTION"]["outcome"], "UNRESOLVED")
        self.assertEqual(vq.validate_qualification(qual, bundle), [])


class BetfairSingleOperatorTests(unittest.TestCase):
    def test_single_operator_spotboard_not_qualified(self):
        qual = _load(os.path.join(EVID, "betfair-exchange.qualification.json"))
        self.assertEqual(qual["technical_matrix"]["multi_operator_coverage"], "UNSUPPORTED")
        self.assertEqual(qual["capabilities"]["PUBLIC_SPOTBOARD"]["outcome"], "NOT_QUALIFIED")


class EvidenceChainClosureTests(unittest.TestCase):
    """A qualification is never valid unless its bound evidence bundle is valid.

    validate_qualification incorporates the bundle findings, so no separate call
    ordering can smuggle a valid qualification past an invalid bundle.
    """

    def test_invalid_bundle_makes_qualification_invalid(self):
        # Baseline: a synced synthetic pair is valid on both validators.
        bundle, qual = _synth()
        _sync_committed(qual)
        self.assertEqual(vq.validate_evidence_bundle(bundle), [])
        self.assertEqual(vq.validate_qualification(qual, bundle), [])
        # Corrupt only the bundle (non-HTTPS url); the qualification is untouched.
        bundle["evidence_items"][0]["source_url"] = "http://synthetic-odds.example/docs"
        codes = _codes(vq.validate_qualification(qual, bundle))
        self.assertIn("INVALID_EVIDENCE_BUNDLE", codes)
        self.assertIn("EVIDENCE_URL_NOT_HTTPS", codes)
        self.assertFalse(vq.is_valid_qualification(qual, bundle))

    def test_is_valid_qualification_never_true_against_invalid_bundle(self):
        bundle, qual = _synth()
        _sync_committed(qual)
        # Malformed technical posture in the bundle item -> bundle invalid.
        bundle["evidence_items"][0]["technical_posture"] = "MAYBE"
        self.assertFalse(vq.is_valid_evidence_bundle(bundle))
        self.assertFalse(vq.is_valid_qualification(qual, bundle))
        self.assertIn("INVALID_EVIDENCE_BUNDLE", _codes(vq.validate_qualification(qual, bundle)))

    def test_duplicate_evidence_id_propagates_to_qualification(self):
        bundle, qual = _synth()
        _sync_committed(qual)
        bundle["evidence_items"].append(copy.deepcopy(bundle["evidence_items"][0]))
        codes = _codes(vq.validate_qualification(qual, bundle))
        self.assertIn("INVALID_EVIDENCE_BUNDLE", codes)
        self.assertIn("DUPLICATE_EVIDENCE_ID", codes)

    def test_combined_pair_api_matches_and_requires_both_valid(self):
        bundle, qual = _synth()
        _sync_committed(qual)
        # Argument order for the combined API is (bundle, qualification).
        self.assertEqual(vq.validate_source_qualification_pair(bundle, qual), [])
        self.assertTrue(vq.is_valid_source_qualification_pair(bundle, qual))
        bundle["evidence_items"][0]["source_url"] = "https://not-official.example/docs"
        self.assertFalse(vq.is_valid_source_qualification_pair(bundle, qual))
        self.assertIn("EVIDENCE_DOMAIN_MISMATCH", _codes(vq.validate_source_qualification_pair(bundle, qual)))

    def test_valid_bundle_no_spurious_invalid_bundle_finding(self):
        bundle, qual = _synth()
        _sync_committed(qual)
        self.assertNotIn("INVALID_EVIDENCE_BUNDLE", _codes(vq.validate_qualification(qual, bundle)))


class OutcomeIdentityTests(unittest.TestCase):
    """outcome_identifier_or_label: a source-native id OR an explicit source
    outcome label preserves the raw assertion. A raw label does NOT establish
    canonical outcome identity (LBIR-001 / DEC-014, DEC-016)."""

    def test_technical_key_renamed(self):
        self.assertIn("outcome_identifier_or_label", vq.TECHNICAL_KEYS)
        self.assertNotIn("outcome_identifier_or_stable_key", vq.TECHNICAL_KEYS)

    def test_outcome_label_gates_current_price_observation(self):
        # Dropping the outcome gate makes CPO underivable as QUALIFIED.
        _, qual = _synth()
        qual["technical_matrix"]["outcome_identifier_or_label"] = "NOT_VERIFIED"
        self.assertEqual(vq.derive_capabilities(qual)["CURRENT_PRICE_OBSERVATION"], "UNRESOLVED")

    def test_odds_api_outcome_label_verified_without_native_id_claim(self):
        bundle = _load(os.path.join(EVID, "the-odds-api.evidence.json"))
        qual = _load(os.path.join(EVID, "the-odds-api.qualification.json"))
        self.assertEqual(qual["technical_matrix"]["outcome_identifier_or_label"], "VERIFIED")
        item = _by_claim(bundle, "outcome_identifier_or_label")
        self.assertEqual(item["technical_posture"], "VERIFIED")
        # The claim rests on the source label, and does not assert a native id.
        self.assertIn("label", item["claim_summary"].lower())
        self.assertIn("no provider-native outcome id", item["claim_summary"].lower())

    def test_sportmonks_outcome_label_and_fixture_event_id(self):
        bundle = _load(os.path.join(EVID, "sportmonks.evidence.json"))
        qual = _load(os.path.join(EVID, "sportmonks.qualification.json"))
        self.assertEqual(qual["technical_matrix"]["outcome_identifier_or_label"], "VERIFIED")
        outcome = _by_claim(bundle, "outcome_identifier_or_label")
        self.assertIn("label", outcome["claim_summary"].lower())
        event = _by_claim(bundle, "stable_event_identifier")
        # Event identity references the provider fixture id (fixture id / fixture_id).
        self.assertIn("fixture", event["claim_summary"].lower())


class BetfairEvidenceCompletionTests(unittest.TestCase):
    def setUp(self):
        self.bundle = _load(os.path.join(EVID, "betfair-exchange.evidence.json"))
        self.qual = _load(os.path.join(EVID, "betfair-exchange.qualification.json"))

    def test_documented_rate_limits_verified(self):
        self.assertEqual(self.qual["technical_matrix"]["documented_rate_limits"], "VERIFIED")
        item = _by_claim(self.bundle, "documented_rate_limits")
        self.assertEqual(item["technical_posture"], "VERIFIED")
        self.assertTrue(item.get("excerpt"))

    def test_historical_odds_access_verified(self):
        self.assertEqual(self.qual["technical_matrix"]["historical_odds_access"], "VERIFIED")
        item = _by_claim(self.bundle, "historical_odds_access")
        self.assertEqual(item["technical_posture"], "VERIFIED")

    def test_outcome_identity_not_over_upgraded(self):
        # No selectionId evidence retrieved -> outcome identity stays NOT_VERIFIED.
        self.assertEqual(self.qual["technical_matrix"]["outcome_identifier_or_label"], "NOT_VERIFIED")
        self.assertEqual(self.qual["technical_matrix"]["epl_coverage"], "NOT_VERIFIED")
        self.assertEqual(self.qual["technical_matrix"]["source_observed_timestamp"], "NOT_VERIFIED")

    def test_rights_fail_closed(self):
        for key in vq.RIGHTS_KEYS:
            self.assertEqual(self.qual["rights_matrix"][key], "UNKNOWN", key)
        # No rights-establishing capability may be QUALIFIED under all-UNKNOWN rights.
        for cap in vq.CAPABILITY_KEYS:
            self.assertNotEqual(self.qual["capabilities"][cap]["outcome"], "QUALIFIED", cap)

    def test_current_price_observation_unresolved(self):
        self.assertEqual(self.qual["capabilities"]["CURRENT_PRICE_OBSERVATION"]["outcome"], "UNRESOLVED")

    def test_pair_is_valid(self):
        self.assertEqual(vq.validate_source_qualification_pair(self.bundle, self.qual), [])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
