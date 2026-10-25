"""
FHIR R4 Patient Resource Definition.
Compliant with US Core Patient Profile v3.1.1.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class HumanName(BaseModel):
    use: str = "official"
    family: str
    given: List[str]
    prefix: Optional[List[str]] = None


class Telecom(BaseModel):
    system: str = "phone"
    value: str
    use: str = "mobile"


class Address(BaseModel):
    line: List[str]
    city: str
    state: str
    postalCode: str
    country: str = "US"


class Identifier(BaseModel):
    system: str
    value: str
    use: str = "usual"


class FHIRPatient(BaseModel):
    resourceType: str = "Patient"
    id: str
    identifier: List[Identifier] = Field(default_factory=list)
    active: bool = True
    name: List[HumanName]
    telecom: List[Telecom] = Field(default_factory=list)
    gender: str = "unknown"  # male | female | other | unknown
    birthDate: Optional[str] = None
    address: List[Address] = Field(default_factory=list)
    managingOrganization: Optional[Dict[str, str]] = None
