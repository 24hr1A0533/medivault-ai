"""
Multimodal Clinical Confidence Scoring Engine
Combines:
1. OCR recognition confidence (character certainty)
2. BioBERT token classification posterior probabilities
3. Medical ontology resolution distance (LOINC / RxNorm match certainty)
4. Syntax & biological plausibility verification rules
"""

from typing import Dict, Any, List, Optional
from ..schemas.document_schema import VerificationStatus, StructuredMedicalDocument


class ConfidenceEngine:
    """
    Computes rigorous, explainable confidence metrics for extracted medical entities.
    Enforces quality guardrails before structured data is indexed in the vector database.
    """

    AUTO_VERIFY_THRESHOLD = 0.88
    CRITICAL_FIELD_MIN_THRESHOLD = 0.75

    # Weights for composite confidence formula
    WEIGHT_OCR = 0.25
    WEIGHT_BERT = 0.35
    WEIGHT_ONTOLOGY = 0.25
    WEIGHT_RULE = 0.15

    def compute_field_confidence(
        self,
        ocr_conf: float = 0.90,
        bert_prob: float = 0.90,
        ontology_resolved: bool = True,
        rule_valid: bool = True,
    ) -> float:
        """
        Calculates composite confidence for an individual extracted entity.
        Returns float in [0.0, 1.0].
        """
        s_ont = 1.0 if ontology_resolved else 0.50
        s_rule = 1.0 if rule_valid else 0.40

        score = (
            self.WEIGHT_OCR * max(0.0, min(1.0, ocr_conf))
            + self.WEIGHT_BERT * max(0.0, min(1.0, bert_prob))
            + self.WEIGHT_ONTOLOGY * s_ont
            + self.WEIGHT_RULE * s_rule
        )
        return round(score, 3)

    def evaluate_document(self, doc: StructuredMedicalDocument) -> Tuple[float, VerificationStatus, List[str]]:
        """
        Evaluates overall document confidence and determines HITL verification status.
        Returns:
            Tuple[overall_confidence, verification_status, reasons]
        """
        all_scores: List[float] = []
        flagged_reasons: List[str] = []

        # 1. Demographics check
        if doc.patient_details.name:
            all_scores.append(doc.patient_details.confidence)
        if doc.patient_details.age is not None:
            if doc.patient_details.age < 0 or doc.patient_details.age > 120:
                flagged_reasons.append(f"Implausible patient age: {doc.patient_details.age}")
                all_scores.append(0.30)
            else:
                all_scores.append(0.95)

        # 2. Lab tests check
        for test in doc.medical_data.tests:
            all_scores.append(test.confidence)
            if test.confidence < self.CRITICAL_FIELD_MIN_THRESHOLD:
                flagged_reasons.append(
                    f"Low confidence ({test.confidence:.2f}) on lab test '{test.test_name}'"
                )
            if not test.loinc_code:
                flagged_reasons.append(f"Unmapped test ontology for '{test.test_name}'")

        # 3. Prescriptions check
        for rx in doc.prescriptions:
            all_scores.append(rx.confidence)
            if rx.confidence < self.CRITICAL_FIELD_MIN_THRESHOLD:
                flagged_reasons.append(
                    f"Low confidence ({rx.confidence:.2f}) on prescription '{rx.medicine}'"
                )
            if not rx.dosage:
                flagged_reasons.append(f"Missing dosage specification for medication '{rx.medicine}'")

        if not all_scores:
            return 0.50, VerificationStatus.FLAGGED_FOR_REVIEW, ["No structured medical entities could be extracted."]

        overall = round(sum(all_scores) / len(all_scores), 3)

        # Determine verification status
        if overall >= self.AUTO_VERIFY_THRESHOLD and not flagged_reasons:
            status = VerificationStatus.AUTO_VERIFIED
        else:
            status = VerificationStatus.FLAGGED_FOR_REVIEW

        return overall, status, flagged_reasons
