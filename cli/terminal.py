"""
Rich-based terminal renderer for Bandit assessment output.

Replaces the plain-ANSI _print_report() in main.py.

Components:
  - Progress spinner with phase labels during assessment
  - Panel header with risk tier
  - Table of pages analysed
  - Dimension scores table — bars color-coded red/yellow/green
  - Red flags panel
  - Frameworks panel
  - Recommended actions panel (border matches risk tier)
"""
from __future__ import annotations

from contextlib import contextmanager

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text
from rich import box as richbox

# Shared console — import this in main.py for consistent styling
console = Console()

# ─────────────────────────────────────────────────────────────────────
# Style constants
# ─────────────────────────────────────────────────────────────────────

_TIER_STYLE = {
    "HIGH":   "bold color(196)",
    "MEDIUM": "bold color(220)",
    "LOW":    "bold color(82)",
}
_TIER_BORDER = {
    "HIGH":   "color(196)",
    "MEDIUM": "color(220)",
    "LOW":    "color(82)",
}

# Score 1–5 → colour
_SCORE_COLOUR = ["", "color(196)", "color(202)", "color(220)", "color(112)", "color(82)"]


def _bar(score: int, total: int = 5) -> Text:
    """Colour-coded block bar: ██░░░"""
    t = Text()
    col = _SCORE_COLOUR[min(score, 5)]
    for i in range(1, total + 1):
        t.append("█" if i <= score else "░", style=col if i <= score else "color(238)")
    return t


def _fmt(slug: str) -> str:
    """'d1_purposes_stated' → 'purposes stated'"""
    parts = slug.split("_", 1)
    return parts[1].replace("_", " ") if len(parts) == 2 else slug.replace("_", " ")


# ─────────────────────────────────────────────────────────────────────
# Progress context manager
# ─────────────────────────────────────────────────────────────────────

@contextmanager
def assessment_progress(verbose: bool = False):
    """Context manager that yields an update(msg) callable.

    verbose=False  — Rich spinner; progress lines overwrite each other.
    verbose=True   — each progress line is printed permanently so the
                     full stage trace is visible after the run.

    Usage in main.py:
        with assessment_progress(verbose=args.verbose) as update:
            bandit = PrivacyBandit(provider, on_progress=update)
            result = bandit.assess(vendor)
    """
    if verbose:
        def update(msg: str) -> None:
            console.print(f"  [dim color(245)]{msg}[/]")
        yield update
    else:
        with Progress(
            SpinnerColumn(style="color(172)"),
            TextColumn("[color(245)]{task.description}"),
            transient=True,
            console=console,
        ) as progress:
            task = progress.add_task("Initialising…")

            def update(msg: str) -> None:
                progress.update(task, description=msg)

            yield update


# ─────────────────────────────────────────────────────────────────────
# Report renderer
# ─────────────────────────────────────────────────────────────────────

