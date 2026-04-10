"""
Bandit vendor commands — manage vendor profiles and intake data.
"""
from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table
from rich import box
from datetime import datetime, date
from core.profiles.vendor_cache import VendorProfileCache
from core.profiles.intake import IntakeWizard
from core.profiles.auto_detect import VendorAutoDetector
from core.config import BanditConfig

console = Console()


@click.group()
def vendor():
    """Manage vendor profiles and intake data."""
    pass


@vendor.command("add")
@click.argument("vendor_name")
def vendor_add(vendor_name):
    """
    Run intake wizard for a new vendor.
    Stores profile locally and syncs to Drive
    if configured.
    """
    cache = VendorProfileCache()
    config = BanditConfig()

    # Step 1 — Check local profile exists
    existing = cache.get(vendor_name)
    if existing and existing.intake_completed:
        console.print(
            f"\n  Profile already exists for "
            f"[bold]{vendor_name}[/bold].\n"
            f"  Use [bold]bandit vendor edit "
            f'"{vendor_name}"[/bold] to update.'
        )
        return

    # Step 2 — Check Drive for existing folder
    drive_folder_id = None
    drive_folder_name = None
    drive = None

    drive_config = config.get_profile().get(
        "integrations", {}
    ).get("google_drive", {})
    drive_enabled = drive_config.get("enabled", False)
    root_folder_id = drive_config.get(
        "root_folder_id"
    )

    if drive_enabled and root_folder_id:
        try:
            from core.integrations.google_drive import (
                GoogleDriveClient
            )
            drive = GoogleDriveClient()
            drive.authenticate()

            candidates = drive.find_vendor_folder_fuzzy(
                vendor_name, root_folder_id
            )

            if candidates:
                exact = [
                    c for c in candidates
                    if c["match"] == "exact"
                ]
                close = [
                    c for c in candidates
                    if c["match"] == "close"
                ]

                if exact:
                    drive_folder_id = exact[0]["id"]
                    drive_folder_name = exact[0]["name"]
                    console.print(
                        f"  [green]✓[/green] "
                        f"Found Drive folder: "
                        f"{drive_folder_name}"
                    )

                elif close:
                    console.print(
                        f"\n  Found similar Drive "
                        f"folder: "
                        f"[bold]{close[0]['name']}"
                        f"[/bold]"
                    )
                    use_existing = click.confirm(
                        "  Is this the same vendor?",
                        default=True
                    )
                    if use_existing:
                        drive_folder_id = close[0]["id"]
                        drive_folder_name = (
                            close[0]["name"]
                        )
                    else:
                        create = click.confirm(
                            f'  Create new folder '
                            f'"{vendor_name}" '
                            f'in Drive?',
                            default=True
                        )
                        if create:
                            drive_folder_id = (
                                drive.create_vendor_folder(
                                    vendor_name,
                                    root_folder_id
                                )
                            )
                            drive_folder_name = (
                                vendor_name
                            )
                            console.print(
                                f"  [green]✓[/green] "
                                f"Created Drive folder: "
                                f"{vendor_name}"
                            )
            else:
                console.print()
                create = click.confirm(
                    f'  No Drive folder found for '
                    f'"{vendor_name}". Create one?',
                    default=True
                )
                if create:
                    drive_folder_id = (
                        drive.create_vendor_folder(
                            vendor_name, root_folder_id
                        )
                    )
                    drive_folder_name = vendor_name
                    console.print(
                        f"  [green]✓[/green] "
                        f"Created: "
                        f"Bandit/{vendor_name}/"
                    )

        except Exception as e:
            console.print(
                f"  [yellow]⚠ Could not check Drive: "
                f"{e}[/yellow]"
            )

    # Step 3 — Run intake wizard
    wizard = IntakeWizard(vendor_name)
    answers = wizard.run()

    if answers is None:
        return  # Cancelled by user

    # Step 4 — Build IT action items
    it_actions = wizard.build_it_actions()

    # Step 5 — Build and save profile
    detector = VendorAutoDetector()
    detect_result = detector.detect(vendor_name)

    # Get existing profile or create new
    profile = cache.get(vendor_name)
    if not profile:
        profile = cache._build_new_profile(
            vendor_name, detect_result
        )

    # Apply intake answers to profile
    profile.intake_completed = True
    profile.intake_date = datetime.now().strftime(
        "%Y-%m-%d"
    )
    profile.data_types = answers.get("data_types", [])
    profile.environment_access = answers.get(
        "environment_access"
    )
    profile.access_level = answers.get("access_level")
    profile.sole_source = answers.get("sole_source")
    profile.integrations = answers.get("integrations", [])
    profile.sso_required = answers.get("sso_required")
    profile.ai_in_service = answers.get("ai_in_service")
    profile.ai_trains_on_data = answers.get(
        "ai_trains_on_data"
    )
    profile.criticality = answers.get("criticality")
    profile.annual_spend = answers.get("annual_spend")
    profile.renewal_date = answers.get("renewal_date")
    profile.last_updated = datetime.now().strftime(
        "%Y-%m-%d"
    )

    # Drive folder
    if drive_folder_id:
        profile.drive_folder_id = drive_folder_id
        profile.drive_folder_name = drive_folder_name

    # IT notification queue
    if it_actions:
        profile.pending_it_notification = {
            "status": "pending",
            "created": datetime.now().strftime(
                "%Y-%m-%d"
            ),
            "integrations": [
                i["system_name"]
                for i in answers.get("integrations", [])
            ],
            "it_actions": it_actions,
        }

    # Save locally
    cache.save(vendor_name, profile)

    # Show summary
    wizard.show_summary()

    # IT notification note
    if it_actions:
        console.print(
            f"\n  [dim]IT notification queued "
            f"({len(it_actions)} action items).[/dim]"
            "\n  [dim]Configure sending: "
            "bandit setup --notify[/dim]"
        )

    # Sync to Drive
    if drive_enabled and root_folder_id and drive:
        try:
            synced = cache.sync_to_drive(
                drive, root_folder_id
            )
            if synced:
                console.print(
                    "  [green]✓[/green] "
                    "Profile synced to Drive"
                )
        except Exception:
            pass  # Fail silently

    console.print(
        f"\n  [dim]Next: bandit assess "
        f'"{vendor_name}" --drive[/dim]\n'
    )


