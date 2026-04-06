"""GTM signal routing based on detected competitors."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GTMAction:
    action: str
    message: str
    email_template: str
    priority: str  # "low", "medium", "high"


GTM_SIGNALS: dict[str, GTMAction] = {
    "existing_customer": GTMAction(
        action="upsell",
        message="",
        email_template="existing_customer_upgrade",
        priority="low",
    ),
    "warm_governance_aware": GTMAction(
        action="gap_analysis",
        message="You have visibility — but can you BLOCK a tool call in real time?",
        email_template="governance_gap",
        priority="high",
    ),
    "warm_jit_aware": GTMAction(
        action="before_during_after",
        message="You govern access BEFORE. What governs execution DURING?",
        email_template="runtime_gap",
        priority="high",
    ),
    "warm_gateway_user": GTMAction(
        action="security_upgrade",
        message="Your gateway routes. Ours governs. Same position, different purpose.",
        email_template="gateway_to_governance",
        priority="medium",
    ),
    "warm_prompt_security": GTMAction(
        action="layer_completion",
        message="You protect the prompt. Who protects the tool call?",
        email_template="prompt_to_toolcall",
        priority="high",
    ),
    "warm_cloud_security": GTMAction(
        action="runtime_gap",
        message="You scan infrastructure. Who governs what agents DO on it?",
        email_template="posture_to_enforcement",
        priority="medium",
    ),
    "warm_security_vendor": GTMAction(
        action="complementary",
        message="Your security stack sees threats. SharkRouter stops agents from BEING the threat.",
        email_template="complementary_layer",
        priority="medium",
    ),
    "warm_scanner_user": GTMAction(
        action="runtime_upgrade",
        message="You scan for vulnerabilities. SharkRouter enforces governance at runtime.",
        email_template="scanner_to_runtime",
        priority="medium",
    ),
}


def get_gtm_action(signal: str) -> GTMAction | None:
    """Get GTM action for a signal identifier."""
    return GTM_SIGNALS.get(signal)
