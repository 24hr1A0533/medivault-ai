"""
FHIR R4 Observation Resource Definition.
Models clinical lab results, vital signs, and biomarker measurements with LOINC coding.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class Coding(BaseModel):
    system: str = "http://loinc.org"
    code: str
    display: str


class CodeableConcept(BaseModel):
    coding: List[Coding]
    text: Optional[str] = None


class Reference(BaseModel):
    reference: str
    display: Optional[str] = None


class Quantity(BaseModel):
    value: float
    unit: str
    system: str = "http://unitsofmeasure.org"
    code: str


class ReferenceRange(BaseModel):
    low: Optional[Quantity] = None
    high: Optional[Quantity] = None
    text: Optional[str] = None


class FHIRObservation(BaseModel):
    resourceType: str = "Observation"
    id: str
    status: str = "final"  # registered | preliminary | final | amended
    category: List[CodeableConcept] = Field(default_factory=list)
    code: CodeableConcept
    subject: Reference
    effectiveDateTime: str
    valueQuantity: Optional[Quantity] = None
    valueString: Optional[str] = None
    interpretation: List[CodeableConcept] = Field(default_factory=list)
    referenceRange: List[ReferenceRange] = Field(default_factory=list)
