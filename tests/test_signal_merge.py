"""
Tests for multi-document signal merging behaviour.

The merge rule: documents add evidence (True), they never overwrite
an existing True signal with False, and never introduce a new False signal.
"""
import pytest
from core.agents.privacy_bandit import PrivacyBandit
from core.scoring.rubric import RUBRIC


class TestReshapeSignals:
    def test_flat_signals_routed_to_correct_dimension(self):
        raw = {
            "signals": {
                "d1_purposes_stated": True,
                "d5_breach_notification_timeline_stated": True,
            },
            "art28_checklist": {},
            "framework_certifications": {},
        }
        per_dim, frameworks = PrivacyBandit._reshape_signals(raw)
        assert per_dim["D1"].get("d1_purposes_stated") is True
        assert per_dim["D5"].get("d5_breach_notification_timeline_stated") is True

    def test_framework_certifications_returned(self):
        raw = {
            "signals": {},
            "art28_checklist": {},
            "framework_certifications": {"soc2_type2": True, "iso27001": False},
        }
        _, frameworks = PrivacyBandit._reshape_signals(raw)
        assert "soc2_type2" in frameworks
        assert "iso27001" not in frameworks

    def test_art28_checklist_added_to_d8(self):
        raw = {
            "signals": {},
            "art28_checklist": {"subject_matter_defined": True},
            "framework_certifications": {},
        }
        per_dim, _ = PrivacyBandit._reshape_signals(raw)
        assert per_dim["D8"].get("subject_matter_defined") is True


class TestSignalMergeRule:
    """Test the merge rule: True wins, False never overwrites True."""

    def _apply_merge(self, policy_signals: dict, doc_signals: dict) -> dict:
        """Simulate the merge logic from privacy_bandit.assess()."""
        merged = dict(policy_signals)
        for key, value in doc_signals.items():
            if value and not merged.get(key):
                merged[key] = value
        return merged

    def test_doc_true_fills_policy_false(self):
        policy = {"d5_breach_notification_timeline_stated": False}
        docs = {"d5_breach_notification_timeline_stated": True}
        merged = self._apply_merge(policy, docs)
        assert merged["d5_breach_notification_timeline_stated"] is True

    def test_policy_true_not_overwritten_by_doc_false(self):
        policy = {"d5_breach_notification_timeline_stated": True}
        docs = {"d5_breach_notification_timeline_stated": False}
        merged = self._apply_merge(policy, docs)
        assert merged["d5_breach_notification_timeline_stated"] is True

    def test_doc_false_does_not_introduce_new_false_key(self):
        policy = {}
        docs = {"d1_purposes_stated": False}
        merged = self._apply_merge(policy, docs)
        # False signal from doc should NOT be added as a new key
        assert "d1_purposes_stated" not in merged

    def test_multiple_docs_accumulate_true_signals(self):
        all_doc_signals: dict = {}
        doc1 = {"d1_purposes_stated": True}
        doc2 = {"d5_breach_notification_timeline_stated": True}
        for key, value in doc1.items():
            if value and not all_doc_signals.get(key):
                all_doc_signals[key] = value
        for key, value in doc2.items():
            if value and not all_doc_signals.get(key):
                all_doc_signals[key] = value
        assert all_doc_signals["d1_purposes_stated"] is True
        assert all_doc_signals["d5_breach_notification_timeline_stated"] is True
