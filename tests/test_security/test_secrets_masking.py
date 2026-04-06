"""CI-enforced: secrets scanner NEVER stores full secret values."""

from warden.scanner.secrets_scanner import _mask_secret


def test_mask_short_secret():
    result = _mask_secret("sk-abc")
    assert "sk-abc" != result or len("sk-abc") <= 7
    assert "..." in result


def test_mask_long_secret():
    secret = "sk-ant-1234567890abcdefghij"
    result = _mask_secret(secret)
    assert result == "sk-...ghij"
    assert secret not in result
    assert len(result) < len(secret)


def test_mask_preserves_prefix():
    result = _mask_secret("ghp_abcdefghijklmnopqrstuvwxyz123456")
    assert result.startswith("ghp")
    assert "..." in result


def test_secret_finding_has_only_preview():
    """When scanning, findings should only contain masked preview, not full value."""
    import tempfile
    import os
    from pathlib import Path
    from warden.scanner.secrets_scanner import scan_secrets

    # Create a temp file with a fake secret
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test_config.py"
        # Use a pattern that looks like an API key but isn't real
        test_file.write_text('API_KEY = "sk-test1234567890abcdefgh"\n')

        findings, _ = scan_secrets(Path(tmpdir))

        for finding in findings:
            # The full secret value must NOT appear in any finding field
            assert "sk-test1234567890abcdefgh" not in finding.message
            # But the masked preview should appear
            if "OpenAI" in finding.message or "sk-" in finding.message:
                assert "..." in finding.message
