"""
FHIR Bidirectional Mapper.
Transforms internal MediVault clinical models (Emergency Case Files, Lab Findings,
OCR Extracts, Doctor Summaries) into standard FHIR R4 resources and vice versa.
"""

from typing import Dict, Any, List
import uuid
from datetime import datetime, timezone

from .patient_resource import FHIRPatient, HumanName, Identifier
from .observation_resource import FHIRObservation, CodeableConcept, Coding, Quantity, Reference
from .medication_resource import FHIRMedicationStatement, Dosage
from .condition_resource import FHIRCondition
from .diagnostic_report_resource import FHIRDiagnosticReport, Attachment


class FHIRMapper:
    """Translates MediVault internal entities to standard FHIR R4 structures."""

    @staticmethod
    def patient_to_fhir(
        patient_id: str,
        name: str,
        gender: str = "male",
        birth_date: str = "1968-04-12",
        mrn: str = "",
    ) -> FHIRPatient:
        parts = name.strip().split(" ")
        family = parts[-1] if len(parts) > 1 else name
        given = parts[:-1] if len(parts) > 1 else [name]

        identifiers = [
            Identifier(system="urn:medivault:patient:id", value=patient_id)
        ]
        if mrn:
            identifiers.append(Identifier(system="http://hospital.org/mrn", value=mrn))

        return FHIRPatient(
            id=patient_id,
            identifier=identifiers,
            active=True,
            name=[HumanName(family=family, given=given)],
            gender=gender.lower(),
            birthDate=birth_date,
        )

    @staticmethod
    def lab_marker_to_fhir_observation(
        patient_id: str,
        marker_name: str,
        value: float,
        unit: str,
        effective_date: str,
        loinc_code: str = "2345-7",
    ) -> FHIRObservation:
        obs_id = f"obs-{uuid.uuid4().hex[:8]}"
        return FHIRObservation(
            id=obs_id,
            status="final",
            code=CodeableConcept(
                coding=[Coding(system="http://loinc.org", code=loinc_code, display=marker_name)],
                text=marker_name,
            ),
            subject=Reference(reference=f"Patient/{patient_id}"),
            effectiveDateTime=effective_date,
            valueQuantity=Quantity(value=value, unit=unit, code=unit),
        )

    @staticmethod
    def medication_to_fhir(
        patient_id: str,
        drug_name: str,
        dosage_text: str,
        rxnorm_code: str = "860975",
    ) -> FHIRMedicationStatement:
        med_id = f"med-{uuid.uuid4().hex[:8]}"
        return FHIRMedicationStatement(
            id=med_id,
            status="active",
            medicationCodeableConcept=CodeableConcept(
                coding=[Coding(system="http://www.nlm.nih.gov/research/umls/rxnorm", code=rxnorm_code, display=drug_name)],
                text=drug_name,
            ),
            subject=Reference(reference=f"Patient/{patient_id}"),
            dateAsserted=datetime.now(timezone.utc).isoformat(),
            dosage=[Dosage(text=dosage_text)],
        )

    @staticmethod
    def diagnosis_to_fhir_condition(
        patient_id: str,
        condition_name: str,
        icd10_code: str = "E11.9",
    ) -> FHIRCondition:
        cond_id = f"cond-{uuid.uuid4().hex[:8]}"
        return FHIRCondition(
            id=cond_id,
            clinicalStatus=CodeableConcept(
                coding=[Coding(system="http://terminology.hl7.org/CodeSystem/condition-clinical", code="active", display="Active")]
            ),
            code=CodeableConcept(
                coding=[Coding(system="http://hl7.org/fhir/sid/icd-10-cm", code=icd10_code, display=condition_name)],
                text=condition_name,
            ),
            subject=Reference(reference=f"Patient/{patient_id}"),
            recordedDate=datetime.now(timezone.utc).date().isoformat(),
        )
