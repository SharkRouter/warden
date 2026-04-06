"""CI-enforced: Warden NEVER imports from SharkRouter internals."""

import ast
import pathlib

BANNED_PREFIXES = ("toolguard", "sharkrouter", "server", "router")


def test_no_sharkrouter_imports():
    """No warden module imports from SharkRouter internals."""
    warden_dir = pathlib.Path("warden")
    assert warden_dir.exists(), "warden/ not found"

    for f in warden_dir.rglob("*.py"):
        tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith(BANNED_PREFIXES), \
                    f"{f}:{node.lineno} imports from SharkRouter internal: {node.module}"
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith(BANNED_PREFIXES), \
                        f"{f}:{node.lineno} imports SharkRouter internal: {alias.name}"
