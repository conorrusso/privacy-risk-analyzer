"""
Bandit setup wizard — industry and regulatory context profiles.

Run with:
  bandit setup           Run full 18-question wizard
  bandit setup --reset   Start fresh, overwrite existing config
  bandit setup --show    Print current config summary
"""
from __future__ import annotations

import pathlib
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text


# ─────────────────────────────────────────────────────────────────────
# Prompt helpers
# ─────────────────────────────────────────────────────────────────────

def _ask_single(
    con: Console,
    prompt: str,
    options: list[str],
    default: int = 1,
) -> str:
    """Show a numbered list and return the selected option string."""
    for i, opt in enumerate(options, 1):
        con.print(f"  [color(245)]{i}.[/] {opt}")
    while True:
        raw = con.input(
            f"\n  [color(220)]Enter number[/] [color(245)](1–{len(options)}, default {default}):[/] "
        ).strip()
        if not raw:
            return options[default - 1]
        try:
            n = int(raw)
            if 1 <= n <= len(options):
                return options[n - 1]
        except ValueError:
            pass
        con.print(f"  [red]Please enter a number between 1 and {len(options)}.[/]")


def _ask_multi(
    con: Console,
    prompt: str,
    options: list[str],
    defaults: list[int] | None = None,
    min_count: int = 1,
) -> list[str]:
    """Show a numbered list and return a list of selected option strings."""
    for i, opt in enumerate(options, 1):
        con.print(f"  [color(245)]{i}.[/] {opt}")
    default_str = ",".join(str(d) for d in (defaults or []))
    hint = f"(e.g. 1,3 — default {default_str})" if default_str else f"(e.g. 1,3)"
    while True:
        raw = con.input(
            f"\n  [color(220)]Enter numbers, comma-separated[/] [color(245)]{hint}:[/] "
        ).strip()
        if not raw and defaults:
            return [options[d - 1] for d in defaults]
        try:
            indices = [int(x.strip()) for x in raw.split(",") if x.strip()]
            if len(indices) >= min_count and all(1 <= n <= len(options) for n in indices):
                return [options[n - 1] for n in indices]
        except ValueError:
            pass
        con.print(f"  [red]Please enter valid numbers between 1 and {len(options)}, comma-separated.[/]")


def _ask_bool(con: Console, prompt: str, default: bool = False) -> bool:
    """Ask a yes/no question."""
    yn = "[color(220)]y[/]/[color(245)]N[/]" if not default else "[color(220)]Y[/]/[color(245)]n[/]"
    while True:
        raw = con.input(f"  {prompt} {yn}: ").strip().lower()
        if not raw:
            return default
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        con.print("  [red]Please enter y or n.[/]")


def _section_header(con: Console, number: int, title: str, subtitle: str = "") -> None:
    con.print()
    con.print(Rule(style="color(238)"))
    con.print()
    t = Text()
    t.append(f"  Section {number}/6  ", style="bold color(172)")
    t.append(title, style="bold color(250)")
    if subtitle:
        t.append(f"  — {subtitle}", style="color(245)")
    con.print(t)
    con.print()


def _section_summary(con: Console, items: list[tuple[str, str]]) -> None:
    t = Table(box=None, show_header=False, padding=(0, 2))
    t.add_column(style="color(245)", no_wrap=True, min_width=22)
    t.add_column(style="color(220)")
    for k, v in items:
        t.add_row(k, v)
    con.print(Panel(t, title="[color(245)]Section summary[/]", border_style="color(238)"))


# ─────────────────────────────────────────────────────────────────────
# Wizard
# ─────────────────────────────────────────────────────────────────────

