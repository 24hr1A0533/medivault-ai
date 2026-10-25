"""
Comprehensive Test Suite for Patient-Specific RAG LLM System
Verifies:
1. Strict Multi-User Tenant Isolation (Cross-patient leakage prevention)
2. Negative Constraint Fallback ("I could not find that information in your medical records.")
3. Mandatory Citations (Report Name, Page Number, Report Date)
4. Feature 1: Explain Report
5. Feature 2: Summarize Reports
6. Feature 3: Compare Reports
7. Feature 4: Medical Timeline Generation
8. Feature 5: Doctor Visit Summary
9. FastAPI REST API Endpoints
"""

import pytest
from fastapi.testclient import TestClient

from medivault_patient_rag.schemas import (
    RAGFeature,
    IngestDocumentRequest,
    PatientRAGQueryRequest,
    PatientRAGResponse,
)
from medivault_patient_rag.service import PatientRAGService, SecurityIsolationError
from medivault_patient_rag.main import app


# ==============================================================================
# 1. Multi-User Tenant Isolation Tests
# ==============================================================================

def test_strict_multi_user_isolation(tmp_path):
    """
    Guarantees that Patient A can never see Patient B's medical records under any prompt.
    """
    service = PatientRAGService(vector_store_dir=str(tmp_path))

    # Ingest private record for Patient Alice
    alice_doc = IngestDocumentRequest(
        patient_id="PAT_ALICE",
        document_id="doc_alice_endocrine",
        report_name="Diabetes & Endocrine Evaluation",
        report_date="2026-05-10",
        pages=[
            {
                "page_number": 1,
                "text": "Diagnosis: Type 2 Diabetes Mellitus. Fasting Glucose: 165 mg/dL. Rx: Metformin 1000mg BD.",
            }
        ],
    )
    service.ingest_document(alice_doc)

    # Ingest private record for Patient Bob
    bob_doc = IngestDocumentRequest(
        patient_id="PAT_BOB",
        document_id="doc_bob_cardiology",
        report_name="Cardiovascular Assessment",
        report_date="2026-06-20",
        pages=[
            {
                "page_number": 1,
                "text": "Diagnosis: Essential Hypertension. BP: 145/95 mmHg. Rx: Lisinopril 10mg OD.",
            }
        ],
    )
    service.ingest_document(bob_doc)

    # 1. Bob queries for diabetes medication (which belongs to Alice)
    bob_query = PatientRAGQueryRequest(
        patient_id="PAT_BOB",
        query="What is my diabetes medication and fasting glucose?",
        feature=RAGFeature.GENERAL_QUERY,
    )
    bob_res = service.query(bob_query)

    # MUST NOT leak Alice's Metformin or Fasting Glucose
    assert "Metformin" not in bob_res.answer
    assert "165" not in bob_res.answer
    assert bob_res.answer == "I could not find that information in your medical records."
    assert len(bob_res.citations) == 0
    assert bob_res.grounded is False

    # 2. Alice queries her own records
    alice_query = PatientRAGQueryRequest(
        patient_id="PAT_ALICE",
        query="What is my diabetes medication and dosage?",
        feature=RAGFeature.GENERAL_QUERY,
    )
    alice_res = service.query(alice_query)
    assert "Metformin" in alice_res.answer
    assert len(alice_res.citations) >= 1
    assert alice_res.citations[0].report_name == "Diabetes & Endocrine Evaluation"
    assert alice_res.citations[0].page_number == 1
    assert alice_res.citations[0].report_date == "2026-05-10"

    # 3. Query without valid patient_id raises SecurityIsolationError
    with pytest.raises(SecurityIsolationError):
        service.query(PatientRAGQueryRequest(patient_id="", query="What are my records?"))


# ==============================================================================
# 2. Hallucination Prevention & Missing Information Fallback
# ==============================================================================

def test_hallucination_prevention_fallback(tmp_path):
    """
    Verifies that asking about unrecorded tests strictly outputs:
    'I could not find that information in your medical records.'
    """
    service = PatientRAGService(vector_store_dir=str(tmp_path))

    doc = IngestDocumentRequest(
        patient_id="PAT_CHARLIE",
        document_id="doc_charlie_01",
        report_name="Routine Blood Panel",
        report_date="2026-08-15",
        pages=[
            {
                "page_number": 1,
                "text": "Hemoglobin: 14.5 g/dL. Platelets: 250,000 /uL. White Blood Cells: 6,500 /uL.",
            }
        ],
    )
    service.ingest_document(doc)

    # Ask for unrecorded brain MRI
    req = PatientRAGQueryRequest(
        patient_id="PAT_CHARLIE",
        query="What did my brain MRI and lumbar puncture scan show?",
        feature=RAGFeature.GENERAL_QUERY,
    )
    res = service.query(req)
    assert res.answer == "I could not find that information in your medical records."
    assert len(res.citations) == 0


