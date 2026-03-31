"""
Bandit setup wizard — industry and regulatory context profiles.

Run with:
  bandit setup             Run wizard (5 core + up to 3 conditional questions)
  bandit setup --reset     Start fresh, overwrite existing config
  bandit setup --show      Print current config summary
  bandit setup --advanced  Advanced configuration (coming soon)
"""
from __future__ import annotations

import json
import pathlib
import sys
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text


# ─────────────────────────────────────────────────────────────────────
# Progress persistence
# ─────────────────────────────────────────────────────────────────────

PROGRESS_PATH = pathlib.Path.home() / ".bandit" / ".setup_progress.json"


def _save_progress(answers: dict, last_q: int) -> None:
    """Write current answers and last completed question (atomic)."""
    try:
        import tempfile
        PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = pathlib.Path(tempfile.mktemp(dir=PROGRESS_PATH.parent, suffix=".tmp"))
        tmp.write_text(json.dumps({"last_completed_question": last_q, "answers": answers}, indent=2))
        tmp.replace(PROGRESS_PATH)
    except OSError:
        pass


def _load_progress() -> dict | None:
    """Return saved progress dict or None if not found / unreadable."""
    if not PROGRESS_PATH.exists():
        return None
    try:
        with open(PROGRESS_PATH) as f:
            data = json.load(f)
        if isinstance(data.get("last_completed_question"), int):
            return data
    except Exception:
        pass
    return None


def _clear_progress() -> None:
    try:
        if PROGRESS_PATH.exists():
            PROGRESS_PATH.unlink()
    except OSError:
        pass


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
    allow_none: bool = False,
) -> list[str]:
    """Show a numbered list and return a list of selected option strings.

    If allow_none is True, pressing Enter with no default returns [].
    """
    for i, opt in enumerate(options, 1):
        con.print(f"  [color(245)]{i}.[/] {opt}")
    if defaults:
        default_str = ",".join(str(d) for d in defaults)
        hint = f"(e.g. 1,3 — default {default_str})"
    elif allow_none:
        hint = "(e.g. 1,3 — Enter for none)"
    else:
        hint = "(e.g. 1,3)"
    while True:
        raw = con.input(
            f"\n  [color(220)]Enter numbers, comma-separated[/] [color(245)]{hint}:[/] "
        ).strip()
        if not raw:
            if defaults:
                return [options[d - 1] for d in defaults]
            if allow_none:
                return []
        if raw:
            try:
                indices = [int(x.strip()) for x in raw.split(",") if x.strip()]
                if (allow_none or len(indices) >= min_count) and all(1 <= n <= len(options) for n in indices):
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


def _days_label(days: int) -> str:
    """Convert a cadence day count to a human-readable string."""
    if days == 0:
        return "One time / on change"
    _known = {
        30: "Monthly", 60: "Every 2 months", 90: "Quarterly",
        180: "Every 6 months", 365: "Every year",
        548: "Every 18 months", 730: "Every 2 years",
        1095: "Every 3 years", 1825: "Every 5 years",
    }
    if days in _known:
        return _known[days]
    months = round(days / 30.44)
    if months < 24:
        return f"Every ~{months} months"
    y = days / 365.25
    return f"Every ~{round(y, 1):.1g} years".replace(".0", "")


def _section_header(con: Console, number: int, total: int, title: str, subtitle: str = "") -> None:
    con.print()
    con.print(Rule(style="color(238)"))
    con.print()
    t = Text()
    t.append(f"  Q{number}/{total}  ", style="bold color(172)")
    t.append(title, style="bold color(250)")
    if subtitle:
        t.append(f"  — {subtitle}", style="color(245)")
    con.print(t)
    con.print()


# ─────────────────────────────────────────────────────────────────────
# Inference engine
# ─────────────────────────────────────────────────────────────────────

_DEFAULT_WEIGHTS: dict[str, float] = {
    "D1": 1.0, "D2": 1.0, "D3": 1.0, "D4": 1.0,
    "D5": 1.0, "D6": 1.5, "D7": 1.0, "D8": 1.5,
}
_WEIGHT_MIN = 0.5
_WEIGHT_MAX = 3.0


