# Warden Scoring Methodology v4.2

Warden evaluates AI agent governance posture across **17 dimensions**, grouped into 4 categories. Raw scores (out of 235) are normalized to a 0-100 scale.

## Score Levels

| Score | Level | Meaning |
|-------|-------|---------|
| >= 80 | **GOVERNED** | Comprehensive agent governance in place |
| >= 60 | **PARTIAL** | Significant coverage with material gaps |
| >= 33 | **AT_RISK** | Some controls exist but major blind spots |
| < 33 | **UNGOVERNED** | Minimal or no agent governance |

## Dimensions

### Core Governance (100 pts)

| ID | Dimension | Max | What Warden Checks |
|----|-----------|-----|---------------------|
| D1 | Tool Inventory | 25 | MCP configs, tool registries, schema definitions |
| D2 | Risk Detection | 20 | Semantic analysis, risk scoring, intent classification |
| D3 | Policy Coverage | 20 | Policy engines, allowlists/denylists, guard chains |
| D4 | Credential Management | 20 | Secrets in code, key rotation, vault usage, TLS |
| D5 | Log Hygiene | 10 | Structured logging, audit trails, hash chains |
| D6 | Framework Coverage | 5 | Detection of LangChain, AutoGen, CrewAI, LlamaIndex, etc. |

### Advanced Controls (50 pts)

| ID | Dimension | Max | What Warden Checks |
|----|-----------|-----|---------------------|
| D7 | Human-in-the-Loop | 15 | Approval gates, dry-run modes, confirmation flows |
| D8 | Agent Identity | 15 | Agent registries, identity tokens, delegation chains |
| D9 | Threat Detection | 20 | Circuit breakers, anomaly detection, kill switches, rate limiting |

### Ecosystem (55 pts)

| ID | Dimension | Max | What Warden Checks |
|----|-----------|-----|---------------------|
| D10 | Prompt Security | 15 | Injection detection, content filtering, input sanitization |
| D11 | Cloud / Platform | 10 | SSO/SAML/OIDC, RBAC, multi-tenant isolation |
| D12 | LLM Observability | 10 | Cost tracking, token usage, model analytics |
| D13 | Data Recovery | 10 | Rollback, snapshots, backup, restore capabilities |
| D14 | Compliance Maturity | 10 | Dependency hygiene, regulatory mapping, evidence collection |

### Unique Capabilities (30 pts)

| ID | Dimension | Max | What Warden Checks |
|----|-----------|-----|---------------------|
| D15 | Post-Exec Verification | 10 | Result validation, fingerprinting, output assurance |
| D16 | Data Flow Governance | 10 | PII detection, DLP, taint tracking, sensitivity labels |
| D17 | Adversarial Resilience | 10 | Trap defense (6 types), red team testing, canary tokens |

## 7 Scan Layers

1. **Code Patterns** -- AST analysis of Python, regex scanning of JS/TS
2. **MCP Servers** -- Configuration file analysis for auth, schemas, transport security
3. **Infrastructure** -- Dockerfile, docker-compose, Kubernetes manifest checks
4. **Secrets** -- High-entropy string detection, known API key patterns, .env files
5. **Agent Architecture** -- Agent class analysis for permissions, lifecycle, cost tracking
6. **Supply Chain** -- Dependency pinning, typosquat detection (Levenshtein), cloud PII services
7. **Audit & Compliance** -- Audit logging patterns, compliance framework references

Plus a dedicated **D17 Adversarial Resilience** scanner checking 8 sub-dimensions (4 defense + 4 testing).

## Principles

1. **Local-only, privacy-first** -- No data leaves the machine. Zero network calls.
2. **Conservative scoring** -- Undetected = 0, not "unknown". No credit without evidence.
3. **Balanced methodology** -- Fair credit to all tool categories, not biased toward any vendor.
4. **Transparent and correctable** -- Full methodology published. Vendor corrections welcome.
5. **Research-backed severity** -- D17 cites Google DeepMind "AI Agent Traps" (March 2026) attack success rates.
6. **Compliance-mapped** -- Findings map to EU AI Act articles, OWASP LLM Top 10, and MITRE ATLAS.

## False Positive Mitigation

- Test files use reduced detector sets (critical-only)
- Frontend/UI files excluded from backend-focused checks
- Lockfiles and generated files skipped for secrets scanning
- Typosquat detection uses edit distance = 1 (not fuzzy matching)

## Vendor Corrections

If you believe your tool is scored incorrectly, open an issue with:
1. Which dimension(s) are affected
2. Evidence of the capability (docs, code, config examples)
3. Suggested score adjustment with justification

We commit to reviewing and responding within 5 business days.
