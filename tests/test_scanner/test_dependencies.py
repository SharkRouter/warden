"""Tests for Layer 6: Dependency / supply chain scanner."""

import tempfile
from pathlib import Path

from warden.scanner.dependency_scanner import _levenshtein_distance, scan_dependencies


def test_levenshtein_identical():
    assert _levenshtein_distance("hello", "hello") == 0


def test_levenshtein_one_edit():
    assert _levenshtein_distance("openai", "opanai") == 1


def test_levenshtein_two_edits():
    assert _levenshtein_distance("openai", "opanbi") == 2


def test_unpinned_ai_dependency():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "requirements.txt").write_text("openai\nfastapi==0.100.0\n")
        findings, _ = scan_dependencies(Path(tmpdir))
        assert any("Unpinned" in f.message and "openai" in f.message for f in findings)


def test_pinned_dependency_ok():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "requirements.txt").write_text("openai==1.30.0\n")
        findings, _ = scan_dependencies(Path(tmpdir))
        assert not any("Unpinned" in f.message and "openai" in f.message for f in findings)


def test_typosquat_detection():
    with tempfile.TemporaryDirectory() as tmpdir:
        # "opanai" is 1 edit from "openai"
        (Path(tmpdir) / "requirements.txt").write_text("opanai==1.0.0\n")
        findings, _ = scan_dependencies(Path(tmpdir))
        typo_findings = [f for f in findings if "typosquat" in f.message.lower()]
        assert len(typo_findings) >= 1


def test_cloud_pii_detection():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "requirements.txt").write_text("nightfall==2.0.0\nfastapi==0.100.0\n")
        findings, _ = scan_dependencies(Path(tmpdir))
        assert any("cloud" in f.message.lower() and "pii" in f.message.lower() for f in findings)


def test_clean_requirements_no_findings():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "requirements.txt").write_text("fastapi==0.100.0\nuvicorn==0.23.0\n")
        findings, _ = scan_dependencies(Path(tmpdir))
        assert len(findings) == 0


def test_package_json_unpinned():
    with tempfile.TemporaryDirectory() as tmpdir:
        import json
        pkg = {"dependencies": {"openai": "^4.0.0"}}
        (Path(tmpdir) / "package.json").write_text(json.dumps(pkg))
        findings, _ = scan_dependencies(Path(tmpdir))
        assert any("Unpinned" in f.message for f in findings)