@vendor.command("show")
@click.argument("vendor_name")
def vendor_show(vendor_name):
    """Show vendor profile and assessment history."""
    cache = VendorProfileCache()
    profile = cache.get(vendor_name)

    if not profile:
        console.print(
            f"\n  No profile found for "
            f"[bold]{vendor_name}[/bold].\n"
            f"  Run: bandit vendor add "
            f'"{vendor_name}"'
        )
        return

    console.print(
        f"\n  [bold dark_orange]"
        f"{profile.vendor_name}[/bold dark_orange]"
    )

    if profile.intake_completed:
        console.print(
            f"  Intake completed: {profile.intake_date}"
        )
    else:
        console.print(
            "  [yellow]No intake data — "
            "run bandit vendor add to complete[/yellow]"
        )

    # Profile details
    if profile.intake_completed:
        console.print("\n  [dim]PROFILE[/dim]")

        rows = [
            ("Data types", ", ".join(
                profile.data_types or []
            ) or "—"),
            ("Environment", profile.environment_access or "—"),
            ("Access", profile.access_level or "—"),
            ("Sole source", (
                "Yes" if profile.sole_source else "No"
            )),
            ("Integrations", ", ".join(
                i["system_name"]
                for i in (profile.integrations or [])
            ) or "None"),
            ("AI in service", profile.ai_in_service or "—"),
            ("AI training", profile.ai_trains_on_data or "—"),
            ("Criticality", profile.criticality or "—"),
            ("Annual spend", profile.annual_spend or "—"),
            ("Renewal", profile.renewal_date or "—"),
        ]
        for key, val in rows:
            console.print(
                f"  [dim]{key:<16}[/dim] {val}"
            )

    # Assessment history
    history = profile.assessment_history or []
    if history:
        console.print("\n  [dim]ASSESSMENT HISTORY[/dim]")
        for entry in history[:5]:
            tier = entry.get("risk_tier", "?")
            avg = entry.get("weighted_average", 0)
            d = entry.get("date", "?")
            next_d = entry.get("next_due", "?")
            color = (
                "red" if tier == "HIGH"
                else "yellow" if tier == "MEDIUM"
                else "green"
            )
            console.print(
                f"  {d}  "
                f"[{color}]{tier}[/{color}]  "
                f"{avg}/5.0  "
                f"[dim]next due: {next_d}[/dim]"
            )
    else:
        console.print(
            "\n  [dim]No assessments yet.[/dim]"
            "\n  [dim]Run: bandit assess "
            f'"{vendor_name}"[/dim]'
        )

    console.print()


