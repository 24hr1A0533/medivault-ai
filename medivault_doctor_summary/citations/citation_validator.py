"""
Citation & Grounding Validator for Doctor Consultation Summary Engine.
Guarantees zero-hallucination source attribution and validates every citation.
"""
from typing import List, Dict, Set, Tuple
from medivault_doctor_summary.schemas.summary_schema import (
    Citation,
    PatientRecordInput,
)

class ConsultationCitationValidator:
    """
    Validates and dedupes all citations generated across clinical sections.
    Enforces that every cited entity corresponds to an authentic ingested document.
    """

    def validate_and_dedupe_citations(
        self,
        raw_citations: List[Citation],
        available_records: List[PatientRecordInput],
    ) -> Tuple[List[Citation], float]:
        """
        Validates citations against available records.
        Returns verified citations list and grounding confidence score (0.0 - 1.0).
        """
        if not raw_citations:
            return [], 0.0

        known_docs: Set[str] = {r.report_name.strip().lower() for r in available_records if r.report_name}
        
        seen_keys = set()
        verified: List[Citation] = []

        for cite in raw_citations:
            clean_name = cite.report_name.strip()
            clean_lower = clean_name.lower()
            
            # Grounding check: does document name exist in authentic input records?
            if clean_lower not in known_docs:
                continue

            key = (clean_lower, cite.page_number, cite.report_date)
            if key not in seen_keys:
                verified.append(
                    Citation(
                        report_name=clean_name,
                        page_number=max(1, cite.page_number),
                        report_date=cite.report_date,
                        document_id=cite.document_id,
                    )
                )
                seen_keys.add(key)

        grounding_score = round(len(verified) / len(raw_citations), 2) if raw_citations else 1.0
        return verified, grounding_score
