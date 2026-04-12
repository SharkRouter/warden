# Contributing to Warden

Warden is an open-source AI agent governance scanner. Contributions are welcome — bug reports, feature requests, documentation improvements, and code changes.

## Reporting Issues

- **Bug reports:** Open an issue at [github.com/SharkRouter/warden/issues](https://github.com/SharkRouter/warden/issues) with steps to reproduce, expected vs actual behavior, and your Python version / OS.
- **Security vulnerabilities:** Email [security@sharkrouter.ai](mailto:security@sharkrouter.ai) — do not open a public issue for security bugs.
- **Feature requests:** Open an issue with the `enhancement` label. Describe the use case, not just the feature.
- **Scoring methodology feedback:** We welcome challenges to dimension weights, pattern classifications, and scoring logic. Open an issue or a PR — the scoring model is transparent and versioned.

## Development Setup

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Setup

```bash
# Clone
git clone https://github.com/SharkRouter/warden.git
cd warden

# With uv (recommended)
uv sync --extra dev
uv run pytest tests/ -v

# With pip
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
# .venv\Scripts\activate       # Windows
pip install -e ".[dev]"
pytest tests/ -v
```

### Running Tests

```bash
# All tests (with 30s timeout per test)
pytest tests/ -v

# Specific test directory
pytest tests/test_scanner/ -v
pytest tests/test_scoring/ -v
pytest tests/test_security/ -v

# Single test file
pytest tests/test_scanner/test_multilang_csharp.py -v
```

All tests must pass before submitting a PR. Current suite: **142 tests** across 7 test directories.

### Linting

```bash
# Check
ruff check warden/ tests/

# Auto-fix
ruff check --fix warden/ tests/

# Import sorting
ruff check --select I --fix warden/ tests/
```

Ruff is configured in `pyproject.toml`: Python 3.10 target, 120-char line length, E/F/W/I rules enabled.

## Architecture Constraints

These constraints are enforced by CI tests. PRs that violate them will not pass:

1. **Zero network access** — scanners never import `httpx`, `requests`, or `urllib`. Warden is local-only forever.
2. **Zero SharkRouter imports** — Warden is a standalone package with no internal dependencies.
3. **Secrets never stored** — only file path, line number, pattern name, and masked preview (first 3 + last 4 chars).
4. **HTML report self-contained** — no CDN links, no Google Fonts, no external requests. Must work air-gapped.
5. **2 runtime dependencies** — `click` and `rich`. Everything else is optional extras or dev-only.

## Pull Request Guidelines

### Before Submitting

- [ ] All tests pass (`pytest tests/ -v`)
- [ ] Linting is clean (`ruff check warden/ tests/`)
- [ ] New scanner patterns have tests
- [ ] New findings include `remediation` text
- [ ] SCORING.md updated if scoring logic changed
- [ ] CHANGELOG.md updated with your changes

### Commit Messages

Use conventional commit format:

```
feat(scanner): add Kotlin governance patterns
fix(scoring): correct D14 co-occurrence threshold
docs: update README with new CLI flag
test: add regression test for MCP auth detection
perf: parallelize IaC file reading
chore: bump version to 1.8.0
```

### Adding a New Scanner Pattern

1. Add the regex/AST pattern to the relevant scanner in `warden/scanner/`
2. Map it to the correct dimension(s) in the scanner's `_scan()` method
3. Include a `remediation` string in any findings generated
4. Add test cases in `tests/test_scanner/` covering both positive match and no-match scenarios
5. If adding a new language, update the `file_counts` tracking in `cli.py`

### Adding a Competitor to the Registry

1. Edit `warden/scanner/competitors.py`
2. Provide: `display_name`, `category`, `warden_score` (estimated), `strengths`, `weaknesses`, and at least 2 detection signals from different layers
3. Include a rationale comment for the `warden_score` estimate
4. Add a test in `tests/test_competitors/`

### Scoring Changes

Scoring methodology changes are high-impact. If your PR modifies `warden/scoring/`:

1. Document the rationale in the PR description
2. Show before/after scores on at least 2 real projects
3. Update `SCORING.md` with the new methodology version
4. Update `__scoring_model__` in `warden/__init__.py`

## Code Style

- Python 3.10+ (no walrus operator unless it significantly improves readability)
- Type hints encouraged but not required
- Docstrings for public functions
- `_private_name` convention for internal helpers
- Constants as `UPPER_SNAKE_CASE`
- No star imports

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
