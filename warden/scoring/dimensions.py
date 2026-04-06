"""17 governance dimensions with weights and max values.

Total raw: 235 points across 4 groups.
Normalized to /100.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Dimension:
    id: str
    name: str
    group: str
    max_score: int
    description: str


# Group 1: Core Governance (100 pts)
D1 = Dimension("D1", "Tool Inventory", "Core Governance", 25,
               "MCP tool discovery, live catalog, schema completeness, auto-discovery")
D2 = Dimension("D2", "Risk Detection", "Core Governance", 20,
               "Risk classification, semantic analysis, intent-parameter consistency")
D3 = Dimension("D3", "Policy Coverage", "Core Governance", 20,
               "Policy engine, allow/deny/audit modes, signed policies, deny-by-default")
D4 = Dimension("D4", "Credential Management", "Core Governance", 20,
               "Env var exposure, secrets manager, key rotation, NHI credential lifecycle")
D5 = Dimension("D5", "Log Hygiene", "Core Governance", 10,
               "PII in logs, WORM/immutable storage, hash chain integrity, retention policy")
D6 = Dimension("D6", "Framework Coverage", "Core Governance", 5,
               "LangChain/AutoGen/CrewAI/custom framework detection")

# Group 2: Advanced Controls (50 pts)
D7 = Dimension("D7", "Human-in-the-Loop", "Advanced Controls", 15,
               "Approval gates, dry-run preview, plan-execute separation")
D8 = Dimension("D8", "Agent Identity", "Advanced Controls", 15,
               "Agent registry, identity tokens, delegation chains, lifecycle states")
D9 = Dimension("D9", "Threat Detection", "Advanced Controls", 20,
               "Behavioral baselines, anomaly detection, cross-session tracking, kill switch")

# Group 3: Ecosystem (55 pts)
D10 = Dimension("D10", "Prompt Security", "Ecosystem", 15,
                "Prompt injection detection, jailbreak prevention, content filtering")
D11 = Dimension("D11", "Cloud / Platform", "Ecosystem", 10,
                "Multi-cloud, marketplace, SSO/IdP, SIEM integration")
D12 = Dimension("D12", "LLM Observability", "Ecosystem", 10,
                "Cost tracking, latency monitoring, model analytics")
D13 = Dimension("D13", "Data Recovery", "Ecosystem", 10,
                "Rollback, undo, point-in-time recovery for agent actions")
D14 = Dimension("D14", "Compliance Maturity", "Ecosystem", 10,
                "SOC2/ISO evidence, compliance reports, regulatory mapping")

# Group 4: Unique Capabilities (30 pts)
D15 = Dimension("D15", "Post-Exec Verification", "Unique Capabilities", 10,
                "Result validation, PASS/FAIL verdicts, failure fingerprinting")
D16 = Dimension("D16", "Data Flow Governance", "Unique Capabilities", 10,
                "Taint labels, data classification, cross-tool leakage prevention")
D17 = Dimension("D17", "Adversarial Resilience", "Unique Capabilities", 10,
                "Trap defense + adversarial testing (DeepMind AI Agent Traps)")


ALL_DIMENSIONS: list[Dimension] = [
    D1, D2, D3, D4, D5, D6,
    D7, D8, D9,
    D10, D11, D12, D13, D14,
    D15, D16, D17,
]

DIMENSIONS_BY_ID: dict[str, Dimension] = {d.id: d for d in ALL_DIMENSIONS}

TOTAL_RAW_MAX: int = sum(d.max_score for d in ALL_DIMENSIONS)  # 235

GROUPS = {
    "Core Governance": [D1, D2, D3, D4, D5, D6],
    "Advanced Controls": [D7, D8, D9],
    "Ecosystem": [D10, D11, D12, D13, D14],
    "Unique Capabilities": [D15, D16, D17],
}

# Sanity check
assert TOTAL_RAW_MAX == 235, f"Expected 235, got {TOTAL_RAW_MAX}"
assert len(ALL_DIMENSIONS) == 17, f"Expected 17 dimensions, got {len(ALL_DIMENSIONS)}"
