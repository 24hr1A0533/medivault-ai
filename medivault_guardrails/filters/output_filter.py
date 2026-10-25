"""
Output Filter for MediVault Medical AI Safety Guardrails.

Inspects generated outputs to prevent diagnostic declarations, prescription orders,
dosage alterations, and physician replacements.
"""
import re
from typing import List, Tuple
from medivault_guardrails.schemas.guardrail_schema import (
    OutputFilterResult,
    GuardrailAction,
    STANDARD_SAFETY_RESPONSE,
)

class MedicalOutputFilter:
    """
    Scans LLM generation before sending to patients.
    Blocks forbidden phrases and replaces non-compliant claims with
    standard educational disclaimers.
    """

    # Explicit literal forbidden strings from clinical safety policy
    EXPLICIT_FORBIDDEN_PHRASES = [
        "you have diabetes",
        "stop taking medicine",
        "increase dosage",
        "decrease dosage",
        "double your dosage",
        "stop taking your medication",
        "stop taking your medicine",
        "you do not need a doctor",
        "you don't need a doctor",
    ]

    # Generalized regex patterns detecting forbidden medical practices
    FORBIDDEN_DIAGNOSIS_PATTERNS = [
        r"\byou\s+have\s+(?:type\s+[12]\s+)?(?:diabetes|hypertension|cancer|leukemia|asthma|covid(?:-19)?|kidney\s+disease|anemia|pneumonia|hepatitis|depression)\b",
        r"\byou\s+(?:are\s+diagnosed\s+with|suffer\s+from)\s+[a-zA-Z\s]+",
        r"\b(?:I\s+diagnose\s+you\s+with|my\s+diagnosis\s+is\s+that\s+you\s+have)\b",
        r"\b(?:your\s+official\s+diagnosis\s+is)\b",
    ]

    FORBIDDEN_PRESCRIPTION_PATTERNS = [
        r"\b(?:start\s+taking|take)\s+\d+\s*(?:mg|milligrams|ml|tablets?|pills?)\s+of\s+[a-zA-Z]+",
        r"\b(?:I\s+prescribe\s+you|I\s+recommend\s+taking)\s+[a-zA-Z]+",
        r"\b(?:take\s+(?:metformin|lisinopril|amoxicillin|atorvastatin|insulin|prednisone|omeprazole))\b",
    ]

    FORBIDDEN_DOSAGE_PATTERNS = [
        r"\b(?:increase|decrease|double|halve|adjust)\s+(?:your\s+|the\s+)?(?:dose|dosage)\b",
        r"\b(?:stop\s+taking|discontinue)\s+(?:your\s+|the\s+)?(?:medicine|medication|pills?|drugs?|prescriptions?)\b",
        r"\b(?:take\s+more\s+(?:dose|pills?|medicine))\b",
    ]

    FORBIDDEN_TREATMENT_PATTERNS = [
        r"\b(?:your\s+treatment\s+plan\s+is|I\s+prescribe\s+this\s+treatment\s+regimen)\b",
        r"\b(?:you\s+must\s+undergo\s+surgery|follow\s+this\s+home\s+cure)\b",
    ]

    FORBIDDEN_DOCTOR_REPLACEMENT_PATTERNS = [
        r"\b(?:you\s+do\s+not\s+need\s+(?:a\s+)?doctor|no\s+need\s+to\s+see\s+a\s+physician)\b",
        r"\b(?:do\s+not\s+consult\s+your\s+doctor|instead\s+of\s+visiting\s+a\s+hospital)\b",
    ]

    def __init__(self):
        self._compiled_diagnosis = [re.compile(p, re.IGNORECASE) for p in self.FORBIDDEN_DIAGNOSIS_PATTERNS]
        self._compiled_prescription = [re.compile(p, re.IGNORECASE) for p in self.FORBIDDEN_PRESCRIPTION_PATTERNS]
        self._compiled_dosage = [re.compile(p, re.IGNORECASE) for p in self.FORBIDDEN_DOSAGE_PATTERNS]
        self._compiled_treatment = [re.compile(p, re.IGNORECASE) for p in self.FORBIDDEN_TREATMENT_PATTERNS]
        self._compiled_doctor_rep = [re.compile(p, re.IGNORECASE) for p in self.FORBIDDEN_DOCTOR_REPLACEMENT_PATTERNS]

    def filter_output(self, text: str) -> OutputFilterResult:
        """
        Scans model output text. If any forbidden phrase or pattern is detected,
        intercepts and overrides with the educational safety disclaimer.
        """
        raw_text = text.strip()
        lower_text = raw_text.lower()
        forbidden_matches: List[str] = []
        audit_notes: List[str] = []

        # 1. Exact forbidden phrases check
        for phrase in self.EXPLICIT_FORBIDDEN_PHRASES:
            if phrase in lower_text:
                forbidden_matches.append(f"Literal forbidden phrase: '{phrase}'")

        # 2. Diagnostic regex check
        for pat in self._compiled_diagnosis:
            m = pat.search(raw_text)
            if m:
                forbidden_matches.append(f"Diagnostic claim match: '{m.group(0)}'")

        # 3. Prescription regex check
        for pat in self._compiled_prescription:
            m = pat.search(raw_text)
            if m:
                forbidden_matches.append(f"Prescription claim match: '{m.group(0)}'")

        # 4. Dosage adjustment regex check
        for pat in self._compiled_dosage:
            m = pat.search(raw_text)
            if m:
                forbidden_matches.append(f"Dosage alteration match: '{m.group(0)}'")

        # 5. Treatment plan regex check
        for pat in self._compiled_treatment:
            m = pat.search(raw_text)
            if m:
                forbidden_matches.append(f"Treatment plan match: '{m.group(0)}'")

        # 6. Doctor replacement regex check
        for pat in self._compiled_doctor_rep:
            m = pat.search(raw_text)
            if m:
                forbidden_matches.append(f"Doctor replacement match: '{m.group(0)}'")

        if forbidden_matches:
            audit_notes.append(f"Blocked {len(forbidden_matches)} forbidden clinical assertions.")
            return OutputFilterResult(
                is_clean=False,
                action_taken=GuardrailAction.SANITIZE,
                forbidden_matches=forbidden_matches,
                original_text=raw_text,
                filtered_text=STANDARD_SAFETY_RESPONSE,
                audit_notes=audit_notes,
            )

        # Output is clean and adheres to educational standards
        audit_notes.append("Output passed all clinical safety assertions without violations.")
        return OutputFilterResult(
            is_clean=True,
            action_taken=GuardrailAction.ALLOW,
            forbidden_matches=[],
            original_text=raw_text,
            filtered_text=raw_text,
            audit_notes=audit_notes,
        )
