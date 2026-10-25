"""
MediVault Unified Medical LLM Service.
Integrates all 10 clinical AI capabilities into a single cohesive production orchestrator.
"""
import time
import logging
from typing import List, Dict, Any, Optional

from medivault_medical_llm.core.config import CONFIG
from medivault_medical_llm.core.security import HIPAASecurityManager, SecurityIsolationError
from medivault_medical_llm.core.hallucination_detector import HallucinationDetector
from medivault_medical_llm.ocr.ocr_engine import MedicalOCREngine, OCRDocumentResult
from medivault_medical_llm.rag.rag_orchestrator import (
    RAGDocumentChunk,
    IsolatedChromaRAGStore,
)
from medivault_guardrails.layer.safety_layer import ClinicalSafetyLayer
from medivault_guardrails.schemas.guardrail_schema import (
    InputCheckRequest,
    OutputCheckRequest,
    STANDARD_SAFETY_RESPONSE,
)
from medivault_trend_engine.engine.trend_analyzer import ClinicalTrendAnalyzer
from medivault_trend_engine.schemas.trend_schema import BiomarkerMeasurement, PatientTrendAnalysisResponse
from medivault_doctor_summary.service import DoctorConsultationService
from medivault_doctor_summary.schemas.summary_schema import (
    DoctorSummaryRequest,
    PatientRecordInput,
    DoctorConsultationSummaryResponse,
)

logger = logging.getLogger("medivault.medical_llm")

