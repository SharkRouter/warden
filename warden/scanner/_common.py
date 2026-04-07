"""Shared constants for all scanner modules."""

from __future__ import annotations

# Directories to prune during os.walk — never descend into these.
# Only directories that NEVER contain user-authored source code.
# When in doubt, DON'T skip — false negatives are worse than slow scans.
SKIP_DIRS: frozenset[str] = frozenset({
    # Version control internals
    ".git", ".hg", ".svn",
    # Python: virtual environments & caches (never user code)
    ".venv", "venv", "__pycache__", ".eggs", "site-packages",
    ".tox", ".nox", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    ".pytype", "__pypackages__",
    # JavaScript: installed packages & framework caches
    "node_modules", ".next", ".nuxt", ".output",
    "bower_components", ".parcel-cache", ".turbo",
    # IDE / editor metadata
    ".idea", ".vscode", ".vs",
    # Rust / Java build output (compiled bytecode, never source)
    "target",
    # Coverage tool output
    "htmlcov",
})
