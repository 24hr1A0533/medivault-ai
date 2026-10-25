"""
FastAPI REST API Routes for Unified MediVault Medical LLM Platform.
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from medivault_medical_llm.services.unified_service import UnifiedMedicalLLMService
from medivault_trend_engine.schemas.trend_schema import BiomarkerMeasurement
from medivault_doctor_summary.schemas.summary_schema import DoctorSummaryRequest

router = APIRouter(prefix="/api/v1/medical-llm", tags=["MediVault Medical LLM"])

_service = UnifiedMedicalLLMService()

class OCRRequest(BaseModel):
    document_id: str
    report_name: str
    report_date: str
    raw_content: str
    page_number: int = 1

class IngestRequest(BaseModel):
    patient_id: str
    document_id: str
    report_name: str
    report_date: str
    content: str
    page_number: int = 1
    category: str = "LAB_REPORT"

class RAGQueryRequest(BaseModel):
    patient_id: str
    query: str
    top_k: int = 5

class ExplainRequest(BaseModel):
    patient_id: str
    report_text: str
    report_name: str
    report_date: str
    page_number: int = 1

class TrendRequest(BaseModel):
    patient_id: str
    measurements: List[BiomarkerMeasurement]

@router.post("/ocr", status_code=status.HTTP_200_OK)
async def process_ocr(request: OCRRequest):
    """Capability 1: Medical OCR & Layout Understanding."""
    return _service.process_ocr_document(
        document_id=request.document_id,
        report_name=request.report_name,
        report_date=request.report_date,
        raw_content=request.raw_content,
        page_number=request.page_number,
    )

@router.post("/extract-entities", status_code=status.HTTP_200_OK)
async def extract_entities(request: OCRRequest):
    """Capability 2: Medical Knowledge Extraction."""
    return _service.extract_medical_knowledge(
        document_text=request.raw_content,
        report_name=request.report_name,
        report_date=request.report_date,
        page_number=request.page_number,
    )

@router.post("/ingest", status_code=status.HTTP_201_CREATED)
async def ingest_document(request: IngestRequest):
    """Capability 3 & 10: Ingest into Isolated ChromaDB Vector Store."""
    chunk_count = _service.ingest_patient_document(
        patient_id=request.patient_id,
        document_id=request.document_id,
        report_name=request.report_name,
        report_date=request.report_date,
        content=request.content,
        page_number=request.page_number,
        category=request.category,
    )
    return {"status": "ingested", "chunks_indexed": chunk_count, "patient_id": request.patient_id}

@router.post("/query-rag", status_code=status.HTTP_200_OK)
async def query_rag(request: RAGQueryRequest):
    """Capability 3, 7, 8, 9, 10: Patient-Specific RAG with Safety Guardrails & Hallucination Checks."""
    return _service.query_patient_rag(
        patient_id=request.patient_id,
        query=request.query,
        top_k=request.top_k,
    )

@router.post("/explain-report", status_code=status.HTTP_200_OK)
async def explain_report(request: ExplainRequest):
    """Capability 4: Medical Report Explanation."""
    return _service.explain_medical_report(
        patient_id=request.patient_id,
        report_text=request.report_text,
        report_name=request.report_name,
        report_date=request.report_date,
        page_number=request.page_number,
    )

@router.post("/trends", status_code=status.HTTP_200_OK)
async def analyze_trends(request: TrendRequest):
    """Capability 5: Medical Trend Analysis & Graphing."""
    return _service.analyze_medical_trends(
        patient_id=request.patient_id,
        measurements=request.measurements,
    )

@router.post("/doctor-summary", status_code=status.HTTP_200_OK)
async def generate_doctor_summary(request: DoctorSummaryRequest):
    """Capability 6: Doctor Consultation Briefing Note."""
    return _service.generate_doctor_summary(request)

@router.get("/capabilities", status_code=status.HTTP_200_OK)
async def list_capabilities():
    """Returns the 10 core clinical AI capabilities."""
    return {
        "platform": "MediVault Medical LLM",
        "model": "Qwen 2.5 7B",
        "embedding": "BAAI BGE Large (1024-dim)",
        "vector_database": "ChromaDB",
        "inference_engine": "vLLM",
        "capabilities": [
            "1. Medical OCR Understanding",
            "2. Medical Knowledge Extraction",
            "3. Patient-Specific RAG",
            "4. Medical Report Explanation",
            "5. Medical Trend Analysis",
            "6. Doctor Summary Generation",
            "7. Medical Safety Guardrails",
            "8. Citation Engine",
            "9. Hallucination Detection",
            "10. Multi-user Isolation",
        ],
    }

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {
        "status": "healthy",
        "service": "medivault-medical-llm",
        "version": "1.0.0",
        "hipaa_phi_masking": True,
        "zero_hallucination_policy": True,
    }
