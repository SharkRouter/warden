"""CI-enforced: Warden NEVER imports from WhiteFin (formerly SharkRouter) internals."""

import ast
import pathlib

# Banned prefixes cover both legacy (SharkRouter) and current (WhiteFin) product
# naming. Warden is a standalone scanner with no dependency on the gateway code.
BANNED_PREFIXES = ("toolguard", "sharkrouter", "whitefin", "server", "router")


def test_no_sharkrouter_imports():
    """No warden module imports from WhiteFin/SharkRouter product internals."""
    warden_dir = pathlib.Path("warden")
    assert warden_dir.exists(), "warden/ not found"

    for f in warden_dir.rglob("*.py"):
        tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith(BANNED_PREFIXES), \
                    f"{f}:{node.lineno} imports from product internal: {node.module}"
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith(BANNED_PREFIXES), \
                        f"{f}:{node.lineno} imports product internal: {alias.name}"
