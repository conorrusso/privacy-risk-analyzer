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
import pathlib
import sys

import click

from core.data.resolver import (
    VendorDataResolver,
    get_all_vendor_resolvers,
)

_HISTORY_PATH = pathlib.Path.home() / ".bandit" / "vendor-history.json"


def _load_history() -> dict:
    try:
        if _HISTORY_PATH.exists():
            with open(_HISTORY_PATH) as f:
                return json.load(f)
    except (OSError, json.JSONDecodeError):
        pass
    return {}


def _save_history(slug: str, risk_tier: str, weighted_average: float) -> None:
    import datetime
    import tempfile
    history = _load_history()
    history[slug] = {
        "last_assessed": datetime.date.today().isoformat(),
        "risk_tier": risk_tier,
        "weighted_average": weighted_average,
    }
    try:
        _HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = pathlib.Path(tempfile.mktemp(dir=_HISTORY_PATH.parent, suffix=".tmp"))
        tmp.write_text(json.dumps(history, indent=2))
        tmp.replace(_HISTORY_PATH)
    except OSError:
        pass


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
@click.option(
    "--docs",
    type=click.Path(exists=True, file_okay=False),
    default=None,
    metavar="PATH",
    help="Path to folder containing vendor documents (DPA, MSA, SOC 2, etc.)",
)
@click.option("--drive", is_flag=True, default=False, help="Fetch vendor documents from configured Google Drive folder")
@click.option("--force", is_flag=True, help="Run assessment even if cadence says not due")
@click.option("--no-legal-brief", is_flag=True, default=False, help="Skip generating the standalone legal brief")
def assess(
    vendor: tuple,
    model: str,
    api_key: str | None,
    output_json: bool,
    verbose: bool,
    no_report: bool,
    docs: str | None,
    drive: bool,
    force: bool,
    no_legal_brief: bool,
) -> None:
    """Assess a vendor's privacy practices.

    VENDOR can be a company name, domain, or URL.
    An HTML report is saved to ./reports/ after every run.

    \b
    Examples:
      bandit assess "Salesforce"
      bandit assess hubspot.com --verbose
      bandit assess "Acme Corp" --docs ./vendor-docs/acme/
      bandit assess "Acme Corp" --drive
      bandit assess "Acme Corp" --json > acme.json
    """
    import datetime
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

    # Show active profile — or prompt first-time setup
    from core.config import get_profile_label, load_config
    _config = load_config()
    if _config:
        _label = get_profile_label(_config)
        if _label:
            console.print(f"  [color(245)]Profile:[/] [color(220)]{_label}[/]")
    else:
        console.print()
        console.print(
            "  [bold color(220)]No profile configured.[/]  "
            "[color(245)]Bandit will use default weights.[/]"
        )
        console.print(
            "  [color(245)]Run [color(220)]bandit setup[/][color(245)] first to tailor scoring "
            "to your industry and regulatory context.[/]"
        )
        console.print()
        console.print("  [color(245)]s)[/]  Run setup now (recommended)")
        console.print("  [color(245)]a)[/]  Assess anyway with default weights")
        console.print("  [color(245)]q)[/]  Quit")
        console.print()
        _choice = console.input(
            "  [color(220)]Choice[/] [color(245)](default s):[/] "
        ).strip().lower()
        if _choice == "q":
            sys.exit(0)
        elif _choice == "a":
            console.print()
        else:
            from cli.setup import run_wizard
            run_wizard(console)
            _config = load_config()
            console.print()

    vendor_str = " ".join(vendor)

    # ── Cadence check ─────────────────────────────────────────────────
    from core.config import get_reassessment_config
    slug = _vendor_slug(vendor_str)
    history = _load_history()
    if slug in history and not force:
        entry = history[slug]
        last_tier = entry.get("risk_tier", "LOW")
        last_date_str = entry.get("last_assessed", "")
        _rc = get_reassessment_config(_config)
        tier_cfg = _rc.get(last_tier.lower(), {"depth": "full", "days": 365, "triggers": []})
        cadence_days = tier_cfg["days"]
        depth = tier_cfg["depth"]
        if depth == "none":
            console.print(
                f"\n  [color(220)]Cadence:[/] [color(245)]Re-assessment depth for {last_tier} vendors is set to [color(220)]none[/][color(245)] — skipping.[/]"
            )
            console.print("  [color(245)]Use [color(220)]--force[/][color(245)] to run anyway.[/]\n")
            sys.exit(0)
        if last_date_str and cadence_days > 0:
            try:
                last_date = datetime.date.fromisoformat(last_date_str)
                days_since = (datetime.date.today() - last_date).days
                days_remaining = cadence_days - days_since
                if days_remaining > 0:
                    due_date = (last_date + datetime.timedelta(days=cadence_days)).strftime("%B %d, %Y")
                    console.print(
                        f"\n  [color(220)]Cadence:[/] [color(245)]{vendor_str} was last assessed {days_since}d ago "
                        f"(tier: {last_tier}, cadence: {cadence_days}d).[/]"
                    )
                    console.print(f"  [color(245)]Next assessment due: [color(220)]{due_date}[/] "
                                  f"[color(245)]({days_remaining}d from now)[/]")
                    console.print("  [color(245)]Use [color(220)]--force[/][color(245)] to run early.\n[/]")
                    sys.exit(0)
            except ValueError:
                pass

    provider = AnthropicProvider(model=model, api_key=api_key)

    # ── v1.4: Unified data resolver ───────────────────────────────────
    from core.data.resolver import VendorDataResolver as _Resolver
    _resolver = _Resolver(
        vendor_name=vendor_str,
        local_docs_path=pathlib.Path(docs) if docs else None,
        on_progress=lambda p: console.print(
            f"  [dim]{p['message']}[/dim]"
        ) if verbose else None,
    )

    # ── Sync vendor profiles FROM Drive at start of assess ───────────
    _assess_drive_cfg = None
    _assess_drive_folder_id = None
    _assess_drive_client = None
    if drive:
        try:
            from core.config import load_config as _lc2
            _assess_drive_cfg = (_lc2() or {}).get("integrations", {}).get("google_drive", {})
            _assess_drive_folder_id = _assess_drive_cfg.get("root_folder_id") if _assess_drive_cfg else None
            if _assess_drive_folder_id:
                from core.integrations.google_drive import GoogleDriveClient as _GDC
                _assess_drive_client = _GDC()
                _assess_drive_client.authenticate()
                from core.profiles.vendor_cache import VendorProfileCache as _VPC2
                _VPC2().sync_from_drive(_assess_drive_client, _assess_drive_folder_id)
        except Exception:
            pass  # Use local cache if Drive unavailable

    # ── 7G: Prompt for intake on first assess ─────────────────────────
    from core.profiles.vendor_cache import VendorProfileCache as _VPC3
    _vendor_profile = _VPC3().get(vendor_str)
    if not _vendor_profile or not _vendor_profile.intake_completed:
        console.print()
        console.print(
            "  [color(245)]New vendor — no intake data on file.[/]\n\n"
            "  [color(245)]a)[/]  Run quick intake (12 questions, ~3 min)\n"
            "       Better accuracy and risk context\n\n"
            "  [color(245)]s)[/]  Skip — assess with available data only\n"
        )
        _intake_choice = console.input(
            "  [color(220)]Choice[/] [color(245)](default s):[/] "
        ).strip().lower()
        if _intake_choice == "a":
            from core.profiles.intake import IntakeWizard as _IW
            _iw = _IW(vendor_str)
            _iw_answers = _iw.run()
            if _iw_answers:
                from core.profiles.auto_detect import VendorAutoDetector as _VAD
                _det = _VAD()
                _det_result = _det.detect(vendor_str)
                _vp3 = _VPC3()
                _vp_obj = _vp3.get(vendor_str) or _vp3._build_new_profile(vendor_str, _det_result)
                _vp_obj.intake_completed = True
                import datetime as _idt
                _vp_obj.intake_date = _idt.date.today().isoformat()
                for _k, _v in _iw_answers.items():
                    if hasattr(_vp_obj, _k):
                        setattr(_vp_obj, _k, _v)
                _vp3.save(vendor_str, _vp_obj)
                _vendor_profile = _vp_obj
            console.print()

    # ── 7E: Build integration context from intake data ────────────────
    _integration_context = None
    if _vendor_profile and _vendor_profile.intake_completed:
        from core.profiles.intake import build_integration_context_paragraph
        _integration_context = build_integration_context_paragraph(_vendor_profile)

    # ── 7F: Show intake context in verbose mode ───────────────────────
    if verbose and _vendor_profile and _vendor_profile.intake_completed:
        _data_labels = ", ".join(
            t.replace("_", " ") for t in (_vendor_profile.data_types or [])
        ) or "—"
        _int_names = " · ".join(
            i["system_name"] for i in (_vendor_profile.integrations or [])
        ) or "none"
        console.print(
            f"  [color(245)]Intake context loaded:[/]\n"
            f"    Data: [color(220)]{_data_labels}[/] · "
            f"{_vendor_profile.data_volume or '—'} · "
            f"{_vendor_profile.environment_access or '—'}\n"
            f"    Integrations: [color(220)]{_int_names}[/]\n"
            f"    Criticality:  {_vendor_profile.criticality or '—'}\n"
            f"    AI: {_vendor_profile.ai_in_service or '—'} · "
            f"Training: {_vendor_profile.ai_trains_on_data or '—'}"
        )
        console.print()

    # Resolve docs folder — Drive download if --drive
    docs_folder = docs
    _drive_tmp = None
    if drive and not docs_folder:
        try:
            from core.integrations.drive_ingestor import DriveDocumentIngestor
            from core.config import load_config
            _cfg = load_config() or {}
            _drive_cfg = _cfg.get("integrations", {}).get("google_drive", {})
            _folder_id = _drive_cfg.get("root_folder_id")
            if not _folder_id:
                console.print(
                    "\n  [color(196)]✗[/]  [bold color(245)]Google Drive not configured.[/]\n\n"
                    "     Run [color(220)]bandit setup --drive[/][color(245)] to connect your Drive.\n"
                    "     Takes about 10 minutes — requires a free\n"
                    "     Google Cloud project.\n\n"
                    "     Full setup guide:\n"
                    "     [color(220)]docs/google-drive-setup.md[/]\n"
                )
                sys.exit(1)
            import tempfile
            _drive_tmp = tempfile.mkdtemp(prefix="bandit_drive_")
            from core.integrations.google_drive import GoogleDriveClient
            _drive_client = GoogleDriveClient()
            _drive_client.authenticate()
            _local_paths = _drive_client.download_vendor_documents(
                vendor_name=vendor_str,
                parent_folder_id=_folder_id,
                temp_dir=_drive_tmp,
            )
            if _local_paths:
                docs_folder = _drive_tmp
            else:
                console.print(
                    f"  [color(245)]No Drive documents found for {vendor_str}.[/]"
                )
        except Exception as exc:
            console.print(f"  [color(245)]Drive integration error: {exc}[/]")

    try:
        with assessment_progress(verbose=verbose) as update:
            bandit = PrivacyBandit(provider=provider, on_progress=update)
            assessment = bandit.assess(
                vendor_str,
                docs_folder=docs_folder,
                integration_context=_integration_context,
            )
        legal_result = getattr(assessment.result, "legal_bandit_result", None)
        if legal_result:
            _CONTRACT_DIMS = {"D2", "D5", "D7", "D8"}
            changed = [
                ds for ds in legal_result.dimension_scores
                if ds.score_changed
            ]
            console.print()
            console.print(
                "  [bold color(172)]Contract findings[/]"
                f"  [color(245)](DPA: {legal_result.dpa_source or '—'})[/]"
            )
            for ds in changed:
                arrow = (
                    "[color(82)]↑[/]" if ds.score_direction == "up"
                    else "[color(196)]↓[/]"
                )
                console.print(
                    f"    [color(172)]{ds.dimension}[/]  "
                    f"[color(245)]{ds.policy_score}→{ds.final_score}[/]  "
                    f"{arrow}  [color(243)]{ds.evidence_summary}[/]"
                )
            for c in legal_result.conflicts:
                console.print(
                    f"    [color(220)]⚠[/]   [color(245)]{c.dimension} conflict "
                    f"— policy vs DPA[/]"
                )
            console.print(
                f"  [color(245)]Updated score:[/] "
                f"[bold]{assessment.result.risk_tier}[/] "
                f"[bold]{assessment.result.weighted_average}[/]/5.0"
            )
        elif docs_folder or drive:
            console.print(
                "\n  [color(245)]Legal Bandit — no DPA or MSA found, skipped.[/]\n"
                "  [color(245)]Provide documents via --docs or --drive to enable "
                "contract gap analysis.[/]"
            )
    except KeyboardInterrupt:
        console.print("\n  [bold color(196)]✗[/]  [color(245)]Assessment cancelled.[/]")
        sys.exit(0)
    except Exception as exc:
        console.print(f"[bold red]Error:[/] {exc}")
        sys.exit(1)
    finally:
        if _drive_tmp:
            import shutil
            shutil.rmtree(_drive_tmp, ignore_errors=True)

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
        reports_dir = pathlib.Path("reports")
        reports_dir.mkdir(exist_ok=True)
        report_path = reports_dir / f"{slug}-{datetime.date.today().isoformat()}.html"
        from cli.report import write_html_report
        write_html_report(report_path, assessment)
        console.print(
            f"\n  [color(243)]Report saved →[/] [color(172)]{report_path}[/]"
        )

        # ── Legal brief (6A) ──────────────────────────────────────────
        legal_report_path = None
        _legal_result = getattr(assessment.result, "legal_bandit_result", None)
        if _legal_result and not no_legal_brief:
            from core.reports.legal_report import generate_legal_brief
            legal_report_path = str(report_path).replace(".html", "-legal.html")
            generate_legal_brief(
                result=_legal_result,
                output_path=legal_report_path,
            )
            console.print(
                f"  [color(243)]Legal brief  →[/] [color(172)]{legal_report_path}[/]"
            )

        # ── Save report to Drive if --drive and auto_save_reports ─────
        if drive:
            try:
                from core.config import load_config as _lc
                _drive_cfg = (_lc() or {}).get("integrations", {}).get("google_drive", {})
                if _drive_cfg.get("auto_save_reports", True) and _drive_cfg.get("root_folder_id"):
                    from core.integrations.google_drive import GoogleDriveClient
                    _dc = GoogleDriveClient()
                    _dc.authenticate()
                    _file_id = _dc.save_report_to_drive(
                        local_file_path=str(report_path),
                        vendor_name=vendor_str,
                        parent_folder_id=_drive_cfg["root_folder_id"],
                    )
                    if _file_id:
                        console.print(
                            f"  [color(82)]✓[/]  [color(245)]Report saved to Drive →[/] "
                            f"[color(172)]{vendor_str}/{report_path.name}[/]"
                        )
                    else:
                        console.print(
                            "  [color(220)]⚠[/]  [color(245)]Could not save to Drive — "
                            f"no folder named '{vendor_str}' found in Drive root.[/]"
                        )
                    # 6B — save legal brief to Drive
                    if legal_report_path:
                        try:
                            _dc.save_report_to_drive(
                                local_file_path=legal_report_path,
                                vendor_name=vendor_str,
                                parent_folder_id=_drive_cfg["root_folder_id"],
                            )
                            console.print(
                                f"  [color(82)]✓[/]  [color(245)]Legal brief saved to Drive →[/] "
                                f"[color(172)]{vendor_str}/"
                                f"{pathlib.Path(legal_report_path).name}[/]"
                            )
                        except Exception:
                            pass
            except Exception as _e:
                console.print(
                    f"  [color(220)]⚠[/]  [color(245)]Drive save failed: {_e}[/]"
                )

    # ── Save to vendor history ────────────────────────────────────────
    _save_history(slug, assessment.result.risk_tier, assessment.result.weighted_average)

    # ── Write assessment history to vendor profile ────────────────────
    try:
        from core.profiles.vendor_cache import VendorProfileCache as _VPC
        _hist_report_path = str(report_path) if not no_report else ""
        _hist_legal_path = str(legal_report_path) if (not no_report and legal_report_path) else None
        assessment.result.report_path = _hist_report_path
        assessment.result.legal_brief_path = _hist_legal_path
        _VPC().update_assessment_history(vendor_str, assessment.result)
    except Exception:
        pass  # Never let history writing crash the assess

    # ── v1.4: Sync vendor profiles TO Drive at end of assess ─────────
    try:
        _resolver.sync_profile_to_drive()
    except Exception:
        pass  # Never block assess for Drive sync

    # Tip when no profile configured
    if not _config:
        console.print(
            "\n  [color(245)]Tip: run [color(220)]bandit setup[/][color(245)] to tailor scores"
            " to your industry and regulatory profile.[/]"
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
# setup
# ─────────────────────────────────────────────────────────────────────

@main.command()
@click.option("--reset",    is_flag=True, help="Overwrite existing config and start fresh")
@click.option("--show",     is_flag=True, help="Print current config summary and exit")
@click.option("--advanced", is_flag=True, help="Advanced configuration (coming soon)")
@click.option("--drive",    is_flag=True, help="Configure Google Drive integration")
@click.option("--stack",    is_flag=True, help="Configure your tech stack")
@click.option("--notify",   is_flag=True, help="Configure IT notification settings")
def setup(reset: bool, show: bool, advanced: bool, drive: bool, stack: bool, notify: bool) -> None:
    """Configure your industry and regulatory profile.

    Runs a short wizard (5 core + up to 3 conditional questions) that
    infers frameworks and dimension weights for your context.
    Saves to ./bandit.config.yml.

    \b
    Examples:
      bandit setup
      bandit setup --reset
      bandit setup --show
      bandit setup --drive
      bandit setup --stack
      bandit setup --notify
      bandit setup --advanced
    """
    from rich.console import Console
    from cli.setup import run_wizard, show_config

    con = Console()

    if drive:
        _run_drive_setup(con)
        return

    if stack:
        _run_stack_setup(con)
        return

    if notify:
        _run_notify_setup(con)
        return

    if show:
        show_config(con)
        return

    if reset:
        import pathlib
        from core.config import CONFIG_PATHS
        for p in CONFIG_PATHS:
            if p.is_file():
                p.unlink()
                con.print(f"  [color(245)]Removed existing config: {p}[/]")
                break

    try:
        run_wizard(con, reset=reset, advanced=advanced)
    except KeyboardInterrupt:
        con.print("\n  [bold color(196)]✗[/]  [color(245)]Setup cancelled.[/]\n")
        sys.exit(0)
    except Exception as exc:
        con.print(f"\n  [bold color(196)]✗[/]  [color(245)]Setup error: {exc}[/]")
        con.print("  [dim color(245)]Run [color(220)]bandit setup[/][dim color(245)] to try again.[/]\n")
        sys.exit(1)


def _run_stack_setup(con) -> None:
    """Interactive tech stack wizard."""
    import re as _re
    import pathlib
    import yaml
    from core.config import load_config, CATEGORY_DATA_MAP
    from rich.prompt import Prompt

    con.print("\n  [bold color(172)]TECH STACK SETUP[/]\n")
    con.print(
        "  [color(245)]Tell Bandit which tools your organisation uses.[/]\n"
        "  [color(245)]This improves vendor intake — Q6 will show real system names.[/]\n"
        "  [color(245)]Press Enter to skip any category.[/]\n"
    )

    # Load org profile for industry-specific sections
    cfg = load_config() or {}
    company = cfg.get("company", {})
    org_type = company.get("org_type", "").lower()

    # Section definitions
    SECTIONS = [
        ("customer_revenue", "Customer & Revenue", [
            ("crm",              "CRM / Customer database",         "customer_data"),
            ("billing",          "Billing / Invoicing",             "financial_processing"),
            ("customer_support", "Customer support / Helpdesk",     "customer_data"),
        ]),
        ("people_operations", "People & Operations", [
            ("hr_payroll",       "HR / Payroll / People",           "hr_people"),
            ("identity_sso",     "Identity / SSO / Directory",      "identity_access"),
            ("finance_erp",      "Finance / ERP / Accounting",      "financial_processing"),
            ("procurement",      "Procurement / Spend",             "financial_processing"),
        ]),
        ("infrastructure_data", "Infrastructure & Data", [
            ("cloud_infra",      "Cloud infrastructure",            "infrastructure"),
            ("data_warehouse",   "Data warehouse / Analytics",      "analytics_bi"),
            ("communication",    "Communication / Collaboration",   "communication"),
            ("source_code",      "Source code / Engineering",       "infrastructure"),
        ]),
    ]

    # Industry-specific sections
    if "healthcare" in org_type or "health" in org_type:
        SECTIONS.append(("healthcare", "Healthcare", [
            ("ehr",              "Clinical / EHR",                  "healthcare_clinical"),
        ]))
    if "financial" in org_type or "finance" in org_type or "bank" in org_type:
        SECTIONS.append(("financial_services", "Financial Services", [
            ("core_banking",     "Core banking",                    "financial_processing"),
        ]))
    if "manufactur" in org_type:
        SECTIONS.append(("manufacturing", "Manufacturing", [
            ("erp_supply",       "ERP / Supply chain",              "supply_chain"),
        ]))
    if "education" in org_type or "school" in org_type or "university" in org_type:
        SECTIONS.append(("education", "Education", [
            ("student_lms",      "Student / LMS",                   "general_saas"),
        ]))
    if "legal" in org_type or "law" in org_type:
        SECTIONS.append(("legal", "Legal", [
            ("case_management",  "Case management",                 "legal_compliance"),
        ]))
    if "government" in org_type or "public sector" in org_type:
        SECTIONS.append(("government", "Government", [
            ("grc_compliance",   "GRC / Compliance",                "legal_compliance"),
        ]))

    tech_stack: dict = {}
    total_tools = 0

    for section_key, section_label, categories in SECTIONS:
        con.print(f"  [bold color(250)]{section_label}[/]")
        section_data: dict = {}

        for cat_key, cat_label, category in categories:
            raw = Prompt.ask(
                f"  [dim]{cat_label}[/]",
                default=""
            ).strip()
            if not raw:
                continue

            cat_info = CATEGORY_DATA_MAP.get(category, {})
            tools = []
            for tool_name in [t.strip() for t in raw.split(",") if t.strip()]:
                slug = _re.sub(r"[^a-z0-9-]", "-", tool_name.lower()).strip("-")
                tools.append({
                    "name": tool_name,
                    "slug": slug,
                    "category": category,
                    "category_label": cat_label,
                    "section_label": section_label,
                    "data_sensitivity": cat_info.get("sensitivity", "medium"),
                    "data_description": cat_info.get("data_description", "business data"),
                })
                total_tools += 1
            if tools:
                section_data[cat_key] = tools

        if section_data:
            tech_stack[section_key] = section_data
        con.print()

    if not tech_stack:
        con.print("  [color(245)]No tools entered — nothing saved.[/]\n")
        return

    # Save to config
    cfg = load_config() or {}
    cfg["tech_stack"] = tech_stack

    config_path = pathlib.Path("bandit.config.yml")
    try:
        config_path.write_text(
            yaml.dump(cfg, default_flow_style=False, allow_unicode=True)
        )
        category_count = sum(len(v) for v in tech_stack.values())
        con.print(
            f"  [green]✓[/green] Tech stack saved — "
            f"{total_tools} system(s) across {category_count} category/categories\n"
            f'  [dim]Run bandit vendor add "VendorName" to use in intake.[/dim]\n'
        )
    except Exception as e:
        con.print(f"  [color(196)]✗[/]  Could not save config: {e}\n")


def _run_notify_setup(con) -> None:
    """Configure IT notification settings."""
    import pathlib
    import yaml
    from core.config import load_config
    from rich.prompt import Prompt

    con.print("\n  [bold color(172)]IT NOTIFICATION SETUP[/]\n")
    con.print(
        "  [color(245)]When you run bandit vendor add, Bandit queues[/]\n"
        "  [color(245)]IT notifications for integration setup.[/]\n"
        "  [color(245)]Configure where to send them.[/]\n"
    )

    email = Prompt.ask(
        "  IT team email address (or Enter to skip)",
        default=""
    ).strip()

    slack_channel = Prompt.ask(
        "  Slack channel name e.g. #it-helpdesk (or Enter to skip)",
        default=""
    ).strip()

    con.print()
    con.print(
        "  [color(245)]Slack webhook URL — find it at:[/]\n"
        "  [color(220)]api.slack.com/apps[/] [color(245)]→ Incoming Webhooks → Add webhook[/]\n"
        "  [color(245)]Leave blank to use email only.[/]\n"
    )
    slack_webhook = Prompt.ask(
        "  Slack webhook URL (or Enter to skip)",
        default=""
    ).strip()

    if not email and not slack_channel and not slack_webhook:
        con.print("  [color(245)]No notification settings saved.[/]\n")
        return

    cfg = load_config() or {}
    notifications = {}
    if email:
        notifications["it_contact_email"] = email
    if slack_channel:
        notifications["it_slack_channel"] = slack_channel
    if slack_webhook:
        notifications["slack_webhook_url"] = slack_webhook
    cfg["notifications"] = notifications

    config_path = pathlib.Path("bandit.config.yml")
    try:
        config_path.write_text(
            yaml.dump(cfg, default_flow_style=False, allow_unicode=True)
        )
        saved = []
        if email:
            saved.append(f"email → {email}")
        if slack_channel:
            saved.append(f"channel → {slack_channel}")
        if slack_webhook:
            saved.append("Slack webhook → configured")
        con.print(
            f"  [green]✓[/green] Notification settings saved: "
            f"{', '.join(saved)}\n"
        )
    except Exception as e:
        con.print(f"  [color(196)]✗[/]  Could not save config: {e}\n")


def _run_drive_setup(con) -> None:
    """Interactive Google Drive setup wizard with progress saving."""
    import json
    import pathlib
    import shutil

    _PROGRESS_PATH = pathlib.Path.home() / ".bandit" / ".drive_setup_progress.json"

    def _load_progress() -> dict:
        try:
            return json.loads(_PROGRESS_PATH.read_text())
        except (OSError, json.JSONDecodeError):
            return {}

    def _save_progress(data: dict) -> None:
        try:
            _PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
            _tmp = _PROGRESS_PATH.with_suffix(".tmp")
            _tmp.write_text(json.dumps(data))
            _tmp.replace(_PROGRESS_PATH)
        except OSError:
            pass

    def _clear_progress() -> None:
        try:
            _PROGRESS_PATH.unlink(missing_ok=True)
        except OSError:
            pass

    progress = _load_progress()

    con.print("\n  [bold color(172)]GOOGLE DRIVE SETUP[/]\n")

    # ── Already fully configured? ─────────────────────────────────────
    if progress.get("credentials_saved") and progress.get("authenticated") and progress.get("folder_id"):
        answer = con.input(
            "  [color(245)]Drive already configured. Reconfigure?[/] [color(220)][y/N][/] "
        ).strip().lower()
        if answer != "y":
            con.print()
            return
        _clear_progress()
        progress = {}

    # ── Resume banner ─────────────────────────────────────────────────
    if progress.get("authenticated"):
        con.print("  [color(245)]Resuming from[/] [bold]Step 3[/] [color(245)]— Folder ID[/]\n")
    elif progress.get("credentials_saved"):
        con.print("  [color(245)]Resuming from[/] [bold]Step 2[/] [color(245)]— Authenticate[/]\n")

    creds_dest = pathlib.Path.home() / ".bandit" / "google-credentials.json"

    # ── Step 1 — Credentials ──────────────────────────────────────────
    if not progress.get("credentials_saved"):
        con.print("  [bold]Step 1[/] — Download credentials")
        con.print("  [color(245)]Google Drive integration requires a credentials file.[/]\n")
        con.print("  [color(245)]1. Go to console.cloud.google.com[/]")
        con.print("  [color(245)]2. Create a project (or select existing)[/]")
        con.print("  [color(245)]3. Enable Google Drive API[/]")
        con.print("  [color(245)]4. Create OAuth 2.0 credentials (Desktop app)[/]")
        con.print("  [color(245)]5. Download credentials.json[/]\n")

        creds_input = con.input(
            "  [color(220)]Path to your credentials.json file:[/] "
        ).strip()
        if not creds_input:
            con.print("  [color(196)]✗[/]  No path provided.\n")
            return

        creds_src = pathlib.Path(creds_input).expanduser()
        if not creds_src.exists():
            con.print(f"  [color(196)]✗[/]  File not found: {creds_src}\n")
            return

        creds_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(creds_src, creds_dest)
        con.print(f"  [color(82)]✓[/]  Credentials saved to {creds_dest}\n")

        progress["credentials_saved"] = True
        _save_progress(progress)

    # ── Step 2 — Authenticate ─────────────────────────────────────────
    client = None
    if not progress.get("authenticated"):
        con.print("  [bold]Step 2[/] — Authenticate")
        con.print("  [color(245)]Opening browser for Google authorization…[/]\n")
        try:
            from core.integrations.google_drive import GoogleDriveClient
            client = GoogleDriveClient()
            client.authenticate()
            con.print("  [color(82)]✓[/]  Authenticated successfully\n")
            progress["authenticated"] = True
            _save_progress(progress)
        except ImportError:
            con.print(
                "\n  [color(220)]⚠[/]  [bold color(245)]Google Drive packages not installed.[/]\n\n"
                "  Run this command to install them:\n"
                "  [color(220)]pip install -e \".[drive]\"[/]\n\n"
                "  After installing, run [color(220)]bandit setup --drive[/] again.\n"
                "  Your credentials file has already been saved —\n"
                "  setup will resume from Step 2.\n"
            )
            con.input("  Press Enter to exit…")
            con.print()
            return
        except Exception as exc:
            con.print(f"  [color(196)]✗[/]  Authentication failed: {exc}\n")
            return
    else:
        # Already authenticated — reconnect client for Step 4 verify
        try:
            from core.integrations.google_drive import GoogleDriveClient
            client = GoogleDriveClient()
            client.authenticate()
        except Exception:
            client = None

    # ── Step 3 — Configure folder ─────────────────────────────────────
    folder_id = progress.get("folder_id", "")
    if not folder_id:
        con.print("  [bold]Step 3[/] — Configure folder")
        con.print("  [color(245)]Paste your Drive folder ID or URL:[/]")
        con.print("  [color(245)](Any folder name works — Vendor Reviews, TPRM,[/]")
        con.print("  [color(245)] GRC Documents, etc. Bandit does not care what[/]")
        con.print("  [color(245)] the folder is named.)[/]\n")
        con.print("  [color(245)]You can paste either:[/]")
        con.print("  [color(245)]  - Just the ID: 1YOYAT1DxmLjFRfoN3irpm3xGbafVZv7_[/]")
        con.print("  [color(245)]  - The full URL from your browser[/]\n")
        raw_input = con.input("  [color(220)]Folder ID or URL:[/] ").strip()
        if not raw_input:
            con.print("  [color(196)]✗[/]  No folder ID provided.\n")
            return
        if "/folders/" in raw_input:
            folder_id = raw_input.split("/folders/")[-1].split("?")[0].strip()
        else:
            folder_id = raw_input
        con.print(f"  [color(82)]✓[/]  Folder ID: {folder_id}\n")
        progress["folder_id"] = folder_id
        _save_progress(progress)

    # ── Step 4 — Verify ───────────────────────────────────────────────
    con.print("\n  [bold]Step 4[/] — Verify")
    con.print("  [color(245)]Scanning folder…[/]")
    folder_ok = True
    if client:
        try:
            folders = client.list_vendor_folders(folder_id)
            con.print(f"  [color(82)]✓[/]  Found {len(folders)} vendor subfolder(s)\n")
        except Exception as exc:
            folder_ok = False
            con.print(
                f"\n  [color(196)]✗[/]  [bold color(245)]Could not access folder.[/]\n\n"
                "     Check the folder ID and try again.\n"
                "     Make sure the folder is accessible to the\n"
                "     Google account you authenticated with.\n"
            )
            # Clear the bad folder_id from progress so Step 3 re-runs next time
            progress.pop("folder_id", None)
            _save_progress(progress)
            return
    else:
        con.print("  [color(245)]Skipped — Drive client unavailable.\n")

    if not folder_ok:
        return

    # ── Save to config ────────────────────────────────────────────────
    from core.config import load_config
    import yaml
    config_path = pathlib.Path("bandit.config.yml")
    cfg = load_config() or {}
    cfg.setdefault("integrations", {})["google_drive"] = {
        "enabled": True,
        "root_folder_id": folder_id,
        "credentials_path": str(creds_dest),
        "auto_save_reports": True,
    }
    try:
        config_path.write_text(yaml.dump(cfg, default_flow_style=False, allow_unicode=True))
        con.print(f"  [color(82)]✓[/]  Drive integration configured\n")
    except Exception:
        con.print("  [color(245)]Could not save config. Add manually to bandit.config.yml[/]\n")

    _clear_progress()

    con.print("  [bold]Usage:[/]")
    con.print('  [color(220)]bandit assess "Salesforce" --drive[/]')
    con.print("  [color(220)]bandit batch vendors.txt --drive[/]\n")


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
@click.option(
    "--docs-root",
    type=click.Path(exists=True, file_okay=False),
    default=None,
    metavar="DIR",
    help="Root folder containing vendor subfolders (./docs-root/<vendor-name>/)",
)
@click.option("--drive", is_flag=True, default=False, help="Fetch vendor documents from Google Drive for each vendor")
def batch(
    file: str,
    model: str,
    api_key: str | None,
    out_dir: str,
    docs_root: str | None,
    drive: bool,
) -> None:
    """Assess a list of vendors from a text file.

    FILE should contain one vendor per line (name, domain, or URL).
    Optionally add columns: vendor, URL, functions, docs_path.
    Lines starting with # and blank lines are ignored.

    \b
    Examples:
      bandit batch vendors.txt
      bandit batch vendors.txt --docs-root ./vendor-docs/
      bandit batch vendors.txt --drive
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

    # Parse vendors file — supports up to 4 columns:
    # vendor_name, optional_url, optional_functions, optional_docs_path
    vendor_entries = []  # list of (vendor_name, docs_path)
    with open(file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [col.strip() for col in line.split(",")]
            vendor_name = parts[0]
            docs_path = parts[3] if len(parts) >= 4 and parts[3] else None
            vendor_entries.append((vendor_name, docs_path))

    if not vendor_entries:
        con.print("[yellow]No vendors found in file.[/]")
        sys.exit(0)

    con.print(f"\n[bold color(172)]BANDIT BATCH[/]  [color(243)]{len(vendor_entries)} vendor(s) from {file}[/]\n")

    out_path = pathlib.Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    provider = AnthropicProvider(model=model, api_key=api_key)
    date = datetime.date.today().isoformat()
    results = []   # (vendor, tier, score, report_path, error)

    # Pre-authenticate Drive if needed
    _drive_client = None
    _drive_folder_id = None
    if drive:
        try:
            from core.integrations.google_drive import GoogleDriveClient
            from core.config import load_config
            _cfg = load_config() or {}
            _drive_folder_id = _cfg.get("integrations", {}).get("google_drive", {}).get("root_folder_id")
            if not _drive_folder_id:
                con.print(
                    "\n  [color(196)]✗[/]  [bold color(245)]Google Drive not configured.[/]\n\n"
                    "     Run [color(220)]bandit setup --drive[/][color(245)] to connect your Drive.\n"
                    "     Takes about 10 minutes — requires a free\n"
                    "     Google Cloud project.\n\n"
                    "     Full setup guide:\n"
                    "     [color(220)]docs/google-drive-setup.md[/]\n"
                )
                sys.exit(1)
            _drive_client = GoogleDriveClient()
            _drive_client.authenticate()
        except Exception as exc:
            con.print(f"  [color(245)]Drive authentication error: {exc}[/]")
            _drive_client = None

    try:
        for i, (vendor, inline_docs) in enumerate(vendor_entries, 1):
            con.print(f"[color(245)][{i}/{len(vendor_entries)}][/]  [color(220)]{vendor}[/]")

            # Resolve docs folder for this vendor
            docs_folder = inline_docs
            _tmp_dir = None

            if not docs_folder and docs_root:
                import re as _re
                slug = _re.sub(r"[^a-z0-9-]", "-", vendor.lower().strip()).strip("-")
                _root = pathlib.Path(docs_root)
                for candidate in [_root / vendor, _root / slug, _root / vendor.lower()]:
                    if candidate.is_dir():
                        docs_folder = str(candidate)
                        break

            if not docs_folder and drive and _drive_client and _drive_folder_id:
                try:
                    import tempfile
                    _tmp_dir = tempfile.mkdtemp(prefix="bandit_drive_")
                    _paths = _drive_client.download_vendor_documents(
                        vendor_name=vendor,
                        parent_folder_id=_drive_folder_id,
                        temp_dir=_tmp_dir,
                    )
                    if _paths:
                        docs_folder = _tmp_dir
                except Exception:
                    pass

            try:
                with assessment_progress() as update:
                    bandit = PrivacyBandit(provider=provider, on_progress=update)
                    assessment = bandit.assess(vendor, docs_folder=docs_folder)

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
            finally:
                if _tmp_dir:
                    import shutil
                    shutil.rmtree(_tmp_dir, ignore_errors=True)
    except KeyboardInterrupt:
        completed = len(results)
        all_vendor_names = [v for v, _ in vendor_entries]
        remaining = all_vendor_names[completed:]
        con.print(
            f"\n  [bold color(196)]✗[/]  "
            f"[color(245)]Batch cancelled after {completed}/{len(vendor_entries)} vendors.[/]"
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
        title=f"[bold color(172)]BATCH SUMMARY — {len(vendor_entries)} vendor(s)[/]",
        border_style="color(238)",
    ))
    con.print()


# ─────────────────────────────────────────────────────────────────────
# profile
# ─────────────────────────────────────────────────────────────────────

@main.command()
@click.argument("vendor", required=False, default=None)
@click.option("--show",    is_flag=True, help="List all cached vendor profiles")
@click.option("--unknown", is_flag=True, help="Show vendors with unknown function classification")
def profile(vendor: str | None, show: bool, unknown: bool) -> None:
    """Manage and inspect vendor function profiles.

    Auto-detects what category a vendor belongs to (HR, payments, AI/ML, etc.)
    and shows the weight modifiers and document requirements that apply.

    \b
    Examples:
      bandit profile "Salesforce"
      bandit profile salesforce.com
      bandit profile --show
      bandit profile --unknown
    """
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from core.profiles.auto_detect import detector
    from core.profiles.vendor_cache import profile_cache
    from core.profiles.vendor_functions import FUNCTION_LABELS, FUNCTION_MODIFIERS

    con = Console()

    if show or (not vendor and not unknown):
        profiles = profile_cache.list_all()
        if not profiles:
            con.print("\n  [color(245)]No cached vendor profiles yet.[/]")
            con.print("  [color(245)]Run [color(220)]bandit assess <vendor>[/][color(245)] to build up the cache.[/]\n")
            return
        t = Table(box=None, show_header=True, padding=(0, 2))
        t.add_column("Vendor",     style="color(250)", min_width=20)
        t.add_column("Functions",  style="color(245)")
        t.add_column("Method",     style="color(243)", no_wrap=True)
        t.add_column("Updated",    style="color(243)", no_wrap=True)
        for p in profiles:
            if unknown and p.detection_method != "unknown":
                continue
            t.add_row(
                p.vendor_name,
                ", ".join(p.function_labels()),
                p.detection_method,
                p.last_updated,
            )
        con.print(Panel(
            t,
            title=f"[bold color(172)]VENDOR PROFILES[/]  [color(243)]({len(profiles)} cached)[/]",
            border_style="color(238)",
        ))
        return

    if unknown:
        profiles = profile_cache.list_all()
        unknown_profiles = [p for p in profiles if p.detection_method == "unknown"]
        if not unknown_profiles:
            con.print("\n  [color(82)]✓[/]  [color(245)]No vendors with unknown classification.[/]\n")
        else:
            con.print(f"\n  [color(220)]{len(unknown_profiles)} vendor(s) with unknown function:[/]")
            for p in unknown_profiles:
                con.print(f"  [color(245)]  •  {p.vendor_name}[/]")
        return

    if vendor:
        # Check cache first
        cached = profile_cache.get(vendor)
        if cached:
            result_functions = [f for f in cached.functions]
            method = cached.detection_method
            confidence = 1.0 if method == "known_vendor" else 0.9 if method == "domain_match" else 0.6 if method == "keyword" else 0.0
        else:
            detect_result = detector.detect(vendor)
            result_functions = [f.value for f in detect_result.functions]
            method = detect_result.method
            confidence = detect_result.confidence

        # Display
        fn_table = Table(box=None, show_header=True, padding=(0, 2))
        fn_table.add_column("Function",  style="bold color(172)", min_width=24)
        fn_table.add_column("Weight modifiers", style="color(250)")
        fn_table.add_column("Expected docs",    style="color(245)")

        try:
            from core.profiles.vendor_functions import VendorFunction
            fns = [VendorFunction(f) for f in result_functions]
        except (ValueError, ImportError):
            fns = []

        for fn in fns:
            mods = FUNCTION_MODIFIERS.get(fn, {})
            wm = mods.get("weight_modifiers", {})
            wm_str = "  ".join(f"{d}+{v}" for d, v in wm.items()) if wm else "—"
            docs = ", ".join(mods.get("expected_docs", [])) or "—"
            fn_table.add_row(FUNCTION_LABELS.get(fn, fn.value), wm_str, docs)

        conf_style = "color(82)" if confidence >= 0.9 else "color(220)" if confidence >= 0.6 else "color(245)"
        conf_label = f"[{conf_style}]{confidence:.0%}[/]  [color(243)]({method})[/]"

        con.print()
        con.print(Panel(
            fn_table,
            title=f"[bold color(172)]{vendor}[/]  [color(243)]Confidence: {conf_label}[/]",
            border_style="color(238)",
        ))

        # Show required docs
        try:
            from core.profiles.vendor_functions import get_required_docs, get_expected_docs
            req_docs = get_required_docs(fns)
            exp_docs = get_expected_docs(fns)
            if req_docs or exp_docs:
                doc_t = Table(box=None, show_header=False, padding=(0, 2))
                doc_t.add_column(style="color(245)", min_width=18)
                doc_t.add_column(style="color(220)")
                if req_docs:
                    doc_t.add_row("Required", ", ".join(req_docs))
                if exp_docs:
                    doc_t.add_row("Expected", ", ".join(exp_docs))
                con.print(Panel(doc_t, title="[bold color(172)]DOCUMENT REQUIREMENTS[/]", border_style="color(238)"))
        except ImportError:
            pass
        con.print()


# ─────────────────────────────────────────────────────────────────────
# legal
# ─────────────────────────────────────────────────────────────────────

@main.command()
@click.argument("vendor")
@click.option(
    "--docs",
    type=click.Path(exists=True, file_okay=False),
    default=None,
    metavar="PATH",
    help="Path to folder containing vendor documents (DPA, MSA, SCCs)",
)
@click.option("--drive", is_flag=True, default=False, help="Fetch vendor documents from Google Drive")
@click.option(
    "--api-key", default=None, metavar="KEY", envvar="ANTHROPIC_API_KEY",
    help="Anthropic API key (default: $ANTHROPIC_API_KEY)",
)
@click.option(
    "--model", default="claude-haiku-4-5-20251001", metavar="MODEL", show_default=True,
    help="Claude model ID",
)
def legal(vendor: str, docs: str | None, drive: bool, api_key: str | None, model: str) -> None:
    """Run Legal Bandit contract gap analysis.

    Reads DPA, MSA, and SCCs and generates a redline brief for legal review.

    \b
    Examples:
      bandit legal "Salesforce" --docs ./vendor-docs/Salesforce/
      bandit legal "Salesforce" --drive
    """
    import datetime
    from cli.terminal import console
    from core.llm.anthropic import AnthropicProvider

    if not api_key:
        console.print(
            "[bold red]Error:[/] ANTHROPIC_API_KEY not set.\n"
            "Set the environment variable or pass [color(220)]--api-key <key>[/]."
        )
        sys.exit(1)

    if not docs and not drive:
        console.print(
            "  [color(220)]⚠[/]  No document source specified.\n"
            "  Provide documents via:\n"
            "  [color(220)]bandit legal \"Vendor\" --docs ./vendor-docs/[/]\n"
            "  [color(220)]bandit legal \"Vendor\" --drive[/]"
        )
        sys.exit(1)

    provider = AnthropicProvider(model=model, api_key=api_key)

    # Resolve docs folder
    docs_folder = docs
    _drive_tmp = None
    if drive and not docs_folder:
        try:
            from core.config import load_config
            from core.integrations.google_drive import GoogleDriveClient
            _cfg = load_config() or {}
            _drive_cfg = _cfg.get("integrations", {}).get("google_drive", {})
            _folder_id = _drive_cfg.get("root_folder_id")
            if not _folder_id:
                console.print(
                    "\n  [color(196)]✗[/]  Google Drive not configured.\n"
                    "     Run [color(220)]bandit setup --drive[/] to connect."
                )
                sys.exit(1)
            import tempfile
            _drive_tmp = tempfile.mkdtemp(prefix="bandit_legal_drive_")
            _dc = GoogleDriveClient()
            _dc.authenticate()
            _local_paths = _dc.download_vendor_documents(
                vendor_name=vendor,
                parent_folder_id=_folder_id,
                temp_dir=_drive_tmp,
            )
            if _local_paths:
                docs_folder = _drive_tmp
            else:
                console.print(
                    f"  [color(245)]No Drive documents found for {vendor}.[/]"
                )
                sys.exit(1)
        except Exception as exc:
            console.print(f"  [color(245)]Drive error: {exc}[/]")
            sys.exit(1)

    try:
        from core.documents.ingestor import DocumentIngestor
        from core.documents.classifier import DocumentType
        from core.agents.legal_bandit import LegalBandit
        from core.reports.legal_report import generate_legal_brief

        console.print(f"\n  [bold color(172)]LEGAL BANDIT[/]  [color(245)]{vendor}[/]\n")
        console.print("  [color(245)]Ingesting documents…[/]")

        ingestor = DocumentIngestor(llm_provider=provider)
        manifest = ingestor.ingest_folder(docs_folder)
        ready_docs = [
            d for d in manifest.documents
            if d.extraction_ok and d.doc_type != DocumentType.UNKNOWN
        ]

        if not ready_docs:
            console.print("  [color(220)]⚠[/]  No documents could be extracted.")
            sys.exit(1)

        console.print(f"  [color(82)]✓[/]  {len(ready_docs)} document(s) ready")
        console.print("  [color(245)]Running Art. 28(3) checklist…[/]")

        lb = LegalBandit(provider)
        legal_result = lb.assess(
            vendor_name=vendor,
            documents=ready_docs,
            policy_signals={},
            policy_scores={},
        )

        if not legal_result:
            console.print(
                "  [color(220)]⚠[/]  No DPA or MSA found in documents.\n"
                "  [color(245)]Legal Bandit requires at least a DPA or MSA.[/]"
            )
            sys.exit(1)

        reports_dir = pathlib.Path("reports")
        reports_dir.mkdir(exist_ok=True)
        slug = _vendor_slug(vendor)
        brief_path = str(
            reports_dir / f"{slug}-{datetime.date.today().isoformat()}-legal.html"
        )
        generate_legal_brief(result=legal_result, output_path=brief_path)

        console.print(
            f"\n  [color(82)]✓[/]  Required:    {legal_result.required_changes}\n"
            f"  [color(82)]✓[/]  Recommended: {legal_result.recommended_changes}\n"
            f"  [color(82)]✓[/]  Acceptable:  {legal_result.acceptable_provisions}\n"
            f"  [color(82)]✓[/]  Conflicts:   {legal_result.conflicts_count}\n"
            f"\n  [color(243)]Legal brief →[/] [color(172)]{brief_path}[/]"
        )

    finally:
        if _drive_tmp:
            import shutil
            shutil.rmtree(_drive_tmp, ignore_errors=True)


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




# Register vendor command group
from cli.vendor import vendor as _vendor_group  # noqa: E402
main.add_command(_vendor_group, "vendor")

# ── v1.4: Dashboard command group ────────────────────────
from cli.dashboard import dashboard  # noqa: E402
from cli.dashboard import schedule_show, notify_send, register_export  # noqa: E402
main.add_command(dashboard)


# ── v1.4: Top-level aliases ──────────────────────────────

@main.command("schedule")
@click.option("--due", is_flag=True, default=False,
    help="Show only due/overdue vendors")
@click.option("--within", default=None, type=int,
    help="Show vendors due within N days")
@click.option("--json", "as_json", is_flag=True, default=False,
    help="Output raw JSON")
@click.pass_context
def schedule_alias(ctx, due, within, as_json):
    """Reassessment schedule (alias for dashboard schedule)."""
    ctx.invoke(
        schedule_show,
        due=due,
        within=within,
        as_json=as_json,
    )


@main.command("notify")
@click.argument("vendor_name", required=False)
@click.option("--all", "send_all", is_flag=True, default=False,
    help="Send all pending notifications")
@click.option("--json", "as_json", is_flag=True, default=False,
    help="Output raw JSON")
@click.pass_context
def notify_alias(ctx, vendor_name, send_all, as_json):
    """Send IT notifications (alias for dashboard notify)."""
    ctx.invoke(
        notify_send,
        vendor_name=vendor_name,
        send_all=send_all,
        as_json=as_json,
    )


@main.command("register")
@click.option("--format", "fmt",
    type=click.Choice(["csv", "json", "html"]),
    default="csv", help="Output format")
@click.option("--out", default=None,
    help="Output file path")
@click.pass_context
def register_alias(ctx, fmt, out):
    """Export TPRM register (alias for dashboard register)."""
    ctx.invoke(register_export, fmt=fmt, out=out)


@main.command("sync")
@click.argument("vendor_name", required=False)
@click.option("--json", "as_json", is_flag=True,
    default=False, help="Output raw JSON")
@click.option("--verbose", "-v", is_flag=True,
    default=False)
@click.option("--discover", is_flag=True,
    default=False,
    help="Scan Drive root folder and link subfolders "
         "to matching vendor profiles")
def sync(vendor_name, as_json, verbose, discover):
    """
    Sync vendor profiles and documents from Drive.

    Pulls latest profiles from Drive, scans vendor
    folders for new documents, updates local cache.
    Runs without triggering a full assessment.

    \b
    Examples:
      bandit sync                   # all vendors
      bandit sync "Cyera"           # one vendor
      bandit sync --json            # structured output
      bandit sync --discover        # link Drive folders
    """
    import json as json_module
    from rich.console import Console
    console = Console()

    if discover:
        from core.config import BanditConfig
        from core.integrations.google_drive import (
            GoogleDriveClient
        )
        from core.profiles.vendor_cache import (
            VendorProfileCache
        )

        config = BanditConfig()
        cache = VendorProfileCache()

        drive_cfg = (
            config.get_profile()
            .get("integrations", {})
            .get("google_drive", {})
        )
        root_folder_id = drive_cfg.get("root_folder_id")

        if not root_folder_id:
            console.print(
                "\n  [red]Drive not configured.[/red]"
                " Run: bandit setup --drive\n"
            )
            return

        try:
            drive = GoogleDriveClient()
            drive.authenticate()
            folders = drive.list_vendor_folders(
                root_folder_id
            )
        except Exception as e:
            console.print(
                f"\n  [red]Could not reach Drive: "
                f"{e}[/red]\n"
            )
            return

        console.print(
            f"\n  [dim]Found {len(folders)} folders "
            f"in Drive root[/dim]\n"
        )

        all_profiles = cache.list_all()

        for folder in folders:
            folder_name = folder["name"]
            folder_id = folder["id"]

            # Skip hidden files (e.g. .vendor-profiles.json)
            if folder_name.startswith("."):
                continue

            # Find matching local profile
            # 1. Exact match (case-insensitive, stripped)
            match = next(
                (p for p in all_profiles
                 if p.vendor_name.lower().strip()
                 == folder_name.lower().strip()),
                None
            )
            # 2. Fuzzy match
            if not match:
                match = next(
                    (p for p in all_profiles
                     if folder_name.lower().strip()
                     in p.vendor_name.lower().strip()
                     or p.vendor_name.lower().strip()
                     in folder_name.lower().strip()),
                    None
                )

            if match:
                if match.drive_folder_id:
                    console.print(
                        f"  [dim]·[/dim]  "
                        f"[bold]{match.vendor_name}[/bold]"
                        f"  [dim]already linked[/dim]"
                    )
                else:
                    match.drive_folder_id = folder_id
                    match.drive_folder_name = folder_name
                    cache.save(match.vendor_name, match)
                    console.print(
                        f"  [green]✓[/green]  "
                        f"[bold]{match.vendor_name}[/bold]"
                        f"  [dim]linked to "
                        f"{folder_name}[/dim]"
                    )
            else:
                console.print(
                    f"  [yellow]?[/yellow]  "
                    f"[bold]{folder_name}[/bold]"
                    f"  [dim]no local profile —[/dim]"
                    f"  [dim]run: bandit vendor add "
                    f'"{folder_name}"[/dim]'
                )

        console.print()

        # Re-initialize resolvers so they pick up
        # folder IDs that were just linked by --discover
        if vendor_name:
            resolvers = [VendorDataResolver(vendor_name)]
        else:
            resolvers = get_all_vendor_resolvers()

    if vendor_name:
        resolvers = [VendorDataResolver(
            vendor_name,
            on_progress=(
                lambda p: console.print(
                    f"  [dim]{p['message']}[/dim]"
                ) if verbose else None
            )
        )]
    else:
        resolvers = get_all_vendor_resolvers()

    results = []

    for resolver in resolvers:
        result = resolver.resolve(include_documents=True)
        synced = resolver.sync_profile_to_drive()

        results.append({
            "vendor": result.vendor_name,
            "drive_available": result.drive_available,
            "drive_folder_id": result.drive_folder_id,
            "documents_found": len(result.documents),
            "document_names": [
                d.filename for d in result.documents
            ],
            "profile_synced": synced,
            "errors": result.errors,
        })

    # Check whether stored Drive folder IDs still exist
    for resolver in resolvers:
        profile = resolver.profile
        if not profile:
            continue

        folder_id = getattr(
            profile, "drive_folder_id", None
        )
        if not folder_id:
            continue

        if resolver._drive_configured and resolver._drive:
            try:
                resolver._drive.list_files_in_folder(
                    folder_id
                )
            except Exception:
                console.print(
                    f"  [yellow]⚠[/yellow]  "
                    f"[bold]{profile.vendor_name}[/bold]"
                    f"  [dim]Drive folder not found — "
                    f"may have been deleted or moved. "
                    f"Run bandit sync --discover to "
                    f"relink.[/dim]"
                )

    if as_json:
        click.echo(json_module.dumps(results, indent=2))
        return

    console.print()
    for r in results:
        name = r["vendor"]
        doc_count = r["documents_found"]
        errors = r["errors"]

        if r["drive_available"] and r["drive_folder_id"]:
            icon = "[green]☁[/green]"
            detail = f"{doc_count} docs from Drive"
        elif r["drive_available"]:
            icon = "[yellow]☁[/yellow]"
            detail = "Drive configured — no folder linked"
        else:
            icon = "[dim]⊙[/dim]"
            detail = f"{doc_count} docs (local only)"

        console.print(
            f"  {icon}  [bold]{name}[/bold]"
            f"  [dim]{detail}[/dim]"
        )

        if verbose and r["document_names"]:
            for doc in r["document_names"]:
                console.print(
                    f"     [dim]· {doc}[/dim]"
                )

        if errors:
            for err in errors:
                console.print(
                    f"     [red]⚠ {err}[/red]"
                )

    total_docs = sum(r["documents_found"] for r in results)
    drive_vendors = sum(
        1 for r in results if r["drive_folder_id"]
    )
    console.print(
        f"\n  [dim]"
        f"{len(results)} vendors  ·  "
        f"{drive_vendors} on Drive  ·  "
        f"{total_docs} total documents"
        f"[/dim]\n"
    )


if __name__ == "__main__":
    main()