def run_wizard(con: Console | None = None, reset: bool = False) -> None:
    from core.config import (
        CONFIG_PATHS, calculate_weights, get_profile_label,
        load_config, write_config,
    )
    from core.scoring.rubric import RUBRIC

    if con is None:
        con = Console()

    con.print()
    con.print("[bold color(172)]BANDIT SETUP[/]  [color(245)]Industry & Regulatory Profile Wizard[/]")
    con.print()
    con.print("[color(245)]This wizard configures Bandit to weight dimensions according to your")
    con.print("regulatory environment and data risk profile. Answers are saved to")
    con.print(f"[color(220)]bandit.config.yml[/][color(245)] in the current directory.[/]")
    con.print()

    # Check for existing config
    existing = load_config()
    if existing and not reset:
        label = get_profile_label(existing)
        label_str = f" ({label})" if label else ""
        con.print(f"[color(220)]Note:[/] [color(245)]Existing config found{label_str}.")
        con.print("[color(245)]Run [color(220)]bandit setup --reset[/][color(245)] to overwrite, or continue to update.[/]")
        con.print()

    answers: dict[str, Any] = {}

    # ── Section 1 — Where you operate ───────────────────────────────

    _section_header(con, 1, "Where you operate")

    con.print("  [bold]Q1.[/] [color(250)]Where is your company headquartered?[/]\n")
    hq_options = ["US", "EU/EEA", "UK", "Canada", "APAC", "Other"]
    answers["hq_region"] = _ask_single(con, "", hq_options)

    con.print()
    con.print("  [bold]Q2.[/] [color(250)]Which regions have your customers? (select all that apply)[/]\n")
    region_options = ["US", "EU/EEA", "UK", "Canada", "APAC", "Global", "Other"]
    answers["customer_regions"] = _ask_multi(con, "", region_options, defaults=[1])

    con.print()
    con.print("  [bold]Q3.[/] [color(250)]Where is your infrastructure hosted? (select all that apply)[/]\n")
    infra_options = ["US", "EU/EEA", "UK", "APAC", "Other"]
    answers["infra_regions"] = _ask_multi(con, "", infra_options, defaults=[1])

    con.print()
    _section_summary(con, [
        ("HQ",           answers["hq_region"]),
        ("Customers",    ", ".join(answers["customer_regions"])),
        ("Infrastructure", ", ".join(answers["infra_regions"])),
    ])

    # ── Section 2 — Industry ─────────────────────────────────────────

    _section_header(con, 2, "Your industry")

    con.print("  [bold]Q4.[/] [color(250)]Which industry best describes your company?[/]\n")
    industry_options = [
        "Technology",
        "Healthcare",
        "Financial Services",
        "Education",
        "Retail / E-commerce",
        "Government / Public sector",
        "Professional Services",
        "Other",
    ]
    answers["industry"] = _ask_single(con, "", industry_options)

    con.print()
    _section_summary(con, [("Industry", answers["industry"])])

    # ── Section 3 — Your data ─────────────────────────────────────────

    _section_header(con, 3, "Your data", "affects D1, D3, D5, D6, D8 weights")

    con.print("  [bold]Q5.[/] [color(250)]Do any vendors handle Protected Health Information (PHI)?[/]")
    con.print("       [color(245)]Medical records, diagnoses, treatment data covered by HIPAA / Art. 9[/]\n")
    answers["phi_in_scope"] = _ask_bool(con, "")

    con.print()
    con.print("  [bold]Q6.[/] [color(250)]Do any vendors handle payment card data (PCI)?[/]")
    con.print("       [color(245)]Card numbers, CVVs, or data covered by PCI DSS[/]\n")
    answers["pci_in_scope"] = _ask_bool(con, "")

    con.print()
    con.print("  [bold]Q7.[/] [color(250)]Do any vendors process children's data?[/]")
    con.print("       [color(245)]Under 13 (COPPA) or under 16 (GDPR Art. 8)[/]\n")
    answers["childrens_data"] = _ask_bool(con, "")

    con.print()
    con.print("  [bold]Q8.[/] [color(250)]Do any vendors process special-category data?[/]")
    con.print("       [color(245)]Race, ethnic origin, health, biometric, religious, political, sexual orientation[/]\n")
    answers["special_categories"] = _ask_bool(con, "")

    con.print()
    con.print("  [bold]Q9.[/] [color(250)]Do you onboard AI/ML vendors that may train on your data?[/]")
    con.print("       [color(245)]Applies D6 weight modifier and enables AI red-flag escalation[/]\n")
    answers["ai_vendors"] = _ask_bool(con, "")

    con.print()
    con.print("  [bold]Q10.[/] [color(250)]Approximately how many vendors will you assess per month?[/]\n")
    volume_options = ["1–10 (occasional)", "11–50 (regular)", "51–200 (high volume)", "200+ (enterprise)"]
    answers["vendor_volume"] = _ask_single(con, "", volume_options)

    con.print()
    _section_summary(con, [
        ("PHI in scope",        "Yes" if answers["phi_in_scope"] else "No"),
        ("PCI in scope",        "Yes" if answers["pci_in_scope"] else "No"),
        ("Children's data",     "Yes" if answers["childrens_data"] else "No"),
        ("Special categories",  "Yes" if answers["special_categories"] else "No"),
        ("AI vendors",          "Yes" if answers["ai_vendors"] else "No"),
        ("Monthly volume",      answers["vendor_volume"]),
    ])

    # ── Section 4 — Regulatory obligations ──────────────────────────

    _section_header(con, 4, "Regulatory obligations")

    con.print("  [bold]Q11.[/] [color(250)]Which regulations apply to your organisation? (select all that apply)[/]\n")
    reg_options = ["GDPR", "CCPA/CPRA", "HIPAA", "PCI DSS", "UK GDPR", "LGPD", "PIPL", "Other"]
    answers["regulations"] = _ask_multi(con, "", reg_options, min_count=1)

    con.print()
    con.print("  [bold]Q12.[/] [color(250)]Does your organisation have a designated Data Protection Officer (DPO)?[/]\n")
    answers["dpo_present"] = _ask_bool(con, "")

    con.print()
    _section_summary(con, [
        ("Regulations",  ", ".join(answers["regulations"])),
        ("DPO present",  "Yes" if answers["dpo_present"] else "No"),
    ])

    # ── Section 5 — Risk appetite ────────────────────────────────────

    _section_header(con, 5, "Risk appetite", "controls auto-escalation thresholds")

    con.print("  [bold]Q13.[/] [color(250)]What is your organisation's risk appetite for vendor privacy risk?[/]\n")
    appetite_options = [
        "Conservative  (lower thresholds — escalate early)",
        "Moderate      (balanced — follow risk tier)",
        "Liberal       (higher thresholds — escalate only on HIGH)",
    ]
    appetite_val = _ask_single(con, "", appetite_options, default=2)
    _appetite_map = {1: "conservative", 2: "moderate", 3: "liberal"}
    answers["risk_appetite"] = _appetite_map[appetite_options.index(appetite_val) + 1]

    con.print()
    con.print("  [bold]Q14.[/] [color(250)]At what risk tier should auto-escalation trigger?[/]")
    con.print("       [color(245)]Escalation means DPO / security review required before proceeding[/]\n")
    escalate_options = [
        "HIGH tier only",
        "HIGH or MEDIUM tier",
        "Never (manual review only)",
    ]
    answers["escalate_at"] = _ask_single(con, "", escalate_options)

    con.print()
    con.print("  [bold]Q15.[/] [color(250)]Should AI training red flags trigger escalation regardless of overall score?[/]")
    con.print("       [color(245)]Any detection of 'AI training bundled under generic improvement' → immediate escalation[/]\n")
    answers["ai_escalate"] = _ask_bool(con, "")

    con.print()
    _section_summary(con, [
        ("Risk appetite",     answers["risk_appetite"].capitalize()),
        ("Escalate at",       answers["escalate_at"]),
        ("AI training flag",  "Escalate always" if answers["ai_escalate"] else "Follow risk tier"),
    ])

    # ── Section 6 — Team context ─────────────────────────────────────

    _section_header(con, 6, "Team context")

    con.print("  [bold]Q16.[/] [color(250)]Who typically reviews vendor assessments at your organisation?[/]\n")
    team_options = [
        "GRC team",
        "Legal / Privacy counsel",
        "Security team",
        "DPO",
        "Individual / ad hoc",
        "Shared responsibility",
    ]
    answers["review_team"] = _ask_single(con, "", team_options)

    con.print()
    con.print("  [bold]Q17.[/] [color(250)]What is your target re-assessment cycle for active vendors?[/]\n")
    cycle_options = [
        "90 days  (HIGH risk focus)",
        "180 days (standard)",
        "Annual   (once per year)",
        "On-change only",
    ]
    cycle_val = _ask_single(con, "", cycle_options, default=2)
    _reassess_map = {1: 90, 2: 180, 3: 365, 4: 0}
    answers["reassess_cycle"] = _reassess_map[cycle_options.index(cycle_val) + 1]

    con.print()
    con.print("  [bold]Q18.[/] [color(250)]What describes your current vendor assessment maturity?[/]\n")
    maturity_options = [
        "Just starting  (building a programme from scratch)",
        "Have a process (informal or spreadsheet-based)",
        "Mature programme (policy-driven, tool-supported)",
    ]
    maturity_val = _ask_single(con, "", maturity_options)
    _maturity_map = {1: "just starting", 2: "have a process", 3: "mature programme"}
    answers["maturity"] = _maturity_map[maturity_options.index(maturity_val) + 1]

    con.print()
    _section_summary(con, [
        ("Review team",     answers["review_team"]),
        ("Re-assess cycle", f"{answers['reassess_cycle']} days" if answers["reassess_cycle"] else "On-change"),
        ("Maturity",        answers["maturity"].capitalize()),
    ])

    # ── Calculate weights ─────────────────────────────────────────────

    weights = calculate_weights(answers)
    _default = {"D1": 1.0, "D2": 1.0, "D3": 1.0, "D4": 1.0, "D5": 1.0, "D6": 1.5, "D7": 1.0, "D8": 1.5}

    # ── Build auto_escalate list ──────────────────────────────────────

    auto_escalate: list[dict] = []
    if "HIGH" in answers["escalate_at"]:
        auto_escalate.append({
            "type": "tier",
            "tier": "HIGH",
            "label": "Vendor risk tier is HIGH — requires DPO / security review",
        })
    if "MEDIUM" in answers["escalate_at"]:
        auto_escalate.append({
            "type": "tier",
            "tier": "MEDIUM",
            "label": "Vendor risk tier is MEDIUM — requires conditional approval with gap remediation",
        })
    if answers.get("ai_escalate"):
        auto_escalate.append({
            "type": "red_flag",
            "flag_label": "AI training",
            "label": "AI training on customer data detected with no opt-out mechanism",
        })

    # ── Confirmation screen ───────────────────────────────────────────

    con.print()
    con.print(Rule(style="color(238)"))
    con.print()
    con.print("[bold color(172)]REVIEW[/]  [color(245)]Check your profile before saving.[/]")
    con.print()

    # Weight table
    wt = Table(box=None, show_header=True, padding=(0, 2))
    wt.add_column("Dim",     style="bold color(172)", no_wrap=True)
    wt.add_column("Name",    style="color(245)")
    wt.add_column("Default", style="color(245)", justify="right")
    wt.add_column("Profile", justify="right")

    dim_names = {
        "D1": "Data Minimization", "D2": "Sub-processor Management",
        "D3": "Data Subject Rights", "D4": "Cross-Border Transfers",
        "D5": "Breach Notification", "D6": "AI/ML Data Usage",
        "D7": "Retention & Deletion", "D8": "DPA Completeness",
    }
    for k in ["D1","D2","D3","D4","D5","D6","D7","D8"]:
        pw = weights[k]
        dw = _default[k]
        diff = pw - dw
        if abs(diff) > 0.001:
            sign = "+" if diff > 0 else ""
            pw_str = f"[bold color(220)]×{pw:.1f} ({sign}{diff:.1f})[/]"
        else:
            pw_str = f"[color(245)]×{pw:.1f}[/]"
        wt.add_row(k, dim_names[k], f"×{dw:.1f}", pw_str)

    # Profile summary
    industry = answers["industry"]
    hq = answers["hq_region"]
    regs = answers["regulations"]
    profile_name = (f"{hq} " if hq in ("EU/EEA", "UK") else "") + industry

    con.print(Panel(
        wt,
        title=f"[bold color(172)]DIMENSION WEIGHTS — {profile_name}[/]",
        border_style="color(238)",
    ))

    if auto_escalate:
        esc_lines = Text()
        for t in auto_escalate:
            esc_lines.append("  ⚠  ", style="color(220)")
            esc_lines.append(t["label"] + "\n", style="color(245)")
        con.print(Panel(esc_lines, title="[bold color(220)]AUTO-ESCALATION TRIGGERS[/]", border_style="color(220)"))
    else:
        con.print("[color(245)]  No auto-escalation configured.[/]")

    con.print()
    config_path = pathlib.Path("bandit.config.yml")
    con.print(f"  [color(245)]Config will be saved to:[/] [color(220)]{config_path.resolve()}[/]")
    con.print()

    confirmed = _ask_bool(con, "Save this profile?", default=True)
    if not confirmed:
        con.print("\n  [color(245)]Setup cancelled. No changes saved.[/]\n")
        return

    # ── Build and write config ────────────────────────────────────────

    profile = {
        "name": profile_name,
        "industry": industry,
        "hq_region": hq,
        "customer_regions": answers["customer_regions"],
        "infra_regions": answers["infra_regions"],
        "regulations": regs,
        "risk_appetite": answers["risk_appetite"],
        "dpo_present": answers["dpo_present"],
        "phi_in_scope": answers["phi_in_scope"],
        "pci_in_scope": answers["pci_in_scope"],
        "childrens_data": answers["childrens_data"],
        "special_categories": answers["special_categories"],
        "ai_vendors": answers["ai_vendors"],
        "reassess_cycle": answers["reassess_cycle"],
        "review_team": answers["review_team"],
        "maturity": answers["maturity"],
        "weights": {k: float(v) for k, v in weights.items()},
    }

    write_config(config_path, profile, auto_escalate)

    con.print()
    con.print(
        f"  [bold color(82)]✓[/]  [color(245)]Profile saved to[/] [color(220)]{config_path}[/]"
    )
    con.print(f"  [color(245)]All future assessments will use the [color(220)]{profile_name}[/] profile.[/]")
    con.print()


