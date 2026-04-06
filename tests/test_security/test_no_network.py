"""CI-enforced: scanners NEVER import network libraries."""

import ast
import pathlib


BANNED_IMPORTS = {
    "httpx", "requests", "urllib", "aiohttp", "socket", "http.client",
    "urllib3", "urllib.request",
}


def test_no_network_imports_in_scanners():
    """No scanner module imports network libraries."""
    scanner_dir = pathlib.Path("warden/scanner")
    assert scanner_dir.exists(), "warden/scanner/ not found"

    for f in scanner_dir.glob("*.py"):
        if f.name == "__init__.py":
            continue
        tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name not in BANNED_IMPORTS, \
                        f"{f}:{node.lineno} imports banned network library: {alias.name}"
            elif isinstance(node, ast.ImportFrom) and node.module:
                top_module = node.module.split(".")[0]
                assert top_module not in BANNED_IMPORTS, \
                    f"{f}:{node.lineno} imports from banned network library: {node.module}"


def test_no_network_imports_in_report():
    """No report module imports network libraries."""
    report_dir = pathlib.Path("warden/report")
    assert report_dir.exists(), "warden/report/ not found"

    for f in report_dir.glob("*.py"):
        if f.name == "__init__.py":
            continue
        tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name not in BANNED_IMPORTS, \
                        f"{f}:{node.lineno} imports banned network library: {alias.name}"
            elif isinstance(node, ast.ImportFrom) and node.module:
                top_module = node.module.split(".")[0]
                assert top_module not in BANNED_IMPORTS, \
                    f"{f}:{node.lineno} imports from banned network library: {node.module}"
