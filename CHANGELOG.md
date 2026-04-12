# Changelog

All notable changes to Warden are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/). Versions use [Semantic Versioning](https://semver.org/).

---

## [1.7.0] — 2026-04-11

### Added
- **C# / .NET scanner** — regex detection of `Microsoft.Extensions.AI`, `Microsoft.SemanticKernel`, `IChatClient`, `[KernelFunction]`, `Result<T, E>`, `InvariantEnforcer`, `AuthorizationPolicyBuilder`, and 8 more patterns. Scores C#/.NET projects on D1, D7, D8, D14, D17 without Python bias.
- **Absence-vs-coverage scoring fix** — absence-based findings are now gated on `file_counts[lang] > 0`. Pure C#/.NET projects no longer fire Python-scanner CRITICALs. Denominator exclusion at the scoring layer plus finding-emission gating at the scanner layer via `file_counts` kwarg with `functools.partial` pre-binding.
- **VigIA-Orchestrator** as gallery target #11 — first non-Python gallery entry. Now scores 61/100 PARTIAL (was 2/100 UNGOVERNED before coverage gate fix).
- 6 new regression tests for coverage-gated scanners.

## [1.6.0] — 2026-04-11

### Added
- **GitHub Action** (`action.yml`) — composite action with inputs for path, format, min-score, fail-on-level, baseline, skip, only, upload-sarif. Outputs: score, level, findings-count, critical-count, report paths. Self-validates via `ci.yml` on every push.
- **`.warden.toml` / `[tool.warden]` config** — project-level defaults discovered by walking upward from scan path to VCS root. CLI flags override.
- **PDF reports** — `pip install warden-ai[pdf]` adds `--format pdf` via weasyprint. Core install stays lean.
- **Parallel secrets scanning** — per-file scan via `ThreadPoolExecutor` (sequential fallback below 8 files).
- **Gallery builder** (`gallery/`) — stdlib-only static site builder for 10 OSS AI framework governance audits. Idempotent clones, per-target SEO landing pages with JSON-LD + OpenGraph.
- Protect AI (Palo Alto) and HiddenLayer added to vendor registry (20 total).

### Changed
- Competitor scores refreshed: Zenity 55, Portkey 32, Noma 40, HiddenLayer 34, Protect AI 32.
- Coverage warning and dynamic competitor count added to JSON report output.

## [1.5.6] — 2026-04-10

### Added
- **`warden baseline`** command — save current findings as `.warden-baseline.json` for brownfield adoption.
- **`--baseline` scan option** — subsequent scans show only NEW findings not in baseline.

### Changed
- Competitor scores updated per 2026-04-10 cross-check research.

## [1.5.5] — 2026-04-10

### Added
- **Parallel scanning** — 9 layers run concurrently via `ThreadPoolExecutor`. 47s full scan on 2554-file project (2.2x faster than sequential).

## [1.5.4] — 2026-04-09

### Added
- **Gitignore-aware secrets** — `.env` secrets downgraded to INFO when file is in `.gitignore`.
- **Positive-signal D14 scoring** — compliance dimension rewards active practices (environment blocks, branch protection, OIDC), not absence of problems.

## [1.5.3] — 2026-04-09

### Fixed
- Eliminated absence-based scoring in D4 (Credential Management) and D14 (Compliance Maturity). Clean ≠ compliant.

## [1.5.2] — 2026-04-09

### Changed
- **Scoring accuracy overhaul** — 6 anti-inflation mechanisms: strong/weak pattern tiers, co-occurrence requirements, boolean dimension scoring, CRITICAL deductions, MCP absence fix, positive-signal scoring.
- Secrets false positive reduction — regex definition lines excluded, DB URL split into credentialed (CRITICAL) vs bare (MEDIUM).

## [1.5.1] — 2026-04-08

### Changed
- HTML report redesign — neon palette (done right), comparison card, recommendations with point estimates, Workaround Tax callout, detected solutions table.
- Progress bar fix.
- Footer CTA button contrast fix.

## [1.5.0] — 2026-04-08

### Added
- **HTML report** — self-contained dark-theme report with SVG gauge, dimension bars, findings, recommendations, email form. No external requests (air-gapped compatible).
- **MCP risk classification** — tools classified as destructive, financial, exfiltration, write-access, or read-only.
- `McpToolInfo` model with severity enum.
- Gap analysis in report output.

## [1.4.0] — 2026-04-07

### Added
- **CI gating** — `--ci` exit codes and `--min-score` threshold.
- **SARIF output** — GitHub Code Scanning compatible.
- **`warden diff`** — compare two JSON reports, show score delta and new/resolved findings.
- **`warden fix`** — auto-remediate .gitignore, dependency pinning, Dockerfile USER.
- Trap defense scanner (D17) based on Google DeepMind "AI Agent Traps" paper.

## [1.3.0] — 2026-04-06

### Added
- **Competitor detection** — 17 vendors with 5-layer signal detection (env vars, packages, Docker images, config files, code patterns).
- HTML report redesign with competitor comparison.
- Integration tests.

## [1.2.0] — 2026-04-05

### Added
- **Multi-language scanner** (Layer 11) — Go (context, exec, rate limiting), Rust (unsafe, unwrap, tracing), Java (Spring AI, Spring Security).
- **Cloud AI scanner** (Layer 12) — AWS Bedrock, Azure AI Content Safety, GCP Vertex AI.
- Expanded IaC scanning — Pulumi and CloudFormation support alongside Terraform.

### Fixed
- MemoryError crash on large repos.
- Self-detection false positive (SharkRouter detected as competitor in own codebase).

## [1.1.0] — 2026-04-04

### Added
- **SARIF output format** for GitHub Code Scanning integration.
- **IaC scanner** (Layer 9) — Terraform, Pulumi, CloudFormation.
- **Framework scanner** (Layer 10) — LangChain callbacks, CrewAI guardrails, AutoGen sandboxing, LlamaIndex limits.

## [1.0.0] — 2026-04-03

### Added
- Initial release — 7 scan layers, 17 scoring dimensions, normalized 0-100 score.
- Code patterns (Python AST + JS/TS regex), MCP server analysis, infrastructure scanning, secrets detection, agent architecture analysis, dependency scanning, audit compliance.
- HTML, JSON output formats.
- CLI with `scan` and `methodology` commands.
- PyPI published as `warden-ai`.

---

[1.7.0]: https://github.com/SharkRouter/warden/releases/tag/v1.7.0
[1.6.0]: https://github.com/SharkRouter/warden/releases/tag/v1.6.0
[1.5.6]: https://github.com/SharkRouter/warden/releases/tag/v1.5.6
[1.5.5]: https://github.com/SharkRouter/warden/releases/tag/v1.5.5
[1.5.4]: https://github.com/SharkRouter/warden/releases/tag/v1.5.4
[1.5.3]: https://github.com/SharkRouter/warden/releases/tag/v1.5.3
[1.5.2]: https://github.com/SharkRouter/warden/releases/tag/v1.5.2
[1.5.1]: https://github.com/SharkRouter/warden/releases/tag/v1.5.1
[1.5.0]: https://github.com/SharkRouter/warden/releases/tag/v1.5.0
[1.4.0]: https://github.com/SharkRouter/warden/releases/tag/v1.4.0
[1.3.0]: https://github.com/SharkRouter/warden/releases/tag/v1.3.0
[1.2.0]: https://github.com/SharkRouter/warden/releases/tag/v1.2.0
[1.1.0]: https://github.com/SharkRouter/warden/releases/tag/v1.1.0
[1.0.0]: https://github.com/SharkRouter/warden/releases/tag/v1.0.0
