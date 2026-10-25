"""
MediVault Patient-Specific RAG LLM System Schemas
Enforces strict multi-user tenant isolation, structured citation models,
and request/response payloads for clinical reasoning features:
1. Explain Report
2. Summarize Reports
3. Compare Reports
4. Medical Timeline Generation
5. Doctor Visit Summary
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class RAGFeature(str, Enum):
    EXPLAIN_REPORT = "EXPLAIN_REPORT"
    SUMMARIZE_REPORTS = "SUMMARIZE_REPORTS"
    COMPARE_REPORTS = "COMPARE_REPORTS"
    MEDICAL_TIMELINE = "MEDICAL_TIMELINE"
    DOCTOR_VISIT_SUMMARY = "DOCTOR_VISIT_SUMMARY"
    GENERAL_QUERY = "GENERAL_QUERY"


class DocumentChunk(BaseModel):
    """
    Atomic clinical chunk containing text and mandatory grounding metadata.
    """
    chunk_id: str = Field(description="Unique chunk UUID")
    document_id: str = Field(description="Parent document UUID")
    patient_id: str = Field(description="Patient owner UUID - strict isolation key")
    report_name: str = Field(description="Clinical report name (e.g. Complete Blood Count)")
    report_date: str = Field(description="Report issuance or specimen date (ISO-8601 string)")
    page_number: int = Field(default=1, ge=1, description="Page number where text occurs")
    text: str = Field(description="Raw chunk textual content")
    category: Optional[str] = Field(default="LAB_REPORT", description="Report category")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional custom metadata")

    model_config = ConfigDict(from_attributes=True)


class Citation(BaseModel):
    """
    Mandatory grounding citation extracted from retrieved context.
    Must include report_name, page_number, and report_date.
    """
    report_name: str = Field(description="Originating medical report name")
    page_number: int = Field(ge=1, description="Page number of the cited content")
    report_date: str = Field(description="Date of the originating report")
    quoted_snippet: Optional[str] = Field(default=None, description="Exact cited passage snippet")

    model_config = ConfigDict(from_attributes=True)


class IngestDocumentRequest(BaseModel):
    """Request to ingest and index patient documents into isolated vector space."""
    patient_id: str = Field(description="Patient owner UUID (Mandatory tenant isolation)")
    document_id: str = Field(description="Unique document identifier")
    report_name: str = Field(description="Human readable report title")
    report_date: str = Field(description="Date of report (YYYY-MM-DD)")
    category: Optional[str] = Field(default="LAB_REPORT")
    pages: List[Dict[str, Any]] = Field(
        description="List of page objects: [{'page_number': 1, 'text': '...'}]"
    )


class PatientRAGQueryRequest(BaseModel):
    """Request to execute a patient-specific RAG query."""
    patient_id: str = Field(description="Requesting patient's ID (Mandatory tenant isolation key)")
    query: str = Field(description="Patient question or instruction")
    feature: RAGFeature = Field(default=RAGFeature.GENERAL_QUERY, description="Clinical feature mode")
    filter_report_ids: Optional[List[str]] = Field(default=None, description="Optional target report UUIDs (e.g. for Compare)")
    filter_category: Optional[str] = Field(default=None, description="Optional category filter")
    top_k: int = Field(default=5, ge=1, le=20, description="Max chunks to retrieve")


class PatientRAGResponse(BaseModel):
    """Response returned by the Patient-Specific RAG LLM System."""
    patient_id: str
    feature: RAGFeature
    answer: str = Field(description="Grounded clinical response with citations or fallback message")
    citations: List[Citation] = Field(default_factory=list, description="Verified source citations")
    grounded: bool = Field(description="Whether the response is grounded in retrieved records")
    source_documents_count: int = Field(description="Number of distinct patient records utilized")
    retrieved_chunks_count: int = Field(description="Number of relevant chunks retrieved")
    processing_time_ms: float

    model_config = ConfigDict(from_attributes=True)
