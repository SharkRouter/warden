"""Tests for warden.config.load_config and related helpers."""

from __future__ import annotations

from pathlib import Path

from warden.config import load_config, normalize_list_option


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_load_warden_toml_at_root(tmp_path: Path) -> None:
    _write(
        tmp_path / ".warden.toml",
        """
format = "json"
output_dir = "reports"
skip = ["secrets", "deps"]
min_score = 75
ci = true
""".strip(),
    )
    cfg, source = load_config(tmp_path)
    assert source == tmp_path / ".warden.toml"
    assert cfg["format"] == "json"
    assert cfg["output_dir"] == "reports"
    assert cfg["skip"] == ["secrets", "deps"]
    assert cfg["min_score"] == 75
    assert cfg["ci"] is True


def test_pyproject_tool_warden_fallback(tmp_path: Path) -> None:
    _write(
        tmp_path / "pyproject.toml",
        """
[project]
name = "demo"

[tool.warden]
format = "sarif"
only = ["code", "mcp"]
""".strip(),
    )
    cfg, source = load_config(tmp_path)
    assert source == tmp_path / "pyproject.toml"
    assert cfg == {"format": "sarif", "only": ["code", "mcp"]}


def test_warden_toml_wins_over_pyproject(tmp_path: Path) -> None:
    _write(
        tmp_path / "pyproject.toml",
        """
[tool.warden]
format = "html"
""".strip(),
    )
    _write(tmp_path / ".warden.toml", 'format = "json"\n')
    cfg, source = load_config(tmp_path)
    assert source == tmp_path / ".warden.toml"
    assert cfg["format"] == "json"


def test_unknown_keys_are_dropped(tmp_path: Path, capsys) -> None:
    _write(
        tmp_path / ".warden.toml",
        """
format = "json"
nonsense = true
bogus = "x"
""".strip(),
    )
    cfg, _ = load_config(tmp_path)
    assert cfg == {"format": "json"}
    err = capsys.readouterr().err
    assert "nonsense" in err and "bogus" in err


def test_walks_up_to_find_config(tmp_path: Path) -> None:
    _write(tmp_path / ".warden.toml", 'format = "html"\n')
    nested = tmp_path / "pkg" / "sub"
    nested.mkdir(parents=True)
    cfg, source = load_config(nested)
    assert source == tmp_path / ".warden.toml"
    assert cfg["format"] == "html"


def test_stops_at_vcs_root(tmp_path: Path) -> None:
    # .warden.toml lives ABOVE a git root — should NOT be picked up from inside repo
    _write(tmp_path / ".warden.toml", 'format = "html"\n')
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    scan_dir = repo / "src"
    scan_dir.mkdir()
    cfg, source = load_config(scan_dir)
    assert cfg == {}
    assert source is None


def test_no_config_returns_empty(tmp_path: Path) -> None:
    cfg, source = load_config(tmp_path)
    assert cfg == {}
    assert source is None


def test_malformed_toml_is_reported(tmp_path: Path, capsys) -> None:
    _write(tmp_path / ".warden.toml", "format = [unterminated")
    cfg, source = load_config(tmp_path)
    assert cfg == {}
    assert source == tmp_path / ".warden.toml"
    err = capsys.readouterr().err
    assert "failed to read" in err


def test_pyproject_without_tool_warden_section(tmp_path: Path) -> None:
    _write(
        tmp_path / "pyproject.toml",
        """
[project]
name = "demo"
""".strip(),
    )
    cfg, source = load_config(tmp_path)
    assert cfg == {}
    assert source == tmp_path / "pyproject.toml"


def test_normalize_list_option_list() -> None:
    assert normalize_list_option(["code", "mcp"]) == "code,mcp"
    assert normalize_list_option([" code ", "", "mcp "]) == "code,mcp"
    assert normalize_list_option([]) is None


def test_normalize_list_option_string() -> None:
    assert normalize_list_option("code,mcp") == "code,mcp"
    assert normalize_list_option("  ") is None
    assert normalize_list_option(None) is None
