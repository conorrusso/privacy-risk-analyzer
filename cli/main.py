"""
Bandit CLI

Run with no arguments or --help to see the welcome screen.

Usage
-----
  bandit assess "Acme Corp"
  bandit assess acme.com -v
  bandit assess https://acme.com/privacy --json
  bandit rubric
  bandit rubric --dim D6
  bandit batch vendors.txt

Environment
-----------
  ANTHROPIC_API_KEY   Required for assess/batch (unless --api-key is passed).
"""
from __future__ import annotations

import json
import os
import sys

import click


def _load_dotenv() -> None:
    """Load config.env from repo root if present (no external dependencies)."""
    env_path = os.path.join(os.path.dirname(__file__), "..", "config.env")
    env_path = os.path.normpath(env_path)
    if not os.path.isfile(env_path):
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


_load_dotenv()


# ─────────────────────────────────────────────────────────────────────
# CLI group
# ─────────────────────────────────────────────────────────────────────

class _BanditGroup(click.Group):
    """Custom group that shows the welcome screen when invoked with no args."""

    def invoke(self, ctx: click.Context) -> None:
        if not ctx.protected_args and not ctx.args and not ctx.params.get("help"):
            from cli.welcome import show_welcome
            from rich.console import Console
            show_welcome(Console())
            return
        super().invoke(ctx)


@click.group(cls=_BanditGroup, invoke_without_command=True)
@click.pass_context
def main(ctx: click.Context) -> None:
    """Bandit — Vendor Privacy Risk Intelligence."""
    if ctx.invoked_subcommand is None and not ctx.args:
        pass


# ─────────────────────────────────────────────────────────────────────
# assess
# ─────────────────────────────────────────────────────────────────────

@main.command()
@click.argument("vendor", nargs=-1, required=True)
@click.option(
    "--model", default="claude-haiku-4-5-20251001", metavar="MODEL", show_default=True,
    help="Claude model ID",
)
@click.option(
    "--api-key", default=None, metavar="KEY", envvar="ANTHROPIC_API_KEY",
    help="Anthropic API key (default: $ANTHROPIC_API_KEY)",
)
@click.option("--json", "output_json", is_flag=True, help="Print JSON to terminal (report still saved)")
@click.option("-v", "--verbose", is_flag=True, help="Show discovery stages and extra detail")
@click.option("--no-report", is_flag=True, help="Skip saving the HTML report")
def assess(
    vendor: tuple,
    model: str,
    api_key: str | None,
    output_json: bool,
    verbose: bool,
    no_report: bool,
) -> None:
    """Assess a vendor's privacy practices.

    VENDOR can be a company name, domain, or URL.
    An HTML report is saved to ./reports/ after every run.

    \b
    Examples:
      bandit assess "Salesforce"
      bandit assess hubspot.com --verbose
      bandit assess "Acme Corp" --json > acme.json
      bandit assess "Acme Corp" --no-report
    """
    import datetime
    import pathlib
    from cli.terminal import assessment_progress, console, print_assessment
    from core.agents.privacy_bandit import PrivacyBandit
    from core.llm.anthropic import AnthropicProvider
    from core.scoring.rubric import result_to_dict

    if not api_key:
        console.print(
            "[bold red]Error:[/] ANTHROPIC_API_KEY not set.\n"
            "Set the environment variable or pass [color(220)]--api-key <key>[/]."
        )
        sys.exit(1)

    vendor_str = " ".join(vendor)
    provider = AnthropicProvider(model=model, api_key=api_key)

    try:
        with assessment_progress(verbose=verbose) as update:
            bandit = PrivacyBandit(provider=provider, on_progress=update)
            assessment = bandit.assess(vendor_str)
    except KeyboardInterrupt:
        console.print("\n  [bold color(196)]✗[/]  [color(245)]Assessment cancelled.[/]")
        sys.exit(0)
    except Exception as exc:
        console.print(f"[bold red]Error:[/] {exc}")
        sys.exit(1)

    # ── Terminal output ───────────────────────────────────────────────
    if output_json:
        output = result_to_dict(assessment.result)
        output["sources"] = [
            {"url": s.url, "chars": s.chars, "via": s.via}
            for s in assessment.sources
        ]
        click.echo(json.dumps(output, indent=2))
    else:
        print_assessment(assessment, verbose=verbose)

    # ── HTML report (always, unless --no-report) ──────────────────────
    if not no_report:
        date = datetime.date.today().isoformat()
        slug = _vendor_slug(vendor_str)
        reports_dir = pathlib.Path("reports")
        reports_dir.mkdir(exist_ok=True)
        report_path = reports_dir / f"{slug}-{date}.html"
        from cli.report import write_html_report
        write_html_report(report_path, assessment)
        console.print(
            f"\n  [color(243)]Report saved →[/] [color(172)]{report_path}[/]"
        )


