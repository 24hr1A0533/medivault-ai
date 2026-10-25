"""
FastAPI REST API Router for Patient-Specific RAG System
Exposes production endpoints for:
1. Document Ingestion
2. Patient-Isolated RAG Queries
3. Explain Report
4. Summarize Reports
5. Compare Reports
6. Medical Timeline Generation
7. Doctor Visit Summary
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from ..schemas.rag_schema import (
    IngestDocumentRequest,
    PatientRAGQueryRequest,
    PatientRAGResponse,
    RAGFeature,
)
from ..service import PatientRAGService, SecurityIsolationError

router = APIRouter(prefix="/patient-rag", tags=["Patient-Specific Clinical RAG"])

_service_instance: Optional[PatientRAGService] = None


def get_rag_service() -> PatientRAGService:
    global _service_instance
    if _service_instance is None:
        _service_instance = PatientRAGService()
    return _service_instance


@router.post(
    "/ingest",
    status_code=status.HTTP_201_CREATED,
    summary="Ingest Patient Document",
    description="Indexes multi-page medical reports into patient-isolated vector storage with exact page metadata.",
)
async def ingest_document(
    request: IngestDocumentRequest,
    service: PatientRAGService = Depends(get_rag_service),
):
    try:
        count = service.ingest_document(request)
        return {
            "success": True,
            "patient_id": request.patient_id,
            "document_id": request.document_id,
            "chunks_indexed": count,
            "message": f"Successfully indexed {count} grounded chunks for patient '{request.patient_id}'.",
        }
    except SecurityIsolationError as sec_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(sec_err))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post(
    "/query",
    response_model=PatientRAGResponse,
    status_code=status.HTTP_200_OK,
    summary="Query Medical Records",
    description="Executes patient-isolated semantic RAG query with mandatory citations.",
)
async def query_records(
    request: PatientRAGQueryRequest,
    service: PatientRAGService = Depends(get_rag_service),
) -> PatientRAGResponse:
    try:
        return service.query(request)
    except SecurityIsolationError as sec_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(sec_err))


@router.post(
    "/explain",
    response_model=PatientRAGResponse,
    status_code=status.HTTP_200_OK,
    summary="Feature 1: Explain Report",
    description="Translates complex clinical markers and lab findings into clear, patient-friendly explanations.",
)
async def explain_report(
    patient_id: str,
    document_id: Optional[str] = None,
    query: str = "Please explain the clinical findings in my medical report.",
    service: PatientRAGService = Depends(get_rag_service),
) -> PatientRAGResponse:
    return service.explain_report(patient_id=patient_id, document_id=document_id, query=query)


@router.post(
    "/summarize",
    response_model=PatientRAGResponse,
    status_code=status.HTTP_200_OK,
    summary="Feature 2: Summarize Reports",
    description="Synthesizes multiple medical reports into a unified longitudinal summary.",
)
async def summarize_reports(
    patient_id: str,
    document_ids: Optional[List[str]] = None,
    query: str = "Summarize all my recent medical reports and active conditions.",
    service: PatientRAGService = Depends(get_rag_service),
) -> PatientRAGResponse:
    return service.summarize_reports(patient_id=patient_id, document_ids=document_ids, query=query)


@router.post(
    "/compare",
    response_model=PatientRAGResponse,
    status_code=status.HTTP_200_OK,
    summary="Feature 3: Compare Reports",
    description="Side-by-side comparative analysis of reports across different dates/intervals.",
)
async def compare_reports(
    patient_id: str,
    document_ids: List[str],
    query: str = "Compare the lab test values and clinical parameters across these reports.",
    service: PatientRAGService = Depends(get_rag_service),
) -> PatientRAGResponse:
    return service.compare_reports(patient_id=patient_id, document_ids=document_ids, query=query)


@router.post(
    "/timeline",
    response_model=PatientRAGResponse,
    status_code=status.HTTP_200_OK,
    summary="Feature 4: Medical Timeline Generation",
    description="Constructs a chronological health timeline of all recorded clinical encounters and tests.",
)
async def generate_timeline(
    patient_id: str,
    query: str = "Generate a chronological medical timeline of all my healthcare events.",
    service: PatientRAGService = Depends(get_rag_service),
) -> PatientRAGResponse:
    return service.generate_medical_timeline(patient_id=patient_id, query=query)


@router.post(
    "/doctor-summary",
    response_model=PatientRAGResponse,
    status_code=status.HTTP_200_OK,
    summary="Feature 5: Doctor Visit Summary",
    description="Prepares a targeted executive summary and discussion checklist for an upcoming physician consultation.",
)
async def generate_doctor_summary(
    patient_id: str,
    query: str = "Prepare an executive consultation summary for my next doctor visit.",
    service: PatientRAGService = Depends(get_rag_service),
) -> PatientRAGResponse:
    return service.generate_doctor_visit_summary(patient_id=patient_id, query=query)


@router.get("/health", tags=["Health"])
async def health():
    return {
        "status": "healthy",
        "service": "MediVault Patient-Specific RAG System",
        "multi_tenant_isolation": "ENFORCED",
        "hallucination_guard": "STRICT_NEGATIVE_CONSTRAINT",
    }
