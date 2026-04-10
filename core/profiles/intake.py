"""
Bandit Vendor Intake Wizard
============================
12-question intake wizard capturing business context per vendor.
Called by cli/vendor.py.
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.prompt import Prompt, Confirm
from core.config import BanditConfig, CATEGORY_DATA_MAP
from core.config import INTEGRATION_IT_ACTIONS

PROGRESS_FILE = (
    Path.home() / ".bandit" / ".intake_progress.json"
)

# ── Question definitions ──────────────────────────────

Q1_DATA_TYPES = [
    # ── Sensitivity tiers ────────────────────────
    (
        "public",
        "Public data",
        "Publicly available, no confidentiality restrictions"
    ),
    (
        "internal",
        "Internal / operational data",
        "Internal systems, logs, configs — not sensitive"
    ),
    (
        "confidential_business",
        "Confidential business data",
        "Financials, strategy, IP, source code, "
        "internal communications"
    ),
    # ── Personal / people data ───────────────────
    (
        "customer_data",
        "Customer or user data",
        "Any data about your customers, users, "
        "or prospects"
    ),
    (
        "employee_data",
        "Employee or HR data",
        "Personnel records, payroll, performance, "
        "HR systems"
    ),
    # ── Regulated data ───────────────────────────
    (
        "phi",
        "Regulated — health data (PHI / HIPAA)",
        "Any health, medical, or clinical information"
    ),
    (
        "pci",
        "Regulated — payment data (PCI)",
        "Payment card numbers, CVV, cardholder data"
    ),
    # ── None ─────────────────────────────────────
    (
        "none",
        "No personal or confidential data",
        "Infrastructure / tooling only"
    ),
]

# ── Legacy slug migration ─────────────────────────────
LEGACY_DATA_TYPE_MAP = {
    "customer_pii":  "customer_data",
    "employee_pii":  "employee_data",
    "source_code":   "confidential_business",
    "financial":     "confidential_business",
    "operational":   "internal",
    # phi, pci, none — unchanged
}


def normalise_data_types(
    data_types: list[str]
) -> list[str]:
    """
    Migrate old slugs to new slugs.
    Called when loading an existing profile.
    Idempotent — new slugs pass through unchanged.
    """
    result = []
    for t in data_types:
        mapped = LEGACY_DATA_TYPE_MAP.get(t, t)
        if mapped not in result:
            result.append(mapped)
    return result

Q2_VOLUME = [
    ("none",    "None"),
    ("low",     "Low  (fewer than 1,000 records)"),
    ("medium",  "Medium  (1,000 – 100,000 records)"),
    ("high",    "High  (100,000+ records)"),
]

Q3_ENVIRONMENT = [
    ("production",  "Production data"),
    ("sandbox",     "Sandbox / test only"),
    ("both",        "Both"),
    ("none",        "No direct data access"),
]

Q4_ACCESS = [
    (
        "minimal",
        "Minimal impact",
        "View-only or limited scope — read access to "
        "non-sensitive data, sandboxes, or logs only"
    ),
    (
        "data_exposure",
        "Data exposure risk",
        "Could read or export sensitive, personal, "
        "or confidential data from production systems"
    ),
    (
        "data_change",
        "Data or config change risk",
        "Could modify, delete, or corrupt data — "
        "or change application/service configuration"
    ),
    (
        "systemic",
        "Infrastructure or identity risk",
        "Network position (CDN/proxy/firewall), "
        "identity provider (SSO/directory), "
        "secrets manager, or infrastructure admin — "
        "compromise affects systems beyond this vendor"
    ),
]

# ── Legacy access level migration ─────────────────────
LEGACY_ACCESS_LEVEL_MAP = {
    "none":          "minimal",
    "read_only":     "data_exposure",
    "read_write":    "data_change",
    "admin":         "systemic",
    # New slugs pass through unchanged
    "minimal":       "minimal",
    "data_exposure": "data_exposure",
    "data_change":   "data_change",
    "systemic":      "systemic",
}


def normalise_access_level(
    access_level: str | None
) -> str | None:
    """Migrate old access_level slugs to new ones."""
    if not access_level:
        return None
    return LEGACY_ACCESS_LEVEL_MAP.get(
        access_level, access_level
    )

Q5_REPLACEABILITY = [
    (
        "easily_replaceable",
        "Easily replaceable",
        "Clear alternatives exist — low switching cost"
    ),
    (
        "difficult",
        "Difficult to replace",
        "Alternatives exist but switching cost is "
        "high — significant migration effort required"
    ),
    (
        "not_replaceable",
        "Not replaceable",
        "No viable alternative — business-critical "
        "dependency, no realistic switching option"
    ),
]

# ── Legacy sole_source migration ──────────────────────
LEGACY_SOLE_SOURCE_MAP = {
    True:    "not_replaceable",
    False:   "easily_replaceable",
    "true":  "not_replaceable",
    "false": "easily_replaceable",
    # New slugs pass through
    "easily_replaceable": "easily_replaceable",
    "difficult":          "difficult",
    "not_replaceable":    "not_replaceable",
}


def normalise_sole_source(
    value,
) -> str | None:
    """Migrate old boolean to new replaceability slug."""
    if value is None:
        return None
    return LEGACY_SOLE_SOURCE_MAP.get(
        value, str(value)
    )


Q8_AI = [
    ("yes",     "Yes"),
    ("no",      "No"),
    ("unknown", "Unknown"),
]

Q9_TRAINING = [
    ("yes",         "Yes"),
    ("no",          "No"),
    ("opt_out",     "Opt-out available"),
    ("unknown",     "Unknown"),
    ("na",          "N/A — vendor does not use AI"),
]

Q10_CRITICALITY = [
    ("critical",      "Critical — immediate business impact if down"),
    ("important",     "Important — degraded operations"),
    ("useful",        "Useful — workaround available"),
    ("non_essential", "Non-essential"),
]

Q11_SPEND = [
    ("under_10k",     "Under $10,000"),
    ("10k_50k",       "$10,000 – $50,000"),
    ("50k_250k",      "$50,000 – $250,000"),
    ("over_250k",     "$250,000+"),
]

# ── Integration weight modifiers ─────────────────────

INTEGRATION_WEIGHT_MODIFIERS = {
    "customer_data":       {"D1": 0.3, "D3": 0.3},
    "analytics_bi":        {"D1": 0.3, "D6": 0.5, "D7": 0.2},
    "identity_access":     {"D1": 0.3, "D5": 0.3, "D7": 0.2},
    "source_code":         {"D1": 0.5, "D6": 0.3, "D7": 0.2},
    "hr_people":           {"D1": 0.3, "D3": 0.3, "D5": 0.2},
    "healthcare_clinical": {"D1": 0.5, "D5": 1.0, "D8": 0.5},
    "financial_processing":{"D1": 0.3, "D7": 0.5, "D8": 0.3},
    "infrastructure":      {"D2": 0.3, "D5": 0.3, "D8": 0.3},
    "communication":       {"D1": 0.2, "D7": 0.2},
    "security_tooling":    {"D2": 0.5, "D5": 0.5},
    "payments":            {"D7": 0.5},
}

# ── Intake data type → sensitivity mapping ─────────────
INTAKE_DATA_SENSITIVITY = {
    # Public data — no additional weight
    "public": {},

    # Internal operational — slight D1 attention
    "internal": {
        "D1": 0.1,
    },

    # Confidential business data — IP/source code
    # focus on minimization and AI usage
    "confidential_business": {
        "D1": 0.4,
        "D6": 0.3,
        "D7": 0.2,
    },

    # Customer data — PII obligations apply
    # GDPR controller/processor relationship core
    "customer_data": {
        "D1": 0.4,
        "D3": 0.4,
        "D5": 0.2,
        "D7": 0.2,
    },

    # Employee/HR data — sensitive PII
    # employment law obligations
    "employee_data": {
        "D1": 0.4,
        "D3": 0.3,
        "D5": 0.2,
        "D7": 0.2,
    },

    # PHI — highest weight increases
    # HIPAA + GDPR special category
    "phi": {
        "D1": 0.5,
        "D5": 1.0,
        "D7": 0.3,
        "D8": 0.5,
    },

    # PCI — payment card obligations
    "pci": {
        "D1": 0.3,
        "D7": 0.5,
        "D8": 0.3,
    },

    # No personal data — reduce GDPR-specific
    # dimension weights
    "none": {
        "D1": -0.2,
        "D3": -0.3,
    },
}


class IntakeWizard:

    def __init__(self, vendor_name: str):
        self.vendor_name = vendor_name
        self.console = Console()
        self.config = BanditConfig()
        self.answers = {}

    def run(self) -> dict | None:
        """
        Run the full intake wizard.
        Returns answers dict or None if cancelled.
        Saves progress after each question.
        Offers resume if interrupted.
        """
        # Check for existing progress
        saved = self._load_progress()
        if saved and saved.get("vendor") == self.vendor_name:
            resume = Confirm.ask(
                f"\n  Incomplete intake found "
                f"(completed Q{saved.get('last_q', 0)} "
                f"of 12). Resume?",
                default=True
            )
            if resume:
                self.answers = saved.get("answers", {})
                start_q = saved.get("last_q", 0) + 1
            else:
                self._clear_progress()
                start_q = 1
        else:
            start_q = 1

        self.console.print(
            f"\n  [bold dark_orange]Vendor intake "
            f"— {self.vendor_name}[/bold dark_orange]"
            f"\n  [dim]12 questions · "
            f"takes about 3 minutes[/dim]\n"
        )

        try:
            questions = [
                self._q1_data_types,
                self._q2_volume,
                self._q3_environment,
                self._q4_access,
                self._q5_sole_source,
                self._q6_integrations,
                self._q7_sso,
                self._q8_ai,
                self._q9_training,
                self._q10_criticality,
                self._q11_spend,
                self._q12_renewal,
            ]

            for i, question_fn in enumerate(questions):
                q_num = i + 1
                if q_num < start_q:
                    continue
                question_fn()
                self._save_progress(q_num)

            # Data type confirmation check
            self._check_data_type_consistency()

            self._clear_progress()
            return self.answers

        except KeyboardInterrupt:
            self.console.print(
                f"\n  [yellow]Intake paused at "
                f"Q{len(self.answers)}.[/yellow]"
                f"\n  [dim]Run bandit vendor add "
                f'"{self.vendor_name}" to resume.[/dim]'
            )
            return None

    def _q1_data_types(self):
        """Q1 — Data types (multi-select)"""
        self.console.print(
            "\n  [bold]Q1.[/bold] What data will "
            f"{self.vendor_name} come into contact with?\n"
            "  [dim]Include data it stores, transmits, "
            "or can access.\n"
            "  (Select all that apply — "
            "enter numbers separated by commas)[/dim]\n"
        )
        for i, (slug, label, desc) in enumerate(
            Q1_DATA_TYPES
        ):
            self.console.print(
                f"  {i+1:2}.  [bold]{label}[/bold]\n"
                f"       [dim]{desc}[/dim]"
            )

        while True:
            raw = Prompt.ask("\n  Selection").strip()
            try:
                indices = [
                    int(x.strip()) - 1
                    for x in raw.split(",")
                    if x.strip()
                ]
                if all(
                    0 <= idx < len(Q1_DATA_TYPES)
                    for idx in indices
                ):
                    self.answers["data_types"] = [
                        Q1_DATA_TYPES[idx][0]
                        for idx in indices
                    ]
                    break
                self.console.print(
                    "  [red]Invalid selection[/red]"
                )
            except ValueError:
                self.console.print(
                    "  [red]Enter numbers "
                    "separated by commas[/red]"
                )

    def _q2_volume(self):
        """Q2 — Data volume (single select)"""
        self.console.print(
            "\n  [bold]Q2.[/bold] Volume of records "
            f"{self.vendor_name} will access?\n"
        )
        for i, (_, label) in enumerate(Q2_VOLUME):
            self.console.print(f"  {i+1}.  {label}")

        choice = self._single_select(Q2_VOLUME)
        self.answers["data_volume"] = choice

    def _q3_environment(self):
        """Q3 — Production vs sandbox"""
        self.console.print(
            "\n  [bold]Q3.[/bold] Will "
            f"{self.vendor_name} access production "
            f"data?\n"
        )
        for i, (_, label) in enumerate(Q3_ENVIRONMENT):
            self.console.print(f"  {i+1}.  {label}")

        choice = self._single_select(Q3_ENVIRONMENT)
        self.answers["environment_access"] = choice

    def _q4_access(self):
        """Q4 — Blast radius (access impact)"""
        self.console.print(
            "\n  [bold]Q4.[/bold] If "
            f"{self.vendor_name}'s access "
            f"was compromised, what is the "
            f"worst-case impact?\n"
            "  [dim](Pick the highest risk "
            "scenario that applies)[/dim]\n"
        )
        for i, (slug, label, desc) in enumerate(
            Q4_ACCESS
        ):
            self.console.print(
                f"  {i+1}.  [bold]{label}[/bold]\n"
                f"       [dim]{desc}[/dim]"
            )

        choice = self._single_select(Q4_ACCESS)
        self.answers["access_level"] = choice

    def _q5_sole_source(self):
        """Q5 — Replaceability"""
        self.console.print(
            f"\n  [bold]Q5.[/bold] How easily "
            f"could you replace "
            f"{self.vendor_name} if needed?\n"
            "  [dim]This affects your negotiating "
            "leverage on contract terms.[/dim]\n"
        )
        for i, (slug, label, desc) in enumerate(
            Q5_REPLACEABILITY
        ):
            self.console.print(
                f"  {i+1}.  [bold]{label}[/bold]\n"
                f"       [dim]{desc}[/dim]"
            )

        choice = self._single_select(Q5_REPLACEABILITY)
        self.answers["sole_source"] = choice

    def _q6_integrations(self):
        """Q6 — System integrations"""
        all_tools = self.config.get_all_stack_tools()

        if not all_tools:
            # Tech stack not configured — free text
            self.console.print(
                "\n  [bold]Q6.[/bold] Which of your "
                "systems will "
                f"{self.vendor_name} integrate with?\n"
                "  [dim]Tip: Run bandit setup --stack "
                "to see your actual tools here.[/dim]\n"
                "  Enter system names separated by "
                "commas, or press Enter to skip:"
            )
            raw = Prompt.ask("  Systems", default="")
            if raw.strip():
                # Store as basic integration entries
                self.answers["integrations"] = [
                    {
                        "system_name": name.strip(),
                        "system_slug": name.strip().lower().replace(" ", "-"),
                        "category": "general_saas",
                        "category_label": "Unknown",
                        "data_description": "business data",
                    }
                    for name in raw.split(",")
                    if name.strip()
                ]
            else:
                self.answers["integrations"] = []
            return

        # Tech stack configured — show real tools
        self.console.print(
            "\n  [bold]Q6.[/bold] Which of your "
            "systems will "
            f"{self.vendor_name} have access to?\n"
            "  [dim](Select all that apply — "
            "enter numbers, or 0 for none)[/dim]\n"
        )

        # Group by category label for display
        sections = {}
        for tool in all_tools:
            section = tool.get(
                "section_label", "Other"
            )
            if section not in sections:
                sections[section] = []
            sections[section].append(tool)

        display_tools = []
        for section_name, tools in sections.items():
            self.console.print(
                f"  [dim]{section_name.upper()}[/dim]"
            )
            for tool in tools:
                idx = len(display_tools) + 1
                display_tools.append(tool)
                self.console.print(
                    f"  {idx:2}.  "
                    f"{tool['name']} "
                    f"[dim]({tool['category_label']})"
                    f"[/dim]"
                )
            self.console.print()

        none_idx = len(display_tools) + 1
        self.console.print(
            f"  {none_idx:2}.  None — standalone tool"
        )

        while True:
            raw = Prompt.ask("\n  Selection").strip()
            try:
                if raw == "0" or raw == str(none_idx):
                    self.answers["integrations"] = []
                    break

                indices = [
                    int(x.strip()) - 1
                    for x in raw.split(",")
                    if x.strip()
                ]

                valid = all(
                    0 <= idx < len(display_tools)
                    for idx in indices
                )

                if valid:
                    selected = [
                        display_tools[idx]
                        for idx in indices
                    ]
                    # Build IntegrationEntry-compatible dicts
                    integrations = []
                    for tool in selected:
                        cat = tool.get(
                            "category", "general_saas"
                        )
                        cat_data = CATEGORY_DATA_MAP.get(
                            cat, {}
                        )
                        integrations.append({
                            "system_name": tool["name"],
                            "system_slug": tool["slug"],
                            "category": cat,
                            "category_label": tool.get(
                                "category_label", cat
                            ),
                            "data_description": cat_data.get(
                                "data_description",
                                "business data"
                            ),
                        })
                    self.answers["integrations"] = (
                        integrations
                    )
                    break
                self.console.print(
                    "  [red]Invalid selection[/red]"
                )
            except ValueError:
                self.console.print(
                    "  [red]Enter numbers "
                    "separated by commas[/red]"
                )

    def _q7_sso(self):
        """Q7 — SSO required"""
        idp = self.config.get_idp_name()
        through = f" through {idp}" if idp else ""

        self.console.print(
            f"\n  [bold]Q7.[/bold] Does "
            f"{self.vendor_name} require SSO setup"
            f"{through}?\n"
            "  1.  Yes\n"
            "  2.  No\n"
            "  3.  Unknown"
        )
        mapping = {"1": True, "2": False, "3": None}
        while True:
            choice = Prompt.ask(
                "\n  Choice", default="3"
            ).strip()
            if choice in mapping:
                self.answers["sso_required"] = (
                    mapping[choice]
                )
                break
            self.console.print(
                "  [red]Enter 1, 2, or 3[/red]"
            )

    def _q8_ai(self):
        """Q8 — AI in service"""
        self.console.print(
            f"\n  [bold]Q8.[/bold] Does "
            f"{self.vendor_name} use AI or ML "
            f"in their service?\n"
        )
        for i, (_, label) in enumerate(Q8_AI):
            self.console.print(f"  {i+1}.  {label}")

        choice = self._single_select(Q8_AI)
        self.answers["ai_in_service"] = choice

    def _q9_training(self):
        """Q9 — AI training (only shown if AI = yes)"""
        if self.answers.get("ai_in_service") == "no":
            self.answers["ai_trains_on_data"] = "na"
            return

        self.console.print(
            f"\n  [bold]Q9.[/bold] Will your data be "
            f"used to train {self.vendor_name}'s "
            f"AI models?\n"
        )
        for i, (_, label) in enumerate(Q9_TRAINING):
            self.console.print(f"  {i+1}.  {label}")

        choice = self._single_select(Q9_TRAINING)
        self.answers["ai_trains_on_data"] = choice

    def _q10_criticality(self):
        """Q10 — Business criticality"""
        self.console.print(
            f"\n  [bold]Q10.[/bold] How critical is "
            f"{self.vendor_name} to your operations?\n"
        )
        for i, (_, label) in enumerate(Q10_CRITICALITY):
            self.console.print(f"  {i+1}.  {label}")

        choice = self._single_select(Q10_CRITICALITY)
        self.answers["criticality"] = choice

    def _q11_spend(self):
        """Q11 — Annual spend"""
        self.console.print(
            f"\n  [bold]Q11.[/bold] Estimated annual "
            f"spend with {self.vendor_name}?\n"
        )
        for i, (_, label) in enumerate(Q11_SPEND):
            self.console.print(f"  {i+1}.  {label}")

        choice = self._single_select(Q11_SPEND)
        self.answers["annual_spend"] = choice

    def _q12_renewal(self):
        """Q12 — Renewal date"""
        self.console.print(
            f"\n  [bold]Q12.[/bold] Contract renewal "
            f"date for {self.vendor_name}?\n"
            "  [dim]Format: MM/YYYY "
            "(or press Enter to skip)[/dim]"
        )
        raw = Prompt.ask(
            "  Renewal date", default=""
        ).strip()

        if raw:
            import re
            if re.match(r"^\d{2}/\d{4}$", raw):
                self.answers["renewal_date"] = raw
            else:
                self.console.print(
                    "  [yellow]Invalid format — "
                    "skipping date.[/yellow]"
                )
                self.answers["renewal_date"] = None
        else:
            self.answers["renewal_date"] = None

    def _check_data_type_consistency(self):
        """
        Check if integrations imply higher data
        sensitivity than stated in Q1.
        If so, prompt user to confirm or correct.
        Never silently override.
        """
        stated_types = set(
            self.answers.get("data_types", [])
        )
        integrations = self.answers.get(
            "integrations", []
        )

        # Check for potential mismatches
        mismatches = []

        for integration in integrations:
            cat = integration.get("category", "")

            # customer_data integration → should have
            # customer_data in data types
            if (cat in ("customer_data", "crm")
                    and "customer_data" not in stated_types
                    and "none" not in stated_types):
                mismatches.append((
                    integration["system_name"],
                    "customer or user data",
                    "customer_data"
                ))

            # hr_people integration → should have
            # employee_data in data types
            if (cat == "hr_people"
                    and "employee_data" not in stated_types
                    and "none" not in stated_types):
                mismatches.append((
                    integration["system_name"],
                    "employee or HR data",
                    "employee_data"
                ))

            # healthcare_clinical → should have phi
            if (cat == "healthcare_clinical"
                    and "phi" not in stated_types
                    and "none" not in stated_types):
                mismatches.append((
                    integration["system_name"],
                    "regulated health data (PHI)",
                    "phi"
                ))

            # payments → should have pci
            if (cat == "payments"
                    and "pci" not in stated_types
                    and "none" not in stated_types):
                mismatches.append((
                    integration["system_name"],
                    "regulated payment data (PCI)",
                    "pci"
                ))

            # source_code integration → should have
            # confidential_business
            if (cat in ("source_code", "infrastructure")
                    and "confidential_business"
                    not in stated_types
                    and "none" not in stated_types):
                mismatches.append((
                    integration["system_name"],
                    "confidential business data "
                    "(source code / infrastructure)",
                    "confidential_business"
                ))

        if not mismatches:
            return

        self.console.print()
        for system_name, data_type, type_key in mismatches:
            self.console.print(
                f"  [yellow]⚠ Data type check[/yellow]\n"
                f"  You selected {system_name} as an "
                f"integration,\n"
                f"  which typically involves "
                f"{data_type}.\n\n"
                f"  1. Add {data_type} to data types "
                f"(recommended)\n"
                f"  2. Keep as stated — access is limited "
                f"to non-personal data\n"
            )
            while True:
                choice = Prompt.ask(
                    "  Choice", default="1"
                ).strip()
                if choice == "1":
                    current = self.answers.get(
                        "data_types", []
                    )
                    if type_key not in current:
                        current.append(type_key)
                    self.answers["data_types"] = current
                    self.console.print(
                        f"  [green]✓ Added "
                        f"{data_type}[/green]"
                    )
                    break
                elif choice == "2":
                    self.console.print(
                        "  [dim]Keeping stated "
                        "data types.[/dim]"
                    )
                    break
                else:
                    self.console.print(
                        "  [red]Enter 1 or 2[/red]"
                    )

    def build_it_actions(self) -> list[str]:
        """
        Generate IT action items based on
        selected integrations.
        """
        actions = []
        idp = self.config.get_idp_name() or "your IdP"
        integrations = self.answers.get(
            "integrations", []
        )

        for integration in integrations:
            cat = integration.get("category", "")
            system = integration.get("system_name", "")
            cat_actions = INTEGRATION_IT_ACTIONS.get(
                cat, []
            )
            for action in cat_actions:
                formatted = action.format(
                    system=system,
                    idp=idp
                )
                actions.append(
                    f"{system}: {formatted}"
                )

        access = normalise_access_level(
            self.answers.get("access_level")
        )

        if access == "systemic":
            systemic_actions = [
                "Security team review required before "
                "access is granted",
                "Network segmentation review — confirm "
                "blast radius is understood and accepted",
                "Access governance review — confirm "
                "standing vs just-in-time access model",
                "Incident response plan updated to include "
                "this vendor as high-blast-radius system",
            ]
            for action in systemic_actions:
                if action not in actions:
                    actions.append(action)

        elif access == "data_change":
            actions.append(
                "Confirm write access is scoped to "
                "minimum necessary objects and fields"
            )
            actions.append(
                "Verify change audit logging is enabled "
                "and alerts configured for bulk operations"
            )

        elif access == "data_exposure":
            actions.append(
                "Confirm read access is scoped to "
                "minimum necessary data"
            )
            actions.append(
                "Verify data export/download controls "
                "are in place if applicable"
            )

        # Keep existing SSO action for all non-minimal
        if (self.answers.get("sso_required")
                and access != "minimal"):
            sso_action = (
                f"SSO setup required through {idp}"
            )
            if sso_action not in actions:
                actions.insert(0, sso_action)

        return actions

    def show_summary(self) -> None:
        """Show intake summary after completion."""
        a = self.answers

        def label(options, key):
            for k, v in options:
                if k == key:
                    return v
            return key or "—"

        DTYPE_LABELS = {
            slug: lbl
            for slug, lbl, _ in Q1_DATA_TYPES
        }
        data_type_labels = ", ".join(
            DTYPE_LABELS.get(t, t)
            for t in a.get("data_types", [])
        ) or "—"

        integration_names = ", ".join(
            i["system_name"]
            for i in a.get("integrations", [])
        ) or "None"

        self.console.print(
            f"\n  [bold dark_orange]"
            f"✓ {self.vendor_name} intake complete"
            f"[/bold dark_orange]\n"
        )

        rows = [
            ("Data types", data_type_labels),
            ("Volume", label(
                Q2_VOLUME, a.get("data_volume")
            )),
            ("Environment", label(
                Q3_ENVIRONMENT,
                a.get("environment_access")
            )),
            ("Blast radius", {
                slug: lbl
                for slug, lbl, _ in Q4_ACCESS
            }.get(
                normalise_access_level(
                    a.get("access_level", "")
                ) or "", "—"
            )),
            ("Replaceability", {
                slug: lbl
                for slug, lbl, _ in Q5_REPLACEABILITY
            }.get(
                normalise_sole_source(
                    a.get("sole_source")
                ) or "", "—"
            )),
            ("Integrations", integration_names),
            ("AI in service", label(
                Q8_AI, a.get("ai_in_service")
            )),
            ("AI training", label(
                Q9_TRAINING,
                a.get("ai_trains_on_data")
            )),
            ("Criticality", label(
                Q10_CRITICALITY,
                a.get("criticality")
            )),
            ("Annual spend", label(
                Q11_SPEND, a.get("annual_spend")
            )),
            ("Renewal", a.get("renewal_date") or "—"),
        ]

        for key, val in rows:
            self.console.print(
                f"  [dim]{key:<16}[/dim] {val}"
            )

    # ── Helper methods ────────────────────────────

    def _single_select(
        self, options: list[tuple]
    ) -> str:
        """Single selection from numbered list."""
        while True:
            raw = Prompt.ask("\n  Choice").strip()
            try:
                idx = int(raw) - 1
                if 0 <= idx < len(options):
                    return options[idx][0]
                self.console.print(
                    f"  [red]Enter 1–"
                    f"{len(options)}[/red]"
                )
            except ValueError:
                self.console.print(
                    f"  [red]Enter 1–"
                    f"{len(options)}[/red]"
                )

    def _save_progress(self, last_q: int) -> None:
        PROGRESS_FILE.parent.mkdir(
            parents=True, exist_ok=True
        )
        PROGRESS_FILE.write_text(
            json.dumps({
                "vendor": self.vendor_name,
                "last_q": last_q,
                "answers": self.answers,
            }, indent=2)
        )

    def _load_progress(self) -> dict | None:
        if not PROGRESS_FILE.exists():
            return None
        try:
            return json.loads(
                PROGRESS_FILE.read_text()
            )
        except Exception:
            return None

    def _clear_progress(self) -> None:
        if PROGRESS_FILE.exists():
            PROGRESS_FILE.unlink()


def apply_intake_weight_modifiers(
    base_weights: dict,
    profile,  # VendorProfile
    org_profile: dict,
) -> dict:
    """
    Apply intake-derived weight modifiers to
    base weights. Avoids double-counting with
    org profile modifiers already applied.
    """
    weights = dict(base_weights)

    # Data type modifiers
    for data_type in (profile.data_types or []):
        modifiers = INTAKE_DATA_SENSITIVITY.get(
            data_type, {}
        )
        for dim, delta in modifiers.items():
            org_already_covers = _org_covers(
                dim, data_type, org_profile
            )
            if not org_already_covers:
                weights[dim] = min(
                    3.0, weights.get(dim, 1.0) + delta
                )

    # Integration modifiers
    for integration in (profile.integrations or []):
        cat = integration.get("category", "")
        modifiers = INTEGRATION_WEIGHT_MODIFIERS.get(
            cat, {}
        )
        for dim, delta in modifiers.items():
            org_already_covers = _org_covers(
                dim, cat, org_profile
            )
            if not org_already_covers:
                weights[dim] = min(
                    3.0, weights.get(dim, 1.0) + delta
                )

    # Access level (blast radius) modifiers
    access = getattr(profile, "access_level", None)
    access = normalise_access_level(access)

    if access == "minimal":
        # Read-only / sandbox — slight reduction
        # in breach notification urgency
        weights["D5"] = max(
            0.5, weights.get("D5", 1.0) - 0.1
        )

    elif access == "data_exposure":
        # Can read sensitive data — data minimization
        # and subject rights matter more
        weights["D1"] = min(
            3.0, weights.get("D1", 1.0) + 0.3
        )
        weights["D3"] = min(
            3.0, weights.get("D3", 1.0) + 0.2
        )

    elif access == "data_change":
        # Can modify/delete — sub-processor chain
        # and breach notification matter more
        weights["D2"] = min(
            3.0, weights.get("D2", 1.0) + 0.4
        )
        weights["D5"] = min(
            3.0, weights.get("D5", 1.0) + 0.4
        )
        weights["D7"] = min(
            3.0, weights.get("D7", 1.0) + 0.3
        )

    elif access == "systemic":
        # Network position / identity / infra —
        # everything matters, especially breach
        # notification and DPA completeness
        weights["D2"] = min(
            3.0, weights.get("D2", 1.0) + 0.6
        )
        weights["D5"] = min(
            3.0, weights.get("D5", 1.0) + 0.8
        )
        weights["D7"] = min(
            3.0, weights.get("D7", 1.0) + 0.3
        )
        weights["D8"] = min(
            3.0, weights.get("D8", 1.0) + 0.4
        )

    # Cap all at 3.0
    return {
        dim: min(3.0, w)
        for dim, w in weights.items()
    }


def _org_covers(
    dimension: str,
    factor: str,
    org_profile: dict
) -> bool:
    """
    Returns True if the org profile already
    accounts for this dimension/factor combination
    so we don't double-count the modifier.
    """
    data_types = org_profile.get("data_types", {})
    phi_in_scope = data_types.get(
        "phi_in_scope", False
    )
    pci_in_scope = data_types.get(
        "pci_in_scope", False
    )

    if factor in ("phi", "healthcare_clinical"):
        if phi_in_scope and dimension in ("D5", "D8"):
            return True

    if factor in ("pci", "payments"):
        if pci_in_scope and dimension == "D7":
            return True

    # New: customer_data covers D1/D3 for orgs
    # that already weight PII heavily
    if factor in ("customer_data",):
        customer_in_scope = data_types.get(
            "customer_pii_in_scope", False
        )
        if customer_in_scope and dimension in ("D1", "D3"):
            return True

    return False


def build_integration_context_paragraph(
    profile,  # VendorProfile
) -> str | None:
    """
    Build integration + data context paragraph
    injected into Privacy Bandit extraction prompt.
    """
    integrations = profile.integrations or []
    data_types = profile.data_types or []

    if not integrations and not data_types:
        return None

    lines = []

    # Data types context — plain language
    dtype_labels = {
        slug: label
        for slug, label, _ in Q1_DATA_TYPES
    }

    if data_types and "none" not in data_types:
        readable_types = [
            dtype_labels.get(t, t)
            for t in data_types
        ]
        lines.append(
            f"This vendor comes into contact with: "
            f"{', '.join(readable_types)}."
        )

    # Access level context
    access = getattr(profile, "access_level", None)
    access = normalise_access_level(access)
    ACCESS_LABELS = {
        slug: label
        for slug, label, _ in Q4_ACCESS
    }
    if access and access != "minimal":
        lines.append(
            f"Access risk level: "
            f"{ACCESS_LABELS.get(access, access)}. "
            + {
                "data_exposure": (
                    "Attacker could read or export "
                    "sensitive data."
                ),
                "data_change": (
                    "Attacker could modify or delete "
                    "data and configuration."
                ),
                "systemic": (
                    "Compromise could affect systems "
                    "beyond this vendor — evaluate "
                    "breach notification and DPA "
                    "completeness carefully."
                ),
            }.get(access, "")
        )

    # Integration context
    if integrations:
        lines.append(
            "They integrate with or access data from "
            "these of your systems:"
        )
        for i in integrations:
            lines.append(
                f"- {i['system_name']} "
                f"({i['category_label']}): "
                f"{i['data_description']}"
            )

    if not lines:
        return None

    lines.append(
        "\nConsider their obligations for the above "
        "data when evaluating each dimension. "
        "Note: integrations listed are YOUR systems "
        "— not this vendor's sub-processors."
    )

    return "\n".join(lines)
