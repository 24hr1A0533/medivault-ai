"""
FastAPI REST API router for MediVault Medical AI Safety Guardrails.
"""
from fastapi import APIRouter, HTTPException, status
from medivault_guardrails.schemas.guardrail_schema import (
    InputCheckRequest,
    InputCheckResponse,
    OutputCheckRequest,
    OutputCheckResponse,
    SafetyProcessRequest,
    SafetyProcessResponse,
    STANDARD_SAFETY_RESPONSE,
    EMERGENCY_SAFETY_RESPONSE,
)
from medivault_guardrails.layer.safety_layer import ClinicalSafetyLayer

router = APIRouter(prefix="/api/v1/guardrails", tags=["Medical Safety Guardrails"])

_safety_layer = ClinicalSafetyLayer()

@router.post("/check-input", response_model=InputCheckResponse, status_code=status.HTTP_200_OK)
async def check_input(request: InputCheckRequest):
    """
    Evaluates an input query against Prompt Shield and Clinical Risk Classifier.
    """
    try:
        return _safety_layer.check_input(request)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Guardrail input check failed: {str(exc)}",
        )

@router.post("/check-output", response_model=OutputCheckResponse, status_code=status.HTTP_200_OK)
async def check_output(request: OutputCheckRequest):
    """
    Evaluates generated output text against Medical Output Filter.
    """
    try:
        return _safety_layer.check_output(request)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Guardrail output check failed: {str(exc)}",
        )

@router.post("/process", response_model=SafetyProcessResponse, status_code=status.HTTP_200_OK)
async def process_interaction(request: SafetyProcessRequest):
    """
    End-to-end processing: validates input prompt and filters output.
    """
    try:
        return _safety_layer.process(request)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Guardrail processing failed: {str(exc)}",
        )

@router.get("/rules", status_code=status.HTTP_200_OK)
async def get_guardrail_rules():
    """
    Returns clinical guardrail rules, allowed vs forbidden capabilities, and standard disclaimers.
    """
    return {
        "allowed_capabilities": [
            "explain reports",
            "summarize records",
            "compare trends",
            "explain medical terminology",
        ],
        "forbidden_capabilities": [
            "diagnose disease",
            "prescribe medicine",
            "suggest dosage",
            "replace doctors",
            "recommend treatment plans",
        ],
        "explicit_forbidden_responses": [
            "you have diabetes",
            "stop taking medicine",
            "increase dosage",
        ],
        "allowed_response_example": "this report shows elevated glucose values",
        "standard_safety_response": STANDARD_SAFETY_RESPONSE,
        "emergency_safety_response": EMERGENCY_SAFETY_RESPONSE,
    }

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {
        "status": "healthy",
        "service": "medivault-medical-guardrails",
        "version": "1.0.0",
        "protection_status": "active",
    }
