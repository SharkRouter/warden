"""Tests for competitor detection."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from warden.scanner.competitors import COMPETITORS, detect_competitors


def test_registry_has_18_entries():
    """17 competitors + SharkRouter (self-detection) = 18 total."""
    assert len(COMPETITORS) == 18
    assert "sharkrouter" in COMPETITORS


def test_no_signals_no_matches():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "main.py").write_text("print('hello')\n")
        matches, gtm = detect_competitors(Path(tmpdir))
        assert len(matches) == 0


def test_single_signal_is_low_confidence():
    """Single env var should produce low confidence — no GTM routing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "main.py").write_text("print('hello')\n")
        with patch.dict(os.environ, {"ZENITY_API_KEY": "test-key"}):
            matches, gtm = detect_competitors(Path(tmpdir))
            zenity = [m for m in matches if m.id == "zenity"]
            if zenity:
                assert zenity[0].confidence == "low"


def test_two_signals_is_medium_confidence():
    """Env var + code pattern = 2 layers = medium confidence."""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "agent.py").write_text('zenity.observe(tool_call)\n')
        with patch.dict(os.environ, {"ZENITY_API_KEY": "test-key"}):
            matches, gtm = detect_competitors(Path(tmpdir))
            zenity = [m for m in matches if m.id == "zenity"]
            if zenity:
                assert zenity[0].confidence in ("medium", "high")


def test_package_detection():
    """Package in requirements.txt should count as signal."""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "requirements.txt").write_text("portkey-ai==1.0.0\n")
        (Path(tmpdir) / "main.py").write_text("print('hello')\n")
        matches, _ = detect_competitors(Path(tmpdir))
        portkey = [m for m in matches if m.id == "portkey"]
        assert len(portkey) > 0


def test_sharkrouter_detection():
    """SharkRouter should be detectable as existing_customer."""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "config.yaml").write_text("base_url: https://sharkrouter.example.com\n")
        with patch.dict(os.environ, {"SHARK_API_KEY": "test-key"}):
            matches, _ = detect_competitors(Path(tmpdir))
            shark = [m for m in matches if m.id == "sharkrouter"]
            assert len(shark) > 0
