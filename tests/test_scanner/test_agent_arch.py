"""Tests for Layer 5: Agent architecture scanner."""

import tempfile
from pathlib import Path

from warden.scanner.agent_arch_scanner import scan_agent_arch


def test_no_agents_no_findings():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "main.py").write_text("print('hello')\n")
        findings, _ = scan_agent_arch(Path(tmpdir))
        assert len(findings) == 0


def test_agent_no_permissions():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "agent.py").write_text("""
class MyAgent:
    def run(self):
        pass
""")
        findings, _ = scan_agent_arch(Path(tmpdir))
        perm_findings = [f for f in findings if "permission" in f.message.lower()]
        assert len(perm_findings) >= 1


def test_agent_no_cost_tracking():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "agent.py").write_text("""
class TaskAgent:
    def execute(self):
        pass
""")
        findings, _ = scan_agent_arch(Path(tmpdir))
        cost_findings = [f for f in findings if "cost" in f.message.lower()]
        assert len(cost_findings) >= 1


def test_agent_no_lifecycle():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "agent.py").write_text("""
class WorkerAgent:
    def process(self):
        pass
""")
        findings, _ = scan_agent_arch(Path(tmpdir))
        lifecycle_findings = [f for f in findings if "lifecycle" in f.message.lower()]
        assert len(lifecycle_findings) >= 1


def test_unrestricted_tool_access():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "agent.py").write_text("""
tools = all_tools
agent = Agent(tools=all_tools)
""")
        findings, _ = scan_agent_arch(Path(tmpdir))
        # Should detect unrestricted access via regex
        tool_findings = [f for f in findings if "unrestricted" in f.message.lower() or "ALL tools" in f.message]
        assert len(tool_findings) >= 1
