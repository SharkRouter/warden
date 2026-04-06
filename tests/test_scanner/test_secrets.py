"""Tests for Layer 4: Secrets scanner."""

import tempfile
from pathlib import Path

from warden.scanner.secrets_scanner import scan_secrets


def _scan_content(filename: str, content: str):
    with tempfile.TemporaryDirectory() as tmpdir:
        f = Path(tmpdir) / filename
        f.write_text(content)
        return scan_secrets(Path(tmpdir))


def test_detects_openai_key():
    findings, _ = _scan_content(".env", 'OPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwxyz1234567890')
    assert any("OpenAI" in f.message for f in findings)


def test_detects_github_token():
    findings, _ = _scan_content("config.py", 'token = "ghp_abcdefghijklmnopqrstuvwxyz1234567890ab"')
    assert any("GitHub" in f.message for f in findings)


def test_detects_database_url():
    findings, _ = _scan_content(".env", "DATABASE_URL=postgres://user:password@host:5432/db")
    assert any("Database" in f.message for f in findings)


def test_skips_comments():
    findings, _ = _scan_content("config.py", '# sk-abcdefghijklmnopqrstuvwxyz1234567890\n')
    assert len(findings) == 0


def test_clean_file_no_findings():
    findings, _ = _scan_content("main.py", 'print("hello world")\n')
    assert len(findings) == 0


def test_masking_in_findings():
    findings, _ = _scan_content(".env", 'KEY=sk-abcdefghijklmnopqrstuvwxyz1234567890')
    for f in findings:
        # Full key must not appear
        assert "sk-abcdefghijklmnopqrstuvwxyz1234567890" not in f.message
        assert "..." in f.message