class UnifiedMedicalLLMService:
    """
    Flagship MediVault Medical LLM Orchestrator.
    """

    def __init__(self):
        self.ocr_engine = MedicalOCREngine()
        self.security = HIPAASecurityManager()
        self.hallucination_detector = HallucinationDetector(
            confidence_threshold=CONFIG.hallucination_threshold
        )
        self.rag_store = IsolatedChromaRAGStore(persist_dir=CONFIG.chroma_persist_directory)
        self.guardrails = ClinicalSafetyLayer()
        self.trend_analyzer = ClinicalTrendAnalyzer()
        self.doctor_summary_service = DoctorConsultationService()

    # --------------------------------------------------------------------------
    # Capability 1: Medical OCR Understanding
    # --------------------------------------------------------------------------
    def process_ocr_document(
        self,
        document_id: str,
        report_name: str,
        report_date: str,
        raw_content: str,
        page_number: int = 1,
    ) -> OCRDocumentResult:
        """Capability 1: Parses layout, tables, and cleans noisy scanned OCR text."""
        return self.ocr_engine.parse_document(
            document_id=document_id,
            report_name=report_name,
            report_date=report_date,
            raw_content=raw_content,
            page_number=page_number,
        )

    # --------------------------------------------------------------------------
    # Capability 2: Medical Knowledge Extraction
    # --------------------------------------------------------------------------
    def extract_medical_knowledge(
        self,
        document_text: str,
        report_name: str,
        report_date: str,
        page_number: int = 1,
    ) -> Dict[str, Any]:
        """Capability 2: Normalizes biomarkers, values, reference ranges, and medicines."""
        from medivault_trend_engine.extractor.report_parser import ClinicalReportParser
        parser = ClinicalReportParser()
        measurements = parser.parse_report_text(
            text=document_text,
            report_name=report_name,
            report_date=report_date,
            page_number=page_number,
        )
        return {
            "biomarkers_extracted": [m.model_dump() for m in measurements],
            "total_entities": len(measurements),
            "report_name": report_name,
            "report_date": report_date,
        }

    # --------------------------------------------------------------------------
    # Capability 3 & 10: Ingest & Isolated Patient RAG Querying
    # --------------------------------------------------------------------------
    def ingest_patient_document(
        self,
        patient_id: str,
        document_id: str,
        report_name: str,
        report_date: str,
        content: str,
        page_number: int = 1,
        category: str = "LAB_REPORT",
    ) -> int:
        """Indexes document chunks into isolated ChromaDB vector storage."""
        if not patient_id:
            raise SecurityIsolationError("Cannot ingest document without valid patient_id.")

        # Mask PHI if enabled
        safe_content = self.security.mask_phi(content) if CONFIG.hipaa_phi_masking else content

        # Chunk content into paragraphs
        paragraphs = [p.strip() for p in safe_content.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [safe_content]

        chunks = []
        for idx, para in enumerate(paragraphs):
            chunk = RAGDocumentChunk(
                chunk_id=f"{document_id}-p{page_number}-c{idx}",
                patient_id=patient_id,
                document_id=document_id,
                report_name=report_name,
                report_date=report_date,
                page_number=page_number,
                text=para,
                category=category,
            )
            chunks.append(chunk)

        self.rag_store.index_chunks(chunks)
        return len(chunks)

    def query_patient_rag(
        self,
        patient_id: str,
        query: str,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        Capability 3, 7, 8, 9, 10:
        Executes patient-isolated RAG with prompt shield, hallucination verification,
        and citation engine.
        """
        start_time = time.time()

        # 1. Medical Safety Guardrails (Prompt Shield & Risk Classifier)
        input_eval = self.guardrails.check_input(InputCheckRequest(query=query, patient_id=patient_id))
        if not input_eval.is_allowed:
            return {
                "patient_id": patient_id,
                "answer": input_eval.safe_response or STANDARD_SAFETY_RESPONSE,
                "citations": [],
                "faithfulness_score": 1.0,
                "is_hallucination_free": True,
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            }

        # 2. Isolated Semantic Retrieval (ChromaDB + BGE Large)
        retrieved = self.rag_store.query_patient_chunks(
            patient_id=patient_id,
            query_text=query,
            top_k=top_k,
        )

        if not retrieved:
            return {
                "patient_id": patient_id,
                "answer": "I could not find that information in your medical records.",
                "citations": [],
                "faithfulness_score": 1.0,
                "is_hallucination_free": True,
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            }

        # Check if query asks for specific medical findings not present in patient's retrieved chunks
        stop_words = {"what", "was", "my", "is", "the", "in", "records", "did", "have", "test", "please", "results", "levels"}
        query_terms = [w.lower().strip("?,.") for w in query.split() if w.lower().strip("?,.") not in stop_words and len(w) > 3]
        
        combined_text = " ".join([c.text.lower() for c, _ in retrieved])
        if query_terms and not any(term in combined_text for term in query_terms):
            return {
                "patient_id": patient_id,
                "answer": "I could not find that information in your medical records.",
                "citations": [],
                "faithfulness_score": 1.0,
                "is_hallucination_free": True,
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            }

        contexts = [
            f"Report: {c.report_name} Date: {c.report_date} Page: {c.page_number} Content: {c.text}"
            for c, _ in retrieved
        ]
        citations = [
            {
                "report_name": c.report_name,
                "page_number": c.page_number,
                "report_date": c.report_date,
            }
            for c, _ in retrieved
        ]

        # 3. Qwen 2.5 7B Clinical Reasoning Simulation
        top_chunk = retrieved[0][0]
        raw_answer = (
            f"Based on your {top_chunk.report_name} dated {top_chunk.report_date} (Page {top_chunk.page_number}), "
            f"the clinical record documents: {top_chunk.text} "
            f"[Source: {top_chunk.report_name}, Page {top_chunk.page_number}, {top_chunk.report_date}]"
        )

        # 4. Hallucination Detection (Zero-Hallucination Policy)
        is_faithful, faith_score, flagged, validated_answer = self.hallucination_detector.evaluate_response(
            generated_answer=raw_answer,
            retrieved_contexts=contexts,
        )

        # 5. Output Filter Guardrail (Prohibits diagnostic/prescriptive assertions)
        out_eval = self.guardrails.check_output(OutputCheckRequest(text=validated_answer, query_context=query))
        final_answer = out_eval.final_text

        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        return {
            "patient_id": patient_id,
            "answer": final_answer,
            "citations": citations if is_faithful else [],
            "faithfulness_score": faith_score,
            "is_hallucination_free": is_faithful,
            "processing_time_ms": elapsed_ms,
        }

    # --------------------------------------------------------------------------
    # Capability 4: Medical Report Explanation
    # --------------------------------------------------------------------------
    def explain_medical_report(
        self,
        patient_id: str,
        report_text: str,
        report_name: str,
        report_date: str,
        page_number: int = 1,
    ) -> Dict[str, Any]:
        """Capability 4: Translates laboratory findings into patient-friendly educational language."""
        from medivault_trend_engine.extractor.report_parser import ClinicalReportParser
        parser = ClinicalReportParser()
        measurements = parser.parse_report_text(report_text, report_name, report_date, page_number)

        explanations = []
        for m in measurements:
            explanations.append(
                f"- **{m.test_name}**: Measured value is {m.value} {m.unit} (standard reference range {m.reference_range}). "
                f"This parameter was reviewed from {report_name} (Page {page_number}, {report_date})."
            )

        explanation_str = (
            f"### Educational Report Explanation: {report_name} ({report_date})\n"
            + ("\n".join(explanations) if explanations else "Clinical documentation reviewed without specific abnormal lab values.")
            + "\n\n*Note: This information is educational only. Please consult a licensed healthcare professional.*"
        )

        return {
            "patient_id": patient_id,
            "report_name": report_name,
            "report_date": report_date,
            "explanation": explanation_str,
            "citations": [{"report_name": report_name, "page_number": page_number, "report_date": report_date}],
        }

    # --------------------------------------------------------------------------
    # Capability 5: Medical Trend Analysis
    # --------------------------------------------------------------------------
    def analyze_medical_trends(
        self,
        patient_id: str,
        measurements: List[BiomarkerMeasurement],
    ) -> PatientTrendAnalysisResponse:
        """Capability 5: Compares longitudinal reports, generates SVG graphs & deterioration alerts."""
        return self.trend_analyzer.analyze_patient_trends(
            patient_id=patient_id,
            measurements=measurements,
        )

    # --------------------------------------------------------------------------
    # Capability 6: Doctor Summary Generation
    # --------------------------------------------------------------------------
    def generate_doctor_summary(
        self,
        request: DoctorSummaryRequest,
    ) -> DoctorConsultationSummaryResponse:
        """Capability 6: Synthesizes all records into doctor consultation brief."""
        return self.doctor_summary_service.generate_summary(request)