def _infer_frameworks(answers: dict) -> list[str]:
    """Derive applicable frameworks from wizard answers."""
    locations: list[str] = answers.get("locations", [])
    data_types: dict = answers.get("data_types", {})
    org_type: str = answers.get("org_type", "")
    frameworks: list[str] = []

    if "European Union / EEA" in locations:
        frameworks.append("GDPR")
    if "United Kingdom" in locations:
        frameworks.append("UK GDPR")
    if "United States" in locations:
        frameworks.append("CCPA/CPRA")
    if data_types.get("phi") or "Healthcare" in org_type:
        if "HIPAA" not in frameworks:
            frameworks.append("HIPAA")
    if data_types.get("pci"):
        frameworks.append("PCI DSS")
    if data_types.get("children") and "United States" in locations:
        frameworks.append("COPPA")
    if "Canada" in locations:
        frameworks.append("PIPEDA")

    return frameworks


def _infer_weights(answers: dict) -> dict[str, float]:
    """Derive dimension weights from wizard answers."""
    locations: list[str] = answers.get("locations", [])
    data_types: dict = answers.get("data_types", {})
    org_type: str = answers.get("org_type", "")
    infra_location: str = answers.get("infra_location", "")

    weights = dict(_DEFAULT_WEIGHTS)

    eu_present = "European Union / EEA" in locations or "United Kingdom" in locations

    if eu_present:
        weights["D4"] += 1.0
        weights["D3"] += 0.5
        weights["D8"] += 0.5

    # Cross-border: EU presence + US infra
    if eu_present and infra_location in ("us_only", "both"):
        weights["D4"] += 0.5

    if data_types.get("phi") or "Healthcare" in org_type:
        weights["D5"] += 1.0
        weights["D1"] += 0.5
        weights["D3"] += 0.5
        weights["D8"] += 0.5

    if data_types.get("pci"):
        weights["D7"] += 0.5
        weights["D8"] += 0.5
        weights["D5"] += 0.5

    if data_types.get("children"):
        weights["D1"] += 0.5
        weights["D3"] += 0.5

    if data_types.get("biometric") or data_types.get("special_categories"):
        weights["D1"] += 0.5
        weights["D3"] += 0.5
        weights["D6"] += 0.5

    if data_types.get("hr_data"):
        weights["D1"] += 0.3
        weights["D3"] += 0.3

    if "Financial" in org_type:
        weights["D7"] += 0.5
        weights["D5"] += 0.5

    for k in weights:
        weights[k] = round(max(_WEIGHT_MIN, min(_WEIGHT_MAX, weights[k])), 2)

    return weights


def _infer_reassessment(risk_approach: str) -> dict:
    """Derive per-tier reassessment config from risk approach."""
    if risk_approach == "strict":
        return {
            "high":   {"depth": "full",        "days": 180,  "triggers": ["policy_change", "breach_reported", "regulatory_change"]},
            "medium": {"depth": "full",         "days": 365,  "triggers": ["policy_change", "breach_reported"]},
            "low":    {"depth": "scan",         "days": 730,  "triggers": ["breach_reported"]},
        }
    if risk_approach == "pragmatic":
        return {
            "high":   {"depth": "full",         "days": 365,  "triggers": ["breach_reported", "regulatory_change"]},
            "medium": {"depth": "lightweight",  "days": 1095, "triggers": ["breach_reported"]},
            "low":    {"depth": "none",         "days": 0,    "triggers": []},
        }
    # standard (default)
    return {
        "high":   {"depth": "full",        "days": 365,  "triggers": ["policy_change", "breach_reported", "regulatory_change"]},
        "medium": {"depth": "full",        "days": 730,  "triggers": ["policy_change", "breach_reported"]},
        "low":    {"depth": "scan",        "days": 0,    "triggers": ["breach_reported"]},
    }


def _infer_escalation(risk_approach: str, data_types: dict) -> list[dict]:
    """Derive auto-escalation triggers from risk approach and data types."""
    triggers: list[dict] = []

    if risk_approach in ("strict", "standard"):
        triggers.append({
            "type": "tier",
            "tier": "HIGH",
            "label": "Vendor risk tier is HIGH — requires security review",
        })
    if risk_approach == "strict":
        triggers.append({
            "type": "tier",
            "tier": "MEDIUM",
            "label": "Vendor risk tier is MEDIUM — requires conditional approval",
        })
    if data_types.get("phi"):
        triggers.append({
            "type": "red_flag",
            "flag_label": "AI training",
            "label": "AI training on customer PHI data detected — HIPAA violation risk",
        })
    elif risk_approach in ("strict", "standard"):
        triggers.append({
            "type": "red_flag",
            "flag_label": "AI training",
            "label": "AI training on customer data detected with no opt-out mechanism",
        })

    return triggers


