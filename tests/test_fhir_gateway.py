"""
Unit and Integration Tests for EHR Gateway & FHIR R4 Engine.
Tests FHIR validation, resource mapping, US Core conformance, and REST interactions.
"""

import pytest
from services.ehr_gateway.patient_resource import FHIRPatient, HumanName
from services.ehr_gateway.observation_resource import FHIRObservation, CodeableConcept, Coding, Quantity, Reference
from services.ehr_gateway.fhir_validator import FHIRValidator, FHIRValidationError
from services.ehr_gateway.fhir_mapper import FHIRMapper
from services.ehr_gateway.fhir_server import FHIRServer


def test_fhir_patient_validation_success():
    valid_patient = {
        "resourceType": "Patient",
        "id": "pat-101",
        "name": [{"use": "official", "family": "Smith", "given": ["Alice"]}],
        "gender": "female",
    }
    is_valid, errors = FHIRValidator.validate_resource(valid_patient)
    assert is_valid is True
    assert len(errors) == 0


def test_fhir_patient_validation_failure():
    invalid_patient = {
        "resourceType": "Patient",
        # Missing id
        "name": [],  # Empty name
    }
    is_valid, errors = FHIRValidator.validate_resource(invalid_patient)
    assert is_valid is False
    assert any("id" in err for err in errors)
    assert any("name" in err for err in errors)


def test_fhir_mapper_internal_to_fhir():
    patient = FHIRMapper.patient_to_fhir(
        patient_id="p-9901",
        name="Robert C. Taylor",
        gender="male",
        birth_date="1975-11-20",
        mrn="MRN-7712",
    )
    assert patient.id == "p-9901"
    assert patient.name[0].family == "Taylor"
    assert "Robert" in patient.name[0].given
    assert patient.gender == "male"
    assert any(ident.value == "MRN-7712" for ident in patient.identifier)

    # Observation mapper
    obs = FHIRMapper.lab_marker_to_fhir_observation(
        patient_id="p-9901",
        marker_name="HbA1c",
        value=6.4,
        unit="%",
        effective_date="2026-10-24T09:30:00Z",
        loinc_code="4548-4",
    )
    assert obs.status == "final"
    assert obs.subject.reference == "Patient/p-9901"
    assert obs.valueQuantity.value == 6.4
    assert obs.code.coding[0].code == "4548-4"


def test_fhir_server_rest_interactions():
    server = FHIRServer()

    # Search existing seeded patient
    patient = server.get_resource("Patient", "p-1001")
    assert patient is not None
    assert patient["id"] == "p-1001"

    # Search observations
    obs_results = server.search_resources("Observation", {"patient": "p-1001"})
    assert len(obs_results) >= 1
    assert obs_results[0]["valueQuantity"]["value"] == 104.0

    # Save new condition
    cond = {
        "resourceType": "Condition",
        "id": "cond-t2dm-1",
        "clinicalStatus": {"coding": [{"code": "active"}]},
        "code": {"coding": [{"code": "E11.9", "display": "Type 2 diabetes"}]},
        "subject": {"reference": "Patient/p-1001"},
    }
    server.save_resource("Condition", "cond-t2dm-1", cond)
    found_cond = server.get_resource("Condition", "cond-t2dm-1")
    assert found_cond is not None
    assert found_cond["code"]["coding"][0]["code"] == "E11.9"
