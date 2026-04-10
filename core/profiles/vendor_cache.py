"""
Bandit Vendor Profile Cache
============================
Persists detected vendor function profiles to ~/.bandit/vendor-profiles.json.
Allows reuse across assessments without re-running detection.
"""
from __future__ import annotations

import json
import pathlib
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Optional

CACHE_PATH = pathlib.Path.home() / ".bandit" / "vendor-profiles.json"
PROFILES_DRIVE_FILENAME = ".vendor-profiles.json"


@dataclass
class IntegrationEntry:
    system_name: str        # "Snowflake"
    system_slug: str        # "snowflake"
    category: str           # "analytics_bi"
    category_label: str     # "Data warehouse"
    data_description: str   # "aggregated analytics data"


@dataclass
class AssessmentHistoryEntry:
    date: str
    risk_tier: str
    weighted_average: float
    rubric_version: str
    scope: str
    report_path: str
    legal_brief_path: Optional[str] = None
    next_due: Optional[str] = None
    scored_dimensions: int = 8


@dataclass
class VendorProfile:
    """Persisted vendor function profile."""
    # ── Existing fields (keep as-is) ──────────────
    vendor_name: str
    vendor_slug: str
    functions: list
    detection_method: str
    vendor_country: Optional[str] = None
    phi_processor: bool = False
    pci_processor: bool = False
    children_data: bool = False
    last_updated: str = ""
    notes: Optional[str] = None

    # ── Intake fields (new) ───────────────────────
    intake_completed: bool = False
    intake_date: Optional[str] = None

    # Q1
    data_types: list = field(default_factory=list)
    # Q2
    data_volume: Optional[str] = None
    # Q3
    environment_access: Optional[str] = None
    # Q4
    access_level: Optional[str] = None
    # Q5
    sole_source: Optional[bool] = None
    # Q6
    integrations: list = field(default_factory=list)
    # Q7
    sso_required: Optional[bool] = None
    # Q8
    ai_in_service: Optional[str] = None
    # Q9
    ai_trains_on_data: Optional[str] = None
    # Q10
    criticality: Optional[str] = None
    # Q11
    annual_spend: Optional[str] = None
    # Q12
    renewal_date: Optional[str] = None
    business_owner: Optional[str] = None

    # ── Assessment history (new) ──────────────────
    assessment_history: list = field(
        default_factory=list
    )

    # ── Risk register (new) ───────────────────────
    current_risk_tier: Optional[str] = None
    last_assessed: Optional[str] = None
    next_due: Optional[str] = None
    risk_approved: bool = False
    open_findings: int = 0

    # ── Drive (new) ───────────────────────────────
    drive_folder_id: Optional[str] = None
    drive_folder_name: Optional[str] = None
    drive_last_synced: Optional[str] = None

    # ── Pending notifications (new) ───────────────
    pending_it_notification: Optional[dict] = None

    def function_labels(self) -> list[str]:
        """Return human-readable function labels."""
        from core.profiles.vendor_functions import FUNCTION_LABELS, VendorFunction
        labels = []
        for f in self.functions:
            try:
                labels.append(FUNCTION_LABELS[VendorFunction(f)])
            except (ValueError, KeyError):
                labels.append(f)
        return labels


