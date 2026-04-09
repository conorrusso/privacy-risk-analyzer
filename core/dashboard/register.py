from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import csv
import io
import json

from core.profiles.vendor_cache import VendorProfileCache


@dataclass
class RegisterRow:
    """Single row in the TPRM register."""
    vendor_name: str
    risk_tier: Optional[str]
    weighted_average: Optional[float]
    last_assessed: Optional[str]
    next_due: Optional[str]
    assessment_count: int
    intake_completed: bool
    data_types: list[str]
    criticality: Optional[str]
    annual_spend: Optional[str]
    renewal_date: Optional[str]
    integrations: list[str]
    ai_in_service: Optional[str]
    ai_trains_on_data: Optional[str]
    sole_source: Optional[bool]
    drive_folder_id: Optional[str]
    open_findings: int
    assessment_scope: Optional[str]


@dataclass
class RegisterExport:
    """
    Complete TPRM vendor register.
    Returned by build_register().
    CLI saves as file. Future UI renders as table.
    """
    rows: list[RegisterRow]
    total_vendors: int
    generated_at: str
    format: str     # "csv" | "json" | "html"

    def to_csv(self) -> str:
        """CSV string for export."""
        output = io.StringIO()
        if not self.rows:
            return ""

        fields = [
            "Vendor", "Risk Tier", "Score",
            "Last Assessed", "Next Due",
            "Assessments", "Intake Complete",
            "Criticality", "Annual Spend",
            "Renewal Date", "Data Types",
            "Integrations", "AI in Service",
            "AI Training", "Sole Source",
            "Open Findings", "Drive Folder",
        ]

        writer = csv.DictWriter(
            output, fieldnames=fields
        )
        writer.writeheader()

        for row in self.rows:
            writer.writerow({
                "Vendor": row.vendor_name,
                "Risk Tier": row.risk_tier or "Unassessed",
                "Score": row.weighted_average or "—",
                "Last Assessed": row.last_assessed or "Never",
                "Next Due": row.next_due or "—",
                "Assessments": row.assessment_count,
                "Intake Complete": "Yes" if row.intake_completed else "No",
                "Criticality": row.criticality or "—",
                "Annual Spend": row.annual_spend or "—",
                "Renewal Date": row.renewal_date or "—",
                "Data Types": ", ".join(row.data_types),
                "Integrations": ", ".join(row.integrations),
                "AI in Service": row.ai_in_service or "—",
                "AI Training": row.ai_trains_on_data or "—",
                "Sole Source": "Yes" if row.sole_source else "No",
                "Open Findings": row.open_findings,
                "Drive Folder": (
                    "Yes" if row.drive_folder_id else "No"
                ),
            })

        return output.getvalue()

    def to_json(self) -> str:
        """JSON string for export or UI API."""
        import dataclasses
        return json.dumps(
            dataclasses.asdict(self),
            indent=2,
            default=str,
        )

    def to_html(self) -> str:
        """Standalone HTML register file."""
        tier_color = {
            "HIGH": "#d04444",
            "MEDIUM": "#e8922c",
            "LOW": "#3aaa5c",
        }
        rows_html = ""
        for row in self.rows:
            color = tier_color.get(
                row.risk_tier or "", "#9a9288"
            )
            tier_badge = (
                f'<span style="background:{color};'
                f'color:white;padding:2px 8px;'
                f'border-radius:4px;font-size:11px;'
                f'font-weight:700">'
                f'{row.risk_tier or "Unassessed"}</span>'
            )
            rows_html += f"""<tr>
              <td>{row.vendor_name}</td>
              <td>{tier_badge}</td>
              <td>{row.weighted_average or '—'}</td>
              <td>{row.last_assessed or 'Never'}</td>
              <td>{row.next_due or '—'}</td>
              <td>{row.criticality or '—'}</td>
              <td>{row.annual_spend or '—'}</td>
              <td>{row.renewal_date or '—'}</td>
              <td>{'✓' if row.intake_completed else '—'}</td>
              <td>{row.open_findings}</td>
            </tr>"""

        return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>TPRM Register — {self.generated_at[:10]}</title>
<style>
body{{font-family:system-ui,sans-serif;padding:32px;
  background:#faf8f4;color:#1a1814}}
h1{{font-size:22px;margin-bottom:4px}}
.meta{{color:#9a9288;font-size:13px;margin-bottom:28px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{background:#f0ede6;padding:10px 12px;text-align:left;
  font-weight:600;border-bottom:2px solid #e0d8cc;
  white-space:nowrap}}
td{{padding:10px 12px;border-bottom:1px solid #f0ede6}}
tr:hover td{{background:#f8f4ec}}
</style></head><body>
<h1>TPRM Vendor Register</h1>
<div class="meta">
  {self.total_vendors} vendors ·
  Generated {self.generated_at[:10]}
</div>
<table>
<thead><tr>
  <th>Vendor</th><th>Risk</th><th>Score</th>
  <th>Last Assessed</th><th>Next Due</th>
  <th>Criticality</th><th>Spend</th>
  <th>Renewal</th><th>Intake</th><th>Findings</th>
</tr></thead>
<tbody>{rows_html}</tbody>
</table>
</body></html>"""


def build_register() -> RegisterExport:
    """
    Build TPRM register from all vendor profiles.
    Pure data — no output, no side effects.
    """
    cache = VendorProfileCache()
    profiles = cache.list_all()
    rows = []

    for profile in profiles:
        history = profile.assessment_history or []
        avg = history[0].get("weighted_average") if history else None
        scope = history[0].get("scope") if history else None

        integrations = [
            i.get("system_name", "")
            for i in (profile.integrations or [])
            if i.get("system_name")
        ]

        rows.append(RegisterRow(
            vendor_name=profile.vendor_name,
            risk_tier=profile.current_risk_tier,
            weighted_average=avg,
            last_assessed=profile.last_assessed,
            next_due=profile.next_due,
            assessment_count=len(history),
            intake_completed=profile.intake_completed,
            data_types=profile.data_types or [],
            criticality=profile.criticality,
            annual_spend=profile.annual_spend,
            renewal_date=profile.renewal_date,
            integrations=integrations,
            ai_in_service=profile.ai_in_service,
            ai_trains_on_data=profile.ai_trains_on_data,
            sole_source=profile.sole_source,
            drive_folder_id=profile.drive_folder_id,
            open_findings=getattr(
                profile, "open_findings", 0
            ) or 0,
            assessment_scope=scope,
        ))

    # Sort by risk tier then name
    tier_order = {
        "HIGH": 0, "MEDIUM": 1,
        "LOW": 2, None: 3
    }
    rows.sort(key=lambda r: (
        tier_order.get(r.risk_tier, 3),
        r.vendor_name.lower()
    ))

    return RegisterExport(
        rows=rows,
        total_vendors=len(rows),
        generated_at=datetime.now().isoformat(),
        format="json",
    )