def print_assessment(assessment, *, verbose: bool = False) -> None:
    """Render a PrivacyAssessment to the console using Rich components."""
    result = assessment.result
    sources = assessment.sources

    console.print()

    # ── Header ───────────────────────────────────────────────────────
    tier_style = _TIER_STYLE.get(result.risk_tier, "bold")
    header = Text()
    header.append(f"  {result.vendor}\n\n", style="bold color(255)")
    header.append("  Risk:    ", style="color(245)")
    header.append(f"{result.risk_tier}  {result.weighted_average}/5.0\n", style=tier_style)
    header.append("  Rubric:  ", style="color(245)")
    header.append(f"v{result.version}", style="color(240)")

    console.print(Panel(
        header,
        title="[bold color(172)]BANDIT PRIVACY ASSESSMENT[/]",
        border_style="color(172)",
    ))

    # ── Pages analysed ───────────────────────────────────────────────
    if sources:
        src_table = Table(box=None, show_header=False, padding=(0, 1))
        src_table.add_column(no_wrap=True)
        src_table.add_column(style="dim color(238)", no_wrap=True)
        src_table.add_column(style="dim color(238)", no_wrap=True)
        for i, src in enumerate(sources, 1):
            src_table.add_row(
                f"[color(245)]{i}.[/]  [color(240)]{src.url}[/]",
                f"{src.chars:,} chars",
                f"[{src.via}]",
            )
        console.print(Panel(
            src_table,
            title=f"[bold color(172)]PAGES ANALYSED  ({len(sources)})[/]",
            border_style="color(238)",
        ))

    # ── Dimension scores ─────────────────────────────────────────────
    dim_table = Table(
        box=richbox.SIMPLE,
        show_header=False,
        padding=(0, 1),
        expand=False,
    )
    dim_table.add_column(no_wrap=True, min_width=9)   # D1 ×1.5
    dim_table.add_column(min_width=30)                # name + signals
    dim_table.add_column(width=7, no_wrap=True)       # bar
    dim_table.add_column(width=5, no_wrap=True)       # score
    dim_table.add_column()                            # level label + cap

    for dim_key, dr in result.dimensions.items():
        wt = f" [dim]×{dr.weight:.1f}[/]" if dr.weight != 1.0 else "     "

        # Name + signals as a stacked cell
        cell = Text()
        cell.append(dr.name + "\n", style="color(245)")
        if dr.matched_signals:
            cell.append("  ✓ ", style="color(71)")
            cell.append(
                ", ".join(_fmt(s) for s in dr.matched_signals),
                style="dim color(71)",
            )
            cell.append("\n")
        else:
            cell.append("  ✗  nothing found\n", style="dim color(238)")
        if dr.missing_for_next:
            missing = [_fmt(s) for s in dr.missing_for_next[:4]]
            if len(dr.missing_for_next) > 4:
                missing.append(f"+{len(dr.missing_for_next) - 4} more")
            cell.append(
                f"  ↑ to reach {dr.capped_score + 1}/5:  "
                + ", ".join(missing),
                style="dim color(238)",
            )

        # Level label + cap reasons
        label_cell = Text()
        col = _SCORE_COLOUR[min(dr.capped_score, 5)]
        label_cell.append(dr.level_label, style=col)
        for reason in dr.cap_reasons:
            label_cell.append(f"\n  ↓ {reason}", style="dim color(238)")

        dim_table.add_row(
            f"[bold color(172)]{dim_key}[/]{wt}",
            cell,
            _bar(dr.capped_score),
            f"[bold]{dr.capped_score}[/]/5",
            label_cell,
        )

    console.print(Panel(
        dim_table,
        title="[bold color(172)]DIMENSION SCORES[/]",
        border_style="color(238)",
    ))

    # ── Red flags ────────────────────────────────────────────────────
    if result.red_flags:
        rf_text = Text()
        for rf in result.red_flags:
            dims = ", ".join(rf["dims"])
            rf_text.append(f"\n  ⚠  [{dims}]  ", style="color(220)")
            rf_text.append(rf["label"] + "\n", style="bold color(220)")
            match = rf["match"][:80]
            rf_text.append(f'       "{match}"\n', style="dim color(238)")

        console.print(Panel(
            rf_text,
            title=f"[bold color(220)]RED FLAGS  ({len(result.red_flags)})[/]",
            border_style="color(220)",
        ))

    # ── Framework evidence ───────────────────────────────────────────
    if result.framework_evidence:
        fw_text = Text()
        for fw in result.framework_evidence:
            fw_text.append("  ✓  ", style="color(71)")
            fw_text.append(fw + "\n", style="color(245)")
        console.print(Panel(
            fw_text,
            title="[bold color(172)]FRAMEWORKS DETECTED[/]",
            border_style="color(238)",
        ))

    # ── Recommended actions ──────────────────────────────────────────
    _ACTIONS = {
        "HIGH": [
            ("GRC",      "Escalate to security review. Do not proceed to contract."),
            ("Legal",    "Request an updated DPA before signing anything."),
            ("Security", "Request SOC 2 Type II report directly from the vendor."),
        ],
        "MEDIUM": [
            ("GRC",      "Flag specific gaps for contract negotiation."),
            ("Legal",    "Negotiate DPA improvements on flagged dimensions."),
            ("Security", "Verify sub-processor list and confirm breach SLAs."),
        ],
        "LOW": [
            ("GRC",      "Standard onboarding process applies."),
            ("Legal",    "Confirm executed DPA is on file and current."),
            ("Security", "Annual review sufficient unless scope changes."),
        ],
    }
    action_text = Text()
    for role, action in _ACTIONS.get(result.risk_tier, []):
        action_text.append(f"  {role:<12}", style="bold color(245)")
        action_text.append(action + "\n", style="color(240)")

    console.print(Panel(
        action_text,
        title=f"[{_TIER_STYLE.get(result.risk_tier, 'bold')}]RECOMMENDED ACTIONS — {result.risk_tier}[/]",
        border_style=_TIER_BORDER.get(result.risk_tier, "color(238)"),
    ))

    console.print()