# ─────────────────────────────────────────────────────────────────────
# rubric
# ─────────────────────────────────────────────────────────────────────

@main.command()
@click.option(
    "--dim", default=None, metavar="DIM",
    help="Show detail for one dimension, e.g. --dim D5",
)
def rubric(dim: str | None) -> None:
    """Show the scoring rubric.

    \b
    Examples:
      bandit rubric
      bandit rubric --dim D5
    """
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from core.scoring.rubric import RUBRIC, _RED_FLAGS

    con = Console()

    if dim:
        dim_key = dim.upper()
        if dim_key not in RUBRIC:
            con.print(f"[red]Unknown dimension: {dim_key}[/]  Valid: {', '.join(RUBRIC)}")
            sys.exit(1)

        rd = RUBRIC[dim_key]

        t = Table(box=None, show_header=False, padding=(0, 2))
        t.add_column(style="bold color(172)", no_wrap=True, min_width=14)
        t.add_column(style="color(245)")
        for level in sorted(rd["levels"].keys(), reverse=True):
            ld = rd["levels"][level]
            signals = "\n".join(f"  • {s}" for s in ld["required_signals"]) or "  (none required)"
            t.add_row(
                f"{level}  {ld['label']}",
                f"{ld['description']}\n[color(243)]{signals}[/]",
            )

        rf_text = Text()
        for pattern, dims, ceiling, label in _RED_FLAGS:
            if dim_key in dims:
                rf_text.append("  ⚠  ", style="color(220)")
                rf_text.append(label, style="bold color(220)")
                rf_text.append(f"  → caps at {ceiling}/5\n", style="color(243)")

        reg_text = Text()
        for r in rd["regulatory_basis"]:
            reg_text.append(f"  • {r}\n", style="color(245)")

        con.print(Panel(
            t,
            title=f"[bold color(172)]{dim_key} — {rd['name']}[/]  [color(243)](weight ×{rd['weight']:.1f})[/]",
            border_style="color(238)",
        ))

        if rf_text.plain.strip():
            con.print(Panel(
                rf_text,
                title=f"[bold color(220)]RED FLAGS — {dim_key}[/]",
                border_style="color(220)",
            ))

        con.print(Panel(
            reg_text,
            title=f"[bold color(172)]REGULATORY BASIS — {dim_key}[/]",
            border_style="color(238)",
        ))

    else:
        t = Table(box=None, show_header=True, padding=(0, 2))
        t.add_column("Dim",    style="bold color(172)", no_wrap=True)
        t.add_column("Name",   style="color(245)")
        t.add_column("Weight", style="color(243)", justify="right")
        t.add_column("Regulatory basis", style="color(245)")

        for dim_key, rd in RUBRIC.items():
            t.add_row(
                dim_key,
                rd["name"],
                f"×{rd['weight']:.1f}",
                rd["regulatory_basis"][0],
            )

        tier_text = Text()
        tier_text.append("  HIGH    ", style="bold color(196)")
        tier_text.append("weighted average < 2.5\n", style="color(245)")
        tier_text.append("  MEDIUM  ", style="bold color(220)")
        tier_text.append("2.5 ≤ weighted average ≤ 3.5\n", style="color(245)")
        tier_text.append("  LOW     ", style="bold color(82)")
        tier_text.append("weighted average > 3.5\n", style="color(245)")

        con.print(Panel(
            t,
            title="[bold color(172)]BANDIT RUBRIC — 8 Dimensions[/]",
            border_style="color(238)",
        ))
        con.print(Panel(
            tier_text,
            title="[bold color(172)]RISK TIER THRESHOLDS[/]",
            border_style="color(238)",
        ))


# ─────────────────────────────────────────────────────────────────────
# batch
# ─────────────────────────────────────────────────────────────────────

