"""
Doctor Consultation Summary Service Orchestrator.
Coordinates record synthesis, clinical LLM formatting, and citation validation.
"""
import time
import logging
from typing import Optional, List

from medivault_doctor_summary.schemas.summary_schema import (
    DoctorSummaryRequest,
    DoctorConsultationSummaryResponse,
    Citation,
)
from medivault_doctor_summary.synthesizer.record_synthesizer import ClinicalRecordSynthesizer
from medivault_doctor_summary.llm.summary_llm import DoctorSummaryLLMEngine
from medivault_doctor_summary.citations.citation_validator import ConsultationCitationValidator

logger = logging.getLogger("medivault.doctor_summary")

class DoctorConsultationService:
    """
    Main orchestration service for generating doctor consultation briefings.
    """

    def __init__(
        self,
        synthesizer: Optional[ClinicalRecordSynthesizer] = None,
        llm_engine: Optional[DoctorSummaryLLMEngine] = None,
        citation_validator: Optional[ConsultationCitationValidator] = None,
    ):
        self.synthesizer = synthesizer or ClinicalRecordSynthesizer()
        self.llm_engine = llm_engine or DoctorSummaryLLMEngine()
        self.citation_validator = citation_validator or ConsultationCitationValidator()

    def generate_summary(self, request: DoctorSummaryRequest) -> DoctorConsultationSummaryResponse:
        """
        Synthesizes all patient medical records and produces the structured doctor consultation brief.
        """
        start_time = time.time()

        # Step 1: Synthesize all records into clinical domains
        conditions, abnormals, recent_reports, medications, followups = self.synthesizer.synthesize_all_records(
            request.records
        )

        # Step 2: Generate personalized high-yield questions for the doctor
        questions = self.synthesizer.generate_discussion_questions(
            conditions=conditions,
            abnormals=abnormals,
            medications=medications,
            followups=followups,
        )

        # Step 3: Generate high-level Patient Summary paragraph
        patient_summary = self.llm_engine.generate_patient_overview(
            patient_id=request.patient_id,
            patient_name=request.patient_name,
            conditions=conditions,
            abnormals=abnormals,
            medications=medications,
            recent_reports=recent_reports,
        )

        # Step 4: Render exact formatted markdown
        formatted_md = self.llm_engine.render_markdown(
            patient_summary=patient_summary,
            conditions=conditions,
            abnormals=abnormals,
            recent_reports=recent_reports,
            medications=medications,
            followups=followups,
            questions=questions,
        )

        # Step 5: Collect and validate all citations
        raw_citations: List[Citation] = []
        raw_citations.extend([c.citation for c in conditions])
        raw_citations.extend([a.citation for a in abnormals])
        raw_citations.extend([r.citation for r in recent_reports])
        raw_citations.extend([m.citation for m in medications])
        raw_citations.extend([f.citation for f in followups])

        verified_citations, grounding_score = self.citation_validator.validate_and_dedupe_citations(
            raw_citations=raw_citations,
            available_records=request.records,
        )

        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(
            f"Generated doctor consultation summary for patient {request.patient_id} "
            f"in {elapsed_ms}ms with {len(verified_citations)} verified citations."
        )

        return DoctorConsultationSummaryResponse(
            patient_id=request.patient_id,
            patient_name=request.patient_name,
            patient_summary=patient_summary,
            current_conditions=conditions,
            abnormal_findings=abnormals,
            recent_reports=recent_reports,
            current_medications=medications,
            upcoming_followups=followups,
            questions_to_discuss=questions,
            formatted_markdown=formatted_md,
            citations=verified_citations,
            processing_time_ms=elapsed_ms,
        )