# ==============================================================================
# 3. Feature 1: Explain Report
# ==============================================================================

def test_feature_explain_report(tmp_path):
    """Verifies Explain Report feature with clinical markers and citations."""
    service = PatientRAGService(vector_store_dir=str(tmp_path))

    doc = IngestDocumentRequest(
        patient_id="PAT_DAVID",
        document_id="doc_david_lipid",
        report_name="Lipid Profile Analysis",
        report_date="2026-09-10",
        pages=[
            {
                "page_number": 1,
                "text": "Total Cholesterol: 245 mg/dL (Ref: < 200). LDL: 160 mg/dL (Ref: < 100). Triglycerides: 210 mg/dL.",
            }
        ],
    )
    service.ingest_document(doc)

    res = service.explain_report(patient_id="PAT_DAVID", document_id="doc_david_lipid")
    assert res.grounded is True
    assert "Lipid Profile Analysis" in res.answer
    assert "2026-09-10" in res.answer
    assert "Page 1" in res.answer
    assert len(res.citations) == 1
    assert res.citations[0].report_name == "Lipid Profile Analysis"
    assert res.citations[0].page_number == 1
    assert res.citations[0].report_date == "2026-09-10"


# ==============================================================================
# 4. Feature 2: Summarize Reports
# ==============================================================================

def test_feature_summarize_reports(tmp_path):
    """Verifies Summarize Reports across multiple multi-page reports."""
    service = PatientRAGService(vector_store_dir=str(tmp_path))

    doc1 = IngestDocumentRequest(
        patient_id="PAT_EMMA",
        document_id="doc_emma_cbc",
        report_name="Complete Blood Count",
        report_date="2026-04-12",
        pages=[{"page_number": 1, "text": "Hemoglobin: 11.2 g/dL (Mild Anemia). WBC: 7,100 /uL."}],
    )
    doc2 = IngestDocumentRequest(
        patient_id="PAT_EMMA",
        document_id="doc_emma_iron",
        report_name="Iron Studies Panel",
        report_date="2026-04-18",
        pages=[{"page_number": 2, "text": "Serum Ferritin: 15 ng/mL (Low). Rx: Ferrous Sulfate 325mg OD."}],
    )
    service.ingest_document(doc1)
    service.ingest_document(doc2)

    res = service.summarize_reports(patient_id="PAT_EMMA")
    assert res.grounded is True
    assert res.source_documents_count >= 2
    assert "Complete Blood Count" in res.answer
    assert "Iron Studies Panel" in res.answer
    assert len(res.citations) >= 2


# ==============================================================================
# 5. Feature 3: Compare Reports
# ==============================================================================

def test_feature_compare_reports(tmp_path):
    """Verifies longitudinal comparison between baseline and follow-up lab tests."""
    service = PatientRAGService(vector_store_dir=str(tmp_path))

    baseline = IngestDocumentRequest(
        patient_id="PAT_FRANK",
        document_id="doc_frank_base",
        report_name="Glycemic Control Panel",
        report_date="2026-01-15",
        pages=[{"page_number": 1, "text": "Baseline HbA1c: 8.4%. Fasting Blood Glucose: 172 mg/dL."}],
    )
    followup = IngestDocumentRequest(
        patient_id="PAT_FRANK",
        document_id="doc_frank_follow",
        report_name="Glycemic Follow-Up Panel",
        report_date="2026-07-20",
        pages=[{"page_number": 1, "text": "Follow-Up HbA1c: 6.9%. Fasting Blood Glucose: 118 mg/dL."}],
    )
    service.ingest_document(baseline)
    service.ingest_document(followup)

    res = service.compare_reports(
        patient_id="PAT_FRANK",
        document_ids=["doc_frank_base", "doc_frank_follow"],
    )
    assert res.grounded is True
    assert "Comparative Medical Report Analysis" in res.answer
    assert "8.4%" in res.answer or "HbA1c" in res.answer
    assert "6.9%" in res.answer or "118" in res.answer
    assert len(res.citations) == 2


# ==============================================================================
# 6. Feature 4: Medical Timeline Generation
# ==============================================================================

