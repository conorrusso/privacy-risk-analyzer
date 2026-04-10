import click
import json as json_module
from rich.console import Console
from rich.table import Table
from rich import box

from core.dashboard.portfolio import get_summary
from core.dashboard.schedule import get_schedule
from core.dashboard.register import build_register
from core.notifications.sender import (
    send_it_notification, send_all_pending
)

console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
def dashboard(ctx):
    """Portfolio dashboard and reporting commands."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(dashboard_show)


# ── bandit dashboard show ────────────────────────────────

@dashboard.command("show")
@click.option("--risk", default=None,
    help="Filter by risk tier: HIGH/MEDIUM/LOW")
@click.option("--due", is_flag=True, default=False,
    help="Show only vendors due for reassessment")
@click.option("--json", "as_json", is_flag=True,
    default=False, help="Output raw JSON")
def dashboard_show(risk, due, as_json):
    """Show portfolio risk dashboard."""
    summary = get_summary(
        risk_filter=risk,
        due_only=due,
    )

    if as_json:
        click.echo(summary.to_json())
        return

    # Header stats
    console.print()
    console.print(
        f"  [bold dark_orange]"
        f"Bandit Portfolio Dashboard"
        f"[/bold dark_orange]"
        f"  [dim]{summary.generated_at[:10]}[/dim]"
    )
    console.print()

    d = summary.risk_distribution
    console.print(
        f"  [bold]{summary.total_vendors}[/bold] vendors  "
        f"  [red]{d.high} HIGH[/red]  "
        f"[yellow]{d.medium} MEDIUM[/yellow]  "
        f"[green]{d.low} LOW[/green]  "
        f"[dim]{d.unassessed} unassessed[/dim]"
    )
    console.print(
        f"  [dim]"
        f"{summary.vendors_overdue} overdue  ·  "
        f"{summary.vendors_due} due  ·  "
        f"{summary.open_findings_total} open findings  ·  "
        f"Intake {int(summary.intake_completion_rate*100)}% complete  ·  "
        f"{summary.drive_vendors} vendors on Drive"
        f"[/dim]"
    )
    console.print()

    if not summary.vendors:
        console.print(
            "  [dim]No vendors match the filter.[/dim]\n"
        )
        return

    table = Table(box=box.SIMPLE, show_header=True)
    table.add_column("Vendor", style="bold")
    table.add_column("Risk", justify="center")
    table.add_column("Score", justify="right")
    table.add_column("Last assessed", justify="right")
    table.add_column("Next due", justify="right")
    table.add_column("Findings", justify="right")
    table.add_column("Source", justify="center")
    table.add_column("Intake", justify="center")

    for v in summary.vendors:
        tier = v.risk_tier or "—"
        color = (
            "red" if tier == "HIGH"
            else "yellow" if tier == "MEDIUM"
            else "green" if tier == "LOW"
            else "dim"
        )
        score = (
            f"{v.weighted_average}/5.0"
            if v.weighted_average else "—"
        )
        next_due = v.next_due or "—"
        if v.overdue:
            next_due = (
                f"[red]{next_due} "
                f"({v.days_overdue}d)[/red]"
            )
        source_icon = "☁" if v.data_source == "drive" else "⊙"
        intake = "[green]✓[/green]" if v.intake_completed else "[dim]—[/dim]"

        name_display = v.vendor_name
        if v.replaceability == "not_replaceable":
            name_display = (
                f"{v.vendor_name} [dim](locked in)[/dim]"
            )

        table.add_row(
            name_display,
            f"[{color}]{tier}[/{color}]",
            score,
            v.last_assessed or "Never",
            next_due,
            str(v.open_findings),
            source_icon,
            intake,
        )

    console.print(table)
    console.print(
        f"  [dim]{len(summary.vendors)} vendors  "
        f"·  ☁ = Drive  ⊙ = local[/dim]\n"
    )


# ── bandit dashboard schedule ────────────────────────────

@dashboard.command("schedule")
@click.option("--due", is_flag=True, default=False,
    help="Show only due/overdue vendors")
@click.option("--within", default=None, type=int,
    help="Show vendors due within N days")
@click.option("--json", "as_json", is_flag=True,
    default=False, help="Output raw JSON")
def schedule_show(due, within, as_json):
    """Show reassessment schedule."""
    sched = get_schedule(
        due_only=due,
        within_days=within,
    )

    if as_json:
        click.echo(sched.to_json())
        return

    console.print()
    console.print(
        "  [bold dark_orange]"
        "Reassessment Schedule"
        "[/bold dark_orange]"
    )
    console.print(
        f"  [dim]"
        f"{sched.overdue_count} overdue  ·  "
        f"{sched.due_within_30_days} due within 30 days  ·  "
        f"{sched.due_within_90_days} due within 90 days"
        f"[/dim]"
    )
    console.print()

    if not sched.entries:
        console.print("  [dim]No vendors to show.[/dim]\n")
        return

    table = Table(box=box.SIMPLE, show_header=True)
    table.add_column("Vendor", style="bold")
    table.add_column("Risk", justify="center")
    table.add_column("Last assessed", justify="right")
    table.add_column("Next due", justify="right")
    table.add_column("Status", justify="center")
    table.add_column("Depth")
    table.add_column("Data")

    urgency_display = {
        "overdue": "[red]OVERDUE[/red]",
        "due_soon": "[yellow]DUE SOON[/yellow]",
        "upcoming": "[dim]UPCOMING[/dim]",
        "ok": "[green]OK[/green]",
    }

    for e in sched.entries:
        tier = e.risk_tier or "—"
        color = (
            "red" if tier == "HIGH"
            else "yellow" if tier == "MEDIUM"
            else "green" if tier == "LOW"
            else "dim"
        )

        next_due = e.next_due or "—"
        if e.overdue and e.days_overdue:
            next_due = (
                f"[red]{next_due} "
                f"({e.days_overdue}d ago)[/red]"
            )

        data_label = (
            "[blue]Drive[/blue]"
            if e.data_source == "drive"
            else "[dim]Local[/dim]"
        )

        table.add_row(
            e.vendor_name,
            f"[{color}]{tier}[/{color}]",
            e.last_assessed or "Never",
            next_due,
            urgency_display.get(e.urgency, e.urgency),
            e.recommended_depth,
            data_label,
        )

    console.print(table)
    console.print()


# ── bandit dashboard register ────────────────────────────

@dashboard.command("register")
@click.option("--format", "fmt",
    type=click.Choice(["csv", "json", "html"]),
    default="csv", help="Output format")
@click.option("--out", default=None,
    help="Output file path (default: stdout for csv/json, "
         "register-YYYY-MM-DD.html for html)")
def register_export(fmt, out):
    """Export TPRM vendor register."""
    from datetime import date

    data = build_register()
    data.format = fmt

    if fmt == "csv":
        output = data.to_csv()
    elif fmt == "json":
        output = data.to_json()
    else:
        output = data.to_html()

    if out:
        with open(out, "w", encoding="utf-8") as f:
            f.write(output)
        console.print(
            f"\n  [green]✓[/green] "
            f"Register saved to {out} "
            f"({data.total_vendors} vendors)\n"
        )
    elif fmt == "html":
        default_name = (
            f"bandit-register-{date.today()}.html"
        )
        with open(default_name, "w", encoding="utf-8") as f:
            f.write(output)
        console.print(
            f"\n  [green]✓[/green] "
            f"Register saved to {default_name} "
            f"({data.total_vendors} vendors)\n"
        )
    else:
        click.echo(output)


# ── bandit dashboard notify ──────────────────────────────

@dashboard.command("notify")
@click.argument("vendor_name", required=False)
@click.option("--all", "send_all", is_flag=True,
    default=False,
    help="Send all pending notifications")
@click.option("--json", "as_json", is_flag=True,
    default=False, help="Output raw JSON")
def notify_send(vendor_name, send_all, as_json):
    """Send queued IT notifications."""
    if send_all:
        summary = send_all_pending()

        if as_json:
            click.echo(summary.to_json())
            return

        console.print()
        if summary.sent:
            for r in summary.sent:
                console.print(
                    f"  [green]✓[/green] "
                    f"{r.vendor_name} → {r.channel}"
                )
        if summary.failed:
            for r in summary.failed:
                console.print(
                    f"  [red]✗[/red] "
                    f"{r.vendor_name}: {r.error}"
                )
        console.print(
            f"\n  [dim]"
            f"Sent: {len(summary.sent)}  "
            f"Failed: {len(summary.failed)}  "
            f"Skipped (no pending): {summary.skipped}"
            f"[/dim]\n"
        )
        return

    if not vendor_name:
        console.print(
            "\n  Specify a vendor or use --all\n"
            "  bandit notify \"Cyera\"\n"
            "  bandit notify --all\n"
        )
        return

    result = send_it_notification(vendor_name)

    if as_json:
        import dataclasses
        click.echo(
            json_module.dumps(
                dataclasses.asdict(result),
                indent=2,
                default=str,
            )
        )
        return

    if result.success:
        console.print(
            f"\n  [green]✓[/green] "
            f"Notification sent for {vendor_name} "
            f"via {result.channel}\n"
        )
    else:
        console.print(
            f"\n  [red]✗[/red] "
            f"Failed for {vendor_name}: {result.error}\n"
        )
