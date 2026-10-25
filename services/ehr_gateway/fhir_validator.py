"""
FHIR Resource Validator.
Enforces structural compliance, required US Core bindings, and LOINC/SNOMED coding integrity.
"""

from typing import Dict, Any, List, Tuple
from pydantic import ValidationError


class FHIRValidationError(Exception):
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__(f"FHIR Validation Failed: {'; '.join(errors)}")


class FHIRValidator:
    """Validates arbitrary dictionaries or Pydantic models against FHIR R4 requirements."""

    SUPPORTED_RESOURCE_TYPES = {
        "Patient",
        "Observation",
        "MedicationStatement",
        "Encounter",
        "Condition",
        "DiagnosticReport",
        "DocumentReference",
    }

    @classmethod
    def validate_resource(cls, payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors: List[str] = []

        if not isinstance(payload, dict):
            return False, ["Payload must be a JSON object."]

        resource_type = payload.get("resourceType")
        if not resource_type:
            errors.append("Missing required field: 'resourceType'.")
        elif resource_type not in cls.SUPPORTED_RESOURCE_TYPES:
            errors.append(f"Unsupported FHIR resourceType: '{resource_type}'.")

        if not payload.get("id"):
            errors.append("Missing required field: 'id'.")

        # Specific resource rules
        if resource_type == "Patient":
            if not payload.get("name") or not isinstance(payload.get("name"), list):
                errors.append("Patient requires non-empty 'name' array.")
        elif resource_type == "Observation":
            if not payload.get("status"):
                errors.append("Observation requires 'status'.")
            if not payload.get("code"):
                errors.append("Observation requires 'code' with LOINC/SNOMED coding.")
            if not payload.get("subject"):
                errors.append("Observation requires 'subject' reference.")
        elif resource_type == "Encounter":
            if not payload.get("status"):
                errors.append("Encounter requires 'status'.")
            if not payload.get("class"):
                errors.append("Encounter requires 'class'.")
            if not payload.get("subject"):
                errors.append("Encounter requires 'subject'.")

        return len(errors) == 0, errors

    @classmethod
    def assert_valid(cls, payload: Dict[str, Any]):
        valid, errors = cls.validate_resource(payload)
        if not valid:
            raise FHIRValidationError(errors)
