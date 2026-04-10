from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
import json

from core.profiles.vendor_cache import VendorProfileCache
from core.data.resolver import VendorDataResolver


@dataclass
class VendorSummary:
    """Single vendor row in portfolio view."""
    vendor_name: str
    risk_tier: Optional[str]        # HIGH/MEDIUM/LOW
    weighted_average: Optional[float]
    last_assessed: Optional[str]
    next_due: Optional[str]
    overdue: bool
    days_overdue: Optional[int]
    intake_completed: bool
    open_findings: int
    drive_folder_id: Optional[str]
    data_source: str               # "local" | "drive" | "both"
    assessment_count: int
    replaceability: Optional[str] = None


@dataclass
class RiskDistribution:
    high: int = 0
    medium: int = 0
    low: int = 0
    unassessed: int = 0

    @property
    def total(self) -> int:
        return self.high + self.medium + self.low + self.unassessed


@dataclass
class PortfolioSummary:
    """
    Complete portfolio picture.
    Returned by get_summary().
    CLI renders this. Future UI calls get_summary() directly.
    """
    total_vendors: int
    risk_distribution: RiskDistribution
    vendors_due: int
    vendors_overdue: int
    open_findings_total: int
    intake_completion_rate: float   # 0.0–1.0
    drive_vendors: int              # vendors with Drive folder
    local_only_vendors: int
    generated_at: str
    vendors: list[VendorSummary] = field(default_factory=list)

    def to_json(self) -> str:
        """Serialise for --json flag or UI API."""
        import dataclasses
        return json.dumps(
            dataclasses.asdict(self),
            indent=2,
            default=str,
        )


def get_summary(
    risk_filter: Optional[str] = None,
    due_only: bool = False,
    overdue_only: bool = False,
) -> PortfolioSummary:
    """
    Build portfolio summary from all vendor profiles.
    Reads local profiles; Drive sync happens per-resolver.

    Args:
        risk_filter:  "HIGH" | "MEDIUM" | "LOW" | None
        due_only:     Only include vendors due/overdue
        overdue_only: Only include overdue vendors

    Returns:
        PortfolioSummary — fully populated dataclass.
    """
    cache = VendorProfileCache()
    profiles = cache.list_all()
    today = date.today()

    vendor_summaries = []
    dist = RiskDistribution()
    open_findings_total = 0
    intake_complete_count = 0
    drive_count = 0
    local_only_count = 0
    due_count = 0
    overdue_count = 0

    for profile in profiles:
        tier = profile.current_risk_tier
        avg = None
        history = profile.assessment_history or []

        if history:
            avg = history[0].get("weighted_average")

        # Risk distribution
        if not tier:
            dist.unassessed += 1
        elif tier == "HIGH":
            dist.high += 1
        elif tier == "MEDIUM":
            dist.medium += 1
        elif tier == "LOW":
            dist.low += 1

        # Due / overdue
        overdue = False
        days_overdue = None
        next_due = profile.next_due

        if next_due and next_due != "scan_only":
            try:
                due_date = datetime.strptime(
                    next_due, "%Y-%m-%d"
                ).date()
                if due_date < today:
                    overdue = True
                    days_overdue = (today - due_date).days
                    overdue_count += 1
                    due_count += 1
                elif due_date <= today:
                    due_count += 1
            except ValueError:
                pass
        elif not next_due and history:
            # Has been assessed but no next_due — flag
            due_count += 1

        # Intake
        if profile.intake_completed:
            intake_complete_count += 1

        # Data source
        has_drive = bool(profile.drive_folder_id)
        if has_drive:
            drive_count += 1
            data_source = "drive"
        else:
            local_only_count += 1
            data_source = "local"

        # Open findings (from last assessment if available)
        findings = getattr(profile, "open_findings", 0) or 0
        open_findings_total += findings

        from core.profiles.intake import normalise_sole_source
        replaceability = normalise_sole_source(
            getattr(profile, "sole_source", None)
        )

        summary = VendorSummary(
            vendor_name=profile.vendor_name,
            risk_tier=tier,
            weighted_average=avg,
            last_assessed=profile.last_assessed,
            next_due=next_due,
            overdue=overdue,
            days_overdue=days_overdue,
            intake_completed=profile.intake_completed,
            open_findings=findings,
            drive_folder_id=profile.drive_folder_id,
            data_source=data_source,
            assessment_count=len(history),
            replaceability=replaceability,
        )
        vendor_summaries.append(summary)

    # Apply filters
    if risk_filter:
        vendor_summaries = [
            v for v in vendor_summaries
            if (v.risk_tier or "").upper() == risk_filter.upper()
        ]
    if overdue_only:
        vendor_summaries = [
            v for v in vendor_summaries if v.overdue
        ]
    elif due_only:
        vendor_summaries = [
            v for v in vendor_summaries
            if v.overdue or v.next_due is None
        ]

    # Sort: overdue first, then by risk tier, then name
    tier_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, None: 3}
    vendor_summaries.sort(key=lambda v: (
        0 if v.overdue else 1,
        tier_order.get(v.risk_tier, 3),
        v.vendor_name.lower(),
    ))

    total = len(profiles)
    intake_rate = (
        intake_complete_count / total if total > 0 else 0.0
    )

    return PortfolioSummary(
        total_vendors=total,
        risk_distribution=dist,
        vendors_due=due_count,
        vendors_overdue=overdue_count,
        open_findings_total=open_findings_total,
        intake_completion_rate=intake_rate,
        drive_vendors=drive_count,
        local_only_vendors=local_only_count,
        generated_at=datetime.now().isoformat(),
        vendors=vendor_summaries,
    )
