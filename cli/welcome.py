"""
Bandit welcome screen — shown when `bandit` is run with no arguments or --help.
"""
from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

VERSION = "1.4.0"

_BANDIT_ART = """\
██████╗  █████╗ ███╗  ██╗██████╗ ██╗████████╗
██╔══██╗██╔══██╗████╗ ██║██╔══██╗██║╚══██╔══╝
██████╔╝███████║██╔██╗██║██║  ██║██║   ██║
██╔══██╗██╔══██║██║╚████║██║  ██║██║   ██║
██████╔╝██║  ██║██║  ███║██████╔╝██║   ██║
╚═════╝ ╚═╝  ╚═╝╚═╝  ╚══╝╚═════╝ ╚═╝   ╚═╝   """


def show_welcome(console: Console | None = None) -> None:
    if console is None:
        console = Console()

    console.print()

    # ── BANDIT logotype ───────────────────────────────────────────────
    console.print(_BANDIT_ART, style="color(172)")

    # ── Tagline ───────────────────────────────────────────────────────
    tagline = Text()
    tagline.append(
        "  Vendor Risk Intelligence Suite  ·  Every vendor has something to hide.",
        style="color(243)",
    )
    console.print(tagline)
    console.print()

    # ── Rule ──────────────────────────────────────────────────────────
    console.print(Rule(style="color(238)"))
    console.print()

    # ── COMMANDS ─────────────────────────────────────────────────────
    cmd_table = Table(box=None, show_header=False, padding=(0, 2), expand=False)
    cmd_table.add_column(no_wrap=True)
    cmd_table.add_column(style="color(250)")

    def _cmd(base: str, arg: str, flag: str = "") -> Text:
        t = Text()
        t.append(base, style="color(220)")
        if arg:
            t.append(" ")
            t.append(arg, style="color(71)")
        if flag:
            t.append(" ")
            t.append(flag, style="color(220)")
        return t

    commands = [
        (_cmd("bandit assess",  "<vendor>"),                        "Run a privacy risk assessment"),
        (_cmd("bandit assess",  "<vendor>", "-v"),                  "Verbose — see agent reasoning"),
        (_cmd("bandit assess",  "<vendor>", "--json"),              "Output raw JSON"),
        (_cmd("bandit assess",  "<vendor>", "--docs <path>"),       "Include local documents"),
        (_cmd("bandit assess",  "<vendor>", "--drive"),             "Fetch docs from Google Drive (run bandit setup --drive first)"),
        (_cmd("bandit batch",   "<vendors.txt>"),                   "Assess a vendor list overnight"),
        (_cmd("bandit batch",   "<vendors.txt>", "--drive"),        "Batch with Drive documents"),
        (_cmd("bandit rubric",  ""),                                "Show scoring rubric summary"),
        (_cmd("bandit rubric",  "", "--dim <D1-D8>"),               "Show one dimension in detail"),
        (_cmd("bandit profile", "<vendor>"),                        "View or set vendor profile"),
        (_cmd("bandit profile", "", "--unknown"),                   "Profile unrecognised vendors"),
        (_cmd("bandit setup",   ""),                                "Configure your org profile"),
        (_cmd("bandit setup",   "", "--drive"),                     "Connect Google Drive — see docs/google-drive-setup.md"),
        (_cmd("bandit dashboard", ""),                              "Portfolio risk overview"),
        (_cmd("bandit schedule", ""),                               "Reassessment schedule"),
        (_cmd("bandit register", ""),                               "Export TPRM register (CSV / JSON / HTML)"),
        (_cmd("bandit notify",  "", "--all"),                       "Send queued IT notifications"),
        (_cmd("bandit sync",    ""),                                "Sync profiles and docs from Drive"),
        (_cmd("bandit sync",    "", "--discover"),                  "Link Drive folders to vendor profiles"),
    ]
    for cmd_text, desc in commands:
        cmd_table.add_row(cmd_text, desc)

    console.print(Panel(
        cmd_table,
        title="[bold color(172)]COMMANDS[/]",
        border_style="color(238)",
    ))

    # ── EXAMPLES ─────────────────────────────────────────────────────
    ex_lines = Text()
    for ex in [
        'bandit assess "Salesforce"',
        'bandit assess anecdotes.ai --verbose',
        'bandit assess "HubSpot" --docs ./vendor-docs/HubSpot/',
        'bandit assess "Salesforce" --drive',
        'bandit batch vendors.txt --docs-root ./vendor-docs/',
        'bandit batch vendors.txt --drive',
    ]:
        ex_lines.append("$ ", style="dim color(71)")
        ex_lines.append(ex + "\n", style="color(71)")

    console.print(Panel(
        ex_lines,
        title="[bold color(172)]EXAMPLES[/]",
        border_style="color(238)",
    ))

    # ── WORKFLOWS ────────────────────────────────────────────────────
    def _step(n: str, cmd: str, note: str = "") -> None:
        pass  # helper used inline below

    wf_lines = Text()

    def _wf_heading(label: str) -> None:
        wf_lines.append(f"  {label}\n", style="bold color(245)")

    def _wf_step(prefix: str, cmd: str, note: str = "") -> None:
        wf_lines.append(f"    {prefix}  ", style="color(245)")
        wf_lines.append(cmd, style="color(220)")
        if note:
            wf_lines.append(f"   # {note}", style="dim color(245)")
        wf_lines.append("\n")

    _wf_heading("First time with Google Drive:")
    _wf_step("1.", "bandit setup --drive")
    _wf_step("2.", "bandit sync --discover", "link existing folders")
    _wf_step("3.", "bandit sync",            "pull docs + profiles")
    _wf_step("4.", "bandit dashboard",       "view portfolio")
    wf_lines.append("\n")

    _wf_heading("Add a new vendor:")
    _wf_step("1.", 'bandit vendor add "VendorName"')
    _wf_step("2.", 'bandit assess "VendorName" --drive')
    wf_lines.append("\n")

    _wf_heading("Run a full assessment:")
    _wf_step("  ", 'bandit assess "VendorName" --drive --verbose')
    wf_lines.append("\n")

    _wf_heading("See what needs reassessment:")
    _wf_step("  ", "bandit schedule --due")
    wf_lines.append("\n")

    _wf_heading("Export vendor register:")
    _wf_step("  ", "bandit register --format html")

    console.print(Panel(
        wf_lines,
        title="[bold color(172)]COMMON WORKFLOWS[/]",
        border_style="color(238)",
    ))

    # ── PROVIDERS ────────────────────────────────────────────────────
    prov_table = Table(box=None, show_header=False, padding=(0, 2), expand=False)
    prov_table.add_column(min_width=20, no_wrap=True)
    prov_table.add_column(style="color(248)", no_wrap=True)
    prov_table.add_column()

    prov_table.add_row(
        Text("Claude  (default)", style="bold color(245)"),
        "export ANTHROPIC_API_KEY=sk-ant-...",
        "",
    )
    prov_table.add_row(
        Text("GPT-4o", style="bold color(245)"),
        "export OPENAI_API_KEY=sk-...   --provider openai",
        "",
    )

    badges = Text()
    badges.append(" FREE ",  style="bold color(255) on color(22)")
    badges.append("  ")
    badges.append(" LOCAL ", style="bold color(255) on color(18)")

    prov_table.add_row(
        Text("Ollama", style="bold color(245)"),
        "ollama pull llama3.1   --provider ollama",
        badges,
    )

    console.print(Panel(
        prov_table,
        title="[bold color(172)]PROVIDERS[/]",
        border_style="color(238)",
    ))

    # ── Cursor prompt ────────────────────────────────────────────────
    console.print()
    prompt = Text()
    prompt.append("  Run ", style="color(245)")
    prompt.append("bandit setup", style="color(220)")
    prompt.append(" to configure  ·  then ", style="color(245)")
    prompt.append("bandit assess <vendor>", style="color(220)")
    prompt.append(" ▋", style="blink bold color(172)")
    console.print(prompt)
    console.print()
