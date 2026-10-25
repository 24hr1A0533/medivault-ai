"""
FastAPI REST API Router for Healthcare Document Intelligence
Provides production endpoints for:
- Asynchronous document upload & extraction
- Retrieval of structured clinical knowledge
- Human-in-the-loop (HITL) review & verification
- Semantic vector search via ChromaDB
- Engine health and dependency status
"""

from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends
from ..schemas.document_schema import (
    DocumentProcessResponse,
    StructuredMedicalDocument,
    VerificationRequest,
    VectorQueryRequest,
    VectorQueryResponse,
    DocumentCategory,
)
from ..pipeline.document_pipeline import HealthcareDocumentPipeline

router = APIRouter(prefix="/doc-intelligence", tags=["Healthcare Document Intelligence"])

# Shared pipeline instance
_pipeline_instance: Optional[HealthcareDocumentPipeline] = None


def get_pipeline() -> HealthcareDocumentPipeline:
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = HealthcareDocumentPipeline()
    return _pipeline_instance


@router.post(
    "/process",
    response_model=DocumentProcessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Process Medical Document",
    description="Uploads a PDF, JPG, or PNG document. Executes PaddleOCR, BioBERT NER, LOINC/RxNorm normalization, BGE Large embeddings, and ChromaDB indexing.",
)
async def process_document(
    file: UploadFile = File(..., description="Medical report binary (PDF, PNG, JPG)"),
    patient_id: Optional[str] = Form(None, description="Optional target patient UUID or ID"),
    document_id: Optional[str] = Form(None, description="Optional custom document UUID"),
    pipeline: HealthcareDocumentPipeline = Depends(get_pipeline),
) -> DocumentProcessResponse:
    try:
        raw_bytes = await file.read()
        if not raw_bytes or len(raw_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file uploaded.",
            )

        return pipeline.process_document(
            file_bytes=raw_bytes,
            patient_id=patient_id,
            document_id=document_id,
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline processing failed: {str(exc)}",
        )


@router.get(
    "/documents/{document_id}",
    response_model=StructuredMedicalDocument,
    status_code=status.HTTP_200_OK,
    summary="Get Structured Medical Document",
    description="Retrieves validated structured clinical JSON for an ingested document.",
)
async def get_document(
    document_id: str,
    pipeline: HealthcareDocumentPipeline = Depends(get_pipeline),
) -> StructuredMedicalDocument:
    doc = pipeline.get_document(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )
    return doc


@router.post(
    "/documents/{document_id}/verify",
    response_model=StructuredMedicalDocument,
    status_code=status.HTTP_200_OK,
    summary="Verify Document (HITL Workflow)",
    description="Clinician Human-in-the-Loop review: Approve, Edit fields, or Reject structured knowledge.",
)
async def verify_document(
    document_id: str,
    request: VerificationRequest,
    pipeline: HealthcareDocumentPipeline = Depends(get_pipeline),
) -> StructuredMedicalDocument:
    try:
        return pipeline.verify_document(document_id, request)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(val_err),
        )


@router.post(
    "/search",
    response_model=VectorQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Semantic Vector Search",
    description="Performs dense vector retrieval over clinical records using BAAI BGE Large and ChromaDB.",
)
async def semantic_search(
    request: VectorQueryRequest,
    pipeline: HealthcareDocumentPipeline = Depends(get_pipeline),
) -> VectorQueryResponse:
    return pipeline.search_records(request)


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Service Health Probe",
    description="Reports availability and operational readiness of OCR, NLP, Embedder, and Vector DB.",
)
async def health_check(
    pipeline: HealthcareDocumentPipeline = Depends(get_pipeline),
):
    return {
        "status": "healthy",
        "service": "MediVault Healthcare Document Intelligence",
        "ocr_engine": "PaddleOCR (PP-OCRv4)",
        "ocr_available": pipeline.ocr_engine.is_available(),
        "nlp_model": "BioBERT / ClinicalBERT",
        "embedding_model": pipeline.embedder.MODEL_NAME,
        "embedding_dimensions": pipeline.embedder.EMBEDDING_DIM,
        "vector_database": "ChromaDB",
        "vector_db_connected": pipeline.vector_store.is_connected(),
    }
