"""Tests for Layer 7: Audit & compliance scanner."""

import tempfile
from pathlib import Path

from warden.scanner.audit_scanner import scan_audit


def test_no_audit_logging():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "main.py").write_text("print('hello')\n")
        findings, _ = scan_audit(Path(tmpdir))
        assert any("audit logging" in f.message.lower() for f in findings)


def test_has_audit_logging():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "main.py").write_text("""
import logging
logger = logging.getLogger(__name__)

class AuditLog:
    def record(self, event):
        logger.info(f"AUDIT: {event}")
""")
        findings, scores = scan_audit(Path(tmpdir))
        assert not any("No audit logging" in f.message for f in findings)
        assert scores.get("D5", 0) > 0


def test_no_compliance_reference():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "main.py").write_text("x = 1\n")
        findings, _ = scan_audit(Path(tmpdir))
        assert any("compliance framework" in f.message.lower() for f in findings)


def test_has_compliance_reference():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "main.py").write_text("""
# SOC2 Type II compliance mapping
# GDPR Article 17 - Right to erasure
import logging
logger = logging.getLogger(__name__)

class AuditTrail:
    pass

LOG_RETENTION_DAYS = 90
""")
        findings, scores = scan_audit(Path(tmpdir))
        assert not any("No compliance framework" in f.message for f in findings)
        assert scores.get("D14", 0) > 0


def test_no_structured_logging():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "main.py").write_text("print('debug info')\n")
        findings, _ = scan_audit(Path(tmpdir))
        assert any("structured logging" in f.message.lower() for f in findings)
