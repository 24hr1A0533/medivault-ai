"""
Test suite for MediVault Doctor Consultation Summary Engine.

Verifies:
- Ingestion of all patient medical records
- Extraction of Current Conditions, Recent Reports, Abnormal Findings, Current Medications, Upcoming Followups
- Generation of high-yield Questions To Discuss With Physician
- Exact required format structure:
  Patient Summary
  Abnormal Findings
  Recent Reports
  Current Medications
  Questions To Discuss With Physician
- Citation grounding on every clinical bullet item
- FastAPI REST endpoint integration
"""
import pytest
from fastapi.testclient import TestClient

from medivault_doctor_summary.schemas.summary_schema import (
    PatientRecordInput,
    DoctorSummaryRequest,
)
from medivault_doctor_summary.service import DoctorConsultationService
from medivault_doctor_summary.main import app

@pytest.fixture
def service():
    return DoctorConsultationService()

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def sample_patient_records():
    return [
        PatientRecordInput(
            document_id="DOC-LAB-001",
            report_name="Comprehensive Metabolic Lab",
            report_date="2026-06-15",
            category="LAB_REPORT",
            doctor_name="Sarah Jenkins",
            hospital="Metro General Hospital",
            page_number=1,
            content="""
            CLINICAL LABORATORY FINDINGS:
            Fasting Blood Glucose: 148 mg/dL (Reference: 70 - 99 mg/dL) [HIGH]
            HbA1c: 8.2 % (Reference: 4.0 - 5.6%) [ELEVATED]
            Serum Creatinine: 1.1 mg/dL (Reference: 0.7 - 1.3 mg/dL) [NORMAL]
            Total Cholesterol: 228 mg/dL (Reference: < 200 mg/dL) [ELEVATED]
            LDL Cholesterol: 142 mg/dL (Reference: < 100 mg/dL) [ELEVATED]
            """,
        ),
        PatientRecordInput(
            document_id="DOC-RX-002",
            report_name="Ambulatory Prescription Slip",
            report_date="2026-06-16",
            category="PRESCRIPTION",
            doctor_name="Robert Vance",
            hospital="Cardiometabolic Center",
            page_number=1,
            content="""
            PRESCRIPTION ORDER:
            1. Metformin 500mg twice daily orally with meals.
            2. Lisinopril 10mg once daily in the morning.
            3. Atorvastatin 20mg once daily at bedtime.
            Refills: 3
            """,
        ),
        PatientRecordInput(
            document_id="DOC-NOTE-003",
            report_name="Cardiology Progress Note",
            report_date="2026-06-20",
            category="CLINICAL_NOTE",
            doctor_name="Robert Vance",
            hospital="Cardiometabolic Center",
            page_number=2,
            content="""
            ASSESSMENT AND PLAN:
            Patient presents for routine follow-up of Type 2 Diabetes Mellitus and Essential Hypertension.
            Vitals: Blood Pressure: 142/88 mmHg. Pulse: 74 bpm.
            Assessment: Blood pressure remains sub-optimally controlled. Glycemic control elevated.
            Plan:
            - Continue current medications.
            - Repeat HbA1c in 3 months.
            - Schedule Cardiology follow-up in 6 months for echocardiogram review.
            """,
        ),
    ]


