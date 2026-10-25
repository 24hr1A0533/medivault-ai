"""
FastAPI REST API routes for MediVault Doctor Consultation Summary Engine.
"""
from fastapi import APIRouter, HTTPException, status
from medivault_doctor_summary.schemas.summary_schema import (
    DoctorSummaryRequest,
    DoctorConsultationSummaryResponse,
)
from medivault_doctor_summary.service import DoctorConsultationService

router = APIRouter(prefix="/api/v1/doctor-summary", tags=["Doctor Consultation Summary"])

_service = DoctorConsultationService()

@router.post("/generate", response_model=DoctorConsultationSummaryResponse, status_code=status.HTTP_200_OK)
async def generate_consultation_summary(request: DoctorSummaryRequest):
    """
    Synthesizes all patient medical records and generates a concise,
    citation-grounded doctor consultation briefing note.
    """
    try:
        return _service.generate_summary(request)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Doctor summary generation failed: {str(exc)}",
        )

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {
        "status": "healthy",
        "service": "medivault-doctor-summary-engine",
        "version": "1.0.0",
        "capabilities": [
            "Current Conditions",
            "Recent Reports",
            "Abnormal Findings",
            "Current Medications",
            "Upcoming Followups",
            "Questions To Discuss With Physician",
        ],
    }