@main.command()
@click.argument("file", type=click.Path(exists=True, readable=True, dir_okay=False))
@click.option(
    "--model", default="claude-haiku-4-5-20251001", metavar="MODEL", show_default=True,
    help="Claude model ID",
)
@click.option(
    "--api-key", default=None, metavar="KEY", envvar="ANTHROPIC_API_KEY",
    help="Anthropic API key (default: $ANTHROPIC_API_KEY)",
)
@click.option(
    "--out-dir", default="reports", metavar="DIR", show_default=True,
    help="Directory to save HTML reports",
)
def batch(file: str, model: str, api_key: str | None, out_dir: str) -> None:
    """Assess a list of vendors from a text file.

    FILE should contain one vendor (name, domain, or URL) per line.
    Lines starting with # and blank lines are ignored.

    \b
    Example:
      bandit batch vendors.txt
    """
    import datetime
    import pathlib
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from cli.terminal import assessment_progress
    from core.agents.privacy_bandit import PrivacyBandit
    from core.llm.anthropic import AnthropicProvider

    con = Console()

    if not api_key:
        con.print(
            "[bold red]Error:[/] ANTHROPIC_API_KEY not set.\n"
            "Set the environment variable or pass [color(220)]--api-key <key>[/]."
        )
        sys.exit(1)

    vendors = []
    with open(file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                vendors.append(line)

    if not vendors:
        con.print("[yellow]No vendors found in file.[/]")
        sys.exit(0)

    con.print(f"\n[bold color(172)]BANDIT BATCH[/]  [color(243)]{len(vendors)} vendor(s) from {file}[/]\n")

    out_path = pathlib.Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    provider = AnthropicProvider(model=model, api_key=api_key)
    date = datetime.date.today().isoformat()
    results = []   # (vendor, tier, score, report_path, error)

    try:
        for i, vendor in enumerate(vendors, 1):
            con.print(f"[color(245)][{i}/{len(vendors)}][/]  [color(220)]{vendor}[/]")
            try:
                with assessment_progress() as update:
                    bandit = PrivacyBandit(provider=provider, on_progress=update)
                    assessment = bandit.assess(vendor)

                result = assessment.result
                report_file = out_path / f"{_vendor_slug(vendor)}-{date}.html"
                from cli.report import write_html_report
                write_html_report(report_file, assessment)

                results.append((vendor, result.risk_tier, result.weighted_average, str(report_file), None))
                _TC = {"HIGH": "color(196)", "MEDIUM": "color(220)", "LOW": "color(82)"}
                con.print(
                    f"    [{_TC.get(result.risk_tier,'color(245)')}]{result.risk_tier}[/]  "
                    f"[bold]{result.weighted_average}[/]/5.0  "
                    f"[color(243)]{report_file}[/]"
                )

            except KeyboardInterrupt:
                raise
            except Exception as exc:
                results.append((vendor, "ERROR", 0.0, "", str(exc)))
                con.print(f"    [bold red]ERROR:[/] {exc}")
    except KeyboardInterrupt:
        completed = len(results)
        remaining = vendors[completed:]
        con.print(
            f"\n  [bold color(196)]✗[/]  "
            f"[color(245)]Batch cancelled after {completed}/{len(vendors)} vendors.[/]"
        )
        if completed > 0:
            con.print(f"     [color(243)]Completed reports saved to {out_dir}/[/]")
        if remaining:
            preview = ", ".join(remaining[:5])
            if len(remaining) > 5:
                preview += f" +{len(remaining) - 5} more"
            con.print(f"     [color(243)]Remaining vendors: {preview}[/]")
        sys.exit(0)

    con.print()
    t = Table(box=None, show_header=True, padding=(0, 2))
    t.add_column("Vendor", style="color(250)")
    t.add_column("Risk",   no_wrap=True)
    t.add_column("Score",  style="bold", justify="right")
    t.add_column("Report", style="color(243)")

    _TC2 = {"HIGH": "bold color(196)", "MEDIUM": "bold color(220)", "LOW": "bold color(82)"}
    for vendor, tier, score, report, error in results:
        if error:
            t.add_row(vendor, "[bold red]ERROR[/]", "—", error[:60])
        else:
            t.add_row(vendor, f"[{_TC2.get(tier,'bold')}]{tier}[/]", f"{score}/5.0", report)

    con.print(Panel(
        t,
        title=f"[bold color(172)]BATCH SUMMARY — {len(vendors)} vendor(s)[/]",
        border_style="color(238)",
    ))
    con.print()


# ─────────────────────────────────────────────────────────────────────
# Report helpers
# ─────────────────────────────────────────────────────────────────────

def _vendor_slug(vendor: str) -> str:
    """Convert a vendor name to a filename-safe slug.

    "Salesforce"   → "salesforce"
    "HubSpot"      → "hubspot"
    "Anecdotes AI" → "anecdotes-ai"
    """
    import re
    s = vendor.strip().lower()
    # Strip leading URL components
    s = re.sub(r"^https?://[^\s/]+/?", "", s)
    # Keep alphanumeric, spaces, hyphens
    s = re.sub(r"[^a-z0-9 -]", "", s).strip()
    # Spaces → hyphens, collapse runs
    s = re.sub(r"[\s-]+", "-", s).strip("-")
    return s or "vendor"




if __name__ == "__main__":
    main()
