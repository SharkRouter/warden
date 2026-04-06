"""Tests for Layer 1: Code pattern analysis."""

import tempfile
from pathlib import Path

from warden.scanner.code_analyzer import scan_code


def _scan_source(source: str) -> list:
    """Helper: write source to temp file and scan it."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "agent.py"
        test_file.write_text(source)
        findings, _ = scan_code(Path(tmpdir))
        return findings


def test_unprotected_llm_call():
    source = '''
import openai
client = openai.ChatCompletion.create(model="gpt-4", messages=[])
'''
    findings = _scan_source(source)
    assert any("governance proxy" in f.message for f in findings)


def test_protected_llm_call_no_finding():
    source = '''
import openai
client = openai.ChatCompletion.create(model="gpt-4", messages=[], base_url="https://proxy.example.com")
'''
    findings = _scan_source(source)
    assert not any("governance proxy" in f.message for f in findings)


def test_agent_loop_no_exit():
    source = '''
while True:
    response = client.chat.completions.create(messages=messages)
    messages.append(response)
'''
    findings = _scan_source(source)
    assert any("exit condition" in f.message for f in findings)


def test_agent_loop_with_break_ok():
    source = '''
while True:
    response = client.chat.completions.create(messages=messages)
    if response.done:
        break
'''
    findings = _scan_source(source)
    assert not any("exit condition" in f.message for f in findings)


def test_empty_except():
    source = '''
try:
    result = do_something()
except:
    pass
'''
    findings = _scan_source(source)
    assert any("exception handler" in f.message.lower() for f in findings)


def test_hardcoded_model():
    source = '''
model = "gpt-4"
'''
    findings = _scan_source(source)
    assert any("Hardcoded model" in f.message for f in findings)


def test_print_instead_of_logging():
    source = '''
print("Processing request...")
'''
    findings = _scan_source(source)
    assert any("print()" in f.message for f in findings)


def test_clean_code_minimal_findings():
    source = '''
import logging
logger = logging.getLogger(__name__)

def process(data):
    logger.info("Processing data")
    return data
'''
    findings = _scan_source(source)
    # Clean code should have minimal findings
    critical = [f for f in findings if f.severity.value == "CRITICAL"]
    assert len(critical) == 0