# ─────────────────────────────────────────────────────────────────────
# --show
# ─────────────────────────────────────────────────────────────────────

def show_config(con: Console | None = None) -> None:
    from core.config import CONFIG_PATHS, get_profile_label, load_config
    from core.scoring.rubric import RUBRIC

    if con is None:
        con = Console()

    config = load_config()
    if not config:
        con.print("\n  [color(245)]No config found. Run [color(220)]bandit setup[/][color(245)] to create one.[/]")
        con.print(f"  [color(245)]Looked in: {', '.join(str(p) for p in CONFIG_PATHS)}[/]\n")
        return

    profile = config.get("profile") or {}
    label = get_profile_label(config)

    # Find which config file was loaded
    config_path = next((p for p in CONFIG_PATHS if p.is_file()), None)

    t = Table(box=None, show_header=False, padding=(0, 2))
    t.add_column(style="color(245)", no_wrap=True, min_width=22)
    t.add_column(style="color(220)")

    t.add_row("Profile name",   profile.get("name", "—"))
    t.add_row("Industry",       profile.get("industry", "—"))
    t.add_row("HQ region",      profile.get("hq_region", "—"))
    t.add_row("Customers",      ", ".join(profile.get("customer_regions") or []))
    t.add_row("Regulations",    ", ".join(profile.get("regulations") or []))
    t.add_row("Risk appetite",  (profile.get("risk_appetite") or "—").capitalize())
    t.add_row("DPO present",    "Yes" if profile.get("dpo_present") else "No")
    t.add_row("PHI in scope",   "Yes" if profile.get("phi_in_scope") else "No")
    t.add_row("PCI in scope",   "Yes" if profile.get("pci_in_scope") else "No")
    t.add_row("AI vendors",     "Yes" if profile.get("ai_vendors") else "No")
    t.add_row("Re-assess cycle", f"{profile['reassess_cycle']} days" if profile.get("reassess_cycle") else "On-change")
    t.add_row("Config file",    str(config_path) if config_path else "—")

    con.print()
    con.print(Panel(t, title=f"[bold color(172)]BANDIT PROFILE — {label or 'Active'}[/]", border_style="color(238)"))

    # Weights
    wt = Table(box=None, show_header=True, padding=(0, 2))
    wt.add_column("Dim",     style="bold color(172)", no_wrap=True)
    wt.add_column("Weight",  justify="right")
    wt.add_column("vs default", justify="right", style="color(245)")

    _default = {"D1": 1.0, "D2": 1.0, "D3": 1.0, "D4": 1.0, "D5": 1.0, "D6": 1.5, "D7": 1.0, "D8": 1.5}
    profile_weights = profile.get("weights") or {}
    for dim_key in ["D1","D2","D3","D4","D5","D6","D7","D8"]:
        pw = float(profile_weights.get(dim_key, _default[dim_key]))
        dw = _default[dim_key]
        diff = pw - dw
        if abs(diff) > 0.001:
            sign = "+" if diff > 0 else ""
            diff_str = f"[bold color(220)]{sign}{diff:.1f}[/]"
        else:
            diff_str = "[color(245)]—[/]"
        name = RUBRIC[dim_key]["name"]
        wt.add_row(f"{dim_key} {name}", f"×{pw:.1f}", diff_str)

    con.print(Panel(wt, title="[bold color(172)]DIMENSION WEIGHTS[/]", border_style="color(238)"))

    # Auto-escalation
    triggers = config.get("auto_escalate") or []
    if triggers:
        esc_lines = Text()
        for t_item in triggers:
            esc_lines.append("  ⚠  ", style="color(220)")
            esc_lines.append(t_item.get("label", str(t_item)) + "\n", style="color(245)")
        con.print(Panel(esc_lines, title="[bold color(220)]AUTO-ESCALATION TRIGGERS[/]", border_style="color(220)"))
    else:
        con.print("\n  [color(245)]No auto-escalation configured.[/]")

    con.print()