@vendor.command("edit")
@click.argument("vendor_name")
def vendor_edit(vendor_name):
    """Re-run intake with current values as defaults."""
    cache = VendorProfileCache()
    profile = cache.get(vendor_name)

    if not profile:
        console.print(
            f"\n  No profile found for "
            f"[bold]{vendor_name}[/bold].\n"
            f"  Run: bandit vendor add "
            f'"{vendor_name}"'
        )
        return

    console.print(
        f"\n  Editing profile for "
        f"[bold]{vendor_name}[/bold].\n"
        "  Press Enter to keep current value.\n"
    )

    wizard = IntakeWizard(vendor_name)
    wizard.answers = {
        "data_types": profile.data_types or [],
        "environment_access": profile.environment_access,
        "access_level": profile.access_level,
        "sole_source": profile.sole_source,
        "integrations": profile.integrations or [],
        "sso_required": profile.sso_required,
        "ai_in_service": profile.ai_in_service,
        "ai_trains_on_data": profile.ai_trains_on_data,
        "criticality": profile.criticality,
        "annual_spend": profile.annual_spend,
        "renewal_date": profile.renewal_date,
    }

    answers = wizard.run()
    if answers is None:
        return

    # Update profile fields
    profile.data_types = answers.get(
        "data_types", profile.data_types
    )
    profile.environment_access = answers.get(
        "environment_access", profile.environment_access
    )
    profile.access_level = answers.get(
        "access_level", profile.access_level
    )
    profile.sole_source = answers.get(
        "sole_source", profile.sole_source
    )
    profile.integrations = answers.get(
        "integrations", profile.integrations
    )
    profile.sso_required = answers.get(
        "sso_required", profile.sso_required
    )
    profile.ai_in_service = answers.get(
        "ai_in_service", profile.ai_in_service
    )
    profile.ai_trains_on_data = answers.get(
        "ai_trains_on_data", profile.ai_trains_on_data
    )
    profile.criticality = answers.get(
        "criticality", profile.criticality
    )
    profile.annual_spend = answers.get(
        "annual_spend", profile.annual_spend
    )
    profile.renewal_date = answers.get(
        "renewal_date", profile.renewal_date
    )
    profile.last_updated = datetime.now().strftime(
        "%Y-%m-%d"
    )

    cache.save(vendor_name, profile)
    wizard.show_summary()
    console.print()


@vendor.command("list")
@click.option(
    "--due",
    is_flag=True,
    default=False,
    help="Show only vendors due for reassessment"
)
@click.option(
    "--risk",
    default=None,
    help="Filter by risk tier (HIGH/MEDIUM/LOW)"
)
def vendor_list(due, risk):
    """List all vendor profiles."""
    cache = VendorProfileCache()
    profiles = cache.list_all()

    if not profiles:
        console.print(
            "\n  No vendor profiles found.\n"
            '  Run: bandit vendor add "VendorName"'
        )
        return

    # Filter
    if risk:
        profiles = [
            p for p in profiles
            if (p.current_risk_tier or "").upper()
            == risk.upper()
        ]

    today = date.today()

    if due:
        def is_due(p):
            if not p.next_due:
                return True
            if p.next_due == "scan_only":
                return False
            try:
                due_date = datetime.strptime(
                    p.next_due, "%Y-%m-%d"
                ).date()
                return due_date <= today
            except Exception:
                return False

        profiles = [p for p in profiles if is_due(p)]

    if not profiles:
        console.print(
            "\n  No vendors match the filter.\n"
        )
        return

    table = Table(box=box.SIMPLE, show_header=True)
    table.add_column("Vendor", style="bold")
    table.add_column("Risk", justify="center")
    table.add_column("Score", justify="right")
    table.add_column("Last assessed", justify="right")
    table.add_column("Next due", justify="right")
    table.add_column("Intake", justify="center")

    for p in sorted(
        profiles,
        key=lambda x: x.vendor_name.lower()
    ):
        tier = p.current_risk_tier or "—"
        tier_color = (
            "red" if tier == "HIGH"
            else "yellow" if tier == "MEDIUM"
            else "green" if tier == "LOW"
            else "dim"
        )

        history = p.assessment_history or []
        score = (
            f"{history[0]['weighted_average']}/5.0"
            if history else "—"
        )
        last = history[0]["date"] if history else "—"
        next_d = p.next_due or "—"

        # Flag overdue
        overdue = False
        if p.next_due and p.next_due != "scan_only":
            try:
                due_date = datetime.strptime(
                    p.next_due, "%Y-%m-%d"
                ).date()
                overdue = due_date < today
            except Exception:
                pass

        next_display = (
            f"[red]{next_d} ⚠[/red]"
            if overdue else next_d
        )

        intake_status = (
            "[green]✓[/green]"
            if p.intake_completed
            else "[dim]—[/dim]"
        )

        table.add_row(
            p.vendor_name,
            f"[{tier_color}]{tier}[/{tier_color}]",
            score,
            last,
            next_display,
            intake_status,
        )

    console.print()
    console.print(table)
    console.print(
        f"  [dim]{len(profiles)} vendor(s)[/dim]\n"
    )
