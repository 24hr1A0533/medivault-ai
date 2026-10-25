"""
Pydantic Schemas for MediVault Doctor Consultation Summary Engine.
"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class Citation(BaseModel):
    report_name: str = Field(..., description="Name of the source medical document")
    page_number: int = Field(..., description="1-indexed page number")
    report_date: str = Field(..., description="Date of the report YYYY-MM-DD")
    document_id: Optional[str] = None

class PatientRecordInput(BaseModel):
    document_id: str
    report_name: str
    report_date: str
    category: str = Field(default="LAB_REPORT", description="LAB_REPORT, PRESCRIPTION, DISCHARGE_SUMMARY, CLINICAL_NOTE, IMAGING")
    doctor_name: Optional[str] = None
    hospital: Optional[str] = None
    content: str = Field(..., description="Clinical text of the report")
    page_number: int = Field(default=1)
    extracted_data: Optional[Dict[str, Any]] = None

class ConditionItem(BaseModel):
    name: str
    status: str = Field(default="ACTIVE", description="ACTIVE, CHRONIC, RESOLVED, MANAGED")
    diagnosed_date: Optional[str] = None
    citation: Citation

class AbnormalFindingItem(BaseModel):
    test_name: str
    value: float
    unit: str
    reference_range: str
    clinical_interpretation: str = Field(..., description="Elevated, Low, Critical High, Critical Low")
    citation: Citation

class RecentReportItem(BaseModel):
    report_name: str
    report_date: str
    category: str
    key_impression: str
    citation: Citation

class MedicationItem(BaseModel):
    drug_name: str
    dosage: str
    frequency: str
    indication: Optional[str] = None
    prescribing_doctor: Optional[str] = None
    citation: Citation

class FollowupItem(BaseModel):
    specialty_or_test: str
    target_timeframe: str
    instructions: str
    citation: Citation

class DoctorSummaryRequest(BaseModel):
    patient_id: str = Field(..., min_length=1)
    patient_name: Optional[str] = Field(default=None)
    records: List[PatientRecordInput] = Field(..., min_length=1, description="All patient medical records to synthesize")
    focus_areas: Optional[List[str]] = Field(default=None, description="Optional focus areas (e.g. Cardiology, Glycemic control)")

class DoctorConsultationSummaryResponse(BaseModel):
    patient_id: str
    patient_name: Optional[str] = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    patient_summary: str
    current_conditions: List[ConditionItem]
    abnormal_findings: List[AbnormalFindingItem]
    recent_reports: List[RecentReportItem]
    current_medications: List[MedicationItem]
    upcoming_followups: List[FollowupItem]
    questions_to_discuss: List[str]
    formatted_markdown: str
    citations: List[Citation]
    processing_time_ms: float
