"""
Prompt Shield for MediVault Medical AI Safety Guardrails.

Detects and neutralizes prompt injection, jailbreaks, role reversal attacks,
and adversarial bypasses targeting clinical safety rules.
"""
import re
from typing import List, Tuple
from medivault_guardrails.schemas.guardrail_schema import (
    PromptShieldResult,
    RiskCategory,
    RiskLevel,
    STANDARD_SAFETY_RESPONSE,
)

class MedicalPromptShield:
    """
    Shields LLM prompts from adversarial attacks, role manipulation,
    and prompt injection attempts to bypass clinical constraints.
    """

    JAILBREAK_PATTERNS = [
        r"(?:ignore|disregard|forget|bypass)\s+(?:all\s+)?(?:previous\s+|prior\s+|medical\s+|clinical\s+)*(?:instructions?|rules?|guidelines?|safety|guardrails?|filters?)",
        r"(?:you\s+are\s+now|pretend\s+to\s+be|act\s+as)\s+(?:an?\s+)?(?:unrestricted|uncensored|jailbroken|evil|dan|doctor\s+gpt)",
        r"(?:dan\s+mode|developer\s+mode|god\s+mode|override\s+mode)",
        r"(?:system\s+prompt|show\s+me\s+your\s+hidden\s+prompt|reveal\s+instructions)",
        r"(?:for\s+hypothetical\s+purposes\s+only|in\s+a\s+fictional\s+setting|roleplay\s+as\s+a\s+doctor\s+diagnosing)",
        r"(?:do\s+not\s+say\s+['\"]This\s+information\s+is\s+educational['\"])",
        r"(?:answer\s+without\s+any\s+medical\s+disclaimer)",
    ]

    SUSPICIOUS_OBFUSCATION_PATTERNS = [
        r"(?:base64\s+decode|rot13|hex\s+decode)",
        r"(?:[\u200B-\u200D\uFEFF])", # Zero-width characters
    ]

    def __init__(self):
        self._compiled_jailbreak = [re.compile(p, re.IGNORECASE) for p in self.JAILBREAK_PATTERNS]
        self._compiled_obfuscation = [re.compile(p, re.IGNORECASE) for p in self.SUSPICIOUS_OBFUSCATION_PATTERNS]

    def inspect(self, prompt: str) -> PromptShieldResult:
        """
        Inspects a user prompt for jailbreak and injection risks.
        """
        cleaned = prompt.strip()
        triggered: List[str] = []

        # 1. Obfuscation detection
        for pat in self._compiled_obfuscation:
            m = pat.search(cleaned)
            if m:
                triggered.append(f"Obfuscation match: {m.group(0)}")

        # 2. Jailbreak and bypass patterns
        for pat in self._compiled_jailbreak:
            m = pat.search(cleaned)
            if m:
                triggered.append(f"Adversarial match: {m.group(0)}")

        if triggered:
            return PromptShieldResult(
                is_safe=False,
                risk_category=RiskCategory.ADVERSARIAL_INJECTION,
                risk_level=RiskLevel.HIGH,
                confidence=0.98,
                triggered_rules=triggered,
                reason="Prompt contains adversarial instructions or injection attempts to bypass clinical guardrails.",
                sanitized_prompt=None,
            )

        # Remove any harmful formatting or control codes
        sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", cleaned)

        return PromptShieldResult(
            is_safe=True,
            risk_category=RiskCategory.SAFE_EDUCATIONAL,
            risk_level=RiskLevel.NONE,
            confidence=1.0,
            triggered_rules=[],
            reason="Prompt successfully passed Prompt Shield verification.",
            sanitized_prompt=sanitized,
        )
