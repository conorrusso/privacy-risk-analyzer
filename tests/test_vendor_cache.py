"""
Tests for VendorProfileCache — profile storage, retrieval, and history.
"""
import json
import pathlib
import tempfile
import pytest
from unittest.mock import MagicMock
from core.profiles.vendor_cache import VendorProfile, VendorProfileCache


def _make_cache(tmp_path: pathlib.Path) -> VendorProfileCache:
    """Return a cache that writes to a temp file."""
    cache_file = tmp_path / "vendor-profiles.json"
    return VendorProfileCache(path=cache_file)


def _minimal_profile(name: str = "TestVendor") -> VendorProfile:
    return VendorProfile(
        vendor_name=name,
        vendor_slug=name.lower().replace(" ", "-"),
        functions=[],
        detection_method="test",
    )


class TestSaveAndGet:
    def test_save_and_retrieve(self, tmp_path):
        cache = _make_cache(tmp_path)
        profile = _minimal_profile("Acme")
        cache.save("Acme", profile)
        retrieved = cache.get("Acme")
        assert retrieved is not None
        assert retrieved.vendor_name == "Acme"

    def test_get_returns_none_for_unknown_vendor(self, tmp_path):
        cache = _make_cache(tmp_path)
        assert cache.get("NoSuchVendor") is None

    def test_lookup_is_case_insensitive(self, tmp_path):
        cache = _make_cache(tmp_path)
        profile = _minimal_profile("HubSpot")
        cache.save("HubSpot", profile)
        assert cache.get("hubspot") is not None
        assert cache.get("HUBSPOT") is not None

    def test_list_all_returns_saved_profiles(self, tmp_path):
        cache = _make_cache(tmp_path)
        cache.save("Alpha", _minimal_profile("Alpha"))
        cache.save("Beta", _minimal_profile("Beta"))
        profiles = cache.list_all()
        names = [p.vendor_name for p in profiles]
        assert "Alpha" in names
        assert "Beta" in names


class TestAssessmentHistory:
    def _make_result(self, tier="MEDIUM", avg=3.0):
        class _FakeResult:
            risk_tier = tier
            weighted_average = avg
            assessment_scope = "public_policy_only"
            rubric_version = "1.0.0"
            assessment_date = "2026-04-01"
            report_path = "/tmp/report.html"
            legal_bandit_result = None
        r = _FakeResult()
        r.risk_tier = tier
        r.weighted_average = avg
        return r

    def test_history_written_on_update(self, tmp_path):
        cache = _make_cache(tmp_path)
        result = self._make_result("HIGH", 2.1)
        cache.update_assessment_history("TestCo", result)
        profile = cache.get("TestCo")
        assert profile is not None
        assert len(profile.assessment_history) == 1
        assert profile.assessment_history[0]["risk_tier"] == "HIGH"

    def test_history_capped_at_10_entries(self, tmp_path):
        cache = _make_cache(tmp_path)
        for i in range(12):
            cache.update_assessment_history(
                "TestCo", self._make_result("LOW", 4.0)
            )
        profile = cache.get("TestCo")
        assert len(profile.assessment_history) <= 10

    def test_current_risk_tier_updated(self, tmp_path):
        cache = _make_cache(tmp_path)
        cache.update_assessment_history("TestCo", self._make_result("HIGH", 2.0))
        profile = cache.get("TestCo")
        assert profile.current_risk_tier == "HIGH"

    def test_corrupted_cache_returns_empty(self, tmp_path):
        cache_file = tmp_path / "vendor-profiles.json"
        cache_file.write_text("not valid json")
        cache = VendorProfileCache(path=cache_file)
        # Should not raise — should return None gracefully
        assert cache.get("Anything") is None
        assert cache.list_all() == []
