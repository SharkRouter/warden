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


def test_skips_inline_ts_comment_example():
    """Regression: Portkey gateway TS type comment triggered CRITICAL FP.

    `oraclePrivateKey?: string; // example: -----BEGIN RSA PRIVATE KEY-----...`
    is a TypeScript field declaration with an inline comment illustrating the
    expected shape — not a real secret. The inline `// ...` must be stripped
    before regex scanning.
    """
    content = (
        "interface Body {\n"
        "  oraclePrivateKey?: string; "
        "// example: -----BEGIN RSA PRIVATE KEY-----\\nMIIEpAIBAAKCAQEA\n"
        "}\n"
    )
    findings, _ = _scan_content("requestBody.ts", content)
    assert not any("Private Key" in f.message for f in findings)


def test_skips_inline_python_comment_example():
    findings, _ = _scan_content(
        "docs.py",
        'example = "value"  # sample: sk-abcdefghijklmnopqrstuvwxyz1234567890\n',
    )
    assert not any("OpenAI" in f.message for f in findings)


def test_still_detects_secret_before_inline_comment():
    """Secrets BEFORE an inline comment must still be caught."""
    findings, _ = _scan_content(
        "app.ts",
        'const key = "sk-abcdefghijklmnopqrstuvwxyz1234567890"; // rotate quarterly\n',
    )
    assert any("OpenAI" in f.message for f in findings)


def test_database_url_not_mistaken_for_comment():
    """`postgres://user:pw@host` has `//` but no preceding whitespace — must still match."""
    findings, _ = _scan_content(
        "app.ts",
        'const dsn = "postgres://user:password@host:5432/db";\n',
    )
    assert any("Database" in f.message for f in findings)
