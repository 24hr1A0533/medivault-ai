"""
Patient-Specific RAG LLM Orchestration Service
Provides production orchestration for patient-isolated clinical RAG with:
1. Explain Report
2. Summarize Reports
3. Compare Reports
4. Medical Timeline Generation
5. Doctor Visit Summary
Guarantees zero cross-patient data leakage, mandatory citations, and hallucination rejection.
"""

import time
import logging
from typing import List, Optional, Dict, Any, Tuple

from .schemas.rag_schema import (
    RAGFeature,
    DocumentChunk,
    Citation,
    IngestDocumentRequest,
    PatientRAGQueryRequest,
    PatientRAGResponse,
)
from .chunking.chunker import ClinicalDocumentChunker
from .vector_store.isolated_store import IsolatedPatientVectorStore, SecurityIsolationError
from .context.builder import ClinicalContextBuilder
from .llm.clinical_llm import ClinicalLLMEngine
from .citations.citation_engine import MedicalCitationEngine
from medivault_guardrails.layer.safety_layer import ClinicalSafetyLayer
from medivault_guardrails.schemas.guardrail_schema import InputCheckRequest, OutputCheckRequest

logger = logging.getLogger("patient_rag.service")


class PatientRAGService:
    """
    Main entry point for patient-specific clinical RAG operations.
    """

    def __init__(self, vector_store_dir: Optional[str] = None):
        self.chunker = ClinicalDocumentChunker()
        self.vector_store = IsolatedPatientVectorStore(persist_directory=vector_store_dir)
        self.context_builder = ClinicalContextBuilder()
        self.llm_engine = ClinicalLLMEngine()
        self.citation_engine = MedicalCitationEngine()
        self.safety_layer = ClinicalSafetyLayer()

    def ingest_document(self, request: IngestDocumentRequest) -> int:
        """
        Chunks and indexes a patient's document into isolated vector storage.
        Returns the count of indexed chunks.
        """
        if not request.patient_id or not request.patient_id.strip():
            raise SecurityIsolationError("Cannot ingest document without valid patient_id.")

        chunks = self.chunker.chunk_document(
            document_id=request.document_id,
            patient_id=request.patient_id,
            report_name=request.report_name,
            report_date=request.report_date,
            pages=request.pages,
            category=request.category or "LAB_REPORT",
        )

        self.vector_store.index_chunks(chunks)
        logger.info(f"Ingested {len(chunks)} chunks for patient '{request.patient_id}' from '{request.report_name}'.")
        return len(chunks)

    def query(self, request: PatientRAGQueryRequest) -> PatientRAGResponse:
        """
        Executes a grounded, patient-isolated RAG workflow.
        Guarantees that only documents belonging to request.patient_id are retrieved.
        """
        start_time = time.time()

        if not request.patient_id or not request.patient_id.strip():
            raise SecurityIsolationError("Mandatory patient_id must be provided to query medical records.")

        # Step 0: Medical AI Safety Input Shield & Risk Classifier
        input_eval = self.safety_layer.check_input(InputCheckRequest(query=request.query, patient_id=request.patient_id))
        if not input_eval.is_allowed:
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            return PatientRAGResponse(
                patient_id=request.patient_id,
                feature=request.feature,
                answer=input_eval.safe_response or "This information is educational only. Please consult a licensed healthcare professional.",
                citations=[],
                grounded=False,
                source_documents_count=0,
                retrieved_chunks_count=0,
                processing_time_ms=elapsed_ms,
            )

        # Step 1: Isolated Semantic Retrieval
        retrieved_chunks = self.vector_store.query_patient_chunks(
            patient_id=request.patient_id,
            query_text=request.query,
            filter_report_ids=request.filter_report_ids,
            filter_category=request.filter_category,
            top_k=request.top_k,
        )

        # If zero chunks found for this patient, return standard missing info message immediately
        if not retrieved_chunks:
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            return PatientRAGResponse(
                patient_id=request.patient_id,
                feature=request.feature,
                answer=self.citation_engine.FALLBACK_MESSAGE,
                citations=[],
                grounded=False,
                source_documents_count=0,
                retrieved_chunks_count=0,
                processing_time_ms=elapsed_ms,
            )

        # Step 2: Build Structured Grounding Context
        context_str = self.context_builder.build_context(retrieved_chunks)

        # Step 3: Clinical LLM Reasoning
        raw_answer = self.llm_engine.generate_response(
            feature=request.feature,
            query=request.query,
            context=context_str,
        )

        # Step 4: Validate Citations and Enforce Exact Grounding
        final_answer, citations, is_grounded = self.citation_engine.extract_and_format_citations(
            raw_answer=raw_answer,
            retrieved_chunks=retrieved_chunks,
        )

        # Step 5: Medical AI Output Filter (blocks forbidden diagnostic or prescriptive assertions)
        output_eval = self.safety_layer.check_output(OutputCheckRequest(text=final_answer, query_context=request.query))
        if not output_eval.is_clean:
            final_answer = output_eval.final_text

        distinct_docs = len({c.document_id for c, _ in retrieved_chunks})
        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        return PatientRAGResponse(
            patient_id=request.patient_id,
            feature=request.feature,
            answer=final_answer,
            citations=citations,
            grounded=is_grounded,
            source_documents_count=distinct_docs,
            retrieved_chunks_count=len(retrieved_chunks),
            processing_time_ms=elapsed_ms,
        )

    # --------------------------------------------------------------------------
    # Specialized Clinical Feature Methods
    # --------------------------------------------------------------------------

    def explain_report(
        self,
        patient_id: str,
        document_id: Optional[str] = None,
        query: str = "Please explain the clinical findings in this medical report.",
    ) -> PatientRAGResponse:
        """Feature 1: Explain Report."""
        req = PatientRAGQueryRequest(
            patient_id=patient_id,
            query=query,
            feature=RAGFeature.EXPLAIN_REPORT,
            filter_report_ids=[document_id] if document_id else None,
            top_k=5,
        )
        return self.query(req)

    def summarize_reports(
        self,
        patient_id: str,
        document_ids: Optional[List[str]] = None,
        query: str = "Summarize all my recent medical reports and active conditions.",
    ) -> PatientRAGResponse:
        """Feature 2: Summarize Reports."""
        req = PatientRAGQueryRequest(
            patient_id=patient_id,
            query=query,
            feature=RAGFeature.SUMMARIZE_REPORTS,
            filter_report_ids=document_ids,
            top_k=8,
        )
        return self.query(req)

    def compare_reports(
        self,
        patient_id: str,
        document_ids: List[str],
        query: str = "Compare the lab test values and clinical parameters across these reports.",
    ) -> PatientRAGResponse:
        """Feature 3: Compare Reports."""
        req = PatientRAGQueryRequest(
            patient_id=patient_id,
            query=query,
            feature=RAGFeature.COMPARE_REPORTS,
            filter_report_ids=document_ids,
            top_k=8,
        )
        return self.query(req)

    def generate_medical_timeline(
        self,
        patient_id: str,
        query: str = "Generate a chronological medical timeline of all my recorded healthcare encounters.",
    ) -> PatientRAGResponse:
        """Feature 4: Medical Timeline Generation."""
        req = PatientRAGQueryRequest(
            patient_id=patient_id,
            query=query,
            feature=RAGFeature.MEDICAL_TIMELINE,
            top_k=10,
        )
        return self.query(req)

    def generate_doctor_visit_summary(
        self,
        patient_id: str,
        query: str = "Prepare an executive consultation summary for my next doctor visit.",
    ) -> PatientRAGResponse:
        """Feature 5: Doctor Visit Summary."""
        req = PatientRAGQueryRequest(
            patient_id=patient_id,
            query=query,
            feature=RAGFeature.DOCTOR_VISIT_SUMMARY,
            top_k=6,
        )
        return self.query(req)
