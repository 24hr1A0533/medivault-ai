"""
Clinical Risk Classifier for MediVault Medical AI Safety Guardrails.

Classifies incoming queries into clinical risk categories:
- DIAGNOSIS_SOLICITATION
- PRESCRIPTION_REQUEST
- DOSAGE_ALTERATION
- TREATMENT_PLAN
- DOCTOR_REPLACEMENT
- EMERGENCY_TRIAGE
- SAFE_EDUCATIONAL
"""
import re
from typing import List, Dict, Tuple, Optional
from medivault_guardrails.schemas.guardrail_schema import (
    RiskCategory,
    RiskLevel,
    GuardrailAction,
    RiskClassificationResult,
    STANDARD_SAFETY_RESPONSE,
    EMERGENCY_SAFETY_RESPONSE,
)

class ClinicalRiskClassifier:
    """
    Evaluates queries against strict clinical liability rules.
    Detects diagnostic, therapeutic, and prescriptive solicitations.
    """

    DIAGNOSIS_PATTERNS = [
        r"\b(?:do\s+i\s+have|could\s+i\s+have|might\s+i\s+have)\s+([a-zA-Z\s]+)",
        r"\b(?:diagnose\s+me|give\s+me\s+a\s+diagnosis|what\s+is\s+my\s+diagnosis)\b",
        r"\b(?:am\s+i\s+suffering\s+from|do\s+i\s+suffer\s+from)\s+([a-zA-Z\s]+)",
        r"\b(?:what\s+disease\s+do\s+i\s+have|what\s+illness\s+do\s+i\s+have|what\s+condition\s+do\s+i\s+have)\b",
        r"\b(?:tell\s+me\s+if\s+i\s+have|confirm\s+if\s+i\s+have)\s+([a-zA-Z\s]+)",
        r"\b(?:can\s+you\s+diagnose|please\s+diagnose)\b",
        r"\b(?:is\s+it\s+cancer|is\s+it\s+diabetes|is\s+it\s+a\s+tumor|is\s+it\s+covid)\b",
        r"\b(?:what\s+is\s+wrong\s+with\s+me|why\s+am\s+i\s+sick)\b",
    ]

    PRESCRIPTION_PATTERNS = [
        r"\b(?:what\s+(?:medicine|medication|drug|pill|antibiotic)\s+should\s+i\s+take)\b",
        r"\b(?:prescribe\s+(?:me\s+)?(?:some\s+)?(?:medicine|drugs|pills|antibiotics)?)\b",
        r"\b(?:give\s+me\s+a\s+prescription|can\s+you\s+write\s+a\s+prescription)\b",
        r"\b(?:which\s+(?:medicine|drug|antibiotic)\s+(?:is\s+best|should\s+i\s+use|to\s+cure))\b",
        r"\b(?:what\s+(?:can|should)\s+i\s+take\s+for\b)",
        r"\b(?:recommend\s+(?:a\s+)?(?:medicine|drug|medication|pill))\b",
    ]

    DOSAGE_PATTERNS = [
        r"\b(?:should\s+i\s+(?:increase|decrease|double|halve|stop|discontinue)\s+(?:my\s+)?(?:dose|dosage|medicine|medication|pills?|tablets?))\b",
        r"\b(?:how\s+much\s+(?:mg|milligrams|ml|tablets?|pills?|dose|dosage))\b",
        r"\b(?:can\s+i\s+(?:take\s+more|take\s+less|increase|decrease|double)\s+(?:my\s+)?(?:dose|dosage|tablets?|pills?|medicine|medication))\b",
        r"\b(?:stop\s+taking\s+(?:my\s+)?(?:medicine|medication|pills?|drug|tablets?))\b",
        r"\b(?:is\s+it\s+safe\s+to\s+stop\s+(?:taking\s+)?(?:my\s+)?(?:medicine|medication|tablets?))\b",
    ]

    TREATMENT_PATTERNS = [
        r"\b(?:give\s+me\s+a\s+treatment\s+plan|recommend\s+a\s+treatment\s+plan)\b",
        r"\b(?:how\s+do\s+i\s+cure|how\s+can\s+i\s+cure|how\s+to\s+treat)\s+([a-zA-Z\s]+)",
        r"\b(?:what\s+is\s+the\s+best\s+treatment\s+for)\s+([a-zA-Z\s]+)",
        r"\b(?:create\s+(?:a\s+)?care\s+plan\s+for\s+me|prescribe\s+a\s+therapy)\b",
    ]

    DOCTOR_REPLACEMENT_PATTERNS = [
        r"\b(?:i\s+don'?t\s+want\s+to\s+see\s+a\s+doctor|instead\s+of\s+seeing\s+a\s+doctor)\b",
        r"\b(?:act\s+as\s+my\s+(?:personal\s+)?(?:doctor|physician|clinician|cardiologist|oncologist))\b",
        r"\b(?:replace\s+my\s+doctor|i\s+trust\s+you\s+more\s+than\s+my\s+doctor)\b",
        r"\b(?:don'?t\s+tell\s+me\s+to\s+see\s+a\s+doctor)\b",
    ]

    EMERGENCY_PATTERNS = [
        r"\b(?:crushing\s+chest\s+pain|chest\s+tightness\s+radiating\s+to\s+(?:jaw|arm|shoulder))\b",
        r"\b(?:sudden\s+numbness\s+on\s+one\s+side|facial\s+drooping|slurred\s+speech)\b",
        r"\b(?:difficulty\s+breathing|cannot\s+breathe|severe\s+shortness\s+of\s+breath)\b",
        r"\b(?:coughing\s+up\s+large\s+amounts\s+of\s+blood|vomiting\s+blood)\b",
        r"\b(?:severe\s+allergic\s+reaction|throat\s+swelling|anaphylaxis)\b",
        r"\b(?:unconscious|seizure\s+lasting\s+more\s+than\s+5\s+minutes)\b",
    ]

    EDUCATIONAL_ALLOWED_PATTERNS = [
        r"\b(?:explain\s+(?:my\s+)?(?:report|results?|findings?|lab|test|values?))\b",
        r"\b(?:summarize\s+(?:my\s+)?(?:records?|reports?|history|notes?))\b",
        r"\b(?:compare\s+(?:trends?|results?|reports?|levels?|markers?))\b",
        r"\b(?:what\s+does\s+(?:elevated|high|low|normal)\s+[a-zA-Z0-9\-_]+\s+mean)\b",
        r"\b(?:explain\s+medical\s+terminology|what\s+is\s+the\s+definition\s+of|what\s+does\s+[a-zA-Z0-9\-_]+\s+mean)\b",
        r"\b(?:what\s+are\s+the\s+normal\s+(?:reference\s+)?ranges?\s+for)\b",
    ]

    def __init__(self):
        self._compiled_diagnosis = [re.compile(p, re.IGNORECASE) for p in self.DIAGNOSIS_PATTERNS]
        self._compiled_prescription = [re.compile(p, re.IGNORECASE) for p in self.PRESCRIPTION_PATTERNS]
        self._compiled_dosage = [re.compile(p, re.IGNORECASE) for p in self.DOSAGE_PATTERNS]
        self._compiled_treatment = [re.compile(p, re.IGNORECASE) for p in self.TREATMENT_PATTERNS]
        self._compiled_doctor_rep = [re.compile(p, re.IGNORECASE) for p in self.DOCTOR_REPLACEMENT_PATTERNS]
        self._compiled_emergency = [re.compile(p, re.IGNORECASE) for p in self.EMERGENCY_PATTERNS]
        self._compiled_educational = [re.compile(p, re.IGNORECASE) for p in self.EDUCATIONAL_ALLOWED_PATTERNS]

    def classify_query(self, query: str) -> RiskClassificationResult:
        """
        Classifies incoming query string against clinical risk rules.
        """
        cleaned = query.strip()
        matches: List[str] = []

        # 1. Emergency triage detection
        for pat in self._compiled_emergency:
            m = pat.search(cleaned)
            if m:
                matches.append(m.group(0))
        if matches:
            return RiskClassificationResult(
                category=RiskCategory.EMERGENCY_TRIAGE,
                risk_level=RiskLevel.CRITICAL,
                risk_score=0.99,
                matched_patterns=matches,
                is_allowed=False,
                recommended_action=GuardrailAction.ESCALATE_EMERGENCY,
                refusal_message=EMERGENCY_SAFETY_RESPONSE,
            )

        # 2. Diagnosis solicitation detection
        matches.clear()
        for pat in self._compiled_diagnosis:
            m = pat.search(cleaned)
            if m:
                matches.append(m.group(0))
        if matches:
            return RiskClassificationResult(
                category=RiskCategory.DIAGNOSIS_SOLICITATION,
                risk_level=RiskLevel.HIGH,
                risk_score=0.95,
                matched_patterns=matches,
                is_allowed=False,
                recommended_action=GuardrailAction.BLOCK,
                refusal_message=STANDARD_SAFETY_RESPONSE,
            )

        # 3. Prescription request detection
        matches.clear()
        for pat in self._compiled_prescription:
            m = pat.search(cleaned)
            if m:
                matches.append(m.group(0))
        if matches:
            return RiskClassificationResult(
                category=RiskCategory.PRESCRIPTION_REQUEST,
                risk_level=RiskLevel.HIGH,
                risk_score=0.92,
                matched_patterns=matches,
                is_allowed=False,
                recommended_action=GuardrailAction.BLOCK,
                refusal_message=STANDARD_SAFETY_RESPONSE,
            )

        # 4. Dosage alteration detection
        matches.clear()
        for pat in self._compiled_dosage:
            m = pat.search(cleaned)
            if m:
                matches.append(m.group(0))
        if matches:
            return RiskClassificationResult(
                category=RiskCategory.DOSAGE_ALTERATION,
                risk_level=RiskLevel.HIGH,
                risk_score=0.94,
                matched_patterns=matches,
                is_allowed=False,
                recommended_action=GuardrailAction.BLOCK,
                refusal_message=STANDARD_SAFETY_RESPONSE,
            )

        # 5. Treatment plan recommendation request
        matches.clear()
        for pat in self._compiled_treatment:
            m = pat.search(cleaned)
            if m:
                matches.append(m.group(0))
        if matches:
            return RiskClassificationResult(
                category=RiskCategory.TREATMENT_PLAN,
                risk_level=RiskLevel.HIGH,
                risk_score=0.88,
                matched_patterns=matches,
                is_allowed=False,
                recommended_action=GuardrailAction.BLOCK,
                refusal_message=STANDARD_SAFETY_RESPONSE,
            )

        # 6. Doctor replacement request
        matches.clear()
        for pat in self._compiled_doctor_rep:
            m = pat.search(cleaned)
            if m:
                matches.append(m.group(0))
        if matches:
            return RiskClassificationResult(
                category=RiskCategory.DOCTOR_REPLACEMENT,
                risk_level=RiskLevel.HIGH,
                risk_score=0.90,
                matched_patterns=matches,
                is_allowed=False,
                recommended_action=GuardrailAction.BLOCK,
                refusal_message=STANDARD_SAFETY_RESPONSE,
            )

        # 7. Safe Educational Queries (explain report, summarize, compare trends, terminology)
        for pat in self._compiled_educational:
            m = pat.search(cleaned)
            if m:
                matches.append(m.group(0))

        return RiskClassificationResult(
            category=RiskCategory.SAFE_EDUCATIONAL,
            risk_level=RiskLevel.NONE if matches else RiskLevel.LOW,
            risk_score=0.05 if matches else 0.15,
            matched_patterns=matches,
            is_allowed=True,
            recommended_action=GuardrailAction.ALLOW,
            refusal_message=None,
        )
