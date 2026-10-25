"""
FHIR R4 DiagnosticReport Resource Definition.
Represents laboratory panels, radiology imaging summaries, and pathology reports.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from .observation_resource import CodeableConcept, Reference
from .patient_resource import Identifier


class Attachment(BaseModel):
    contentType: str = "application/pdf"
    language: Optional[str] = "en"
    data: Optional[str] = None  # Base64
    url: Optional[str] = None
    title: Optional[str] = None


class Media(BaseModel):
    comment: Optional[str] = None
    link: Reference


class FHIRDiagnosticReport(BaseModel):
    resourceType: str = "DiagnosticReport"
    id: str
    identifier: List[Identifier] = Field(default_factory=list)
    status: str = "final"  # registered | partial | preliminary | final | amended | corrected
    category: List[CodeableConcept] = Field(default_factory=list)
    code: CodeableConcept
    subject: Reference
    encounter: Optional[Reference] = None
    effectiveDateTime: Optional[str] = None
    issued: Optional[str] = None
    performer: List[Reference] = Field(default_factory=list)
    result: List[Reference] = Field(default_factory=list)  # Pointers to Observation resources
    media: List[Media] = Field(default_factory=list)
    presentedForm: List[Attachment] = Field(default_factory=list)
    conclusion: Optional[str] = None
