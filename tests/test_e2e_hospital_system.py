"""
End-to-End Enterprise Hospital System Integration Test.
Simulates real hospital admission, lab ingestion, FHIR query,
emergency case file retrieval, and tenant billing.
"""

import pytest
import time
from services.ehr_gateway.hl7.adt_parser import HL7ADTParser
from services.ehr_gateway.hl7.oru_parser import HL7ORUParser
from services.ehr_gateway.fhir_mapper import FHIRMapper
from services.ehr_gateway.fhir_server import FHIRServer
from services.emergency_service.emergency_engine import EmergencyCaseFileEngine, EmergencyContact
from services.triage_service.visual_triage import VisualTriageAI, VisualTriageRequest
from services.tenant_service.tenant_repository import TenantRepository, SubscriptionTier
from services.tenant_service.tenant_billing import TenantBillingEngine
from datetime import datetime, timezone, timedelta


def test_full_hospital_admission_to_emergency_flow():
    # 1. HL7 ADT Patient Admission arrives over MLLP
    raw_adt = (
        "MSH|^~\\&|EPIC|FACILITY|MEDIVAULT|HOSPITAL|20261024120000||ADT^A01|MSG9901|P|2.5\r"
        "EVN|A01|20261024120000\r"
        "PID|1||MRN-8920192||DOE^JOHN^A||19680412|M\r"
        "PV1|1|E|RESUS-01||||DR_JENKINS^SARAH\r"
    )
    adt = HL7ADTParser.parse(raw_adt)
    assert adt.mrn == "MRN-8920192"

    # 2. Convert to FHIR Patient and store
    fhir_patient = FHIRMapper.patient_to_fhir(
        patient_id="p-1001",
        name=f"{adt.patient_given_name} {adt.patient_family_name}",
        gender="male",
        birth_date="1968-04-12",
        mrn=adt.mrn,
    )
    fhir_server = FHIRServer()
    fhir_server.save_resource("Patient", "p-1001", fhir_patient.model_dump())

    # 3. Lab Observation arrives via HL7 ORU
    raw_oru = (
        "MSH|^~\\&|LAB_SYS|FACILITY|MEDIVAULT|HOSPITAL|20261024120500||ORU^R01|MSG9902|P|2.5\r"
        "PID|1||MRN-8920192||DOE^JOHN\r"
        "OBR|1||ORD881|2345-7^GLUCOSE_PANEL\r"
        "OBX|1|NM|2345-7^GLUCOSE^LN||104|mg/dL|70-99|H|||F\r"
    )
    oru = HL7ORUParser.parse(raw_oru)
    assert len(oru.results) == 1
    glucose_res = oru.results[0]

    fhir_obs = FHIRMapper.lab_marker_to_fhir_observation(
        patient_id="p-1001",
        marker_name=glucose_res.name,
        value=float(glucose_res.value),
        unit=glucose_res.units,
        effective_date="2026-10-24T12:05:00Z",
    )
    fhir_server.save_resource("Observation", fhir_obs.id, fhir_obs.model_dump())

    # 4. Emergency Case File generation - Benchmark sub-2s SLA
    emergency_engine = EmergencyCaseFileEngine()
    start_time = time.perf_counter()
    raw_clinical_records = [
        {
            "category": "ALLERGY",
            "content": "Severe Penicillin allergy resulting in laryngeal edema and anaphylaxis.",
            "report_name": "Emergency Department Intake 2024",
            "report_date": "2024-05-12",
        },
        {
            "category": "MEDICATION",
            "content": "Apixaban (Eliquis) 5mg BID for atrial fibrillation thromboembolism prophylaxis.",
            "report_name": "Cardiology Consultation Note",
            "report_date": "2026-09-01",
        },
    ]
    contacts = [EmergencyContact(name="Mary Doe", relationship="Spouse", phone_number="+1-555-0199")]
    case_file = emergency_engine.compile_case_file(
        patient_id="p-1001",
        patient_name="John Alexander Doe",
        dob="1968-04-12",
        blood_group="O-NEGATIVE",
        raw_records=raw_clinical_records,
        emergency_contacts=contacts,
    )
    duration = time.perf_counter() - start_time

    assert duration < 2.0  # Must be strictly under 2.0s SLA
    assert case_file.blood_group == "O-NEGATIVE"
    assert any(a.allergen == "Penicillin" for a in case_file.allergies)

    # 5. Visual Urgency Triage Execution
    triage_engine = VisualTriageAI()
    req = VisualTriageRequest(
        patient_id="p-1001",
        image_url_or_b64="data:image/jpeg;base64,/9j/4AAQSkZJRg==",
        symptom_description="Severe crushing retrosternal chest pain radiating to left arm, diaphoresis, dyspnea",
        pain_level_1_to_10=10,
        patient_history_context={"cardiac_risk": "HIGH", "shock_index": 1.56},
    )
    triage_result = triage_engine.process_triage(req)
    assert triage_result.urgency_level.value.startswith("Emergency Care Needed")
    assert triage_result.processing_time_ms < 500

    # 6. Tenant Billing Generation for Hospital Network
    billing = TenantBillingEngine()
    now = datetime.now(timezone.utc)
    invoice = billing.generate_monthly_invoice(
        tenant_id="mayo-clinic-system",
        tier=SubscriptionTier.ENTERPRISE,
        period_start=now - timedelta(days=30),
        period_end=now,
    )
    assert invoice.total_amount_due == 45000.00