def test_feature_medical_timeline(tmp_path):
    """Verifies chronological medical timeline generation with dates and sources."""
    service = PatientRAGService(vector_store_dir=str(tmp_path))

    ev1 = IngestDocumentRequest(
        patient_id="PAT_GRACE",
        document_id="doc_grace_01",
        report_name="Urgent Care Encounter",
        report_date="2026-02-10",
        pages=[{"page_number": 1, "text": "Chief Complaint: Acute bronchitis. Rx: Azithromycin 250mg."}],
    )
    ev2 = IngestDocumentRequest(
        patient_id="PAT_GRACE",
        document_id="doc_grace_02",
        report_name="Pulmonology Follow-Up",
        report_date="2026-03-05",
        pages=[{"page_number": 1, "text": "Spirometry: Normal FEV1/FVC ratio. Lungs clear."}],
    )
    service.ingest_document(ev1)
    service.ingest_document(ev2)

    res = service.generate_medical_timeline(patient_id="PAT_GRACE")
    assert res.grounded is True
    assert "Chronological Health Timeline" in res.answer
    assert "2026-02-10" in res.answer
    assert "2026-03-05" in res.answer
    assert len(res.citations) >= 2


# ==============================================================================
# 7. Feature 5: Doctor Visit Summary
# ==============================================================================

def test_feature_doctor_visit_summary(tmp_path):
    """Verifies pre-consultation executive summary for physician visits."""
    service = PatientRAGService(vector_store_dir=str(tmp_path))

    doc = IngestDocumentRequest(
        patient_id="PAT_HENRY",
        document_id="doc_henry_eval",
        report_name="Annual Comprehensive Health Evaluation",
        report_date="2026-10-01",
        pages=[
            {
                "page_number": 1,
                "text": "BP: 138/88 mmHg. HbA1c: 6.2%. Rx: Metformin 500mg OD. Patient reports occasional fatigue.",
            }
        ],
    )
    service.ingest_document(doc)

    res = service.generate_doctor_visit_summary(patient_id="PAT_HENRY")
    assert res.grounded is True
    assert "Doctor Visit Consultation Summary" in res.answer
    assert "Annual Comprehensive Health Evaluation" in res.answer
    assert "2026-10-01" in res.answer
    assert len(res.citations) >= 1


# ==============================================================================
# 8. FastAPI REST API Endpoint Tests
# ==============================================================================

def test_api_rest_patient_rag_endpoints():
    client = TestClient(app)

    # 1. Health Probe
    health_resp = client.get("/api/v1/patient-rag/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["multi_tenant_isolation"] == "ENFORCED"

    # 2. Ingest Document via API
    ingest_payload = {
        "patient_id": "PAT_REST_100",
        "document_id": "doc_rest_cbc",
        "report_name": "REST Complete Blood Count",
        "report_date": "2026-10-15",
        "category": "LAB_REPORT",
        "pages": [
            {
                "page_number": 1,
                "text": "Hemoglobin: 15.0 g/dL. Platelets: 280,000 /uL. Fasting Blood Glucose: 95 mg/dL.",
            }
        ],
    }
    ing_resp = client.post("/api/v1/patient-rag/ingest", json=ingest_payload)
    assert ing_resp.status_code == 201
    assert ing_resp.json()["chunks_indexed"] >= 1

    # 3. Query via API
    query_payload = {
        "patient_id": "PAT_REST_100",
        "query": "What is my hemoglobin level?",
        "feature": "GENERAL_QUERY",
    }
    q_resp = client.post("/api/v1/patient-rag/query", json=query_payload)
    assert q_resp.status_code == 200
    q_data = q_resp.json()
    assert "15.0" in q_data["answer"]
    assert q_data["grounded"] is True
    assert len(q_data["citations"]) >= 1
    assert q_data["citations"][0]["report_name"] == "REST Complete Blood Count"
    assert q_data["citations"][0]["page_number"] == 1
    assert q_data["citations"][0]["report_date"] == "2026-10-15"

    # 4. Feature Endpoint: Explain
    exp_resp = client.post("/api/v1/patient-rag/explain?patient_id=PAT_REST_100&document_id=doc_rest_cbc")
    assert exp_resp.status_code == 200
    assert "Explanation of REST Complete Blood Count" in exp_resp.json()["answer"]

    # 5. Missing Info Fallback via API
    missing_resp = client.post(
        "/api/v1/patient-rag/query",
        json={
            "patient_id": "PAT_REST_100",
            "query": "What was my brain MRI spinal tap result?",
            "feature": "GENERAL_QUERY",
        },
    )
    assert missing_resp.status_code == 200
    assert missing_resp.json()["answer"] == "I could not find that information in your medical records."
