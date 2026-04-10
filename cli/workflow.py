import click
import sys
from datetime import datetime
from rich.console import Console
from rich.prompt import Confirm
from rich import box
from rich.table import Table
from rich.panel import Panel

from core.profiles.vendor_cache import VendorProfileCache
from core.profiles.intake import IntakeWizard
from core.config import BanditConfig

console = Console()


@click.command("workflow")
@click.option("--drive", is_flag=True, default=False,
    help="Use Drive documents when assessing")
@click.option("--assess/--no-assess",
    default=True,
    help="Offer to assess after intake "
         "(default: yes)")
@click.option("--vendor", default=None,
    help="Run workflow for a single vendor only")
def workflow(drive, assess, vendor):
    """
    Vendor onboarding workflow.

    Finds vendors missing intake data, walks through
    the 12-question profile for each one, then
    batches assessments with Drive documents.

    Works for two scenarios:

    NEW VENDOR PROCUREMENT — run before you sign.
    Intake captures what data they will access.
    Assessment generates a Legal Bandit redline
    brief you can use in contract negotiations.

    EXISTING VENDORS — catches up vendors that were
    added via bandit sync without intake data.

    Examples:
      bandit workflow --drive
      bandit workflow --vendor "Cloudflare" --drive
    """
    cache = VendorProfileCache()
    config = BanditConfig()

    # ── Find vendors needing intake ───────────────

    if vendor:
        profile = cache.get(vendor)
        if not profile:
            console.print(
                f"\n  No profile found for "
                f"[bold]{vendor}[/bold].\n"
                f"  Run bandit sync first.\n"
            )
            return
        pending = [profile]
    else:
        all_profiles = cache.list_all()
        pending = [
            p for p in all_profiles
            if not p.intake_completed
        ]

    if not pending:
        console.print(
            "\n  [green]✓[/green]  "
            "All vendors have intake data.\n"
            "  Run [bold]bandit dashboard[/bold] "
            "to see your portfolio.\n"
        )
        return

    # ── Show what we found ────────────────────────

    console.print()
    console.print(Panel(
        f"[bold dark_orange]Bandit Vendor Workflow[/bold dark_orange]\n"
        f"[dim]Intake + assessment for "
        f"{len(pending)} vendor(s)[/dim]",
        border_style="dim",
        padding=(0, 2),
    ))
    console.print()

    table = Table(box=box.SIMPLE, show_header=True)
    table.add_column("Vendor", style="bold")
    table.add_column("Drive folder", justify="center")
    table.add_column("Last assessed", justify="right")
    table.add_column("Status")

    for p in pending:
        has_drive = "[green]☁[/green]" if p.drive_folder_id else "[dim]—[/dim]"
        last = p.last_assessed or "Never"
        status = (
            "[dim]Needs intake[/dim]"
            if not p.intake_completed
            else "[yellow]Needs assessment[/yellow]"
        )
        table.add_row(
            p.vendor_name,
            has_drive,
            last,
            status,
        )

    console.print(table)

    if not Confirm.ask(
        f"  Start intake for "
        f"{len(pending)} vendor(s)?",
        default=True
    ):
        console.print(
            "\n  [dim]Workflow cancelled.[/dim]\n"
        )
        return

    # ── Run intake for each vendor ────────────────

    completed = []
    skipped = []

    for i, profile in enumerate(pending, 1):
        console.print()
        console.print(
            f"  [bold dark_orange]"
            f"{'━' * 44}[/bold dark_orange]"
        )
        console.print(
            f"  [bold dark_orange]"
            f"Vendor {i} of {len(pending)} — "
            f"{profile.vendor_name}"
            f"[/bold dark_orange]"
        )
        console.print(
            f"  [bold dark_orange]"
            f"{'━' * 44}[/bold dark_orange]"
        )

        # Option to skip this vendor
        action = _ask_vendor_action(
            profile.vendor_name, i, len(pending)
        )

        if action == "skip":
            skipped.append(profile.vendor_name)
            continue

        # Run intake wizard
        wizard = IntakeWizard(profile.vendor_name)

        # Pre-fill any existing answers if re-running
        if profile.intake_completed:
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
            # Ctrl+C — offer to continue with next
            console.print()
            if i < len(pending):
                if not Confirm.ask(
                    "  Continue with next vendor?",
                    default=True
                ):
                    break
            skipped.append(profile.vendor_name)
            continue

        # Build IT action items
        it_actions = wizard.build_it_actions()

        # Apply answers to profile
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

        cache.save(profile.vendor_name, profile)
        wizard.show_summary()
        completed.append(profile.vendor_name)

        # Sync profile to Drive if configured
        try:
            drive_cfg = (
                config.get_profile()
                .get("integrations", {})
                .get("google_drive", {})
            )
            if drive_cfg.get("enabled") and drive_cfg.get(
                "root_folder_id"
            ):
                from core.integrations.google_drive import (
                    GoogleDriveClient
                )
                from core.data.resolver import (
                    VendorDataResolver
                )
                resolver = VendorDataResolver(
                    profile.vendor_name
                )
                resolver.sync_profile_to_drive()
        except Exception:
            pass  # Non-blocking

    # ── Intake summary ────────────────────────────

    console.print()
    console.print(
        f"  [bold]Intake complete[/bold]  "
        f"[green]{len(completed)} done[/green]"
        + (
            f"  [dim]{len(skipped)} skipped[/dim]"
            if skipped else ""
        )
    )

    if not completed or not assess:
        _show_next_steps(completed, drive)
        return

    # ── Offer batch assessment ────────────────────

    console.print()
    drive_note = (
        " with Drive documents"
        if drive else " (public policy only)"
    )

    if not Confirm.ask(
        f"  Assess all {len(completed)} vendor(s)"
        f"{drive_note} now?",
        default=True
    ):
        _show_next_steps(completed, drive)
        return

    console.print()

    # Run assessments in sequence
    assessment_results = []

    for i, vendor_name in enumerate(completed, 1):
        console.print(
            f"  [{i}/{len(completed)}] "
            f"Assessing [bold]{vendor_name}[/bold]..."
        )

        try:
            from cli.main import _run_single_assessment
            result, report_path = _run_single_assessment(
                vendor_name,
                use_drive=drive,
            )

            tier = getattr(result, "risk_tier", "?")
            avg = getattr(result, "weighted_average", 0)
            color = (
                "red" if tier == "HIGH"
                else "yellow" if tier == "MEDIUM"
                else "green"
            )

            console.print(
                f"  [{i}/{len(completed)}] "
                f"[bold]{vendor_name}[/bold]  "
                f"[{color}]{tier}[/{color}]  "
                f"{avg:.1f}/5.0  "
                f"[dim]✓ report saved[/dim]"
            )

            assessment_results.append({
                "vendor": vendor_name,
                "tier": tier,
                "score": avg,
                "success": True,
            })

        except Exception as e:
            console.print(
                f"  [{i}/{len(completed)}] "
                f"[bold]{vendor_name}[/bold]  "
                f"[red]Failed: {e}[/red]"
            )
            assessment_results.append({
                "vendor": vendor_name,
                "tier": None,
                "score": None,
                "success": False,
                "error": str(e),
            })

    # ── Final summary ─────────────────────────────

    console.print()
    console.print(
        f"  [bold dark_orange]"
        f"Workflow complete"
        f"[/bold dark_orange]"
    )
    console.print()

    succeeded = [r for r in assessment_results if r["success"]]
    failed = [r for r in assessment_results if not r["success"]]

    for r in succeeded:
        tier = r["tier"]
        color = (
            "red" if tier == "HIGH"
            else "yellow" if tier == "MEDIUM"
            else "green"
        )
        console.print(
            f"  [green]✓[/green]  "
            f"[bold]{r['vendor']}[/bold]  "
            f"[{color}]{tier}[/{color}]  "
            f"{r['score']:.1f}/5.0"
        )

    for r in failed:
        console.print(
            f"  [red]✗[/red]  "
            f"[bold]{r['vendor']}[/bold]  "
            f"[red]{r.get('error', 'Failed')}[/red]"
        )

    if failed:
        console.print(
            f"\n  [dim]{len(failed)} vendors failed. "
            f"Run bandit assess \"VendorName\" --drive "
            f"individually to retry.[/dim]"
        )

    console.print(
        f"\n  [dim]Run bandit dashboard to see "
        f"your full portfolio.[/dim]\n"
    )


