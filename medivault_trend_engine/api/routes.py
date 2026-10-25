"""
FastAPI REST API routes for MediVault Medical Trend Analysis Engine.
"""
from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any, Optional

from medivault_trend_engine.schemas.trend_schema import (
    PatientTrendAnalysisRequest,
    PatientTrendAnalysisResponse,
    BiomarkerMeasurement,
)
from medivault_trend_engine.engine.trend_analyzer import ClinicalTrendAnalyzer
from medivault_trend_engine.extractor.report_parser import ClinicalReportParser
from medivault_trend_engine.biomarkers.biomarker_catalog import CATALOG

router = APIRouter(prefix="/api/v1/trends", tags=["Medical Trend Analysis"])

_analyzer = ClinicalTrendAnalyzer()
_parser = ClinicalReportParser()

@router.post("/analyze", response_model=PatientTrendAnalysisResponse, status_code=status.HTTP_200_OK)
async def analyze_patient_trends(request: PatientTrendAnalysisRequest):
    """
    Analyzes historical patient reports, extracts actual biomarker measurements,
    generates trend graphs, alerts, and doctor-ready summaries.
    """
    try:
        measurements: List[BiomarkerMeasurement] = []

        # 1. Use pre-parsed measurements if supplied
        if request.preparsed_measurements:
            measurements.extend(request.preparsed_measurements)

        # 2. Parse raw reports if supplied
        if request.raw_reports:
            for rep in request.raw_reports:
                text = rep.get("text", "")
                name = rep.get("report_name", "Clinical Report")
                date = rep.get("report_date", "2026-01-01")
                page = rep.get("page_number", 1)
                doc_id = rep.get("document_id")

                parsed = _parser.parse_report_text(
                    text=text,
                    report_name=name,
                    report_date=date,
                    page_number=page,
                    document_id=doc_id,
                )
                measurements.extend(parsed)

        return _analyzer.analyze_patient_trends(
            patient_id=request.patient_id,
            measurements=measurements,
            target_biomarkers=request.target_biomarkers,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trend analysis failed: {str(exc)}",
        )

@router.get("/supported-markers", status_code=status.HTTP_200_OK)
async def get_supported_markers():
    """
    Returns the catalog of clinical biomarkers, reference ranges, and directionality.
    """
    return {
        name: {
            "canonical_name": profile.canonical_name,
            "unit": profile.default_unit,
            "normal_range": f"{profile.normal_min} - {profile.normal_max} {profile.default_unit}",
            "desired_direction": profile.desired_direction.value,
            "critical_high": profile.critical_high,
            "critical_low": profile.critical_low,
            "description": profile.clinical_description,
        }
        for name, profile in CATALOG.items()
    }

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {
        "status": "healthy",
        "service": "medivault-trend-engine",
        "version": "1.0.0",
        "catalog_size": len(CATALOG),
    }