def test_doctor_consultation_summary_generation(service, sample_patient_records):
    """
    Test full doctor consultation briefing generation with all 5 core sections
    and citation grounding.
    """
    req = DoctorSummaryRequest(
        patient_id="PATIENT-8801",
        patient_name="Eleanor Vance",
        records=sample_patient_records,
    )

    resp = service.generate_summary(req)

    assert resp.patient_id == "PATIENT-8801"
    assert resp.patient_name == "Eleanor Vance"

    # 1. Check Current Conditions
    condition_names = {c.name for c in resp.current_conditions}
    assert "Type 2 Diabetes Mellitus" in condition_names
    assert "Essential Hypertension" in condition_names

    # 2. Check Abnormal Findings
    abnormal_names = {a.test_name for a in resp.abnormal_findings}
    assert "HbA1c" in abnormal_names
    assert "Fasting Blood Glucose" in abnormal_names
    assert "Total Cholesterol" in abnormal_names
    assert "LDL Cholesterol" in abnormal_names
    assert "Blood Pressure" in abnormal_names

    hba1c_ab = next(a for a in resp.abnormal_findings if a.test_name == "HbA1c")
    assert hba1c_ab.value == 8.2
    assert hba1c_ab.unit == "%"
    assert "Elevated" in hba1c_ab.clinical_interpretation
    assert hba1c_ab.citation.report_name == "Comprehensive Metabolic Lab"

    # 3. Check Recent Reports (sorted newest first)
    assert len(resp.recent_reports) == 3
    assert resp.recent_reports[0].report_date == "2026-06-20"
    assert resp.recent_reports[1].report_date == "2026-06-16"
    assert resp.recent_reports[2].report_date == "2026-06-15"

    # 4. Check Current Medications
    med_names = {m.drug_name for m in resp.current_medications}
    assert "Metformin" in med_names
    assert "Lisinopril" in med_names
    assert "Atorvastatin" in med_names

    # 5. Check Upcoming Followups
    assert len(resp.upcoming_followups) > 0
    followup_texts = " ".join([f.instructions for f in resp.upcoming_followups])
    assert "3 months" in followup_texts or "Cardiology" in followup_texts

    # 6. Check Questions To Discuss With Physician
    assert len(resp.questions_to_discuss) >= 3
    questions_str = " ".join(resp.questions_to_discuss)
    assert "HbA1c" in questions_str
    assert "Blood pressure" in questions_str or "blood pressure" in questions_str

    # 7. Check Exact Formatted Markdown Structure
    md = resp.formatted_markdown
    assert "Patient Summary" in md
    assert "Abnormal Findings" in md
    assert "Recent Reports" in md
    assert "Current Medications" in md
    assert "Questions To Discuss With Physician" in md

    # Check that citations appear in the markdown output
    assert "[Source: Comprehensive Metabolic Lab" in md
    assert "[Source: Ambulatory Prescription Slip" in md
    assert "[Source: Cardiology Progress Note" in md

    # 8. Check Verified Citations
    assert len(resp.citations) >= 3
    for c in resp.citations:
        assert c.report_name is not None
        assert c.page_number >= 1
        assert c.report_date is not None


def test_sparse_records_graceful_summary(service):
    """
    Test sparse record with no abnormal findings or prescriptions.
    Must output clear negative statements without hallucinating drugs or conditions.
    """
    sparse_records = [
        PatientRecordInput(
            document_id="DOC-WELL-001",
            report_name="Annual Wellness Exam",
            report_date="2026-05-10",
            category="CLINICAL_NOTE",
            content="Patient presents for routine preventive checkup. No acute complaints. Vital signs normal.",
            page_number=1,
        )
    ]

    req = DoctorSummaryRequest(
        patient_id="PATIENT-SPARSE",
        records=sparse_records,
    )

    resp = service.generate_summary(req)
    assert len(resp.abnormal_findings) == 0
    assert len(resp.current_medications) == 0

    md = resp.formatted_markdown
    assert "No abnormal lab values documented" in md
    assert "No active prescription medications documented" in md
    assert "Questions To Discuss With Physician" in md


def test_fastapi_rest_doctor_summary_endpoints(client, sample_patient_records):
    """
    Test FastAPI REST endpoints for generating consultation briefing.
    """
    # 1. GET /health
    r_health = client.get("/api/v1/doctor-summary/health")
    assert r_health.status_code == 200
    assert r_health.json()["status"] == "healthy"

    # 2. POST /generate
    payload = {
        "patient_id": "PATIENT-REST-99",
        "patient_name": "Eleanor Vance",
        "records": [rec.model_dump() for rec in sample_patient_records],
    }

    r_gen = client.post("/api/v1/doctor-summary/generate", json=payload)
    assert r_gen.status_code == 200
    data = r_gen.json()
    assert data["patient_id"] == "PATIENT-REST-99"
    assert "Patient Summary" in data["formatted_markdown"]
    assert "Abnormal Findings" in data["formatted_markdown"]
    assert "Questions To Discuss With Physician" in data["formatted_markdown"]
    assert len(data["abnormal_findings"]) >= 3
    assert len(data["citations"]) >= 3