class VendorProfileCache:
    """Read/write vendor profiles to a JSON cache file."""

    def __init__(self, path: pathlib.Path = CACHE_PATH) -> None:
        self._path = path
        from core.profiles.auto_detect import VendorAutoDetector
        self.detector = VendorAutoDetector()

    def get(self, vendor_name: str) -> VendorProfile | None:
        """Return cached profile for vendor_name, or None."""
        cache = self._load()
        key = vendor_name.lower().strip()
        entry = cache.get(key)
        if not entry:
            return None
        try:
            profile = VendorProfile(**entry)
            if profile.data_types:
                from core.profiles.intake import normalise_data_types
                profile.data_types = normalise_data_types(
                    profile.data_types
                )
            from core.profiles.intake import normalise_access_level
            profile.access_level = normalise_access_level(
                profile.access_level
            )
            from core.profiles.intake import normalise_sole_source
            if hasattr(profile, "sole_source"):
                profile.sole_source = normalise_sole_source(
                    profile.sole_source
                )
            return profile
        except (TypeError, KeyError):
            return None

    def save(self, vendor_name: str, profile: VendorProfile) -> None:
        """Persist a vendor profile."""
        cache = self._load()
        key = vendor_name.lower().strip()
        cache[key] = asdict(profile)
        self._write(cache)

    def list_all(self) -> list[VendorProfile]:
        """Return all cached profiles."""
        from core.profiles.intake import normalise_data_types
        cache = self._load()
        profiles: list[VendorProfile] = []
        for entry in cache.values():
            if isinstance(entry, dict) and not str(list(entry.keys())[0] if entry else "").startswith("_"):
                try:
                    profile = VendorProfile(**entry)
                    if profile.data_types:
                        profile.data_types = normalise_data_types(
                            profile.data_types
                        )
                    from core.profiles.intake import normalise_access_level
                    profile.access_level = normalise_access_level(
                        profile.access_level
                    )
                    from core.profiles.intake import normalise_sole_source
                    if hasattr(profile, "sole_source"):
                        profile.sole_source = normalise_sole_source(
                            profile.sole_source
                        )
                    profiles.append(profile)
                except (TypeError, KeyError):
                    pass
        return sorted(profiles, key=lambda p: p.vendor_name.lower())

    def _build_new_profile(
        self, vendor_name: str, detect_result
    ) -> VendorProfile:
        """Build a new VendorProfile from detection result."""
        slug = self.detector._normalise(vendor_name)
        functions = [f.value for f in detect_result.functions]
        return VendorProfile(
            vendor_name=vendor_name,
            vendor_slug=slug,
            functions=functions,
            detection_method=detect_result.method,
            last_updated=datetime.now().strftime("%Y-%m-%d"),
        )

    def update_assessment_history(
        self,
        vendor_name: str,
        result,  # AssessmentResult
    ) -> None:
        """
        Write assessment result to vendor profile.
        Called after every bandit assess completes.
        Creates profile if none exists.
        """
        slug = self.detector._normalise(vendor_name)
        profile = self.get(vendor_name)

        if not profile:
            # Create minimal profile if none exists
            profile = VendorProfile(
                vendor_name=vendor_name,
                vendor_slug=slug,
                functions=[],
                detection_method="assessment_only",
                vendor_country=None,
                phi_processor=False,
                pci_processor=False,
                children_data=False,
                last_updated=datetime.now().strftime(
                    "%Y-%m-%d"
                ),
            )

        # Build history entry
        entry = {
            "date": getattr(
                result, "assessment_date",
                datetime.now().strftime("%Y-%m-%d")
            ),
            "risk_tier": getattr(
                result, "risk_tier", "UNKNOWN"
            ),
            "weighted_average": round(
                getattr(result, "weighted_average", 0), 2
            ),
            "rubric_version": getattr(
                result, "rubric_version", "1.0.0"
            ),
            "scope": getattr(
                result, "assessment_scope",
                "public_policy_only"
            ),
            "report_path": getattr(
                result, "report_path", ""
            ) or "",
            "legal_brief_path": getattr(
                result, "legal_brief_path", None
            ),
            "scored_dimensions": getattr(
                result, "scored_dimensions", 8
            ),
            "next_due": self._calculate_next_due(
                getattr(result, "risk_tier", "MEDIUM")
            ),
        }

        # Prepend — most recent first. Keep last 10.
        history = profile.assessment_history or []
        history.insert(0, entry)
        profile.assessment_history = history[:10]

        # Update risk register
        profile.current_risk_tier = entry["risk_tier"]
        profile.last_assessed = entry["date"]
        profile.next_due = entry["next_due"]
        profile.last_updated = entry["date"]

        self.save(vendor_name, profile)

    def _calculate_next_due(
        self, risk_tier: str
    ) -> str:
        """Calculate next assessment due date."""
        from datetime import datetime, timedelta

        # Load from config if available, else defaults
        try:
            from core.config import BanditConfig
            config = BanditConfig()
            reassessment = config.get_reassessment(
                risk_tier
            )
            days = reassessment.get("days", 365)
        except Exception:
            days = {
                "HIGH": 365,
                "MEDIUM": 730,
                "LOW": 0,
            }.get(risk_tier.upper(), 365)

        if days == 0:
            return "scan_only"

        due = datetime.now() + timedelta(days=days)
        return due.strftime("%Y-%m-%d")

    def sync_from_drive(
        self,
        drive_client,
        root_folder_id: str
    ) -> bool:
        """
        Pull vendor profiles from Drive.
        Returns True if successful, False if failed.
        Never raises — always fails gracefully.
        """
        try:
            remote_data = drive_client.read_vendor_profiles(
                root_folder_id
            )
            if not remote_data:
                return False

            # Merge: remote fills in entries that don't
            # exist locally. For existing entries, keep
            # whichever assessment_history is longer
            # (local wins if an assess run just completed
            # but the Drive push hasn't happened yet).
            local_data = self._load()

            for slug, vendor_data in remote_data.items():
                if slug.startswith("_"):
                    continue  # skip metadata keys
                if slug in local_data:
                    local_hist = local_data[slug].get(
                        "assessment_history", []
                    ) or []
                    remote_hist = vendor_data.get(
                        "assessment_history", []
                    ) or []
                    # Start from the remote version
                    merged = dict(vendor_data)
                    # Preserve local history if it is longer
                    # (Drive push may not have completed yet)
                    if len(local_hist) > len(remote_hist):
                        merged["assessment_history"] = local_hist
                        merged["current_risk_tier"] = local_data[slug].get(
                            "current_risk_tier"
                        )
                        merged["last_assessed"] = local_data[slug].get(
                            "last_assessed"
                        )
                        merged["next_due"] = local_data[slug].get(
                            "next_due"
                        )
                    # Always preserve local Drive linkage —
                    # Drive doesn't store folder IDs
                    for drive_field in (
                        "drive_folder_id",
                        "drive_folder_name",
                        "drive_last_synced",
                    ):
                        local_val = local_data[slug].get(drive_field)
                        if local_val:
                            merged[drive_field] = local_val
                    local_data[slug] = merged
                else:
                    local_data[slug] = vendor_data

            self._write(local_data)
            return True

        except Exception as e:
            import logging
            logging.getLogger("bandit").warning(
                f"Drive profile sync failed: {e}"
            )
            return False

    def sync_to_drive(
        self,
        drive_client,
        root_folder_id: str
    ) -> bool:
        """
        Push local vendor profiles to Drive.
        Returns True if successful, False if failed.
        Never raises — always fails gracefully.
        """
        try:
            local_data = self._load()
            local_data["_schema_version"] = "1.3"
            local_data["_last_updated"] = (
                datetime.now().isoformat()
            )

            drive_client.write_vendor_profiles(
                local_data, root_folder_id
            )

            # Update last_synced on all profiles
            for slug in list(local_data.keys()):
                if not slug.startswith("_"):
                    if slug in local_data:
                        local_data[slug][
                            "drive_last_synced"
                        ] = datetime.now().isoformat()

            self._write(local_data)
            return True

        except Exception as e:
            import logging
            logging.getLogger("bandit").warning(
                f"Drive profile push failed: {e}"
            )
            return False

    def delete(self, vendor_name: str) -> bool:
        """
        Remove a vendor profile from local cache.
        Returns True if deleted, False if not found.
        Drive folder is never touched.
        """
        data = self._load()

        # Try exact slug first
        slug = vendor_name.lower().strip()

        if slug in data:
            del data[slug]
            self._write(data)
            return True

        # Try case-insensitive match on raw keys
        for key in list(data.keys()):
            if key.lower() == vendor_name.lower():
                del data[key]
                self._write(data)
                return True

        return False

    def _load(self) -> dict[str, Any]:
        if not self._path.exists():
            return {}
        try:
            with open(self._path) as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    # Keep _read as alias for backward compatibility
    def _read(self) -> dict[str, Any]:
        return self._load()

    def _write(self, cache: dict) -> None:
        """Atomically write cache to disk."""
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            tmp = pathlib.Path(tempfile.mktemp(dir=self._path.parent, suffix=".tmp"))
            tmp.write_text(json.dumps(cache, indent=2))
            tmp.replace(self._path)
        except OSError:
            pass


# Module-level singleton
profile_cache = VendorProfileCache()
