"""
Production Pydantic v2 Schemas for Healthcare Document Intelligence
Defines structured medical knowledge models:
- Patient Demographics
- Medical Lab Test Data
- Prescription Matrix
- Document Extraction & Verification States
- Semantic Search Requests and Responses
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date, timezone
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_validator


class VerificationStatus(str, Enum):
    UNPROCESSED = "UNPROCESSED"
    EXTRACTED = "EXTRACTED"
    FLAGGED_FOR_REVIEW = "FLAGGED_FOR_REVIEW"
    AUTO_VERIFIED = "AUTO_VERIFIED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class DocumentCategory(str, Enum):
    LAB_REPORT = "LAB_REPORT"
    PRESCRIPTION = "PRESCRIPTION"
    DISCHARGE_SUMMARY = "DISCHARGE_SUMMARY"
    CLINICAL_NOTE = "CLINICAL_NOTE"
    IMAGING_REPORT = "IMAGING_REPORT"
    OTHER = "OTHER"


class PatientDetails(BaseModel):
    """Extracted patient demographic baseline."""
    name: Optional[str] = Field(default=None, description="Patient full legal name")
    age: Optional[int] = Field(default=None, ge=0, le=130, description="Patient age in years")
    gender: Optional[str] = Field(default=None, description="Patient gender (Male, Female, Other)")
    blood_group: Optional[str] = Field(default=None, description="ABO + Rh blood group (e.g. O+, A+, B-, AB+)")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score for demographics")

    model_config = ConfigDict(from_attributes=True)


class LabTestItem(BaseModel):
    """Quantitative or qualitative laboratory test result."""
    test_name: str = Field(description="Name of medical test (e.g. Hemoglobin, Fasting Glucose)")
    value: Union[float, str] = Field(description="Quantitative numeric value or qualitative finding")
    unit: Optional[str] = Field(default=None, description="Measurement unit (e.g. mg/dL, g/dL, %)")
    reference_range: Optional[str] = Field(default=None, description="Normal biological reference range")
    is_abnormal: Optional[bool] = Field(default=None, description="Flag indicating out-of-range clinical value")
    loinc_code: Optional[str] = Field(default=None, description="Standardized LOINC ontology code")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score for this specific test item")

    model_config = ConfigDict(from_attributes=True)


class MedicalData(BaseModel):
    """Aggregated clinical findings and laboratory data."""
    tests: List[LabTestItem] = Field(default_factory=list, description="List of extracted medical tests")
    report_date: Optional[date] = Field(default=None, description="Specimen collection or report issuance date")
    hospital: Optional[str] = Field(default=None, description="Hospital, laboratory, or healthcare facility name")
    category: DocumentCategory = Field(default=DocumentCategory.LAB_REPORT, description="Classified document category")
    clinical_notes: Optional[str] = Field(default=None, description="Clinical impression, diagnosis, or remarks")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score for medical data")

    model_config = ConfigDict(from_attributes=True)


class PrescriptionItem(BaseModel):
    """Structured pharmaceutical prescription medication."""
    medicine: str = Field(description="Generic pharmaceutical or brand name")
    dosage: Optional[str] = Field(default=None, description="Strength / dose (e.g. 500mg, 10ml, 5mcg)")
    frequency: Optional[str] = Field(default=None, description="Administration frequency (e.g. OD, BD, TID, PRN)")
    duration: Optional[str] = Field(default=None, description="Treatment course duration (e.g. 5 days, 1 month)")
    rxnorm_code: Optional[str] = Field(default=None, description="Standardized RxNorm Concept Unique Identifier (RxCUI)")
    instructions: Optional[str] = Field(default=None, description="Special route or administration instructions")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score for this medication entry")

    model_config = ConfigDict(from_attributes=True)


class StructuredMedicalDocument(BaseModel):
    """Comprehensive structured medical document representation."""
    document_id: str = Field(description="Unique document UUID")
    patient_id: Optional[str] = Field(default=None, description="Patient identifier")
    patient_details: PatientDetails = Field(default_factory=PatientDetails)
    medical_data: MedicalData = Field(default_factory=MedicalData)
    prescriptions: List[PrescriptionItem] = Field(default_factory=list)
    overall_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    verification_status: VerificationStatus = Field(default=VerificationStatus.UNPROCESSED)
    raw_text: Optional[str] = Field(default=None, description="Raw OCR extracted text layer")
    ocr_engine: str = Field(default="PaddleOCR")
    nlp_engine: str = Field(default="BioBERT+ClinicalBERT")
    embedding_model: str = Field(default="BAAI/bge-large-en-v1.5")
    vector_id: Optional[str] = Field(default=None, description="ID of indexed vector in ChromaDB")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    reviewer_notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class VerificationAction(str, Enum):
    APPROVE = "APPROVE"
    EDIT = "EDIT"
    REJECT = "REJECT"


class VerificationRequest(BaseModel):
    """Clinician Human-in-the-Loop (HITL) verification action."""
    action: VerificationAction
    verified_by: str = Field(description="Clinician or administrator user identifier")
    reviewer_notes: Optional[str] = None
    edited_patient_details: Optional[PatientDetails] = None
    edited_medical_data: Optional[MedicalData] = None
    edited_prescriptions: Optional[List[PrescriptionItem]] = None


class DocumentProcessResponse(BaseModel):
    """Response returned upon processing a medical document."""
    success: bool
    document_id: str
    patient_id: Optional[str]
    verification_status: VerificationStatus
    overall_confidence: float
    structured_document: StructuredMedicalDocument
    processing_time_ms: float
    message: str


class VectorQueryRequest(BaseModel):
    """Semantic vector search query for clinical records."""
    patient_id: Optional[str] = Field(default=None, description="Restrict search to specific patient")
    query: str = Field(description="Natural language clinical question or search keywords")
    n_results: int = Field(default=5, ge=1, le=50, description="Top K nearest records to retrieve")
    category_filter: Optional[DocumentCategory] = None
    min_confidence: Optional[float] = Field(default=0.0, ge=0.0, le=1.0)


class VectorSearchResultItem(BaseModel):
    """Individual semantic search result item retrieved from ChromaDB."""
    document_id: str
    patient_id: Optional[str]
    similarity_score: float
    distance: float
    category: str
    report_date: Optional[str]
    hospital: Optional[str]
    content_snippet: str
    metadata: Dict[str, Any]


class VectorQueryResponse(BaseModel):
    """Response container for semantic vector queries."""
    query: str
    total_found: int
    results: List[VectorSearchResultItem]
