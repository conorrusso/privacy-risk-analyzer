"""
Bandit configuration — industry and regulatory context profiles.

Config is loaded from (in order):
  1. ./bandit.config.yml          (project-level, checked in or gitignored)
  2. ~/.bandit/bandit.config.yml  (user-level fallback)
"""
from __future__ import annotations

import pathlib
from typing import Any

_DEFAULT_WEIGHTS: dict[str, float] = {
    "D1": 1.0, "D2": 1.0, "D3": 1.0, "D4": 1.0,
    "D5": 1.0, "D6": 1.5, "D7": 1.0, "D8": 1.5,
}

_WEIGHT_MIN = 0.5
_WEIGHT_MAX = 3.0

CONFIG_PATHS = [
    pathlib.Path("bandit.config.yml"),
    pathlib.Path.home() / ".bandit" / "bandit.config.yml",
]


# ─────────────────────────────────────────────────────────────────────
# YAML I/O
# ─────────────────────────────────────────────────────────────────────

def _load_yaml(path: pathlib.Path) -> dict | None:
    try:
        import yaml  # pyyaml
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        return _load_yaml_simple(path)
    except Exception:
        return None


def _load_yaml_simple(path: pathlib.Path) -> dict | None:
    """Minimal YAML parser for the specific bandit.config.yml format.

    Fallback when pyyaml is not installed. Handles the exact structure
    that write_config() produces — not a general YAML parser.
    Supports up to 3-level nesting (for the ``reassessment`` section).
    """
    try:
        result: dict = {}
        section_name: str | None = None
        current_section: dict | None = None   # top-level section dict
        current_key: str | None = None         # key at indent=2 within current_section
        current_subsection: dict | None = None # dict at indent=2 (for reassessment tiers)
        current_subkey: str | None = None      # key at indent=4 within current_subsection
        current_list: list | None = None       # list currently being filled

        for raw in path.read_text().splitlines():
            line = raw.rstrip()
            stripped = line.lstrip()
            indent = len(line) - len(stripped)

            if not stripped or stripped.startswith("#"):
                continue

            if indent == 0:
                if stripped.endswith(":"):
                    section_name = stripped[:-1]
                    if section_name == "auto_escalate":
                        result[section_name] = []
                        current_section = None
                    else:
                        result[section_name] = {}
                        current_section = result[section_name]
                    current_key = None
                    current_subsection = None
                    current_subkey = None
                    current_list = None

            elif indent == 2:
                if section_name == "auto_escalate":
                    if stripped.startswith("- "):
                        entry: dict = {}
                        result["auto_escalate"].append(entry)
                        current_section = entry
                        k, _, v = stripped[2:].partition(":")
                        v = v.strip().strip('"').strip("'")
                        if v:
                            current_section[k.strip()] = v
                    elif current_section is not None and ":" in stripped:
                        k, _, v = stripped.partition(":")
                        current_section[k.strip()] = v.strip().strip('"').strip("'")
                elif current_section is not None and ":" in stripped:
                    k, _, v = stripped.partition(":")
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if not v:
                        if section_name == "reassessment":
                            # k is a tier key (high / medium / low)
                            current_section[k] = {}
                            current_subsection = current_section[k]
                            current_key = k
                            current_list = None
                        else:
                            current_key = k
                            current_list = []
                            current_section[k] = current_list
                            current_subsection = None
                    else:
                        current_key = k
                        current_list = None
                        current_subsection = None
                        if v == "true":
                            current_section[k] = True
                        elif v == "false":
                            current_section[k] = False
                        else:
                            try:
                                current_section[k] = float(v) if "." in v else int(v)
                            except ValueError:
                                current_section[k] = v

            elif indent == 4:
                if current_subsection is not None and ":" in stripped:
                    # Inside reassessment.tier — parse depth/days/triggers
                    k, _, v = stripped.partition(":")
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if not v:
                        current_subkey = k
                        current_list = []
                        current_subsection[k] = current_list
                    else:
                        current_subkey = k
                        current_list = None
                        try:
                            current_subsection[k] = float(v) if "." in v else int(v)
                        except ValueError:
                            current_subsection[k] = v
                elif stripped.startswith("- ") and current_list is not None and current_subsection is None:
                    val = stripped[2:].strip().strip('"').strip("'")
                    current_list.append(val)
                elif ":" in stripped and current_key == "weights" and current_section is not None:
                    k, _, v = stripped.partition(":")
                    weights = current_section.setdefault("weights", {})
                    try:
                        weights[k.strip()] = float(v.strip())
                    except ValueError:
                        pass

            elif indent == 6:
                # List items inside reassessment.tier.triggers
                if stripped.startswith("- ") and current_list is not None:
                    val = stripped[2:].strip().strip('"').strip("'")
                    current_list.append(val)

        return result if result else None
    except Exception:
        return None


