"""
Bandit CLI

Usage
-----
  bandit assess "Acme Corp"
  bandit assess acme.com --verbose
  bandit assess https://acme.com/privacy --json
  bandit assess "Acme Corp" --model claude-sonnet-4-6

Environment
-----------
  ANTHROPIC_API_KEY   Required unless --api-key is passed.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap

from core.scoring.rubric import AssessmentResult, result_to_dict


# ─────────────────────────────────────────────────────────────────────
# Terminal formatting
# ─────────────────────────────────────────────────────────────────────

_BOLD = "\033[1m"
_RESET = "\033[0m"
_RED = "\033[91m"
_YELLOW = "\033[93m"
_GREEN = "\033[92m"
_DIM = "\033[2m"

_TIER_COLOUR = {"HIGH": _RED, "MEDIUM": _YELLOW, "LOW": _GREEN}


def _c(text: str, code: str) -> str:
    """Apply ANSI colour if stdout is a TTY."""
    if sys.stdout.isatty():
        return f"{code}{text}{_RESET}"
    return text


def _bar(score: int, total: int = 5) -> str:
    return "█" * score + "░" * (total - score)


# ─────────────────────────────────────────────────────────────────────
# Report formatter
# ─────────────────────────────────────────────────────────────────────

_W = 64  # report width


def _print_report(result: AssessmentResult, *, verbose: bool = False) -> None:
    tier_col = _TIER_COLOUR.get(result.risk_tier, "")

    print()
    print("━" * _W)
    print(f"  {_c('BANDIT PRIVACY ASSESSMENT', _BOLD)}")
    print(f"  Vendor : {result.vendor}")
    print(
        f"  Risk   : "
        + _c(f"{result.risk_tier}  {result.weighted_average}/5.0", tier_col)
    )
    print(f"  Rubric : v{result.version}")
    print("━" * _W)

    # Dimension scores
    print(f"\n{_c('DIMENSION SCORES', _BOLD)}")
    print("─" * _W)
    for dim_key, dr in result.dimensions.items():
        bar = _bar(dr.capped_score)
        cap = ""
        if dr.cap_reasons:
            cap = _c(f"  [{dr.cap_reasons[0]}]", _DIM)
        weight = f"×{dr.weight:.1f}" if dr.weight != 1.0 else "    "
        print(
            f"  {dim_key} {weight}  {dr.name:<34}"
            f"  {bar} {dr.capped_score}/5  {dr.level_label}{cap}"
        )
        if verbose and dr.missing_for_next:
            missing = dr.missing_for_next
            shown = ", ".join(missing[:3])
            if len(missing) > 3:
                shown += f" (+{len(missing) - 3} more)"
            print(_c(f"         ↑ Next level needs: {shown}", _DIM))

    # Red flags
    if result.red_flags:
        print(f"\n{_c('RED FLAGS  (' + str(len(result.red_flags)) + ')', _BOLD)}")
        print("─" * _W)
        for rf in result.red_flags:
            dims = ", ".join(rf["dims"])
            match_text = textwrap.shorten(rf["match"], width=54, placeholder="…")
            print(_c(f'  ⚠  [{dims}]  {rf["label"]}', _YELLOW))
            print(_c(f'       "{match_text}"', _DIM))

    # Framework certifications
    if result.framework_evidence:
        print(f"\n{_c('FRAMEWORKS DETECTED', _BOLD)}")
        print("─" * _W)
        for fw in result.framework_evidence:
            print(f"  ✓  {fw}")

    # Action guidance by tier
    print(f"\n{_c('RECOMMENDED ACTIONS', _BOLD)}")
    print("─" * _W)
    tier = result.risk_tier
    if tier == "HIGH":
        print("  GRC:       Escalate to security review. Do not proceed to contract.")
        print("  Legal:     Request an updated DPA before signing anything.")
        print("  Security:  Request SOC 2 Type II report directly from the vendor.")
    elif tier == "MEDIUM":
        print("  GRC:       Flag specific gaps for contract negotiation.")
        print("  Legal:     Negotiate DPA improvements on flagged dimensions.")
        print("  Security:  Verify sub-processor list and confirm breach SLAs.")
    else:
        print("  GRC:       Standard onboarding process applies.")
        print("  Legal:     Confirm executed DPA is on file and current.")
        print("  Security:  Annual review sufficient unless scope changes.")
    print()


# ─────────────────────────────────────────────────────────────────────
# Command handlers
# ─────────────────────────────────────────────────────────────────────

def _cmd_assess(args: argparse.Namespace) -> int:
    # Lazy imports so --help works without dependencies installed
    from core.agents.privacy_bandit import PrivacyBandit
    from core.llm.anthropic import AnthropicProvider

    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print(
            "Error: ANTHROPIC_API_KEY not set.\n"
            "Set the environment variable or pass --api-key <key>.",
            file=sys.stderr,
        )
        return 1

    vendor = " ".join(args.vendor)
    provider = AnthropicProvider(model=args.model, api_key=api_key)
    bandit = PrivacyBandit(provider=provider)

    print(f"Assessing {vendor!r} …", file=sys.stderr)

    try:
        result = bandit.assess(vendor)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result_to_dict(result), indent=2))
    else:
        _print_report(result, verbose=args.verbose)

    return 0


# ─────────────────────────────────────────────────────────────────────
# Argument parser
# ─────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bandit",
        description="Bandit — Vendor Privacy Risk Intelligence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            examples:
              bandit assess "Acme Corp"
              bandit assess acme.com --verbose
              bandit assess https://acme.com/privacy --json
              bandit assess "Acme Corp" --model claude-sonnet-4-6
        """),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    assess = sub.add_parser(
        "assess",
        help="Assess a vendor's privacy practices",
        description=(
            "Discover, fetch, and score a vendor's privacy policy "
            "using the Bandit 8-dimension rubric."
        ),
    )
    assess.add_argument(
        "vendor",
        nargs="+",
        metavar="VENDOR",
        help=(
            "Vendor name, domain, or URL — e.g. 'Acme Corp', "
            "acme.com, https://acme.com/privacy"
        ),
    )
    assess.add_argument(
        "--model",
        default="claude-opus-4-6",
        metavar="MODEL",
        help="Claude model ID (default: claude-opus-4-6)",
    )
    assess.add_argument(
        "--api-key",
        default=None,
        metavar="KEY",
        help="Anthropic API key (default: $ANTHROPIC_API_KEY)",
    )
    assess.add_argument(
        "--json",
        action="store_true",
        help="Emit raw JSON instead of the formatted report",
    )
    assess.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show which signals are missing to reach the next dimension level",
    )
    assess.set_defaults(func=_cmd_assess)

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
