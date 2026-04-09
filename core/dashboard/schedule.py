from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional
import json

from core.profiles.vendor_cache import VendorProfileCache
from core.config import BanditConfig


@dataclass
class ScheduleEntry:
    """Single vendor in the reassessment schedule."""
    vendor_name: str
    risk_tier: Optional[str]
    last_assessed: Optional[str]
    next_due: Optional[str]
    overdue: bool
    days_until_due: Optional[int]   # negative = overdue
    days_overdue: Optional[int]
    urgency: str    # "overdue" | "due_soon" | "upcoming" | "ok"
    recommended_depth: str  # "full" | "lightweight" | "scan"
    drive_folder_id: Optional[str]
    data_source: str


@dataclass
class ScheduleSummary:
    """
    Full reassessment schedule.
    Returned by get_schedule().
    """
    entries: list[ScheduleEntry]
    overdue_count: int
    due_within_30_days: int
    due_within_90_days: int
    generated_at: str

    def to_json(self) -> str:
        import dataclasses
        return json.dumps(
            dataclasses.asdict(self),
            indent=2,
            default=str,
        )


def get_schedule(
    due_only: bool = False,
    within_days: Optional[int] = None,
) -> ScheduleSummary:
    """
    Build reassessment schedule from all vendor profiles.

    Args:
        due_only:    Only include due/overdue vendors
        within_days: Only include vendors due within N days

    Returns:
        ScheduleSummary — sorted by urgency.
    """
    cache = VendorProfileCache()
    config = BanditConfig()
    profiles = cache.list_all()
    today = date.today()

    entries = []
    overdue_count = 0
    due_30 = 0
    due_90 = 0

    for profile in profiles:
        tier = profile.current_risk_tier
        next_due_str = profile.next_due

        overdue = False
        days_until = None
        days_overdue_val = None
        urgency = "ok"

        if next_due_str and next_due_str != "scan_only":
            try:
                due_date = datetime.strptime(
                    next_due_str, "%Y-%m-%d"
                ).date()
                delta = (due_date - today).days
                days_until = delta

                if delta < 0:
                    overdue = True
                    days_overdue_val = abs(delta)
                    urgency = "overdue"
                    overdue_count += 1
                elif delta <= 30:
                    urgency = "due_soon"
                    due_30 += 1
                    due_90 += 1
                elif delta <= 90:
                    urgency = "upcoming"
                    due_90 += 1
                else:
                    urgency = "ok"

            except ValueError:
                pass

        elif not next_due_str and profile.last_assessed:
            # Assessed but no next_due calculated
            urgency = "due_soon"
            due_30 += 1

        # Depth from config
        try:
            reassessment = config.get_reassessment(
                tier or "MEDIUM"
            )
            depth = reassessment.get("depth", "full")
        except Exception:
            depth = "full"

        entry = ScheduleEntry(
            vendor_name=profile.vendor_name,
            risk_tier=tier,
            last_assessed=profile.last_assessed,
            next_due=next_due_str,
            overdue=overdue,
            days_until_due=days_until,
            days_overdue=days_overdue_val,
            urgency=urgency,
            recommended_depth=depth,
            drive_folder_id=profile.drive_folder_id,
            data_source=(
                "drive" if profile.drive_folder_id
                else "local"
            ),
        )
        entries.append(entry)

    # Filter
    if due_only:
        entries = [
            e for e in entries
            if e.urgency in ("overdue", "due_soon")
        ]

    if within_days is not None:
        entries = [
            e for e in entries
            if (
                e.days_until_due is not None
                and e.days_until_due <= within_days
            ) or e.overdue
        ]

    # Sort: overdue first, then by days_until_due
    urgency_order = {
        "overdue": 0, "due_soon": 1,
        "upcoming": 2, "ok": 3
    }
    entries.sort(key=lambda e: (
        urgency_order.get(e.urgency, 4),
        e.days_until_due or 9999,
        e.vendor_name.lower(),
    ))

    return ScheduleSummary(
        entries=entries,
        overdue_count=overdue_count,
        due_within_30_days=due_30,
        due_within_90_days=due_90,
        generated_at=datetime.now().isoformat(),
    )