def write_config(
    path: pathlib.Path,
    profile: dict,
    auto_escalate: list,
    reassessment: dict | None = None,
) -> None:
    """Write bandit.config.yml to path."""
    try:
        import yaml
        data: dict = {"profile": profile}
        if reassessment:
            data["reassessment"] = reassessment
        if auto_escalate:
            data["auto_escalate"] = auto_escalate
        path.write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True))
        return
    except ImportError:
        pass

    # Manual writer (fallback when pyyaml not installed)
    lines: list[str] = ["profile:"]
    for k, v in profile.items():
        if isinstance(v, dict):
            lines.append(f"  {k}:")
            for dk, dv in v.items():
                lines.append(f"    {dk}: {dv}")
        elif isinstance(v, list):
            lines.append(f"  {k}:")
            for item in v:
                lines.append(f"    - \"{item}\"")
        elif isinstance(v, bool):
            lines.append(f"  {k}: {'true' if v else 'false'}")
        elif isinstance(v, float):
            lines.append(f"  {k}: {v}")
        else:
            lines.append(f"  {k}: \"{v}\"")

    if reassessment:
        lines.append("")
        lines.append("reassessment:")
        for tier, tier_cfg in reassessment.items():
            lines.append(f"  {tier}:")
            lines.append(f"    depth: {tier_cfg.get('depth', 'full')}")
            lines.append(f"    days: {tier_cfg.get('days', 365)}")
            triggers = tier_cfg.get("triggers") or []
            lines.append("    triggers:")
            for t in triggers:
                lines.append(f"      - {t}")

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
# Public API
# ─────────────────────────────────────────────────────────────────────

def load_config() -> dict[str, Any] | None:
    """Load config from the first matching path. Returns None if not found."""
    for path in CONFIG_PATHS:
        if path.is_file():
            data = _load_yaml(path)
            if data:
                return data
    return None


