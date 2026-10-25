"""
FHIR R4 Condition Resource Definition.
Represents clinical diagnoses, problem list items, and medical conditions with ICD-10 / SNOMED-CT.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from .observation_resource import CodeableConcept, Reference


class FHIRCondition(BaseModel):
    resourceType: str = "Condition"
    id: str
    clinicalStatus: CodeableConcept
    verificationStatus: Optional[CodeableConcept] = None
    category: List[CodeableConcept] = Field(default_factory=list)
    severity: Optional[CodeableConcept] = None
    code: CodeableConcept
    subject: Reference
    encounter: Optional[Reference] = None
    onsetDateTime: Optional[str] = None
    recordedDate: Optional[str] = None
    asserter: Optional[Reference] = None