def _ask_vendor_action(
    vendor_name: str,
    current: int,
    total: int,
) -> str:
    """Ask user what to do with this vendor."""
    console.print()
    console.print(
        f"  [dim]Vendor {current} of {total}[/dim]"
    )
    console.print(
        f"  1. Run intake for "
        f"[bold]{vendor_name}[/bold]"
    )
    console.print(f"  2. Skip {vendor_name}")
    console.print()

    while True:
        raw = click.prompt(
            "  Choice",
            default="1"
        ).strip()
        if raw == "1":
            return "intake"
        elif raw == "2":
            return "skip"
        else:
            console.print("  [red]Enter 1 or 2[/red]")


def _show_next_steps(
    completed: list[str],
    drive: bool,
) -> None:
    """Show next steps after workflow."""
    console.print()
    if completed:
        drive_flag = " --drive" if drive else ""
        console.print(
            "  [dim]To assess individually:[/dim]"
        )
        for v in completed[:3]:
            console.print(
                f"  [dim]bandit assess "
                f'"{v}"{drive_flag}[/dim]'
            )
        if len(completed) > 3:
            console.print(
                f"  [dim]... and "
                f"{len(completed) - 3} more[/dim]"
            )
    console.print(
        "\n  [dim]bandit dashboard[/dim]\n"
    )
