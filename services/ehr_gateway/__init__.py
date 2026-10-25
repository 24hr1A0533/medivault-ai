"""
MediVault AI EHR Gateway & FHIR R4 Service Package.
Provides standardized HL7 FHIR R4 resource definitions, validation, mapping,
and FHIR REST server capabilities.
"""

from .patient_resource import FHIRPatient
from .observation_resource import FHIRObservation
from .medication_resource import FHIRMedicationStatement
from .encounter_resource import FHIREncounter
from .condition_resource import FHIRCondition
from .diagnostic_report_resource import FHIRDiagnosticReport
from .document_reference_resource import FHIRDocumentReference
from .fhir_validator import FHIRValidator
from .fhir_mapper import FHIRMapper
from .fhir_server import FHIRServer, fhir_router

__all__ = [
    "FHIRPatient",
    "FHIRObservation",
    "FHIRMedicationStatement",
    "FHIREncounter",
    "FHIRCondition",
    "FHIRDiagnosticReport",
    "FHIRDocumentReference",
    "FHIRValidator",
    "FHIRMapper",
    "FHIRServer",
    "fhir_router",
]
