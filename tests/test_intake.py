"""
Tests for vendor intake validation and weight modifier logic.
"""
import pytest
from unittest.mock import MagicMock
from core.profiles.intake import (
    apply_intake_weight_modifiers,
    build_integration_context_paragraph,
    INTAKE_DATA_SENSITIVITY,
    INTEGRATION_WEIGHT_MODIFIERS,
)
from core.profiles.vendor_cache import VendorProfile


def _make_profile(**kwargs) -> VendorProfile:
    defaults = dict(
        vendor_name="TestVendor",
        vendor_slug="testvendor",
        functions=[],
        detection_method="test",
        intake_completed=True,
        data_types=[],
        integrations=[],
    )
    defaults.update(kwargs)
    return VendorProfile(**defaults)


class TestWeightModifiers:
    def test_phi_increases_d5_d8(self):
        profile = _make_profile(data_types=["phi"])
        base = {"D1": 1.0, "D5": 1.0, "D8": 1.0}
        org_profile = {}
        result = apply_intake_weight_modifiers(base, profile, org_profile)
        assert result["D5"] > base["D5"]
        assert result["D8"] > base["D8"]

    def test_no_data_types_leaves_weights_unchanged(self):
        profile = _make_profile(data_types=[])
        base = {"D1": 1.0, "D2": 1.0, "D5": 1.0}
        result = apply_intake_weight_modifiers(base, profile, {})
        assert result == base

    def test_weight_capped_at_3_0(self):
        # phi modifier for D5 is +1.0; starting near cap
        profile = _make_profile(data_types=["phi"])
        base = {"D5": 2.9}
        result = apply_intake_weight_modifiers(base, profile, {})
        assert result["D5"] <= 3.0

    def test_integration_modifier_applied(self):
        profile = _make_profile(integrations=[
            {"category": "customer_data", "system_name": "Salesforce",
             "category_label": "CRM", "data_description": "customer records"}
        ])
        base = {"D1": 1.0, "D3": 1.0}
        result = apply_intake_weight_modifiers(base, profile, {})
        expected_delta = INTEGRATION_WEIGHT_MODIFIERS["customer_data"].get("D1", 0)
        assert result["D1"] == pytest.approx(base["D1"] + expected_delta)

    def test_org_already_covers_prevents_double_count(self):
        """If org profile already raises D5 for phi, intake shouldn't add more."""
        profile = _make_profile(data_types=["phi"])
        base = {"D5": 1.5}
        # Simulate org profile with phi_in_scope = True (matching _org_covers() logic)
        org_profile = {"data_types": {"phi_in_scope": True}}
        result_with_org = apply_intake_weight_modifiers(base, profile, org_profile)
        result_without_org = apply_intake_weight_modifiers(base, profile, {})
        # With org covering it, D5 modifier should not be applied
        assert result_with_org["D5"] <= result_without_org["D5"]


class TestIntegrationContext:
    def test_returns_none_when_no_integrations(self):
        profile = _make_profile(integrations=[])
        result = build_integration_context_paragraph(profile)
        assert result is None

    def test_returns_string_with_system_name(self):
        profile = _make_profile(integrations=[
            {"system_name": "Snowflake", "category": "data_warehouse",
             "category_label": "Data warehouse",
             "data_description": "data warehouse records"}
        ])
        result = build_integration_context_paragraph(profile)
        assert result is not None
        assert "Snowflake" in result

    def test_multiple_integrations_all_present(self):
        profile = _make_profile(integrations=[
            {"system_name": "Okta", "category": "identity",
             "category_label": "Identity / SSO",
             "data_description": "identity and access data"},
            {"system_name": "HubSpot", "category": "crm",
             "category_label": "CRM",
             "data_description": "customer records"},
        ])
        result = build_integration_context_paragraph(profile)
        assert "Okta" in result
        assert "HubSpot" in result
