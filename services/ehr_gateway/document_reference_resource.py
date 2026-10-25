"""
FHIR R4 DocumentReference Resource Definition.
Represents clinical notes, discharge summaries, and external C-CDA/PDF medical records.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from .observation_resource import CodeableConcept, Reference
from .patient_resource import Identifier
from .diagnostic_report_resource import Attachment


class Content(BaseModel):
    attachment: Attachment
    format: Optional[Dict[str, str]] = None


class Context(BaseModel):
    encounter: List[Reference] = Field(default_factory=list)
    period: Optional[Dict[str, str]] = None


class FHIRDocumentReference(BaseModel):
    resourceType: str = "DocumentReference"
    id: str
    masterIdentifier: Optional[Identifier] = None
    status: str = "current"  # current | superseded | entered-in-error
    type: CodeableConcept
    category: List[CodeableConcept] = Field(default_factory=list)
    subject: Reference
    date: Optional[str] = None
    author: List[Reference] = Field(default_factory=list)
    description: Optional[str] = None
    content: List[Content]
    context: Optional[Context] = None
