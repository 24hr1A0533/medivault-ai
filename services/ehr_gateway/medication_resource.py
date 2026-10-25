"""
FHIR R4 MedicationStatement Resource Definition.
Represents active, historical, and prescribed patient medications with RxNorm coding.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from .observation_resource import CodeableConcept, Reference


class Dosage(BaseModel):
    text: str
    timing: Optional[Dict[str, Any]] = None
    route: Optional[CodeableConcept] = None
    doseQuantity: Optional[Dict[str, Any]] = None


class FHIRMedicationStatement(BaseModel):
    resourceType: str = "MedicationStatement"
    id: str
    status: str = "active"  # active | completed | entered-in-error | intended | stopped | on-hold
    medicationCodeableConcept: CodeableConcept
    subject: Reference
    effectiveDateTime: Optional[str] = None
    dateAsserted: Optional[str] = None
    dosage: List[Dosage] = Field(default_factory=list)
    note: List[Dict[str, str]] = Field(default_factory=list)
