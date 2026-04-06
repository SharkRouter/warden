# Warden — AI Agent Governance Scanner

Open-source, local-only CLI scanner that evaluates AI agent governance posture. Scans filesystems, environment variables, running processes, MCP configs, Docker containers, and code patterns. **No data leaves the machine.**

## Quick Start

```bash
pip install -e .
warden scan /path/to/your-agent-project
```

## What It Does

Warden scores your AI agent project across **17 governance dimensions** (out of 235 raw, normalized to /100):

| Group | Dimensions |
|-------|-----------|
| **Core Governance** (100 pts) | Tool Inventory, Risk Detection, Policy Coverage, Credential Management, Log Hygiene, Framework Coverage |
| **Advanced Controls** (50 pts) | Human-in-the-Loop, Agent Identity, Threat Detection |
| **Ecosystem** (55 pts) | Prompt Security, Cloud/Platform, LLM Observability, Data Recovery, Compliance Maturity |
| **Unique Capabilities** (30 pts) | Post-Exec Verification, Data Flow Governance, Adversarial Resilience |

### Score Levels

| Score | Level | Meaning |
|-------|-------|---------|
| >= 80 | **GOVERNED** | Comprehensive agent governance in place |
| >= 60 | **PARTIAL** | Significant coverage with material gaps |
| >= 33 | **AT_RISK** | Some controls exist but major blind spots |
| < 33 | **UNGOVERNED** | Minimal or no agent governance |

## 7 Scan Layers

1. **Code Patterns** — AST-based Python/JS/TS analysis (unprotected LLM calls, agent loops without exit conditions, unrestricted tool access)
2. **MCP Servers** — MCP config file analysis (write tools without auth, missing schemas, non-TLS transport)
3. **Infrastructure** — Dockerfile, docker-compose, K8s manifests (root containers, exposed secrets, missing healthchecks)
4. **Secrets** — 15+ credential patterns with value masking (OpenAI, Anthropic, AWS, GitHub, Stripe, etc.)
5. **Agent Architecture** — Agent class analysis (no permissions, no cost tracking, unlimited sub-agent spawning)
6. **Supply Chain** — Dependency analysis (unpinned AI packages, typosquat detection, cloud PII services)
7. **Audit & Compliance** — Audit logging, structured logging, retention policies, compliance framework mapping

Plus **D17: Adversarial Resilience** — 8 sub-checks based on Google DeepMind's "AI Agent Traps" paper (Franklin et al., March 2026).

## Competitor Detection

Warden detects **17 governance and security tools** across 5 signal layers (env vars, processes, MCP configs, packages, Docker containers). Detection requires 2+ signals from different layers to prevent false positives.

## Output

```bash
# Scan current directory, generate all reports
warden scan .

# JSON only
warden scan /path/to/project --format json

# HTML only
warden scan /path/to/project --format html

# Custom output directory
warden scan /path/to/project --output-dir /path/to/reports
```

Outputs:
- **CLI summary** — colorized terminal output with score, findings, and D17 warning
- **warden_report.html** — self-contained HTML report (no external requests, works air-gapped)
- **warden_report.json** — machine-readable with `scoring_version` field

## Example Output

```
  ____    __              __   ___            __
 / __/__ / /  ___ _____  / /__/ _ \___  __ __/ /____  ____
_\ \/ _ \/ _ \/ _ `/ __/_/  '_/ , _/ _ \/ // / __/ -_)/ __/
/___/_//_/_//_/\_,_/_/ /_/\_\/_/|_|\___/\_,_/\__/\__/_/

Warden v1.0.0 -- AI Agent Governance Scanner
Scanning: /home/user/my-agent-project
--------------------------------------------

  Layer 1: Code Patterns ...... 12 findings
  Layer 2: MCP Servers ........ 3 findings
  Layer 3: Infrastructure ..... 5 findings
  Layer 4: Secrets ............ 2 findings (2 CRITICAL)
  Layer 5: Agent Architecture . 4 findings
  Layer 6: Supply Chain ....... 1 finding
  Layer 7: Audit & Compliance . 6 findings

  Governance tools detected: Pangea (CrowdStrike)
  Competitors in registry: 17
--------------------------------------------
  GOVERNANCE SCORE: 19 / 100 -- UNGOVERNED

  WARNING: Your environment is exposed to 6 trap types with
    documented 80%+ attack success rates.
    (Franklin, Tomasev, Jacobs, Leibo, Osindero.
     "AI Agent Traps." Google DeepMind, March 2026)
--------------------------------------------
```

## Architecture Constraints

1. **Zero network access** — Scanners never import httpx/requests/urllib. CI-enforced.
2. **Zero SharkRouter imports** — Standalone package with no internal dependencies. CI-enforced.
3. **Secrets never stored** — Only file, line number, pattern name, and masked preview (first 3 + last 4 chars).
4. **HTML report self-contained** — No CDN, no Google Fonts, no external requests. Works in air-gapped environments.

## Development

```bash
# Create venv and install
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Security tests (CI-enforced)
pytest tests/test_security/ -v
```

## Test Suite

94 tests covering:
- Scoring model (17 dimensions, normalization math, all 4 score levels)
- All 7 scan layers with fixture-based tests
- D17 trap defense (env var detection, code pattern detection, full defense max score)
- Competitor detection (confidence levels, multi-signal detection)
- JSON/HTML report generation
- **Security tests**: no network imports, no SharkRouter imports, secrets masking, HTML self-contained

## License

MIT

## Research Citation

Adversarial resilience dimension (D17) cites:

> Franklin, Tomasev, Jacobs, Leibo, Osindero. "AI Agent Traps." Google DeepMind, March 2026.

Every D17 finding maps to EU AI Act articles, OWASP LLM Top 10, and MITRE ATLAS techniques.
