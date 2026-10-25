"""
FHIR R4 Encounter Resource Definition.
Represents inpatient stays, emergency department visits, and outpatient consultations.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from .observation_resource import CodeableConcept, Reference


class Period(BaseModel):
    start: str
    end: Optional[str] = None


class Participant(BaseModel):
    type: List[CodeableConcept] = Field(default_factory=list)
    individual: Reference


class Location(BaseModel):
    location: Reference
    status: str = "active"


class FHIREncounter(BaseModel):
    resourceType: str = "Encounter"
    id: str
    status: str = "in-progress"  # planned | arrived | triaged | in-progress | onleave | finished | cancelled
    class_: Dict[str, str] = Field(..., alias="class")  # inpatient | outpatient | ambulatory | emergency
    type: List[CodeableConcept] = Field(default_factory=list)
    subject: Reference
    participant: List[Participant] = Field(default_factory=list)
    period: Period
    reasonCode: List[CodeableConcept] = Field(default_factory=list)
    location: List[Location] = Field(default_factory=list)

    model_config = {"populate_by_name": True}
