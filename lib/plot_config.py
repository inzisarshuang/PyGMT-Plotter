from __future__ import annotations

import os
import re
from difflib import get_close_matches
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


_CFG_REF_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
_CFG_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_INLINE_COMMENT_RE = re.compile(r"\s+#.*$")


def _expand_cfg_refs(values: Dict[str, str], config_file: Path) -> Dict[str, str]:
    """Expand config and environment references with cycle detection."""
    resolved: Dict[str, str] = {}

    def resolve(key: str, stack: Tuple[str, ...] = ()) -> str:
        """Resolve one key recursively while tracking the active reference chain."""
        if key in resolved:
            return resolved[key]
        if key in stack:
            chain = " -> ".join((*stack, key))
            raise ValueError(f"cyclic configuration reference in {config_file}: {chain}")

        def replace(match: re.Match[str]) -> str:
            """Replace one ${name} token from cfg values or the environment."""
            referenced_key = match.group(1)
            if referenced_key in values:
                return resolve(referenced_key, (*stack, key))
            environment_value = os.environ.get(referenced_key)
            if environment_value is not None:
                return environment_value
            raise ValueError(
                f"unresolved reference '${{{referenced_key}}}' in key '{key}' "
                f"of {config_file}"
            )

        expanded = _CFG_REF_RE.sub(replace, values[key])
        resolved[key] = os.path.expanduser(expanded)
        return resolved[key]

    return {key: resolve(key) for key in values}


def load_key_value_config(config_file: str) -> Dict[str, str]:
    """Read a strict key=value or key:value configuration file."""
    path = Path(config_file).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"configuration file not found: {config_file}")

    values: Dict[str, str] = {}
    with path.open("r", encoding="utf-8") as f:
        for line_number, raw_line in enumerate(f, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            if "=" in line:
                key, raw_value = line.split("=", 1)
            elif ":" in line:
                key, raw_value = line.split(":", 1)
            else:
                raise ValueError(
                    f"invalid configuration line {path}:{line_number}; "
                    "expected key=value"
                )

            key = key.strip()
            if not _CFG_KEY_RE.fullmatch(key):
                raise ValueError(f"invalid configuration key '{key}' at {path}:{line_number}")
            if key in values:
                raise ValueError(f"duplicate configuration key '{key}' at {path}:{line_number}")

            # A comment marker starts an inline comment only when preceded by
            # whitespace, so values such as #1f77b4 remain valid colors.
            value = _INLINE_COMMENT_RE.sub("", raw_value.strip()).strip()
            values[key] = value
    return _expand_cfg_refs(values, path)


def validate_config_keys(
    cfg: Dict[str, str],
    allowed_keys: Iterable[str],
    config_file: str,
    allowed_prefixes: Sequence[str] = (),
) -> None:
    """Reject unknown keys and suggest the closest supported spelling."""
    allowed = set(allowed_keys)
    unknown = sorted(
        key
        for key in cfg
        if key not in allowed and not any(key.startswith(prefix) for prefix in allowed_prefixes)
    )
    if not unknown:
        return

    details = []
    for key in unknown:
        matches = get_close_matches(key, allowed, n=1, cutoff=0.65)
        suggestion = f"; did you mean '{matches[0]}'?" if matches else ""
        details.append(f"'{key}'{suggestion}")
    raise ValueError(f"unknown configuration key(s) in {config_file}: {', '.join(details)}")


def resolve_path(value: str, base_dir: Path) -> str:
    """Resolve a path relative to the config directory when needed."""
    expanded = Path(os.path.expandvars(os.path.expanduser(value)))
    if expanded.is_absolute():
        return str(expanded)
    return str((base_dir / expanded).resolve())


def resolve_output_path(value: str, output_dir: str, base_dir: Path) -> str:
    """Resolve output paths, placing bare filenames inside output_dir."""
    expanded = Path(os.path.expandvars(os.path.expanduser(value)))
    if expanded.is_absolute():
        return str(expanded)
    if expanded.parent == Path("."):
        return str((Path(output_dir) / expanded).resolve())
    return str((base_dir / expanded).resolve())


def get_required(cfg: Dict[str, str], key: str) -> str:
    """Return a required config value or raise a helpful error."""
    value = cfg.get(key, "").strip()
    if not value:
        raise ValueError(f"missing required configuration key: {key}")
    return value


def get_optional(cfg: Dict[str, str], key: str, default: str = "") -> str:
    """Return an optional config value."""
    return cfg.get(key, default).strip()


def parse_bool(value: str | bool | None, default: bool = False) -> bool:
    """Parse common boolean strings."""
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    raise ValueError(f"cannot parse boolean value: {value}")


def parse_float(value: str | None, default: float) -> float:
    """Parse a float with fallback."""
    if value is None or str(value).strip() == "":
        return default
    return float(value)


def parse_int(value: str | None, default: int) -> int:
    """Parse an int with fallback."""
    if value is None or str(value).strip() == "":
        return default
    return int(value)


def parse_csv_strings(value: str | None) -> List[str]:
    """Parse a comma-separated string list."""
    if value is None or str(value).strip() == "":
        return []
    return [item.strip() for item in str(value).split(",") if item.strip()]


def parse_coord_pairs(value: str) -> List[Tuple[float, float]]:
    """Parse 'lon,lat; lon,lat; ...' coordinate pairs."""
    pairs: List[Tuple[float, float]] = []
    for index, item in enumerate(value.split(";"), start=1):
        item = item.strip()
        if not item:
            continue
        parts = [part.strip() for part in item.split(",")]
        if len(parts) != 2:
            raise ValueError(f"invalid coordinate pair #{index}: '{item}'; expected lon,lat")
        pairs.append((float(parts[0]), float(parts[1])))
    return pairs


def parse_choice(value: str, choices: Sequence[str], key: str) -> str:
    """Parse a case-insensitive choice and report the supported values."""
    normalized = value.strip().lower()
    allowed = {choice.lower() for choice in choices}
    if normalized not in allowed:
        raise ValueError(f"invalid value for {key}: '{value}'; choose from {', '.join(choices)}")
    return normalized


def validate_numeric_range(
    minimum: float,
    maximum: float,
    minimum_key: str,
    maximum_key: str,
) -> None:
    """Ensure the lower numeric limit is smaller than the upper limit."""
    if minimum >= maximum:
        raise ValueError(f"{minimum_key} must be smaller than {maximum_key}")


def validate_closed_range(value: float, key: str, minimum: float, maximum: float) -> None:
    """Ensure a numeric value falls inside a closed interval."""
    if not minimum <= value <= maximum:
        raise ValueError(f"{key} must be between {minimum} and {maximum}; got {value}")


def parse_style_block(
    cfg: Dict[str, str],
    prefix: str,
    default_title: str,
    default_annot: str,
    default_label: str,
) -> Dict[str, str]:
    """Collect font-related style values for a named block."""
    return {
        "FONT_TITLE": get_optional(cfg, f"{prefix}_font_title", default_title),
        "FONT_ANNOT_PRIMARY": get_optional(cfg, f"{prefix}_font_annot_primary", default_annot),
        "FONT_LABEL": get_optional(cfg, f"{prefix}_font_label", default_label),
    }


def validate_same_length(items: Sequence[Sequence[object]], names: Sequence[str]) -> None:
    """Ensure multiple parsed lists have the same length."""
    lengths = [len(item) for item in items]
    if len(set(lengths)) > 1:
        detail = ", ".join(f"{name}={length}" for name, length in zip(names, lengths))
        raise ValueError(f"list lengths do not match: {detail}")
