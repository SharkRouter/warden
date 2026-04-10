"""Project-level config loader for Warden.

Warden reads defaults from (first match wins, searching upward from the scan
path until a filesystem or VCS root):

1. ``.warden.toml`` at the project root — top-level keys apply directly
2. ``pyproject.toml`` — the ``[tool.warden]`` table

Example ``.warden.toml``::

    path = "."
    format = "all"
    output_dir = "."
    skip = ["secrets", "deps"]
    only = []
    min_score = 60
    baseline = ".warden-baseline.json"
    ci = true

All keys are optional. CLI flags always override values from the config file.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib  # stdlib
else:  # pragma: no cover - exercised only on Python 3.10
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ImportError:  # pragma: no cover
        tomllib = None  # type: ignore[assignment]


# Keys Warden understands in the config table. Anything else triggers a
# warning so typos surface to users instead of being silently ignored.
_ALLOWED_KEYS = frozenset({
    "format",
    "output_dir",
    "skip",
    "only",
    "min_score",
    "baseline",
    "ci",
})

_STOP_AT_DIRS = frozenset({".git", ".hg", ".svn"})


def _discover_config_file(start: Path) -> tuple[Path | None, str | None]:
    """Walk upward from *start* looking for a Warden config source.

    Returns a tuple of ``(path, source)`` where *source* is ``"warden"`` for
    ``.warden.toml`` or ``"pyproject"`` for ``pyproject.toml``. Returns
    ``(None, None)`` when no config is found.
    """
    current = start if start.is_dir() else start.parent
    visited: set[Path] = set()
    while current not in visited:
        visited.add(current)

        warden_toml = current / ".warden.toml"
        if warden_toml.is_file():
            return warden_toml, "warden"

        pyproject = current / "pyproject.toml"
        if pyproject.is_file():
            return pyproject, "pyproject"

        # Stop when we hit a VCS root so we don't escape the project
        if any((current / d).exists() for d in _STOP_AT_DIRS):
            return None, None

        parent = current.parent
        if parent == current:  # filesystem root
            return None, None
        current = parent

    return None, None


def _parse_toml(path: Path) -> dict[str, Any]:
    if tomllib is None:  # pragma: no cover
        raise RuntimeError(
            "Reading TOML configs requires Python 3.11+ or the 'tomli' package"
        )
    with path.open("rb") as fh:
        return tomllib.load(fh)


def load_config(start: Path) -> tuple[dict[str, Any], Path | None]:
    """Load the Warden config table that governs *start*.

    Returns ``(config_dict, source_path)``. The dict only contains keys listed
    in :data:`_ALLOWED_KEYS`; unknown keys are dropped and logged to stderr so
    users notice typos.
    """
    config_path, source = _discover_config_file(start.resolve())
    if config_path is None or source is None:
        return {}, None

    try:
        data = _parse_toml(config_path)
    except Exception as exc:  # noqa: BLE001 - surface any parse issue
        print(
            f"warden: failed to read {config_path}: {exc}",
            file=sys.stderr,
        )
        return {}, config_path

    if source == "warden":
        raw_table = data
    else:
        raw_table = data.get("tool", {}).get("warden", {})
        if not isinstance(raw_table, dict):
            return {}, config_path

    if not isinstance(raw_table, dict):
        return {}, config_path

    clean: dict[str, Any] = {}
    unknown: list[str] = []
    for key, value in raw_table.items():
        if key in _ALLOWED_KEYS:
            clean[key] = value
        else:
            unknown.append(key)

    if unknown:
        print(
            "warden: ignoring unknown config keys in "
            f"{config_path}: {', '.join(sorted(unknown))}",
            file=sys.stderr,
        )

    return clean, config_path


def normalize_list_option(value: Any) -> str | None:
    """Turn a TOML list or string into the comma-separated form the CLI expects."""
    if value is None:
        return None
    if isinstance(value, str):
        trimmed = value.strip()
        return trimmed or None
    if isinstance(value, (list, tuple)):
        parts = [str(item).strip() for item in value if str(item).strip()]
        return ",".join(parts) if parts else None
    # Anything else (int, bool, dict) is a config error; stringify so the
    # scanner will reject it loudly instead of silently doing the wrong thing.
    return str(value)
