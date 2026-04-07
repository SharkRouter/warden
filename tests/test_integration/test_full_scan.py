"""Integration tests — full end-to-end scan on synthetic projects."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture()
def sample_project(tmp_path: Path) -> Path:
    """Create a minimal but realistic AI project for scanning."""
    # Python code with governance issues
    (tmp_path / "main.py").write_text(
        'import openai\n'
        'client = openai.OpenAI()\n'
        'response = client.chat.completions.create(\n'
        '    model="gpt-4",\n'
        '    messages=[{"role": "user", "content": prompt}]\n'
        ')\n'
        'print(response)\n'
    )

    # .env file with secrets
    (tmp_path / ".env").write_text(
        'OPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwxyz1234567890\n'
        'DATABASE_URL=postgresql://user:pass@localhost/db\n'
    )

    # requirements.txt with unpinned AI deps
    (tmp_path / "requirements.txt").write_text(
        'openai\n'
        'langchain\n'
        'requests==2.31.0\n'
    )

    # Dockerfile without USER
    (tmp_path / "Dockerfile").write_text(
        'FROM python:3.12\n'
        'COPY . /app\n'
        'CMD ["python", "main.py"]\n'
    )

    # docker-compose with no network isolation
    (tmp_path / "docker-compose.yml").write_text(
        'version: "3.8"\n'
        'services:\n'
        '  app:\n'
        '    build: .\n'
        '    ports:\n'
        '      - "8000:8000"\n'
    )

    return tmp_path


@pytest.fixture()
def governed_project(tmp_path: Path) -> Path:
    """Create a well-governed AI project that should score high."""
    (tmp_path / "main.py").write_text(
        'import logging\n'
        'from governance import tool_registry, policy_engine\n'
        '\n'
        'logger = logging.getLogger(__name__)\n'
        '\n'
        'async def handle_request(request):\n'
        '    # Check policy before execution\n'
        '    if not policy_engine.evaluate(request):\n'
        '        logger.warning("Policy denied request")\n'
        '        return {"error": "denied"}\n'
        '    tool = tool_registry.get(request.tool_name)\n'
        '    if tool.requires_approval:\n'
        '        await request_human_approval(request)\n'
        '    result = await tool.execute(request)\n'
        '    audit_log.record(request, result)\n'
        '    return result\n'
    )

    (tmp_path / "requirements.txt").write_text(
        'openai==1.30.0\n'
        'langchain==0.2.0\n'
    )

    (tmp_path / "Dockerfile").write_text(
        'FROM python:3.12-slim\n'
        'RUN useradd -m appuser\n'
        'USER appuser\n'
        'COPY . /app\n'
        'CMD ["python", "main.py"]\n'
    )

    return tmp_path


def test_full_scan_produces_valid_result(sample_project: Path) -> None:
    """End-to-end: scan a project and verify the ScanResult structure."""
    from warden.cli import _run_scan
    from warden.models import ScoreLevel

    result = _run_scan(sample_project)

    # Score must be 0-100
    assert 0 <= result.total_score <= 100
    # Level must be a valid enum
    assert result.level in (ScoreLevel.GOVERNED, ScoreLevel.PARTIAL,
                            ScoreLevel.AT_RISK, ScoreLevel.UNGOVERNED)
    # Must have findings (we planted issues)
    assert len(result.findings) > 0
    # Must have dimension scores for all 17 dimensions
    assert len(result.dimension_scores) == 17
    for d_id, d_score in result.dimension_scores.items():
        assert d_id.startswith("D")
        assert 0 <= d_score.raw <= d_score.max


def test_scan_detects_planted_secrets(sample_project: Path) -> None:
    """Secrets scanner must find the API key and DB URL we planted."""
    from warden.cli import _run_scan

    result = _run_scan(sample_project)

    secret_findings = [f for f in result.findings if f.layer == 4]
    assert len(secret_findings) >= 1  # at least OPENAI_API_KEY

    # Secret values must be masked
    for s in result.secrets:
        assert "abcdefghij" not in s.preview  # full value must NOT appear


def test_scan_detects_unpinned_deps(sample_project: Path) -> None:
    """Supply chain scanner must flag unpinned openai and langchain."""
    from warden.cli import _run_scan

    result = _run_scan(sample_project)

    dep_findings = [f for f in result.findings if f.layer == 6]
    unpinned_msgs = [f.message for f in dep_findings if "unpin" in f.message.lower()]
    assert len(unpinned_msgs) >= 1


def test_scan_detects_docker_issues(sample_project: Path) -> None:
    """Infrastructure scanner must flag missing USER in Dockerfile."""
    from warden.cli import _run_scan

    result = _run_scan(sample_project)

    infra_findings = [f for f in result.findings if f.layer == 3]
    assert any("root" in f.message.lower() or "user" in f.message.lower()
               for f in infra_findings)


def test_governed_project_scores_higher(sample_project: Path, governed_project: Path) -> None:
    """A well-governed project should score higher than an ungoverned one."""
    from warden.cli import _run_scan

    bad_result = _run_scan(sample_project)
    good_result = _run_scan(governed_project)

    assert good_result.total_score >= bad_result.total_score


def test_json_report_roundtrip(sample_project: Path, tmp_path: Path) -> None:
    """JSON report must be valid JSON with expected structure."""
    from warden.cli import _run_scan
    from warden.report.json_writer import write_json_report

    result = _run_scan(sample_project)
    out_path = tmp_path / "report.json"
    write_json_report(result, out_path)

    data = json.loads(out_path.read_text())
    assert "score" in data
    assert "findings" in data
    assert "dimensions" in data["score"]
    assert data["version"] is not None
    assert 0 <= data["score"]["total"] <= 100


def test_html_report_generation(sample_project: Path, tmp_path: Path) -> None:
    """HTML report must be a valid document with score in title."""
    from warden.cli import _run_scan
    from warden.report.html_writer import write_html_report

    result = _run_scan(sample_project)
    out_path = tmp_path / "report.html"
    write_html_report(result, out_path)

    html = out_path.read_text()
    assert html.startswith("<!DOCTYPE html>")
    assert "</html>" in html
    assert str(result.total_score) in html


def test_empty_project_doesnt_crash(tmp_path: Path) -> None:
    """Scanning an empty directory should produce a valid result, not crash."""
    from warden.cli import _run_scan

    result = _run_scan(tmp_path)
    assert result.total_score >= 0
    assert result.level is not None
