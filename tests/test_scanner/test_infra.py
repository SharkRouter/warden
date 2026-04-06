"""Tests for Layer 3: Infrastructure analyzer."""

import tempfile
from pathlib import Path

from warden.scanner.infra_analyzer import scan_infra


def test_dockerfile_no_user():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "Dockerfile").write_text("FROM python:3.12\nRUN pip install app\nCMD python app.py\n")
        findings, _ = scan_infra(Path(tmpdir))
        assert any("root" in f.message.lower() for f in findings)


def test_dockerfile_with_user_ok():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "Dockerfile").write_text("FROM python:3.12\nUSER appuser\nCMD python app.py\n")
        findings, _ = scan_infra(Path(tmpdir))
        assert not any("root" in f.message.lower() and "USER" in f.message for f in findings)


def test_compose_no_network():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "docker-compose.yml").write_text("services:\n  app:\n    image: myapp\n")
        findings, _ = scan_infra(Path(tmpdir))
        assert any("network" in f.message.lower() for f in findings)


def test_no_infra_no_findings():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "main.py").write_text("print('hello')\n")
        findings, _ = scan_infra(Path(tmpdir))
        assert len(findings) == 0