def get_profile(config: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Return the active profile dict, or None."""
    if config is None:
        config = load_config()
    return (config or {}).get("profile")


def get_weights(config: dict[str, Any] | None = None) -> dict[str, float]:
    """Return dimension weights. Falls back to rubric defaults if no config."""
    if config is None:
        config = load_config()
    weights_raw = ((config or {}).get("profile") or {}).get("weights") or {}
    result = dict(_DEFAULT_WEIGHTS)
    result.update({k: float(v) for k, v in weights_raw.items() if k in result})
    return result


def get_profile_label(config: dict[str, Any] | None = None) -> str | None:
    """Return a short human-readable profile label, e.g. 'EU Technology · GDPR · CCPA/CPRA'."""
    profile = get_profile(config)
    if not profile:
        return None
    parts: list[str] = []
    hq = profile.get("hq_region", "")
    industry = profile.get("industry", "")
    if industry:
        parts.append(f"{hq} {industry}".strip() if hq in ("EU/EEA", "UK") else industry)
    for reg in profile.get("regulations", []):
        parts.append(reg)
    return " · ".join(parts) if parts else profile.get("name")


def is_auto_escalate(result: Any, config: dict[str, Any] | None = None) -> tuple[bool, list[str]]:
    """Check result against configured escalation triggers.

    Returns ``(escalation_required, reasons_list)``.
    """
    if config is None:
        config = load_config()
    triggers = (config or {}).get("auto_escalate") or []
    reasons: list[str] = []
    for trigger in triggers:
        t_type = trigger.get("type")
        if t_type == "tier":
            if result.risk_tier == trigger.get("tier"):
                reasons.append(trigger.get("label", f"Risk tier is {result.risk_tier}"))
        elif t_type == "score_below":
            dim = trigger.get("dimension")
            threshold = int(trigger.get("threshold", 2))
            if dim and dim in result.dimensions and result.dimensions[dim].capped_score < threshold:
                reasons.append(trigger.get("label", f"{dim} score below {threshold}"))
        elif t_type == "red_flag":
            flag_label = (trigger.get("flag_label") or "").lower()
            for rf in result.red_flags:
                if flag_label in rf["label"].lower():
                    reasons.append(trigger.get("label", rf["label"]))
                    break
        elif t_type == "weighted_average_below":
            threshold = float(trigger.get("threshold", 2.5))
            if result.weighted_average < threshold:
                reasons.append(trigger.get("label", f"Weighted average {result.weighted_average} < {threshold}"))
    return bool(reasons), reasons


def get_reassessment_config(config: dict[str, Any] | None = None) -> dict[str, dict]:
    """Return per-tier reassessment configuration with defaults.

    Returns a dict keyed by ``"high"``, ``"medium"``, ``"low"``, each containing:
    - ``depth``    — ``"full"`` | ``"lightweight"`` | ``"scan"`` | ``"none"``
    - ``days``     — int, cadence in days
    - ``triggers`` — list of trigger identifiers
    """
    if config is None:
        config = load_config()
    rc = (config or {}).get("reassessment") or {}
    _defaults: dict[str, dict] = {
        "high":   {"depth": "full",        "days": 90,  "triggers": ["policy_change", "breach_reported"]},
        "medium": {"depth": "lightweight",  "days": 180, "triggers": ["policy_change"]},
        "low":    {"depth": "scan",         "days": 365, "triggers": []},
    }
    result: dict[str, dict] = {}
    for tier in ("high", "medium", "low"):
        tier_cfg = rc.get(tier) or {}
        result[tier] = {
            "depth":    tier_cfg.get("depth",    _defaults[tier]["depth"]),
            "days":     int(tier_cfg.get("days", _defaults[tier]["days"])),
            "triggers": tier_cfg.get("triggers", list(_defaults[tier]["triggers"])),
        }
    return result


# ─────────────────────────────────────────────────────────────────────
# Weight calculator
# ─────────────────────────────────────────────────────────────────────

def calculate_weights(answers: dict[str, Any]) -> dict[str, float]:
    """Derive dimension weights from setup wizard answers.

    Applies additive modifiers on top of base weights, then clamps.

    Parameters
    ----------
    answers:
        Keyed by: hq_region, customer_regions, infra_regions, industry,
        phi_in_scope, pci_in_scope, childrens_data, special_categories,
        ai_vendors. All optional — missing keys are treated as False / [].
    """
    weights = dict(_DEFAULT_WEIGHTS)

    hq = answers.get("hq_region", "")
    customer_regions: list[str] = answers.get("customer_regions") or []
    infra_regions: list[str] = answers.get("infra_regions") or []

    eu_hq = hq in ("EU/EEA", "UK")
    eu_customers = "EU/EEA" in customer_regions or "UK" in customer_regions

    # EU/EEA HQ or customers
    if eu_hq or eu_customers:
        weights["D4"] += 1.0
        weights["D3"] += 0.5
        weights["D8"] += 0.5

    # EU + US infrastructure (cross-border transfers)
    if (eu_hq or eu_customers) and "US" in infra_regions:
        weights["D4"] += 0.5

    # Healthcare / PHI in scope
    if answers.get("phi_in_scope"):
        weights["D5"] += 1.0
        weights["D1"] += 0.5
        weights["D3"] += 0.5
        weights["D8"] += 0.5

    # Financial / PCI in scope
    if answers.get("pci_in_scope"):
        weights["D7"] += 0.5
        weights["D8"] += 0.5
        weights["D5"] += 0.5

    # Children's data
    if answers.get("childrens_data"):
        weights["D1"] += 0.5
        weights["D3"] += 0.5

    # Special categories (health, biometric, etc.)
    if answers.get("special_categories"):
        weights["D1"] += 0.5
        weights["D3"] += 0.5
        weights["D6"] += 0.5

    # AI vendors in scope
    if answers.get("ai_vendors"):
        weights["D6"] += 0.5

    # Clamp to [_WEIGHT_MIN, _WEIGHT_MAX]
    for k in weights:
        weights[k] = round(max(_WEIGHT_MIN, min(_WEIGHT_MAX, weights[k])), 2)

    return weights