# ─────────────────────────────────────────────────────────────────────
# Config writer (new format)
# ─────────────────────────────────────────────────────────────────────

def _write_new_config(
    path: pathlib.Path,
    answers: dict,
    weights: dict[str, float],
    frameworks: list[str],
    reassessment: dict,
    auto_escalate: list[dict],
) -> None:
    """Write config in the new structured YAML format."""
    data_types: dict = answers.get("data_types", {})
    certifications: list[str] = answers.get("certifications", [])
    locations: list[str] = answers.get("locations", [])
    org_type: str = answers.get("org_type", "")
    risk_approach: str = answers.get("risk_approach", "standard")

    # Build document requirements from certifications + data types
    doc_requirements: list[str] = list(certifications)
    if data_types.get("phi") and "HIPAA BAA" not in doc_requirements:
        doc_requirements.append("HIPAA BAA")
    if "European Union / EEA" in locations and "GDPR DPA" not in doc_requirements:
        doc_requirements.append("GDPR DPA")
    if "United Kingdom" in locations and "UK GDPR DPA" not in doc_requirements:
        doc_requirements.append("UK GDPR DPA")

    try:
        import yaml

        config_data: dict = {
            "company": {
                "org_type": org_type,
                "locations": locations,
            },
            "data_types": {
                "phi":               data_types.get("phi", False),
                "pci":               data_types.get("pci", False),
                "children":          data_types.get("children", False),
                "biometric":         data_types.get("biometric", False),
                "hr_data":           data_types.get("hr_data", False),
                "special_categories": data_types.get("special_categories", False),
            },
            "frameworks": {
                "inferred": frameworks,
                "certifications_required": certifications,
            },
            "risk_appetite": risk_approach,
            "reassessment": reassessment,
        }
        if doc_requirements:
            config_data["document_requirements"] = doc_requirements
        if answers.get("infra_location"):
            config_data["company"]["infra_location"] = answers["infra_location"]
        if answers.get("baa_required"):
            config_data["company"]["baa_required"] = answers["baa_required"]
        if answers.get("pci_level"):
            config_data["company"]["pci_level"] = answers["pci_level"]
        config_data["dimension_weights"] = {k: float(v) for k, v in weights.items()}
        if auto_escalate:
            config_data["auto_escalate"] = auto_escalate

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.dump(config_data, default_flow_style=False, allow_unicode=True, sort_keys=False))
        return
    except ImportError:
        pass

    # Manual YAML fallback
    lines: list[str] = []

    lines.append("company:")
    lines.append(f'  org_type: "{org_type}"')
    lines.append("  locations:")
    for loc in locations:
        lines.append(f'    - "{loc}"')
    if answers.get("infra_location"):
        lines.append(f'  infra_location: "{answers["infra_location"]}"')
    if answers.get("baa_required"):
        lines.append(f'  baa_required: "{answers["baa_required"]}"')
    if answers.get("pci_level"):
        lines.append(f'  pci_level: "{answers["pci_level"]}"')

    lines.append("")
    lines.append("data_types:")
    for k, v in data_types.items():
        lines.append(f"  {k}: {'true' if v else 'false'}")

    lines.append("")
    lines.append("frameworks:")
    lines.append("  inferred:")
    for f in frameworks:
        lines.append(f'    - "{f}"')
    lines.append("  certifications_required:")
    for c in certifications:
        lines.append(f'    - "{c}"')

    lines.append("")
    lines.append(f"risk_appetite: {risk_approach}")

    lines.append("")
    lines.append("reassessment:")
    for tier, tier_cfg in reassessment.items():
        lines.append(f"  {tier}:")
        lines.append(f"    depth: {tier_cfg['depth']}")
        lines.append(f"    days: {tier_cfg['days']}")
        lines.append("    triggers:")
        for t in tier_cfg.get("triggers", []):
            lines.append(f"      - {t}")

    if doc_requirements:
        lines.append("")
        lines.append("document_requirements:")
        for d in doc_requirements:
            lines.append(f'  - "{d}"')

    lines.append("")
    lines.append("dimension_weights:")
    for k, v in weights.items():
        lines.append(f"  {k}: {v}")

    if auto_escalate:
        lines.append("")
        lines.append("auto_escalate:")
        for trigger in auto_escalate:
            items = list(trigger.items())
            for i, (tk, tv) in enumerate(items):
                prefix = "  - " if i == 0 else "    "
                if isinstance(tv, str) and (" " in tv or ":" in tv):
                    lines.append(f'{prefix}{tk}: "{tv}"')
                else:
                    lines.append(f"{prefix}{tk}: {tv}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


# ─────────────────────────────────────────────────────────────────────
# Wizard
# ─────────────────────────────────────────────────────────────────────

def run_wizard(con: Console | None = None, reset: bool = False, advanced: bool = False) -> None:
    if con is None:
        con = Console()

    if advanced:
        con.print()
        con.print("[bold color(172)]BANDIT SETUP --advanced[/]")
        con.print()
        con.print("[color(245)]Advanced configuration is coming soon.[/]")
        con.print("[color(245)]It will allow you to set per-dimension weights, custom cadence, and team routing directly.[/]")
        con.print()
        con.print("[color(245)]For now, run [color(220)]bandit setup[/][color(245)] to configure your profile with the guided wizard.[/]")
        con.print()
        return

    # --reset clears both progress and config
    if reset:
        _clear_progress()

    # ── Check for saved progress ──────────────────────────────────────
    resume_from = 0
    answers: dict[str, Any] = {}

    if not reset:
        progress = _load_progress()
        if progress:
            last_q = progress.get("last_completed_question", 0)
            if last_q > 0:
                con.print()
                con.print(
                    f"  [color(220)]Incomplete setup found[/] "
                    f"[color(245)](last completed: Q{last_q})[/]\n"
                )
                con.print(f"  [color(245)]r)[/]  Resume from Q{last_q + 1}")
                con.print(f"  [color(245)]s)[/]  Start over")
                choice = con.input(
                    "\n  [color(220)]Choice[/] [color(245)](default r):[/] "
                ).strip().lower()
                if choice == "s":
                    _clear_progress()
                else:
                    answers = dict(progress.get("answers", {}))
                    resume_from = last_q

    # ── Intro ─────────────────────────────────────────────────────────
    if resume_from == 0:
        con.print()
        con.print("[bold color(172)]BANDIT SETUP[/]  [color(245)]Profile Wizard[/]")
        con.print()
        con.print("[color(245)]5 questions (+ up to 3 conditional) — about 2 minutes.")
        con.print("Bandit will infer your applicable frameworks and adjust dimension")
        con.print(f"weights automatically. Saves to [color(220)]bandit.config.yml[/][color(245)].[/]")
        con.print()
    else:
        con.print()
        con.print("[bold color(172)]BANDIT SETUP[/]  [color(245)]Resuming…[/]")

    # ── Count total questions (5 core + conditionals) ─────────────────
    # We'll track max_q dynamically after we know the conditionals
    # For display we show question numbers 1-8 max

    try:
        # ── Q1 — Organisation type ───────────────────────────────────
        if resume_from < 1:
            _section_header(con, 1, "5+", "Organisation type")
            org_options = [
                "Healthcare / Pharma",
                "Financial Services / FinTech",
                "Technology / SaaS",
                "Education / EdTech",
                "Government / Public Sector",
                "Retail / E-commerce",
                "Professional Services",
                "Non-profit",
                "Other",
            ]
            answers["org_type"] = _ask_single(con, "", org_options, default=3)
            _save_progress(answers, 1)

        # ── Q2 — Locations ───────────────────────────────────────────
        if resume_from < 2:
            _section_header(con, 2, "5+", "Where do you and your customers operate?",
                            "select all that apply")
            location_options = [
                "United States",
                "European Union / EEA",
                "United Kingdom",
                "Canada",
                "APAC (Australia, Japan, Singapore, etc.)",
                "Other",
            ]
            answers["locations"] = _ask_multi(con, "", location_options, defaults=[1])
            _save_progress(answers, 2)

        # ── Q3 — Sensitive data types ────────────────────────────────
        if resume_from < 3:
            _section_header(con, 3, "5+", "What sensitive data do vendors handle?",
                            "select all that apply")

            # Pre-select hints based on org type
            org = answers.get("org_type", "")
            data_options = [
                "PHI / Medical records (HIPAA / Art. 9)",
                "Payment card data (PCI DSS)",
                "Children's data (COPPA / GDPR Art. 8)",
                "Biometric data (facial recognition, fingerprints)",
                "Employee / HR records",
                "Special categories (race, religion, sexual orientation, etc.)",
                "None of the above",
            ]
            # Pre-select suggestions based on org type
            preselect: list[int] = []
            if "Healthcare" in org:
                preselect = [1]
            elif "Financial" in org:
                preselect = [2]
            elif "Education" in org:
                preselect = [3]

            if preselect:
                con.print(
                    f"  [color(245)]Suggested for {org}: "
                    + ", ".join(str(p) for p in preselect)
                    + "[/]\n"
                )

            selected = _ask_multi(
                con, "", data_options,
                defaults=preselect if preselect else None,
                min_count=0,
                allow_none=True,
            )

            # Parse into structured data_types dict
            dt: dict[str, bool] = {
                "phi": False, "pci": False, "children": False,
                "biometric": False, "hr_data": False, "special_categories": False,
            }
            for s in selected:
                if "PHI" in s:
                    dt["phi"] = True
                elif "Payment card" in s:
                    dt["pci"] = True
                elif "Children" in s:
                    dt["children"] = True
                elif "Biometric" in s:
                    dt["biometric"] = True
                elif "Employee" in s or "HR" in s:
                    dt["hr_data"] = True
                elif "Special categories" in s:
                    dt["special_categories"] = True
            answers["data_types"] = dt
            _save_progress(answers, 3)

        # ── Q4 — Required certifications ─────────────────────────────
        if resume_from < 4:
            _section_header(con, 4, "5+", "Vendor certifications you require",
                            "select all that apply")
            cert_options = [
                "SOC 2 Type II",
                "ISO 27001",
                "HIPAA BAA",
                "PCI DSS compliance letter (AOC)",
                "GDPR DPA / Article 28 agreement",
                "UK GDPR DPA",
                "None required",
            ]
            # Pre-select based on data types and locations
            dt = answers.get("data_types", {})
            locs = answers.get("locations", [])
            cert_preselect: list[int] = []
            if dt.get("phi"):
                cert_preselect.append(3)  # HIPAA BAA
            if dt.get("pci"):
                cert_preselect.append(4)  # PCI DSS
            if "European Union / EEA" in locs:
                cert_preselect.append(5)  # GDPR DPA
            if "United Kingdom" in locs and 6 not in cert_preselect:
                cert_preselect.append(6)  # UK GDPR DPA
            if not cert_preselect:
                cert_preselect = [1]  # default SOC 2

            if cert_preselect:
                con.print(
                    "  [color(245)]Suggested: "
                    + ", ".join(str(p) for p in cert_preselect)
                    + "[/]\n"
                )

            cert_selected = _ask_multi(
                con, "", cert_options,
                defaults=cert_preselect,
                min_count=0,
                allow_none=True,
            )
            # Strip "None required" from the stored list
            answers["certifications"] = [c for c in cert_selected if c != "None required"]
            _save_progress(answers, 4)

        # ── Q5 — Risk approach ───────────────────────────────────────
        if resume_from < 5:
            _section_header(con, 5, "5+", "Risk approach",
                            "sets escalation thresholds and reassessment cadence")
            approach_options = [
                "Strict     — escalate early, assess HIGH vendors every 6 months",
                "Standard   — balanced, follow risk tier, annual HIGH assessment (default)",
                "Pragmatic  — escalate only on HIGH + critical red flags",
            ]
            approach_val = _ask_single(con, "", approach_options, default=2)
            _approach_map = {1: "strict", 2: "standard", 3: "pragmatic"}
            answers["risk_approach"] = _approach_map[approach_options.index(approach_val) + 1]
            _save_progress(answers, 5)

        # ── Conditional Q6 — Infrastructure (if EU/EEA in locations) ─
        locs = answers.get("locations", [])
        needs_infra_q = "European Union / EEA" in locs or "United Kingdom" in locs

        if needs_infra_q and resume_from < 6:
            _section_header(con, 6, "8", "Where is vendor infrastructure hosted?",
                            "affects cross-border transfer risk (D4)")
            infra_options = [
                "EU / EEA only",
                "US only",
                "Both EU and US (cross-border transfers)",
                "Other / unknown",
            ]
            infra_val = _ask_single(con, "", infra_options, default=3)
            _infra_map = {
                "EU / EEA only":                   "eu_only",
                "US only":                         "us_only",
                "Both EU and US (cross-border transfers)": "both",
                "Other / unknown":                 "other",
            }
            answers["infra_location"] = _infra_map.get(infra_val, "other")
            _save_progress(answers, 6)

        # ── Conditional Q7 — BAA (if PHI in data types) ──────────────
        dt = answers.get("data_types", {})
        needs_baa_q = dt.get("phi", False)

        if needs_baa_q and resume_from < 7:
            _section_header(con, 7, "8", "HIPAA Business Associate Agreement",
                            "required for PHI-handling vendors")
            baa_options = [
                "Yes — required for all PHI-handling vendors",
                "Yes — required for clinical/direct PHI vendors only",
                "No — handled differently",
            ]
            answers["baa_required"] = _ask_single(con, "", baa_options, default=1)
            _save_progress(answers, 7)

        # ── Conditional Q8 — PCI level (if payment card in data types) ─
        needs_pci_q = dt.get("pci", False)

        if needs_pci_q and resume_from < 8:
            _section_header(con, 8, "8", "PCI merchant level",
                            "determines reporting requirements")
            pci_options = [
                "Level 1 — more than 6M Visa/Mastercard transactions per year",
                "Level 2 — 1M to 6M transactions per year",
                "Level 3 / 4 — fewer than 1M transactions per year",
            ]
            answers["pci_level"] = _ask_single(con, "", pci_options, default=3)
            _save_progress(answers, 8)

        # ── Inference engine ──────────────────────────────────────────
        frameworks = _infer_frameworks(answers)
        weights = _infer_weights(answers)
        risk_approach: str = answers.get("risk_approach", "standard")
        reassessment = _infer_reassessment(risk_approach)
        auto_escalate = _infer_escalation(risk_approach, answers.get("data_types", {}))

        # ── Review screen ─────────────────────────────────────────────
        con.print()
        con.print(Rule(style="color(238)"))
        con.print()
        con.print("[bold color(172)]REVIEW[/]  [color(245)]Inferred profile — check before saving.[/]")
        con.print()

        # Company summary
        org_table = Table(box=None, show_header=False, padding=(0, 2))
        org_table.add_column(style="color(245)", no_wrap=True, min_width=22)
        org_table.add_column(style="color(220)")

        org_table.add_row("Organisation type", answers.get("org_type", "—"))
        org_table.add_row("Locations", ", ".join(answers.get("locations", [])) or "—")
        if answers.get("infra_location"):
            _infra_display = {
                "eu_only": "EU / EEA only",
                "us_only": "US only",
                "both":    "Both EU and US",
                "other":   "Other / unknown",
            }
            org_table.add_row("Infra location", _infra_display.get(answers["infra_location"], answers["infra_location"]))
        org_table.add_row("Risk approach", answers.get("risk_approach", "standard").capitalize())
        if frameworks:
            org_table.add_row("Inferred frameworks", ", ".join(frameworks))
        certs = answers.get("certifications", [])
        if certs:
            org_table.add_row("Required certs", ", ".join(certs))

        # Data types summary
        dt = answers.get("data_types", {})
        dt_active = [k for k, v in dt.items() if v]
        _dt_labels = {
            "phi": "PHI / Medical",
            "pci": "Payment card",
            "children": "Children's data",
            "biometric": "Biometric",
            "hr_data": "Employee / HR",
            "special_categories": "Special categories",
        }
        if dt_active:
            org_table.add_row("Sensitive data", ", ".join(_dt_labels.get(k, k) for k in dt_active))
        if answers.get("baa_required"):
            org_table.add_row("BAA", answers["baa_required"])
        if answers.get("pci_level"):
            org_table.add_row("PCI level", answers["pci_level"])

        con.print(Panel(org_table, title="[bold color(172)]PROFILE SUMMARY[/]", border_style="color(238)"))

        # Weights table
        _default = dict(_DEFAULT_WEIGHTS)
        dim_names = {
            "D1": "Data Minimization", "D2": "Sub-processor Management",
            "D3": "Data Subject Rights", "D4": "Cross-Border Transfers",
            "D5": "Breach Notification", "D6": "AI/ML Data Usage",
            "D7": "Retention & Deletion", "D8": "DPA Completeness",
        }
        wt = Table(box=None, show_header=True, padding=(0, 2))
        wt.add_column("Dim",     style="bold color(172)", no_wrap=True)
        wt.add_column("Name",    style="color(245)")
        wt.add_column("Default", style="color(245)", justify="right")
        wt.add_column("Profile", justify="right")
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
        con.print(Panel(wt, title="[bold color(172)]DIMENSION WEIGHTS[/]", border_style="color(238)"))

        # Reassessment schedule
        _tier_color = {"HIGH": "color(196)", "MEDIUM": "color(220)", "LOW": "color(82)"}
        _depth_display = {
            "full": "Full assessment", "lightweight": "Lightweight (D1, D6, D7)",
            "scan": "Privacy policy scan", "none": "No automated assessment",
        }
        rt = Table(box=None, show_header=True, padding=(0, 2))
        rt.add_column("Tier",    style="bold", no_wrap=True, min_width=8)
        rt.add_column("Depth",   style="color(250)")
        rt.add_column("Cadence", style="color(220)")
        for tier_key, tier_label in (("high", "HIGH"), ("medium", "MEDIUM"), ("low", "LOW")):
            tc = reassessment[tier_key]
            rt.add_row(
                f"[{_tier_color[tier_label]}]{tier_label}[/]",
                _depth_display.get(tc["depth"], tc["depth"]),
                _days_label(tc["days"]),
            )
        con.print(Panel(rt, title="[bold color(172)]REASSESSMENT SCHEDULE[/]", border_style="color(238)"))

        # Escalation
        if auto_escalate:
            esc_lines = Text()
            for t in auto_escalate:
                esc_lines.append("  ⚠  ", style="color(220)")
                esc_lines.append(t["label"] + "\n", style="color(245)")
            con.print(Panel(esc_lines, title="[bold color(220)]AUTO-ESCALATION[/]", border_style="color(220)"))

        # ── Save prompt ───────────────────────────────────────────────
        con.print()
        config_path = pathlib.Path("bandit.config.yml")
        con.print(f"  [color(245)]Config will be saved to:[/] [color(220)]{config_path.resolve()}[/]")
        con.print()

        while True:
            choice = con.input(
                "  [color(220)]Y)[/] [color(245)]Save    "
                "[color(220)]n)[/][color(245)] Cancel    "
                "[color(220)]e)[/][color(245)] Edit (restart wizard):[/] "
            ).strip().lower()
            if not choice or choice == "y":
                break
            if choice == "n":
                con.print("\n  [color(245)]Setup cancelled. No changes saved.[/]\n")
                return
            if choice == "e":
                _clear_progress()
                con.print("\n  [color(245)]Restarting wizard…[/]\n")
                run_wizard(con, reset=True)
                return

        # ── Write config ──────────────────────────────────────────────
        _write_new_config(
            config_path, answers, weights, frameworks, reassessment, auto_escalate
        )
        _clear_progress()

        con.print()
        con.print(
            f"  [bold color(82)]✓[/]  [color(245)]Profile saved to[/] [color(220)]{config_path}[/]"
        )
        org_type = answers.get("org_type", "")
        locs = answers.get("locations", [])
        label = f"{org_type}" + (f" · {', '.join(locs[:2])}" if locs else "")
        con.print(f"  [color(245)]Active profile:[/] [color(220)]{label}[/]")
        if frameworks:
            con.print(f"  [color(245)]Frameworks:[/] [color(220)]{', '.join(frameworks)}[/]")
        con.print()

    except KeyboardInterrupt:
        progress = _load_progress()
        if progress and progress.get("last_completed_question", 0) > 0:
            last_q = progress["last_completed_question"]
            con.print(
                f"\n\n  [color(245)]Setup paused at Q{last_q}. "
                f"Run [color(220)]bandit setup[/][color(245)] to resume.[/]\n"
            )
        else:
            con.print("\n  [color(245)]Setup cancelled.[/]\n")
        sys.exit(0)


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

    config_path = next((p for p in CONFIG_PATHS if p.is_file()), None)
    label = get_profile_label(config)

    t = Table(box=None, show_header=False, padding=(0, 2))
    t.add_column(style="color(245)", no_wrap=True, min_width=22)
    t.add_column(style="color(220)")

    # Support both old (profile.*) and new (company.*) format
    company = config.get("company") or {}
    profile = config.get("profile") or {}
    data_types = config.get("data_types") or {}
    frameworks_cfg = config.get("frameworks") or {}

    org_type = company.get("org_type") or profile.get("industry") or "—"
    locations_raw = company.get("locations") or []
    hq_region = profile.get("hq_region") or ""
    locations_str = ", ".join(locations_raw) if locations_raw else hq_region or "—"
    inferred = frameworks_cfg.get("inferred") or profile.get("regulations") or []
    risk_app = config.get("risk_appetite") or profile.get("risk_appetite") or "—"

    t.add_row("Organisation type", org_type)
    t.add_row("Locations",         locations_str)
    t.add_row("Risk appetite",     str(risk_app).capitalize())
    if inferred:
        t.add_row("Frameworks",    ", ".join(inferred))
    certs = frameworks_cfg.get("certifications_required") or []
    if certs:
        t.add_row("Required certs", ", ".join(certs))
    # Data types
    dt_active = [k for k, v in data_types.items() if v]
    if not dt_active and profile:
        if profile.get("phi_in_scope"):  dt_active.append("phi")
        if profile.get("pci_in_scope"):  dt_active.append("pci")
    _dt_labels = {
        "phi": "PHI / Medical", "pci": "Payment card",
        "children": "Children's data", "biometric": "Biometric",
        "hr_data": "Employee / HR", "special_categories": "Special categories",
    }
    if dt_active:
        t.add_row("Sensitive data", ", ".join(_dt_labels.get(k, k) for k in dt_active))
    _drive_cfg = config.get("integrations", {}).get("google_drive", {})
    _drive_folder_id = _drive_cfg.get("root_folder_id")
    if _drive_folder_id:
        t.add_row("Drive", f"Configured (folder: {_drive_folder_id[:20]}…)")
    else:
        t.add_row("Drive", "[color(245)]not configured — run bandit setup --drive[/]")
    t.add_row("Config file", str(config_path) if config_path else "—")

    con.print()
    con.print(Panel(t, title=f"[bold color(172)]BANDIT PROFILE — {label or 'Active'}[/]", border_style="color(238)"))

    # Weights
    wt = Table(box=None, show_header=True, padding=(0, 2))
    wt.add_column("Dim",        style="bold color(172)", no_wrap=True)
    wt.add_column("Weight",     justify="right")
    wt.add_column("vs default", justify="right", style="color(245)")

    _default = {"D1": 1.0, "D2": 1.0, "D3": 1.0, "D4": 1.0, "D5": 1.0, "D6": 1.5, "D7": 1.0, "D8": 1.5}
    # Support both new (dimension_weights) and old (profile.weights) format
    profile_weights = config.get("dimension_weights") or profile.get("weights") or {}
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

    from core.config import get_reassessment_config
    rc = get_reassessment_config(config)
    _tl = {
        "policy_change":     "Policy change",
        "breach_reported":   "Vendor breach",
        "regulatory_change": "Regulatory change",
        "contract_renewal":  "Contract renewal",
    }
    _tc = {"high": "color(196)", "medium": "color(220)", "low": "color(82)"}
    _ddisplay = {
        "full":        "Full assessment",
        "lightweight": "Lightweight (D1, D6, D7)",
        "scan":        "Privacy policy scan",
        "none":        "No automated assessment",
    }
    rct = Table(box=None, show_header=True, padding=(0, 2))
    rct.add_column("Tier",     style="bold", no_wrap=True, min_width=8)
    rct.add_column("Depth",    style="color(250)")
    rct.add_column("Cadence",  style="color(220)")
    rct.add_column("Triggers", style="color(245)")
    for tier_key in ("high", "medium", "low"):
        tc = rc[tier_key]
        trig_str = " · ".join(_tl.get(t, t) for t in tc["triggers"]) or "manual only"
        rct.add_row(
            f"[{_tc[tier_key]}]{tier_key.upper()}[/]",
            _ddisplay.get(tc["depth"], tc["depth"]),
            _days_label(tc["days"]),
            trig_str,
        )
    con.print(Panel(rct, title="[bold color(172)]REASSESSMENT SCHEDULE[/]", border_style="color(238)"))

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
